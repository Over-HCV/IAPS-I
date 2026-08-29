"""
Tabular dataset utilities - scanning, task inference, and feature preprocessing

Deliberately free of Streamlit imports: the training worker runs these in a
background thread where st.session_state does not exist.
"""

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    MinMaxScaler,
    OneHotEncoder,
    OrdinalEncoder,
    StandardScaler,
)

CLASSIFICATION = "classification"
REGRESSION = "regression"

# A numeric target with at most this many distinct whole-number values reads as
# a set of labels rather than a quantity.
MAX_DISCRETE_TARGET_VALUES = 20

SCALING_OPTIONS = ["Standard", "MinMax", "None"]
ENCODING_OPTIONS = ["One-hot", "Ordinal"]
MISSING_OPTIONS = ["Fill (median / most frequent)", "Drop rows"]


def load_dataframe(csv_path: Path) -> pd.DataFrame:
    """Read a CSV into a DataFrame"""
    return pd.read_csv(csv_path)


def infer_task(series: pd.Series) -> str:
    """Guess whether a column is a set of labels or a quantity.

    Non-numeric columns are always labels. A numeric column counts as labels
    only when it holds few distinct whole numbers.
    """
    if not pd.api.types.is_numeric_dtype(series) or pd.api.types.is_bool_dtype(series):
        return CLASSIFICATION

    values = series.dropna()
    if values.empty:
        return CLASSIFICATION

    if values.nunique() > MAX_DISCRETE_TARGET_VALUES:
        return REGRESSION

    is_whole = np.all(np.equal(np.mod(values.to_numpy(dtype=float), 1), 0))
    return CLASSIFICATION if is_whole else REGRESSION


def class_labels(series: pd.Series) -> list[str]:
    """Sorted class labels of a target column, as strings.

    Labels are strings everywhere downstream so they survive the JSON round trip
    through the session file.
    """
    return sorted(str(value) for value in series.dropna().unique())


def scan_tabular_dataset(csv_path: Path, target_column: str) -> dict[str, Any]:
    """Scan a CSV into the same dataset_info shape the image scanner returns.

    Matching the shape is what lets the Overview & Split and Class Distribution
    tabs render a CSV with no changes of their own.
    """
    dataset_info: dict[str, Any] = {
        "samples": {},
        "classes": [],
        "total_samples": 0,
        "sample_paths": {},  # image-only; kept so the shape stays identical
        "columns": [],
        "target_column": target_column,
        "task": CLASSIFICATION,
    }

    if not csv_path.is_file():
        return dataset_info

    try:
        frame = load_dataframe(csv_path)
    except Exception:
        return dataset_info

    dataset_info["columns"] = list(frame.columns)
    dataset_info["total_samples"] = len(frame)

    if target_column not in frame.columns:
        return dataset_info

    target = frame[target_column]
    dataset_info["task"] = infer_task(target)

    if dataset_info["task"] == CLASSIFICATION:
        counts = target.dropna().astype(str).value_counts()
        dataset_info["samples"] = {str(k): int(v) for k, v in counts.items()}
        dataset_info["classes"] = sorted(dataset_info["samples"])

    return dataset_info


def split_column_types(
    frame: pd.DataFrame, feature_columns: list[str]
) -> tuple[list[str], list[str]]:
    """Partition feature columns into (numeric, categorical)"""
    numeric = [
        column
        for column in feature_columns
        if pd.api.types.is_numeric_dtype(frame[column])
        and not pd.api.types.is_bool_dtype(frame[column])
    ]
    categorical = [column for column in feature_columns if column not in numeric]

    return numeric, categorical


def build_preprocessor(
    frame: pd.DataFrame,
    feature_columns: list[str],
    scaling: str,
    encoding: str,
) -> ColumnTransformer:
    """Build the feature transformer for a tabular dataset.

    The caller fits this. See fit_preprocessor for which parts may see which
    rows - that distinction is the whole point.
    """
    numeric, categorical = split_column_types(frame, feature_columns)

    scalers = {"Standard": StandardScaler, "MinMax": MinMaxScaler}
    numeric_steps: list[tuple[str, Any]] = [
        ("impute", SimpleImputer(strategy="median"))
    ]
    if scaling in scalers:
        numeric_steps.append(("scale", scalers[scaling]()))

    if encoding == "Ordinal":
        encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    else:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)

    categorical_steps = [
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("encode", encoder),
    ]

    return ColumnTransformer(
        transformers=[
            ("numeric", Pipeline(numeric_steps), numeric),
            ("categorical", Pipeline(categorical_steps), categorical),
        ],
        remainder="drop",
    )


def fit_preprocessor(
    preprocessor: ColumnTransformer,
    full_frame: pd.DataFrame,
    train_frame: pd.DataFrame,
) -> ColumnTransformer:
    """Fit the transformer, keeping statistics out of the validation and test rows.

    Two different things are being learned here and they have different rules:

      - The *category vocabulary* is schema, not knowledge about the data. It is
        fitted on every selected row so the encoded width is deterministic - the
        input_dim stored when the dataset config is saved has to equal the width
        produced later at training time, or the model will not accept its input.
      - The *statistics* (imputer medians, scaler mean and variance) are learned
        from the training rows only. Fitting those on all rows leaks the test set
        into training, which would quietly inflate every metric the app reports.
    """
    preprocessor.fit(full_frame)

    for name, fitted_pipeline, columns in preprocessor.transformers_:
        if name != "numeric" or not columns:
            continue

        # Refit only the numeric statistics against the training rows.
        fitted_pipeline.fit(train_frame[columns])

    return preprocessor


def feature_matrix_width(
    frame: pd.DataFrame,
    feature_columns: list[str],
    scaling: str,
    encoding: str,
) -> int:
    """Encoded feature count, for reporting and for the model's input_dim"""
    if not feature_columns:
        return 0

    preprocessor = build_preprocessor(frame, feature_columns, scaling, encoding)
    transformed = preprocessor.fit_transform(frame)

    return int(np.asarray(transformed).shape[1])
