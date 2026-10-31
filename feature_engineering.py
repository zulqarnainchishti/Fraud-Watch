from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit
from pyspark.ml.feature import StringIndexer

# 1. Initialize Spark Session
spark = SparkSession.builder \
    .appName("IEEE-CIS-Feature-Engineering") \
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

print("=== Spark Session Initialized for Feature Engineering ===")

# 2. Load Processed Parquet Data from HDFS
input_path = "hdfs://localhost:9000/processed-data/merged_data.parquet"
print(f"Loading merged dataset from HDFS: {input_path}")
df = spark.read.parquet(input_path)

initial_cols = len(df.columns)
initial_rows = df.count()
print(f"Loaded rows: {initial_rows:,}, columns: {initial_cols}")

# 3. Handle Missing Values (Drop columns with extremely high null ratios, e.g., > 80%)
print("Analyzing and dropping highly sparse columns...")
null_threshold = 0.8 * initial_rows
sparse_cols = []
for c in df.columns:
    null_count = df.filter(col(c).isNull()).count()
    if null_count > null_threshold:
        sparse_cols.append(c)

print(f"Dropping {len(sparse_cols)} columns with >80% missing values.")
df_cleaned = df.drop(*sparse_cols)

# 4. Temporal Feature Engineering (`TransactionDT`)
# TransactionDT is seconds from a reference time. 
# We can extract Hour of the Day: (TransactionDT / 3600) % 24
# and Day of the Week approximation: (TransactionDT / 86400) % 7
print("Extracting temporal features from TransactionDT...")
df_engineered = df_cleaned \
    .withColumn("TransactionHour", ((col("TransactionDT") / 3600) % 24).cast("int")) \
    .withColumn("TransactionDayOfWeek", ((col("TransactionDT") / 86400) % 7).cast("int"))

# 5. Basic Categorical Encoding for Key Fields
# Let's handle a few critical categorical features (e.g., ProductCD, card6) using StringIndexer
categorical_cols = ["ProductCD", "card6"]
for c in categorical_cols:
    if c in df_engineered.columns:
        print(f"Encoding categorical column: {c}")
        indexer = StringIndexer(inputCol=c, outputCol=f"{c}_encoded", handleInvalid="keep")
        df_engineered = indexer.fit(df_engineered).transform(df_engineered)

# 6. Save Engineered Data back to HDFS
output_path = "hdfs://localhost:9000/processed-data/engineered_data.parquet"
print(f"Saving engineered dataset to HDFS at {output_path}...")
df_engineered.write.mode("overwrite").parquet(output_path)

print("=== Feature Engineering Pipeline Completed Successfully ===")
print(f"Final columns remaining: {len(df_engineered.columns)}")

spark.stop()