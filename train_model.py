from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier

# 1. Initialize Spark Session with strict memory limits
spark = SparkSession.builder \
    .appName("IEEE-CIS-RandomForest-Training") \
    .master("local[*]") \
    .config("spark.driver.memory", "3g") \
    .config("spark.executor.memory", "3g") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

print("=== Spark Session Initialized (Ultra-Optimized for Codespaces) ===")

# 2. Load Engineered Parquet Data from HDFS
input_path = "hdfs://localhost:9000/processed-data/engineered_data.parquet"
print(f"Loading engineered dataset from HDFS: {input_path}")
df = spark.read.parquet(input_path)

# 3. Apply 10% Stratified Sampling to guarantee memory safety
print("Applying stratified sampling (10% subset)...")
fractions = {0.0: 0.10, 1.0: 0.10}
df_sampled = df.sampleBy("isFraud", fractions, seed=42)

# 4. Select a concise set of 30 numeric features
drop_cols = ["TransactionID", "TransactionDT"]
numeric_types = ["double", "float", "int", "bigint", "integer", "long"]

all_numeric_cols = [
    c for c, dtype in df_sampled.dtypes 
    if c not in drop_cols and c != "isFraud" and dtype in numeric_types
]

feature_cols = all_numeric_cols[:30] # Top 30 features
print(f"Selected {len(feature_cols)} numeric features for training.")

# Fill missing/null values with 0
df_filled = df_sampled.na.fill(0, subset=feature_cols)

# Ensure label column is named correctly and cast to double
df_model_ready = df_filled.withColumn("label", col("isFraud").cast("double"))

# 5. Handle Class Imbalance via Weight Column
total_count = df_model_ready.count()
fraud_count = df_model_ready.filter(col("label") == 1.0).count()
legit_count = total_count - fraud_count

weight_fraud = total_count / (2.0 * fraud_count)
weight_legit = total_count / (2.0 * legit_count)

df_weighted = df_model_ready.withColumn(
    "classWeight",
    when(col("label") == 1.0, weight_fraud).otherwise(weight_legit)
)

# 6. Assemble Features
assembler = VectorAssembler(
    inputCols=feature_cols,
    outputCol="features",
    handleInvalid="skip"
)
df_assembled = assembler.transform(df_weighted)

# 7. Train/Test Split (80% Training, 20% Testing)
train_data, test_data = df_assembled.randomSplit([0.8, 0.2], seed=42)

# 8. Train Lightweight Random Forest Classifier
print("Training Random Forest Classifier...")
rf = RandomForestClassifier(
    labelCol="label",
    featuresCol="features",
    weightCol="classWeight",
    numTrees=10,       # Fast and memory-efficient
    maxDepth=5,        # Shallow depth to prevent JVM exhaustion
    maxBins=16,        # Low bin count for fast splitting
    seed=42
)

rf_model = rf.fit(train_data)
print("=== Model Training Complete Successfully! ===")

# 9. Save Test Predictions for Evaluation Script
print("Saving test predictions for evaluation...")
predictions = rf_model.transform(test_data).select("label", "probability", "prediction")

pred_output_path = "hdfs://localhost:9000/processed-data/rf_predictions.parquet"
predictions.write.mode("overwrite").parquet(pred_output_path)

print("=== Predictions Saved Successfully ===")
spark.stop()