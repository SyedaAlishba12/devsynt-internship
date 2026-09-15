import os
import pandas as pd


def normalize_columns(df):
    df = df.copy()

    normalized_columns = []
    used_names = {}

    for column in df.columns:
        name = str(column).strip().lower()

        name = name.replace(" ", "_")
        name = name.replace("-", "_")
        name = name.replace("/", "_")

        while "__" in name:
            name = name.replace("__", "_")

        name = name.strip("_")

        if not name:
            name = "column"

        if name in used_names:
            used_names[name] += 1
            name = f"{name}_{used_names[name]}"
        else:
            used_names[name] = 0

        normalized_columns.append(name)

    df.columns = normalized_columns

    return df


def infer_data_types(df, date_columns=None):
    df = df.copy()

    date_columns = date_columns or []

    for column in date_columns:
        if column not in df.columns:
            continue

        df[column] = pd.to_datetime(
            df[column],
            errors="coerce",
            format="mixed"
        )

    for column in df.columns:

        if column in date_columns:
            continue

        if pd.api.types.is_numeric_dtype(df[column]):
            continue

        if not (
            pd.api.types.is_object_dtype(df[column])
            or pd.api.types.is_string_dtype(df[column])
        ):
            continue

        series = df[column]

        non_null = series.dropna()

        if len(non_null) == 0:
            continue

        numeric_candidate = pd.to_numeric(
            series,
            errors="coerce"
        )

        conversion_rate = (
            numeric_candidate.notna().sum()
            / len(non_null)
        )

        if conversion_rate >= 0.95:
            df[column] = numeric_candidate

    return df


def handle_missing_values(df):
    df = df.copy()

    missing_before = int(
        df.isna().sum().sum()
    )

    numeric_filled = {}
    text_filled = {}

    for column in df.columns:

        missing_count = int(
            df[column].isna().sum()
        )

        if missing_count == 0:
            continue

        if pd.api.types.is_numeric_dtype(
            df[column]
        ):

            median_value = df[column].median()

            if pd.notna(median_value):
                df[column] = df[column].fillna(
                    median_value
                )

                numeric_filled[column] = (
                    missing_count
                )

        elif pd.api.types.is_datetime64_any_dtype(
            df[column]
        ):

            continue

        else:
            df[column] = df[column].fillna(
                "Unknown"
            )

            text_filled[column] = (
                missing_count
            )

    missing_after = int(
        df.isna().sum().sum()
    )

    return (
        df,
        {
            "missing_before": missing_before,
            "missing_after": missing_after,
            "numeric_values_imputed": numeric_filled,
            "text_values_imputed": text_filled,
        },
    )


def remove_duplicates(df):
    df = df.copy()

    duplicate_count = int(
        df.duplicated().sum()
    )

    if duplicate_count > 0:
        df = df.drop_duplicates()

    return df, duplicate_count


def validate_numeric_values(
    df,
    domain_config=None
):
    df = df.copy()

    invalid_counts = {}

    for column in df.columns:

        if not pd.api.types.is_numeric_dtype(
            df[column]
        ):
            continue

        infinite_mask = df[column].isin(
            [float("inf"), float("-inf")]
        )

        count = int(
            infinite_mask.sum()
        )

        if count > 0:
            invalid_counts[column] = count

            df = df.loc[
                ~infinite_mask
            ].copy()

    return df, invalid_counts


def validate_dates(
    df,
    domain_config=None
):
    df = df.copy()

    date_columns = []

    if domain_config:

        configured_date = domain_config.get(
            "date_column"
        )

        if configured_date:
            date_columns.append(
                configured_date
            )

        configured_dates = domain_config.get(
            "date_columns"
        )

        if configured_dates:
            for column in configured_dates:
                if column not in date_columns:
                    date_columns.append(column)

    invalid_dates = {}

    for column in date_columns:

        if column not in df.columns:
            continue

        if pd.api.types.is_datetime64_any_dtype(
            df[column]
        ):
            invalid_count = int(
                df[column].isna().sum()
            )

            invalid_dates[column] = (
                invalid_count
            )

    return df, {
        "date_column": (
            domain_config.get("date_column")
            if domain_config
            else None
        ),
        "date_columns": date_columns,
        "invalid_or_missing_dates": invalid_dates,
        "invalid_or_missing_dates_total": sum(
            invalid_dates.values()
        ),
    }


def clean_dataset(
    input_path,
    output_path,
    domain_config=None
):
    print("\n" + "=" * 60)
    print("CLEAN AGENT")
    print("=" * 60)

    print(f"\nInput file : {input_path}")
    print(f"Output file: {output_path}")

    print("\n[1] Loading raw dataset...")

    try:
        try:
            df = pd.read_csv(input_path)

        except UnicodeDecodeError:
            print("UTF-8 decoding failed.")
            print("Retrying with latin1 encoding...")

            df = pd.read_csv(
                input_path,
                encoding="latin1"
            )

    except Exception as e:
        print(f"\nDataset loading failed: {e}")

        return None, {
            "status": "failed",
            "error": str(e),
        }

    original_rows = len(df)
    original_columns = len(df.columns)

    print(f"Rows    : {original_rows}")
    print(f"Columns : {original_columns}")

    if df.empty:

        print("\nDataset contains no rows.")

        return None, {
            "status": "failed",
            "error": "Dataset contains no rows.",
            "original_rows": 0,
            "final_rows": 0,
        }

    print("\n[2] Standardizing column names...")

    original_column_names = list(df.columns)

    df = normalize_columns(df)

    print("Column names standardized.")

    print(
        "Columns:",
        ", ".join(df.columns)
    )

    print("\n[3] Inferring data types...")

    date_columns = []

    if domain_config:

        configured_date = domain_config.get(
            "date_column"
        )

        if configured_date:
            date_columns.append(
                configured_date
            )

        configured_dates = domain_config.get(
            "date_columns"
        )

        if configured_dates:
            for column in configured_dates:
                if column not in date_columns:
                    date_columns.append(column)

    df = infer_data_types(
        df,
        date_columns=date_columns
    )

    print("Data type inference complete.")

    if date_columns:
        print(
            "Date columns:",
            ", ".join(date_columns)
        )

    print("\n[4] Handling missing values...")

    (
        df,
        missing_report
    ) = handle_missing_values(df)

    print(
        "Missing values before:",
        missing_report["missing_before"]
    )

    print(
        "Missing values after :",
        missing_report["missing_after"]
    )

    print("\n[5] Checking duplicate rows...")

    (
        df,
        duplicate_count
    ) = remove_duplicates(df)

    print(
        f"Duplicate rows removed: {duplicate_count}"
    )

    print("\n[6] Validating numeric values...")

    (
        df,
        invalid_numeric_values
    ) = validate_numeric_values(
        df,
        domain_config
    )

    invalid_numeric_total = sum(
        invalid_numeric_values.values()
    )

    print(
        "Invalid numeric values removed:",
        invalid_numeric_total
    )

    print("\n[7] Validating date information...")

    (
        df,
        date_report
    ) = validate_dates(
        df,
        domain_config
    )

    if date_report["date_columns"]:

        for column in date_report["date_columns"]:

            print(
                f"{column}:",
                date_report[
                    "invalid_or_missing_dates"
                ].get(column, 0)
            )

    else:

        print("No date columns configured.")

    print("\n[8] Running final dataset checks...")

    final_missing_values = int(
        df.isna().sum().sum()
    )

    final_duplicate_values = int(
        df.duplicated().sum()
    )

    print(
        "Remaining missing values:",
        final_missing_values
    )

    print(
        "Remaining duplicate rows:",
        final_duplicate_values
    )

    print("\n[9] Saving cleaned dataset...")

    output_directory = os.path.dirname(
        output_path
    )

    if output_directory:
        os.makedirs(
            output_directory,
            exist_ok=True
        )

    df.to_csv(
        output_path,
        index=False
    )

    final_rows = len(df)
    final_columns = len(df.columns)

    report = {
        "status": "success",
        "input_file": input_path,
        "output_file": output_path,
        "original_rows": original_rows,
        "final_rows": final_rows,
        "rows_removed": (
            original_rows - final_rows
        ),
        "original_columns": original_columns,
        "final_columns": final_columns,
        "original_column_names": (
            original_column_names
        ),
        "final_column_names": list(
            df.columns
        ),
        "missing_values": missing_report,
        "duplicate_rows_removed": (
            duplicate_count
        ),
        "invalid_numeric_values_removed": (
            invalid_numeric_values
        ),
        "invalid_numeric_total": (
            invalid_numeric_total
        ),
        "date_validation": date_report,
        "remaining_missing_values": (
            final_missing_values
        ),
        "remaining_duplicate_rows": (
            final_duplicate_values
        ),
    }

    print("\n" + "=" * 60)
    print("CLEANING COMPLETE")
    print("=" * 60)

    print(
        f"Original rows       : {original_rows}"
    )

    print(
        f"Final rows          : {final_rows}"
    )

    print(
        f"Rows removed        : "
        f"{original_rows - final_rows}"
    )

    print(
        f"Original columns    : "
        f"{original_columns}"
    )

    print(
        f"Final columns       : "
        f"{final_columns}"
    )

    print(
        f"Missing values left : "
        f"{final_missing_values}"
    )

    print(
        f"Duplicates left     : "
        f"{final_duplicate_values}"
    )

    print(
        "\nCleaned dataset saved to:"
    )

    print(output_path)

    return df, report


if __name__ == "__main__":
    from domain_config_agent import configure_domain

    input_file = (
        "test-datasets/"
        "saas_subscriptions.csv"
    )

    output_file = (
        "test-datasets/"
        "cleaned_saas_subscriptions.csv"
    )

    config = configure_domain(
        input_file
    )

    clean_dataset(
        input_file,
        output_file,
        config
    )