from pyspark.sql import SparkSession
from pyspark.ml.evaluation import BinaryClassificationEvaluator
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.metrics import confusion_matrix, roc_curve, precision_recall_curve

# 1. Initialize Spark Session
spark = SparkSession.builder \
    .appName("IEEE-CIS-Model-Evaluation") \
    .master("local[*]") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

print("=== Loading Predictions for Evaluation ===")
pred_path = "hdfs://localhost:9000/processed-data/rf_predictions.parquet"
df_preds = spark.read.parquet(pred_path)

# 2. Evaluate ROC-AUC via Spark
evaluator = BinaryClassificationEvaluator(labelCol="label", rawPredictionCol="probability", metricName="areaUnderROC")
roc_auc = evaluator.evaluate(df_preds)
print(f"----------------------------------------")
print(f" Test ROC-AUC Score: {roc_auc:.4f}")
print(f"----------------------------------------")

# 3. Convert predictions to Pandas DataFrame for visualization
print("Pulling predictions to Pandas for graph generation...")
pdf = df_preds.select("label", "probability", "prediction").toPandas()

y_true = pdf["label"].values
y_pred = pdf["prediction"].values
y_scores = np.array([p[1] for p in pdf["probability"]])

# 4. Generate Visualizations
sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Graph 1: Confusion Matrix
cm = confusion_matrix(y_true, y_pred)
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=axes[0], cbar=False)
axes[0].set_title("Confusion Matrix")
axes[0].set_xlabel("Predicted Label")
axes[0].set_ylabel("True Label")

# Graph 2: ROC Curve
fpr, tpr, _ = roc_curve(y_true, y_scores)
axes[1].plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC curve (AUC = {roc_auc:.2f})")
axes[1].plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--")
axes[1].set_xlim([0.0, 1.0])
axes[1].set_ylim([0.0, 1.05])
axes[1].set_xlabel("False Positive Rate")
axes[1].set_ylabel("True Positive Rate")
axes[1].set_title("Receiver Operating Characteristic (ROC)")
axes[1].legend(loc="lower right")

# Graph 3: Precision-Recall Curve
precision, recall, _ = precision_recall_curve(y_true, y_scores)
axes[2].plot(recall, precision, color="green", lw=2, label="PR Curve")
axes[2].set_xlabel("Recall")
axes[2].set_ylabel("Precision")
axes[2].set_title("Precision-Recall Curve")
axes[2].legend(loc="upper right")

plt.tight_layout()

output_image = "/workspaces/Fraud-Watch/evaluation_metrics.png"
plt.savefig(output_image, dpi=300)
print(f"Evaluation graphs successfully saved to {output_image}")

spark.stop()