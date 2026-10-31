from pyspark.sql import SparkSession

# 1. Initialize Spark Session configured for Hadoop HDFS
spark = SparkSession.builder \
    .appName("IEEE-CIS-Fraud-Pipeline") \
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

print("=== Spark Session Initialized Successfully ===")

# 2. Define correct HDFS paths (/raw-data)
hdfs_path = "hdfs://localhost:9000/raw-data"
train_trans_path = f"{hdfs_path}/train_transaction.csv"
train_id_path = f"{hdfs_path}/train_identity.csv"

# 3. Load Datasets directly from HDFS
print("Loading transaction and identity datasets from HDFS...")
df_transaction = spark.read.option("header", "true").option("inferSchema", "true").csv(train_trans_path)
df_identity = spark.read.option("header", "true").option("inferSchema", "true").csv(train_id_path)

print(f"Transaction rows: {df_transaction.count():,}")
print(f"Identity rows: {df_identity.count():,}")

# 4. Merge Datasets using TransactionID (Left Join as specified)
print("Merging datasets on TransactionID...")
df_train = df_transaction.join(df_identity, on="TransactionID", how="left")

print(f"Merged dataset rows: {df_train.count():,}")
print(f"Total columns: {len(df_train.columns)}")

# 5. Check target variable distribution (`isFraud`)
print("Target variable distribution (isFraud):")
df_train.groupBy("isFraud").count().show()

# 6. Save the merged dataset back to HDFS as Parquet
output_path = "hdfs://localhost:9000/processed-data/merged_data.parquet"
print(f"Saving merged dataset to HDFS at {output_path}...")
df_train.write.mode("overwrite").parquet(output_path)
print("=== Successfully Saved Merged Dataset to HDFS ===")

spark.stop()