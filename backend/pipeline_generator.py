"""Automatic preprocessing pipeline generation and code export."""

from __future__ import annotations

from typing import Any, Dict, List


def generate_auto_pipeline(report: Dict[str, Any], shape: tuple[int, int]) -> Dict[str, Any]:
    steps: List[Dict[str, str]] = []

    if int(report.get("duplicates", 0)) > 0:
        steps.append({"step": "remove_duplicates", "reason": "duplicate rows detected"})

    if sum(report.get("missing_values", {}).values()) > 0:
        numeric_count = len(report.get("numeric_columns", []))
        if numeric_count >= 2:
            steps.append({"step": "knn_imputation", "reason": "missing values present in multi-feature data"})
        else:
            steps.append({"step": "simple_imputation", "reason": "missing values present"})

    if report.get("type_inconsistencies"):
        steps.append({"step": "fix_column_types", "reason": "data type inconsistencies found"})

    categorical_cols = report.get("categorical_columns", [])
    if categorical_cols:
        high_cardinality = []
        cardinality_map = report.get("categorical_cardinality", {})
        for col in categorical_cols:
            if int(cardinality_map.get(col, 0)) > 20:
                high_cardinality.append(col)

        if high_cardinality:
            steps.append({"step": "frequency_encoding", "reason": "high-cardinality categorical variables found"})

        if len(high_cardinality) < len(categorical_cols):
            steps.append({"step": "one_hot_encoding", "reason": "low-cardinality categorical variables found"})

    if report.get("skewed_features"):
        steps.append({"step": "log_transform", "reason": "skewed numeric distributions detected"})

    if report.get("outliers_detected"):
        steps.append({"step": "isolation_forest_outlier_removal", "reason": "potential outliers detected"})

    if report.get("numeric_columns"):
        steps.append({"step": "standardization", "reason": "numeric features benefit from scaling"})

    rows, cols = shape
    if cols >= 50 or len(report.get("numeric_columns", [])) >= 20:
        steps.append({"step": "pca", "reason": "high-dimensional feature space detected"})

    confidence = min(0.98, 0.60 + len(steps) * 0.05 + (0.05 if rows > 1000 else 0.0))

    return {
        "confidence": round(confidence, 2),
        "steps": steps,
    }


def export_pipeline_as_code(pipeline: Dict[str, Any], export_format: str = "python") -> Dict[str, Any]:
    export_format = (export_format or "python").lower()
    steps = pipeline.get("steps", [])

    if export_format not in {"python", "sklearn", "pyspark"}:
        raise ValueError("Invalid export format. Supported: python, sklearn, pyspark")

    if export_format == "python":
        lines = [
            "import pandas as pd",
            "import numpy as np",
            "from sklearn.impute import KNNImputer",
            "from sklearn.preprocessing import StandardScaler",
            "from sklearn.ensemble import IsolationForest",
            "",
            "# df = pd.read_csv('your_file.csv')",
        ]
        for item in steps:
            step = item.get("step")
            if step == "remove_duplicates":
                lines += ["df = df.drop_duplicates()", ""]
            elif step in {"knn_imputation", "simple_imputation"}:
                lines += [
                    "numeric_cols = df.select_dtypes(include='number').columns",
                    "if len(numeric_cols) > 0:",
                    "    imputer = KNNImputer(n_neighbors=5)",
                    "    df[numeric_cols] = imputer.fit_transform(df[numeric_cols])",
                    "",
                ]
            elif step == "fix_column_types":
                lines += [
                    "for col in df.select_dtypes(include='object').columns:",
                    "    df[col] = pd.to_numeric(df[col], errors='ignore')",
                    "",
                ]
            elif step == "one_hot_encoding":
                lines += [
                    "cat_cols = df.select_dtypes(include=['object', 'category', 'bool']).columns",
                    "df = pd.get_dummies(df, columns=cat_cols, drop_first=False)",
                    "",
                ]
            elif step == "log_transform":
                lines += [
                    "for col in df.select_dtypes(include='number').columns:",
                    "    min_val = df[col].min()",
                    "    shifted = df[col] - min_val + 1 if min_val <= 0 else df[col]",
                    "    df[col] = np.log1p(shifted)",
                    "",
                ]
            elif step == "isolation_forest_outlier_removal":
                lines += [
                    "num_cols = df.select_dtypes(include='number').columns",
                    "if len(num_cols) >= 2:",
                    "    iso = IsolationForest(contamination=0.05, random_state=42)",
                    "    flags = iso.fit_predict(df[num_cols])",
                    "    df = df[flags == 1]",
                    "",
                ]
            elif step == "standardization":
                lines += [
                    "numeric_cols = df.select_dtypes(include='number').columns",
                    "scaler = StandardScaler()",
                    "df[numeric_cols] = scaler.fit_transform(df[numeric_cols])",
                    "",
                ]
            elif step == "pca":
                lines += [
                    "from sklearn.decomposition import PCA",
                    "numeric_cols = df.select_dtypes(include='number').columns",
                    "pca = PCA(n_components=min(10, len(numeric_cols)))",
                    "df_pca = pca.fit_transform(df[numeric_cols])",
                    "",
                ]
        code = "\n".join(lines).strip()

    elif export_format == "sklearn":
        code = "\n".join(
            [
                "from sklearn.pipeline import Pipeline",
                "from sklearn.compose import ColumnTransformer",
                "from sklearn.impute import SimpleImputer, KNNImputer",
                "from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer",
                "from sklearn.decomposition import PCA",
                "from sklearn.ensemble import IsolationForest",
                "",
                "numeric_transformer = Pipeline(steps=[",
                "    ('imputer', KNNImputer(n_neighbors=5)),",
                "    ('scaler', StandardScaler()),",
                "])",
                "",
                "categorical_transformer = Pipeline(steps=[",
                "    ('imputer', SimpleImputer(strategy='most_frequent')),",
                "    ('encoder', OneHotEncoder(handle_unknown='ignore')),",
                "])",
                "",
                "preprocessor = ColumnTransformer(transformers=[",
                "    ('num', numeric_transformer, numeric_cols),",
                "    ('cat', categorical_transformer, categorical_cols),",
                "])",
                "",
                "pipeline = Pipeline(steps=[",
                "    ('preprocessor', preprocessor),",
                "    ('pca', PCA(n_components=10)),",
                "])",
            ]
        )

    else:  # pyspark
        code = "\n".join(
            [
                "from pyspark.sql import SparkSession",
                "from pyspark.sql.functions import col, log1p",
                "from pyspark.ml.feature import VectorAssembler, StandardScaler, OneHotEncoder, StringIndexer, Imputer, PCA",
                "",
                "spark = SparkSession.builder.appName('applydf_pipeline').getOrCreate()",
                "df = spark.read.csv('your_file.csv', header=True, inferSchema=True)",
                "",
                "# Remove duplicates",
                "df = df.dropDuplicates()",
                "",
                "# Missing value imputation",
                "imputer = Imputer(inputCols=numeric_cols, outputCols=numeric_cols)",
                "df = imputer.fit(df).transform(df)",
                "",
                "# Encode categoricals",
                "for c in categorical_cols:",
                "    idx = StringIndexer(inputCol=c, outputCol=f'{c}_idx', handleInvalid='keep')",
                "    df = idx.fit(df).transform(df)",
                "",
                "# Scale numerics",
                "assembler = VectorAssembler(inputCols=numeric_cols, outputCol='features')",
                "df = assembler.transform(df)",
                "scaler = StandardScaler(inputCol='features', outputCol='scaled_features')",
                "df = scaler.fit(df).transform(df)",
            ]
        )

    return {
        "format": export_format,
        "code": code,
        "steps": steps,
    }
