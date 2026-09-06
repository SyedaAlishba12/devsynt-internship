import os
import pandas as pd


def clean_dataset(input_path, output_path):
    """
    Clean the raw Superstore dataset and generate a cleaning report.
    """

    print("\n" + "=" * 60)
    print("CLEAN AGENT")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. Load raw dataset
    # ---------------------------------------------------------
    print("\n[1] Loading raw dataset...")

    df = pd.read_csv(input_path, encoding="latin1")

    original_rows = len(df)
    original_columns = len(df.columns)

    print(f"Rows: {original_rows}")
    print(f"Columns: {original_columns}")

    # ---------------------------------------------------------
    # 2. Standardize column names
    # ---------------------------------------------------------
    print("\n[2] Standardizing column names...")

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    print("Column names standardized.")

    # ---------------------------------------------------------
    # 3. Check missing values
    # ---------------------------------------------------------
    print("\n[3] Checking missing values...")

    missing_before = df.isnull().sum()
    total_missing_before = int(missing_before.sum())

    if total_missing_before == 0:
        print("No missing values found.")
    else:
        print(f"Missing values found: {total_missing_before}")

        # Fill numeric missing values with median
        numeric_columns = df.select_dtypes(include="number").columns

        for column in numeric_columns:
            if df[column].isnull().any():
                df[column] = df[column].fillna(df[column].median())

        # Fill text missing values with "Unknown"
        text_columns = df.select_dtypes(include="object").columns

        for column in text_columns:
            if df[column].isnull().any():
                df[column] = df[column].fillna("Unknown")

    # ---------------------------------------------------------
    # 4. Convert data types
    # ---------------------------------------------------------
    print("\n[4] Correcting data types...")

    if "order_date" in df.columns:
        df["order_date"] = pd.to_datetime(
            df["order_date"],
            errors="coerce"
        )

    if "ship_date" in df.columns:
        df["ship_date"] = pd.to_datetime(
            df["ship_date"],
            errors="coerce"
        )

    numeric_columns = [
        "sales",
        "quantity",
        "discount",
        "profit",
        "postal_code"
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

    print("Data types corrected.")

    # ---------------------------------------------------------
    # 5. Remove duplicate rows
    # ---------------------------------------------------------
    print("\n[5] Checking duplicates...")

    duplicate_count = int(df.duplicated().sum())

    if duplicate_count > 0:
        print(f"Removing {duplicate_count} duplicate rows...")
        df = df.drop_duplicates()
    else:
        print("No duplicate rows found.")

    # ---------------------------------------------------------
    # 6. Remove obviously broken rows
    # ---------------------------------------------------------
    print("\n[6] Checking invalid rows...")

    invalid_rows = 0

    # Sales should not be negative
    if "sales" in df.columns:
        invalid_sales = df["sales"] < 0
        invalid_rows += int(invalid_sales.sum())
        df = df[~invalid_sales]

    # Quantity should be positive
    if "quantity" in df.columns:
        invalid_quantity = df["quantity"] <= 0
        invalid_rows += int(invalid_quantity.sum())
        df = df[~invalid_quantity]

    # Order date should exist after conversion
    if "order_date" in df.columns:
        invalid_dates = df["order_date"].isna()
        invalid_rows += int(invalid_dates.sum())
        df = df[~invalid_dates]

    print(f"Invalid rows removed: {invalid_rows}")

    # ---------------------------------------------------------
    # 7. Save cleaned dataset
    # ---------------------------------------------------------
    print("\n[7] Saving cleaned dataset...")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df.to_csv(output_path, index=False)

    # ---------------------------------------------------------
    # 8. Generate cleaning report
    # ---------------------------------------------------------
    final_rows = len(df)

    report = {
        "original_rows": original_rows,
        "final_rows": final_rows,
        "rows_removed": original_rows - final_rows,
        "original_columns": original_columns,
        "final_columns": len(df.columns),
        "missing_values_found": total_missing_before,
        "duplicate_rows_removed": duplicate_count,
        "invalid_rows_removed": invalid_rows,
    }

    print("\n" + "=" * 60)
    print("CLEANING COMPLETE")
    print("=" * 60)

    print(f"Original rows       : {report['original_rows']}")
    print(f"Final rows          : {report['final_rows']}")
    print(f"Rows removed        : {report['rows_removed']}")
    print(f"Missing values      : {report['missing_values_found']}")
    print(f"Duplicates removed  : {report['duplicate_rows_removed']}")
    print(f"Invalid rows removed: {report['invalid_rows_removed']}")
    print(f"\nCleaned file saved to:")
    print(output_path)

    return df, report


if __name__ == "__main__":
    input_file = "data/Sample - Superstore.csv"
    output_file = "data/cleaned_superstore.csv"

    clean_dataset(input_file, output_file)

