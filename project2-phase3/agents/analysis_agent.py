import json
import os

import pandas as pd
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()


def safe_numeric(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_number(value):
    if value is None:
        return "N/A"

    value = safe_numeric(value)

    if value is None:
        return "N/A"

    return f"{value:,.2f}"


def calculate_ecommerce_metrics(df):
    metrics = {}

    total_records = int(len(df))

    metrics["primary_metric"] = {
        "column": "order_count",
        "total": float(total_records),
        "average": 1.0 if total_records else 0.0,
        "minimum": 1.0 if total_records else 0.0,
        "maximum": 1.0 if total_records else 0.0,
    }

    if "order_id" in df.columns:
        unique_orders = int(
            df["order_id"].nunique()
        )
    else:
        unique_orders = total_records

    metrics["unique_order_count"] = unique_orders

    if "customer_id" in df.columns:
        metrics["unique_customer_count"] = int(
            df["customer_id"].nunique()
        )

    if "order_status" in df.columns:

        status_series = (
            df["order_status"]
            .fillna("Unknown")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        status_counts = (
            status_series.value_counts()
        )

        metrics["status_distribution"] = {
            str(status): int(count)
            for status, count in status_counts.items()
        }

        if total_records > 0:

            delivered_count = int(
                status_counts.get(
                    "delivered",
                    0
                )
            )

            canceled_count = int(
                status_counts.get(
                    "canceled",
                    0
                )
            )

            unavailable_count = int(
                status_counts.get(
                    "unavailable",
                    0
                )
            )

            shipped_count = int(
                status_counts.get(
                    "shipped",
                    0
                )
            )

            processing_count = int(
                status_counts.get(
                    "processing",
                    0
                )
            )

            invoiced_count = int(
                status_counts.get(
                    "invoiced",
                    0
                )
            )

            metrics["delivered_order_count"] = (
                delivered_count
            )

            metrics["canceled_order_count"] = (
                canceled_count
            )

            metrics["unavailable_order_count"] = (
                unavailable_count
            )

            metrics["shipped_order_count"] = (
                shipped_count
            )

            metrics["processing_order_count"] = (
                processing_count
            )

            metrics["invoiced_order_count"] = (
                invoiced_count
            )

            metrics["delivery_completion_rate"] = (
                delivered_count
                / total_records
                * 100
            )

            metrics["cancellation_rate"] = (
                canceled_count
                / total_records
                * 100
            )

            metrics["unavailable_rate"] = (
                unavailable_count
                / total_records
                * 100
            )

    if (
        "order_delivered_customer_date"
        in df.columns
        and "order_purchase_timestamp"
        in df.columns
    ):

        purchase = pd.to_datetime(
            df["order_purchase_timestamp"],
            errors="coerce",
            format="mixed"
        )

        delivered = pd.to_datetime(
            df["order_delivered_customer_date"],
            errors="coerce",
            format="mixed"
        )

        delivery_days = (
            delivered - purchase
        ).dt.total_seconds() / 86400

        valid_delivery_days = delivery_days[
            delivery_days.notna()
            & (delivery_days >= 0)
        ]

        if not valid_delivery_days.empty:

            metrics["delivery_time_days"] = {
                "average": float(
                    valid_delivery_days.mean()
                ),
                "median": float(
                    valid_delivery_days.median()
                ),
                "minimum": float(
                    valid_delivery_days.min()
                ),
                "maximum": float(
                    valid_delivery_days.max()
                ),
                "orders_evaluated": int(
                    len(valid_delivery_days)
                ),
            }

    if (
        "order_delivered_customer_date"
        in df.columns
        and "order_estimated_delivery_date"
        in df.columns
    ):

        actual_delivery = pd.to_datetime(
            df["order_delivered_customer_date"],
            errors="coerce",
            format="mixed"
        )

        estimated_delivery = pd.to_datetime(
            df["order_estimated_delivery_date"],
            errors="coerce",
            format="mixed"
        )

        valid_dates = (
            actual_delivery.notna()
            & estimated_delivery.notna()
        )

        on_time = (
            actual_delivery <= estimated_delivery
        )

        evaluated = on_time[valid_dates]

        if not evaluated.empty:

            on_time_count = int(
                evaluated.sum()
            )

            evaluated_count = int(
                len(evaluated)
            )

            metrics["on_time_delivery_rate"] = (
                on_time_count
                / evaluated_count
                * 100
            )

            metrics["on_time_delivery_count"] = (
                on_time_count
            )

            metrics["late_delivery_count"] = (
                evaluated_count
                - on_time_count
            )

            metrics["delivery_date_evaluated_count"] = (
                evaluated_count
            )

    metrics["record_count"] = total_records

    metrics["unique_id_count"] = unique_orders

    return metrics


def calculate_restaurant_metrics(df):
    metrics = {}

    working_df = df.copy()

    if "price" in working_df.columns:
        working_df["price"] = pd.to_numeric(
            working_df["price"],
            errors="coerce"
        )

    if "quantity" in working_df.columns:
        working_df["quantity"] = pd.to_numeric(
            working_df["quantity"],
            errors="coerce"
        )

    if (
        "price" in working_df.columns
        and "quantity" in working_df.columns
    ):
        working_df["revenue"] = (
            working_df["price"]
            * working_df["quantity"]
        )

    revenue = (
        working_df["revenue"].dropna()
        if "revenue" in working_df.columns
        else pd.Series(dtype=float)
    )

    if not revenue.empty:
        metrics["primary_metric"] = {
            "column": "revenue",
            "total": float(
                revenue.sum()
            ),
            "average": float(
                revenue.mean()
            ),
            "minimum": float(
                revenue.min()
            ),
            "maximum": float(
                revenue.max()
            ),
        }

    if "quantity" in working_df.columns:

        quantity = (
            working_df["quantity"]
            .dropna()
        )

        if not quantity.empty:

            metrics["total_quantity"] = float(
                quantity.sum()
            )

            metrics["average_quantity"] = float(
                quantity.mean()
            )

    if "price" in working_df.columns:

        price = (
            working_df["price"]
            .dropna()
        )

        if not price.empty:

            metrics["average_price"] = float(
                price.mean()
            )

            metrics["minimum_price"] = float(
                price.min()
            )

            metrics["maximum_price"] = float(
                price.max()
            )

    if "order_id" in working_df.columns:

        metrics["unique_order_count"] = int(
            working_df["order_id"].nunique()
        )

    metrics["record_count"] = int(
        len(working_df)
    )

    if "order_id" in working_df.columns:

        metrics["unique_id_count"] = int(
            working_df["order_id"].nunique()
        )

    else:

        metrics["unique_id_count"] = None

    return metrics


def calculate_saas_metrics(df):
    metrics = {}

    total_records = int(len(df))

    numeric_columns = [
        "seats",
        "mrr_amount",
        "arr_amount",
        "is_trial",
        "upgrade_flag",
        "downgrade_flag",
        "churn_flag",
        "auto_renew_flag",
    ]

    working_df = df.copy()

    for column in numeric_columns:

        if column in working_df.columns:

            working_df[column] = pd.to_numeric(
                working_df[column],
                errors="coerce"
            )

    primary_metric = "mrr_amount"

    if primary_metric in working_df.columns:

        series = (
            working_df[primary_metric]
            .dropna()
        )

        if not series.empty:

            metrics["primary_metric"] = {
                "column": primary_metric,
                "total": float(
                    series.sum()
                ),
                "average": float(
                    series.mean()
                ),
                "minimum": float(
                    series.min()
                ),
                "maximum": float(
                    series.max()
                ),
            }

    secondary_metrics = [
        "arr_amount",
        "seats",
    ]

    secondary_results = {}

    for column in secondary_metrics:

        if column not in working_df.columns:
            continue

        series = (
            working_df[column]
            .dropna()
        )

        if series.empty:
            continue

        secondary_results[column] = {
            "total": float(
                series.sum()
            ),
            "average": float(
                series.mean()
            ),
            "minimum": float(
                series.min()
            ),
            "maximum": float(
                series.max()
            ),
        }

    metrics["secondary_metrics"] = (
        secondary_results
    )

    flag_columns = [
        "is_trial",
        "upgrade_flag",
        "downgrade_flag",
        "churn_flag",
        "auto_renew_flag",
    ]

    for column in flag_columns:

        if column not in working_df.columns:
            continue

        series = (
            working_df[column]
            .dropna()
        )

        if series.empty:
            continue

        positive_count = int(
            (series > 0).sum()
        )

        rate = (
            positive_count
            / len(series)
            * 100
        )

        metric_name_map = {
            "is_trial": "trial_rate",
            "upgrade_flag": "upgrade_rate",
            "downgrade_flag": "downgrade_rate",
            "churn_flag": "churn_rate",
            "auto_renew_flag": "auto_renewal_rate",
        }

        metric_name = metric_name_map[column]

        metrics[metric_name] = float(
            rate
        )

        metrics[
            f"{column}_count"
        ] = positive_count

    if "subscription_id" in working_df.columns:

        metrics["unique_subscription_count"] = int(
            working_df["subscription_id"].nunique()
        )

    if "account_id" in working_df.columns:

        metrics["unique_account_count"] = int(
            working_df["account_id"].nunique()
        )

    if (
        "start_date" in working_df.columns
        and "end_date" in working_df.columns
    ):

        start_dates = pd.to_datetime(
            working_df["start_date"],
            errors="coerce",
            format="mixed"
        )

        end_dates = pd.to_datetime(
            working_df["end_date"],
            errors="coerce",
            format="mixed"
        )

        subscription_duration = (
            end_dates - start_dates
        ).dt.total_seconds() / 86400

        valid_duration = subscription_duration[
            subscription_duration.notna()
            & (subscription_duration >= 0)
        ]

        if not valid_duration.empty:

            metrics["subscription_duration_days"] = {
                "average": float(
                    valid_duration.mean()
                ),
                "median": float(
                    valid_duration.median()
                ),
                "minimum": float(
                    valid_duration.min()
                ),
                "maximum": float(
                    valid_duration.max()
                ),
                "subscriptions_evaluated": int(
                    len(valid_duration)
                ),
            }

    metrics["record_count"] = total_records

    if "subscription_id" in working_df.columns:

        metrics["unique_id_count"] = int(
            working_df["subscription_id"].nunique()
        )

    else:

        metrics["unique_id_count"] = None

    return metrics


def calculate_basic_metrics(df, domain_config):
    if domain_config.get(
        "domain"
    ) == "ecommerce_orders":

        return calculate_ecommerce_metrics(
            df
        )

    if domain_config.get(
        "domain"
    ) == "restaurant_sales":

        return calculate_restaurant_metrics(
            df
        )

    if domain_config.get(
        "domain"
    ) == "saas_subscription":

        return calculate_saas_metrics(
            df
        )

    primary_metric = domain_config.get(
        "primary_metric"
    )

    secondary_metrics = domain_config.get(
        "secondary_metrics",
        []
    )

    id_column = domain_config.get(
        "id_column"
    )

    metrics = {}

    if primary_metric in df.columns:

        series = pd.to_numeric(
            df[primary_metric],
            errors="coerce"
        ).dropna()

        if not series.empty:

            metrics["primary_metric"] = {
                "column": primary_metric,
                "total": float(
                    series.sum()
                ),
                "average": float(
                    series.mean()
                ),
                "minimum": float(
                    series.min()
                ),
                "maximum": float(
                    series.max()
                ),
            }

    secondary_results = {}

    for column in secondary_metrics:

        if column not in df.columns:
            continue

        series = pd.to_numeric(
            df[column],
            errors="coerce"
        ).dropna()

        if series.empty:
            continue

        secondary_results[column] = {
            "total": float(
                series.sum()
            ),
            "average": float(
                series.mean()
            ),
            "minimum": float(
                series.min()
            ),
            "maximum": float(
                series.max()
            ),
        }

    metrics["secondary_metrics"] = (
        secondary_results
    )

    metrics["record_count"] = int(
        len(df)
    )

    if (
        id_column
        and id_column in df.columns
    ):

        metrics["unique_id_count"] = int(
            df[id_column].nunique()
        )

    else:

        metrics["unique_id_count"] = None

    return metrics


def analyze_ecommerce_dimensions(df):
    results = {}

    if "order_status" not in df.columns:
        return results

    status_series = (
        df["order_status"]
        .fillna("Unknown")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    status_counts = (
        status_series.value_counts()
    )

    total_orders = len(df)

    top_values = []

    for status, count in status_counts.items():

        percentage = (
            count
            / total_orders
            * 100
            if total_orders
            else 0
        )

        top_values.append(
            {
                "value": str(status),
                "total": float(count),
                "average": 1.0,
                "count": int(count),
                "percentage": float(
                    percentage
                ),
            }
        )

    results["order_status"] = {
        "unique_values": int(
            status_series.nunique()
        ),
        "top_values": top_values,
    }

    return results


def analyze_restaurant_dimensions(df):
    results = {}

    if (
        "price" not in df.columns
        or "quantity" not in df.columns
    ):
        return results

    working_df = df.copy()

    working_df["price"] = pd.to_numeric(
        working_df["price"],
        errors="coerce"
    )

    working_df["quantity"] = pd.to_numeric(
        working_df["quantity"],
        errors="coerce"
    )

    working_df["_analysis_metric"] = (
        working_df["price"]
        * working_df["quantity"]
    )

    dimensions = [
        "product",
        "purchase_type",
        "payment_method",
        "manager",
        "city",
    ]

    for dimension in dimensions:

        if dimension not in working_df.columns:
            continue

        unique_count = working_df[
            dimension
        ].nunique()

        if (
            unique_count < 2
            or unique_count > 100
        ):
            continue

        grouped = (
            working_df
            .dropna(
                subset=[
                    "_analysis_metric"
                ]
            )
            .groupby(
                dimension,
                dropna=False
            )["_analysis_metric"]
            .agg(
                total="sum",
                average="mean",
                count="count"
            )
            .reset_index()
        )

        if grouped.empty:
            continue

        grouped = grouped.sort_values(
            "total",
            ascending=False
        )

        dimension_results = []

        for _, row in grouped.head(10).iterrows():

            dimension_results.append(
                {
                    "value": str(
                        row[dimension]
                    ),
                    "total": float(
                        row["total"]
                    ),
                    "average": float(
                        row["average"]
                    ),
                    "count": int(
                        row["count"]
                    ),
                }
            )

        results[dimension] = {
            "unique_values": int(
                unique_count
            ),
            "top_values": dimension_results,
        }

    return results


def analyze_saas_dimensions(df):
    results = {}

    if "mrr_amount" not in df.columns:
        return results

    working_df = df.copy()

    working_df["mrr_amount"] = pd.to_numeric(
        working_df["mrr_amount"],
        errors="coerce"
    )

    dimensions = [
        "plan_tier",
        "billing_frequency",
    ]

    for dimension in dimensions:

        if dimension not in working_df.columns:
            continue

        unique_count = working_df[
            dimension
        ].nunique()

        if (
            unique_count < 2
            or unique_count > 100
        ):
            continue

        grouped = (
            working_df
            .dropna(
                subset=[
                    "mrr_amount"
                ]
            )
            .groupby(
                dimension,
                dropna=False
            )["mrr_amount"]
            .agg(
                total="sum",
                average="mean",
                count="count"
            )
            .reset_index()
        )

        if grouped.empty:
            continue

        grouped = grouped.sort_values(
            "total",
            ascending=False
        )

        dimension_results = []

        for _, row in grouped.head(10).iterrows():

            dimension_results.append(
                {
                    "value": str(
                        row[dimension]
                    ),
                    "total": float(
                        row["total"]
                    ),
                    "average": float(
                        row["average"]
                    ),
                    "count": int(
                        row["count"]
                    ),
                }
            )

        results[dimension] = {
            "unique_values": int(
                unique_count
            ),
            "top_values": dimension_results,
        }

    return results


def get_analysis_dimensions(
    df,
    domain_config
):
    configured_dimensions = domain_config.get(
        "dimension_columns",
        []
    )

    valid_configured = [
        column
        for column in configured_dimensions
        if column in df.columns
    ]

    if valid_configured:
        return valid_configured

    excluded_columns = {
        domain_config.get("primary_metric"),
        domain_config.get("date_column"),
        domain_config.get("id_column"),
    }

    dimensions = []

    for column in df.columns:

        if column in excluded_columns:
            continue

        column_lower = str(column).lower()

        if (
            column_lower.endswith("_id")
            or column_lower == "id"
            or "identifier" in column_lower
        ):
            continue

        unique_count = df[column].nunique(
            dropna=True
        )

        if (
            unique_count < 2
            or unique_count > 100
        ):
            continue

        if pd.api.types.is_datetime64_any_dtype(
            df[column]
        ):
            continue

        if pd.api.types.is_numeric_dtype(
            df[column]
        ):
            continue

        dimensions.append(column)

    return dimensions


def analyze_dimensions(df, domain_config):
    if domain_config.get(
        "domain"
    ) == "ecommerce_orders":

        return analyze_ecommerce_dimensions(
            df
        )

    if domain_config.get(
        "domain"
    ) == "restaurant_sales":

        return analyze_restaurant_dimensions(
            df
        )

    if domain_config.get(
        "domain"
    ) == "saas_subscription":

        return analyze_saas_dimensions(
            df
        )

    primary_metric = domain_config.get(
        "primary_metric"
    )

    dimensions = get_analysis_dimensions(
        df,
        domain_config
    )
    

    results = {}

    if primary_metric not in df.columns:
        return results

    metric_series = pd.to_numeric(
        df[primary_metric],
        errors="coerce"
    )

    working_df = df.copy()

    working_df["_analysis_metric"] = (
        metric_series
    )

    for dimension in dimensions:

        if dimension not in working_df.columns:
            continue

        unique_count = working_df[
            dimension
        ].nunique()

        if (
            unique_count < 2
            or unique_count > 100
        ):
            continue

        grouped = (
            working_df
            .dropna(
                subset=[
                    "_analysis_metric"
                ]
            )
            .groupby(
                dimension,
                dropna=False
            )["_analysis_metric"]
            .agg(
                total="sum",
                average="mean",
                count="count"
            )
            .reset_index()
        )

        if grouped.empty:
            continue

        grouped = grouped.sort_values(
            "total",
            ascending=False
        )

        top_rows = grouped.head(10)

        dimension_results = []

        for _, row in top_rows.iterrows():

            dimension_results.append(
                {
                    "value": str(
                        row[dimension]
                    ),
                    "total": float(
                        row["total"]
                    ),
                    "average": float(
                        row["average"]
                    ),
                    "count": int(
                        row["count"]
                    ),
                }
            )

        results[dimension] = {
            "unique_values": int(
                unique_count
            ),
            "top_values": dimension_results,
        }

    return results


def analyze_ecommerce_time_trend(
    df,
    domain_config
):
    date_column = domain_config.get(
        "date_column"
    )

    if (
        not date_column
        or date_column not in df.columns
    ):
        return None

    dates = pd.to_datetime(
        df[date_column],
        errors="coerce",
        format="mixed"
    )

    working_df = pd.DataFrame(
        {
            "_date": dates
        }
    ).dropna()

    if working_df.empty:
        return None

    date_range = (
        working_df["_date"].max()
        - working_df["_date"].min()
    ).days

    if date_range <= 31:

        working_df["_period"] = (
            working_df["_date"]
            .dt.to_period("D")
            .astype(str)
        )

    else:

        working_df["_period"] = (
            working_df["_date"]
            .dt.to_period("M")
            .astype(str)
        )

    grouped = (
        working_df
        .groupby("_period")
        .size()
        .reset_index(
            name="order_count"
        )
    )

    trend = []

    for _, row in grouped.iterrows():

        trend.append(
            {
                "period": str(
                    row["_period"]
                ),
                "total": float(
                    row["order_count"]
                ),
                "average": 1.0,
                "count": int(
                    row["order_count"]
                ),
            }
        )

    return {
        "date_column": date_column,
        "metric": "order_count",
        "period_count": len(trend),
        "data": trend,
    }


def analyze_restaurant_time_trend(
    df,
    domain_config
):
    date_column = domain_config.get(
        "date_column"
    )

    if (
        not date_column
        or date_column not in df.columns
    ):
        return None

    if (
        "price" not in df.columns
        or "quantity" not in df.columns
    ):
        return None

    working_df = df.copy()

    working_df[date_column] = pd.to_datetime(
        working_df[date_column],
        errors="coerce",
        format="mixed"
    )

    working_df["price"] = pd.to_numeric(
        working_df["price"],
        errors="coerce"
    )

    working_df["quantity"] = pd.to_numeric(
        working_df["quantity"],
        errors="coerce"
    )

    working_df["revenue"] = (
        working_df["price"]
        * working_df["quantity"]
    )

    working_df = working_df.dropna(
        subset=[
            date_column,
            "revenue"
        ]
    )

    if working_df.empty:
        return None

    date_range = (
        working_df[date_column].max()
        - working_df[date_column].min()
    ).days

    if date_range <= 31:

        working_df["_period"] = (
            working_df[date_column]
            .dt.to_period("D")
            .astype(str)
        )

    else:

        working_df["_period"] = (
            working_df[date_column]
            .dt.to_period("M")
            .astype(str)
        )

    grouped = (
        working_df
        .groupby("_period")["revenue"]
        .agg(
            total="sum",
            average="mean",
            count="count"
        )
        .reset_index()
    )

    trend = []

    for _, row in grouped.iterrows():

        trend.append(
            {
                "period": str(
                    row["_period"]
                ),
                "total": float(
                    row["total"]
                ),
                "average": float(
                    row["average"]
                ),
                "count": int(
                    row["count"]
                ),
            }
        )

    return {
        "date_column": date_column,
        "metric": "revenue",
        "period_count": len(trend),
        "data": trend,
    }


def analyze_saas_time_trend(
    df,
    domain_config
):
    date_column = domain_config.get(
        "date_column"
    )

    if (
        not date_column
        or date_column not in df.columns
    ):
        return None

    if "mrr_amount" not in df.columns:
        return None

    working_df = df.copy()

    working_df[date_column] = pd.to_datetime(
        working_df[date_column],
        errors="coerce",
        format="mixed"
    )

    working_df["mrr_amount"] = pd.to_numeric(
        working_df["mrr_amount"],
        errors="coerce"
    )

    working_df = working_df.dropna(
        subset=[
            date_column,
            "mrr_amount"
        ]
    )

    if working_df.empty:
        return None

    date_range = (
        working_df[date_column].max()
        - working_df[date_column].min()
    ).days

    if date_range <= 31:

        working_df["_period"] = (
            working_df[date_column]
            .dt.to_period("D")
            .astype(str)
        )

    else:

        working_df["_period"] = (
            working_df[date_column]
            .dt.to_period("M")
            .astype(str)
        )

    grouped = (
        working_df
        .groupby("_period")["mrr_amount"]
        .agg(
            total="sum",
            average="mean",
            count="count"
        )
        .reset_index()
    )

    trend = []

    for _, row in grouped.iterrows():

        trend.append(
            {
                "period": str(
                    row["_period"]
                ),
                "total": float(
                    row["total"]
                ),
                "average": float(
                    row["average"]
                ),
                "count": int(
                    row["count"]
                ),
            }
        )

    return {
        "date_column": date_column,
        "metric": "mrr_amount",
        "period_count": len(trend),
        "data": trend,
    }


def analyze_time_trend(
    df,
    domain_config
):
    if domain_config.get(
        "domain"
    ) == "ecommerce_orders":

        return analyze_ecommerce_time_trend(
            df,
            domain_config
        )

    if domain_config.get(
        "domain"
    ) == "restaurant_sales":

        return analyze_restaurant_time_trend(
            df,
            domain_config
        )

    if domain_config.get(
        "domain"
    ) == "saas_subscription":

        return analyze_saas_time_trend(
            df,
            domain_config
        )

    date_column = domain_config.get(
        "date_column"
    )

    primary_metric = domain_config.get(
        "primary_metric"
    )

    if not date_column:
        return None

    if date_column not in df.columns:
        return None

    if primary_metric not in df.columns:
        return None

    working_df = df.copy()

    working_df[date_column] = pd.to_datetime(
        working_df[date_column],
        errors="coerce",
        format="mixed"
    )

    working_df[primary_metric] = pd.to_numeric(
        working_df[primary_metric],
        errors="coerce"
    )

    working_df = working_df.dropna(
        subset=[
            date_column,
            primary_metric
        ]
    )

    if working_df.empty:
        return None

    date_range = (
        working_df[date_column].max()
        - working_df[date_column].min()
    ).days

    if date_range <= 31:

        working_df["_period"] = (
            working_df[date_column]
            .dt.to_period("D")
            .astype(str)
        )

    else:

        working_df["_period"] = (
            working_df[date_column]
            .dt.to_period("M")
            .astype(str)
        )

    grouped = (
        working_df
        .groupby("_period")[primary_metric]
        .agg(
            total="sum",
            average="mean",
            count="count"
        )
        .reset_index()
    )

    trend = []

    for _, row in grouped.iterrows():

        trend.append(
            {
                "period": str(
                    row["_period"]
                ),
                "total": float(
                    row["total"]
                ),
                "average": float(
                    row["average"]
                ),
                "count": int(
                    row["count"]
                ),
            }
        )

    return {
        "date_column": date_column,
        "metric": primary_metric,
        "period_count": len(trend),
        "data": trend,
    }


def identify_performers(
    df,
    domain_config
):
    if domain_config.get(
        "domain"
    ) == "ecommerce_orders":

        if "order_status" not in df.columns:
            return {}

        status_series = (
            df["order_status"]
            .fillna("Unknown")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        counts = (
            status_series
            .value_counts()
            .sort_values(
                ascending=False
            )
        )

        if counts.empty:
            return {}

        top_count = min(
            3,
            len(counts)
        )

        bottom_count = min(
            3,
            max(
                1,
                len(counts) - top_count
            )
        )

        top = counts.head(
            top_count
        )

        bottom = counts.tail(
            bottom_count
        ).sort_values()

        return {
            "order_status": {
                "top": [
                    {
                        "value": str(index),
                        "metric": float(value),
                    }
                    for index, value
                    in top.items()
                ],
                "bottom": [
                    {
                        "value": str(index),
                        "metric": float(value),
                    }
                    for index, value
                    in bottom.items()
                ],
            }
        }

    if domain_config.get(
        "domain"
    ) == "restaurant_sales":

        if (
            "price" not in df.columns
            or "quantity" not in df.columns
        ):
            return {}

        working_df = df.copy()

        working_df["price"] = pd.to_numeric(
            working_df["price"],
            errors="coerce"
        )

        working_df["quantity"] = pd.to_numeric(
            working_df["quantity"],
            errors="coerce"
        )

        working_df["revenue"] = (
            working_df["price"]
            * working_df["quantity"]
        )

        dimensions = [
            "product",
            "purchase_type",
            "payment_method",
            "manager",
            "city",
        ]

        results = {}

        for dimension in dimensions:

            if dimension not in working_df.columns:
                continue

            grouped = (
                working_df
                .dropna(
                    subset=[
                        "revenue"
                    ]
                )
                .groupby(
                    dimension
                )["revenue"]
                .sum()
                .sort_values(
                    ascending=False
                )
            )

            if grouped.empty:
                continue

            top_count = min(
                3,
                len(grouped)
            )

            bottom_count = min(
                3,
                max(
                    1,
                    len(grouped) - top_count
                )
            )

            top = grouped.head(
                top_count
            )

            bottom = grouped.tail(
                bottom_count
            ).sort_values()

            results[dimension] = {
                "top": [
                    {
                        "value": str(index),
                        "metric": float(value),
                    }
                    for index, value
                    in top.items()
                ],
                "bottom": [
                    {
                        "value": str(index),
                        "metric": float(value),
                    }
                    for index, value
                    in bottom.items()
                ],
            }

        return results

    if domain_config.get(
        "domain"
    ) == "saas_subscription":

        if "mrr_amount" not in df.columns:
            return {}

        working_df = df.copy()

        working_df["mrr_amount"] = pd.to_numeric(
            working_df["mrr_amount"],
            errors="coerce"
        )

        dimensions = [
            "plan_tier",
            "billing_frequency",
        ]

        results = {}

        for dimension in dimensions:

            if dimension not in working_df.columns:
                continue

            grouped = (
                working_df
                .dropna(
                    subset=[
                        "mrr_amount"
                    ]
                )
                .groupby(
                    dimension
                )["mrr_amount"]
                .sum()
                .sort_values(
                    ascending=False
                )
            )

            if grouped.empty:
                continue

            top_count = min(
                3,
                len(grouped)
            )

            bottom_count = min(
                3,
                max(
                    1,
                    len(grouped) - top_count
                )
            )

            top = grouped.head(
                top_count
            )

            bottom = grouped.tail(
                bottom_count
            ).sort_values()

            results[dimension] = {
                "top": [
                    {
                        "value": str(index),
                        "metric": float(value),
                    }
                    for index, value
                    in top.items()
                ],
                "bottom": [
                    {
                        "value": str(index),
                        "metric": float(value),
                    }
                    for index, value
                    in bottom.items()
                ],
            }

        return results

    primary_metric = domain_config.get(
        "primary_metric"
    )

    dimensions = get_analysis_dimensions(
        df,
        domain_config
    )

    if primary_metric not in df.columns:
        return {}

    working_df = df.copy()

    working_df[primary_metric] = pd.to_numeric(
        working_df[primary_metric],
        errors="coerce"
    )

    results = {}

    for dimension in dimensions:

        if dimension not in working_df.columns:
            continue

        unique_count = working_df[
            dimension
        ].nunique()

        if (
            unique_count < 2
            or unique_count > 100
        ):
            continue

        grouped = (
            working_df
            .dropna(
                subset=[
                    primary_metric
                ]
            )
            .groupby(
                dimension
            )[primary_metric]
            .sum()
            .sort_values(
                ascending=False
            )
        )

        if grouped.empty:
            continue

        top_count = min(
            3,
            len(grouped)
        )

        bottom_count = min(
            3,
            max(
                1,
                len(grouped) - top_count
            )
        )

        top = grouped.head(
            top_count
        )

        bottom = grouped.tail(
            bottom_count
        ).sort_values()

        results[dimension] = {
            "top": [
                {
                    "value": str(index),
                    "metric": float(value),
                }
                for index, value
                in top.items()
            ],
            "bottom": [
                {
                    "value": str(index),
                    "metric": float(value),
                }
                for index, value
                in bottom.items()
            ],
        }

    return results


def analyze_inventory_risk(
    df,
    domain_config
):
    primary_metric = domain_config.get(
        "primary_metric"
    )

    if primary_metric != "stock_level":
        return None

    required_columns = {
        "stock_level",
        "reorder_point"
    }

    if not required_columns.issubset(
        df.columns
    ):
        return None

    working_df = df.copy()

    working_df["stock_level"] = pd.to_numeric(
        working_df["stock_level"],
        errors="coerce"
    )

    working_df["reorder_point"] = pd.to_numeric(
        working_df["reorder_point"],
        errors="coerce"
    )

    working_df = working_df.dropna(
        subset=[
            "stock_level",
            "reorder_point"
        ]
    )

    if working_df.empty:
        return None

    working_df["_stock_ratio"] = (
        working_df["stock_level"]
        / working_df[
            "reorder_point"
        ].replace(
            0,
            pd.NA
        )
    )

    working_df[
        "_replenishment_needed"
    ] = (
        working_df["stock_level"]
        <= working_df["reorder_point"]
    )

    replenishment_count = int(
        working_df[
            "_replenishment_needed"
        ].sum()
    )

    total_items = int(
        len(working_df)
    )

    replenishment_percentage = (
        replenishment_count
        / total_items
        * 100
    )

    valid_ratios = (
        working_df["_stock_ratio"]
        .replace(
            [
                float("inf"),
                float("-inf")
            ],
            pd.NA
        )
        .dropna()
    )

    risk = {
        "total_items_evaluated": total_items,
        "items_at_or_below_reorder_point": (
            replenishment_count
        ),
        "replenishment_percentage": float(
            replenishment_percentage
        ),
        "average_stock_to_reorder_ratio": (
            float(
                valid_ratios.mean()
            )
            if not valid_ratios.empty
            else None
        ),
    }

    if "item_id" in working_df.columns:

        risk_items = (
            working_df[
                working_df[
                    "_replenishment_needed"
                ]
            ]
            .sort_values(
                [
                    "stock_level",
                    "reorder_point"
                ]
            )
            .head(10)
        )

        risk[
            "items_needing_replenishment"
        ] = [
            {
                "item_id": str(
                    row["item_id"]
                ),
                "stock_level": float(
                    row["stock_level"]
                ),
                "reorder_point": float(
                    row["reorder_point"]
                ),
            }
            for _, row
            in risk_items.iterrows()
        ]

    if "daily_demand" in working_df.columns:

        working_df["daily_demand"] = pd.to_numeric(
            working_df["daily_demand"],
            errors="coerce"
        )

        high_demand = (
            working_df
            .dropna(
                subset=[
                    "daily_demand"
                ]
            )
            .sort_values(
                "daily_demand",
                ascending=False
            )
            .head(10)
        )

        risk[
            "highest_daily_demand_items"
        ] = [
            {
                "item_id": (
                    str(row["item_id"])
                    if "item_id"
                    in working_df.columns
                    else "N/A"
                ),
                "daily_demand": float(
                    row["daily_demand"]
                ),
                "stock_level": float(
                    row["stock_level"]
                ),
            }
            for _, row
            in high_demand.iterrows()
        ]

    if "demand_std_dev" in working_df.columns:

        working_df[
            "demand_std_dev"
        ] = pd.to_numeric(
            working_df[
                "demand_std_dev"
            ],
            errors="coerce"
        )

        high_variability = (
            working_df
            .dropna(
                subset=[
                    "demand_std_dev"
                ]
            )
            .sort_values(
                "demand_std_dev",
                ascending=False
            )
            .head(10)
        )

        risk[
            "highest_demand_variability_items"
        ] = [
            {
                "item_id": (
                    str(row["item_id"])
                    if "item_id"
                    in working_df.columns
                    else "N/A"
                ),
                "demand_std_dev": float(
                    row["demand_std_dev"]
                ),
                "stock_level": float(
                    row["stock_level"]
                ),
            }
            for _, row
            in high_variability.iterrows()
        ]

    if "lead_time_days" in working_df.columns:

        working_df[
            "lead_time_days"
        ] = pd.to_numeric(
            working_df[
                "lead_time_days"
            ],
            errors="coerce"
        )

        long_lead_time = (
            working_df
            .dropna(
                subset=[
                    "lead_time_days"
                ]
            )
            .sort_values(
                "lead_time_days",
                ascending=False
            )
            .head(10)
        )

        risk[
            "longest_lead_time_items"
        ] = [
            {
                "item_id": (
                    str(row["item_id"])
                    if "item_id"
                    in working_df.columns
                    else "N/A"
                ),
                "lead_time_days": float(
                    row["lead_time_days"]
                ),
                "stock_level": float(
                    row["stock_level"]
                ),
            }
            for _, row
            in long_lead_time.iterrows()
        ]

    if "category" in working_df.columns:

        category_demand = None

        if "daily_demand" in working_df.columns:

            category_demand = (
                working_df
                .dropna(
                    subset=[
                        "daily_demand"
                    ]
                )
                .groupby(
                    "category"
                )["daily_demand"]
                .mean()
                .sort_values(ascending=False)
            )

        if (
            category_demand is not None
            and not category_demand.empty
        ):

            risk[
                "highest_average_demand_category"
            ] = {
                "category": str(
                    category_demand.index[0]
                ),
                "average_daily_demand": float(
                    category_demand.iloc[0]
                ),
            }

    return risk


def generate_automatic_observations(
    metrics,
    dimension_analysis,
    trend_analysis,
    domain_config,
    inventory_risk=None
):
    observations = []

    domain = domain_config.get(
        "domain"
    )

    if domain == "ecommerce_orders":

        total_orders = metrics.get(
            "unique_order_count",
            metrics.get(
                "record_count",
                0
            )
        )

        observations.append(
            f"The dataset contains "
            f"{total_orders:,} unique orders."
        )

        unique_customers = metrics.get(
            "unique_customer_count"
        )

        if unique_customers is not None:

            observations.append(
                f"The dataset contains "
                f"{unique_customers:,} unique customers."
            )

        delivered_count = metrics.get(
            "delivered_order_count"
        )

        if delivered_count is not None:

            observations.append(
                f"{delivered_count:,} orders "
                f"were marked as delivered."
            )

        delivery_rate = metrics.get(
            "delivery_completion_rate"
        )

        if delivery_rate is not None:

            observations.append(
                f"{delivery_rate:.2f}% of orders "
                f"were marked as delivered."
            )

        cancellation_rate = metrics.get(
            "cancellation_rate"
        )

        if cancellation_rate is not None:

            observations.append(
                f"The cancellation rate is "
                f"{cancellation_rate:.2f}%."
            )

        unavailable_rate = metrics.get(
            "unavailable_rate"
        )

        if unavailable_rate is not None:

            observations.append(
                f"The unavailable-order rate is "
                f"{unavailable_rate:.2f}%."
            )

        delivery_time = metrics.get(
            "delivery_time_days"
        )

        if delivery_time:

            observations.append(
                f"Average delivery time is "
                f"{delivery_time['average']:.2f} days."
            )

        on_time_rate = metrics.get(
            "on_time_delivery_rate"
        )

        if on_time_rate is not None:

            observations.append(
                f"On-time delivery rate is "
                f"{on_time_rate:.2f}%."
            )

        return observations[:12]

    if domain == "restaurant_sales":

        primary = metrics.get(
            "primary_metric"
        )

        if primary:

            observations.append(
                f"Total restaurant revenue is "
                f"{format_number(primary['total'])}."
            )

            observations.append(
                f"Average revenue per order is "
                f"{format_number(primary['average'])}."
            )

        total_quantity = metrics.get(
            "total_quantity"
        )

        if total_quantity is not None:

            observations.append(
                f"Total quantity sold is "
                f"{format_number(total_quantity)}."
            )

        average_price = metrics.get(
            "average_price"
        )

        if average_price is not None:

            observations.append(
                f"Average item price is "
                f"{format_number(average_price)}."
            )

        record_count = metrics.get(
            "record_count"
        )

        if record_count is not None:

            observations.append(
                f"The dataset contains "
                f"{record_count:,} restaurant orders."
            )

        for dimension, analysis in (
            dimension_analysis.items()
        ):

            top_values = analysis.get(
                "top_values",
                []
            )

            if not top_values:
                continue

            top = top_values[0]

            observations.append(
                f"The highest revenue contribution "
                f"among {dimension} values is "
                f"{top['value']} with "
                f"{format_number(top['total'])}."
            )

        if trend_analysis:

            trend_data = trend_analysis.get(
                "data",
                []
            )

            if len(trend_data) >= 2:

                first = trend_data[0]
                last = trend_data[-1]

                first_total = first["total"]
                last_total = last["total"]

                if first_total != 0:

                    change = (
                        (
                            last_total
                            - first_total
                        )
                        / abs(first_total)
                    ) * 100

                    direction = (
                        "increased"
                        if change >= 0
                        else "decreased"
                    )

                    observations.append(
                        f"Restaurant revenue "
                        f"{direction} by approximately "
                        f"{abs(change):.2f}% between the "
                        f"first and last observed periods."
                    )

        return observations[:12]

    if domain == "saas_subscription":

        primary = metrics.get(
            "primary_metric"
        )

        if primary:

            observations.append(
                f"Total MRR is "
                f"{format_number(primary['total'])}."
            )

            observations.append(
                f"Average MRR per subscription is "
                f"{format_number(primary['average'])}."
            )

        arr = metrics.get(
            "secondary_metrics",
            {}
        ).get(
            "arr_amount"
        )

        if arr:

            observations.append(
                f"Total ARR is "
                f"{format_number(arr['total'])}."
            )

        seats = metrics.get(
            "secondary_metrics",
            {}
        ).get(
            "seats"
        )

        if seats:

            observations.append(
                f"Total seats are "
                f"{format_number(seats['total'])}, "
                f"with an average of "
                f"{format_number(seats['average'])} "
                f"seats per subscription."
            )

        subscription_count = metrics.get(
            "unique_subscription_count"
        )

        if subscription_count is not None:

            observations.append(
                f"The dataset contains "
                f"{subscription_count:,} subscriptions."
            )

        account_count = metrics.get(
            "unique_account_count"
        )

        if account_count is not None:

            observations.append(
                f"The dataset contains "
                f"{account_count:,} unique accounts."
            )

        churn_rate = metrics.get(
            "churn_rate"
        )

        if churn_rate is not None:

            observations.append(
                f"The churn rate is "
                f"{churn_rate:.2f}%."
            )

        upgrade_rate = metrics.get(
            "upgrade_rate"
        )

        if upgrade_rate is not None:

            observations.append(
                f"The upgrade rate is "
                f"{upgrade_rate:.2f}%."
            )

        downgrade_rate = metrics.get(
            "downgrade_rate"
        )

        if downgrade_rate is not None:

            observations.append(
                f"The downgrade rate is "
                f"{downgrade_rate:.2f}%."
            )

        trial_rate = metrics.get(
            "trial_rate"
        )

        if trial_rate is not None:

            observations.append(
                f"The trial rate is "
                f"{trial_rate:.2f}%."
            )

        auto_renewal_rate = metrics.get(
            "auto_renewal_rate"
        )

        if auto_renewal_rate is not None:

            observations.append(
                f"The auto-renewal rate is "
                f"{auto_renewal_rate:.2f}%."
            )

        for dimension, analysis in (
            dimension_analysis.items()
        ):

            top_values = analysis.get(
                "top_values",
                []
            )

            if not top_values:
                continue

            top = top_values[0]

            observations.append(
                f"The highest MRR contribution "
                f"among {dimension} values is "
                f"{top['value']} with "
                f"{format_number(top['total'])}."
            )

        if trend_analysis:

            trend_data = trend_analysis.get(
                "data",
                []
            )

            if len(trend_data) >= 2:

                first = trend_data[0]
                last = trend_data[-1]

                first_total = first["total"]
                last_total = last["total"]

                if first_total != 0:

                    change = (
                        (
                            last_total
                            - first_total
                        )
                        / abs(first_total)
                    ) * 100

                    direction = (
                        "increased"
                        if change >= 0
                        else "decreased"
                    )

                    observations.append(
                        f"MRR {direction} by approximately "
                        f"{abs(change):.2f}% between the first "
                        f"and last observed periods."
                    )

        return observations[:12]

    primary_metric = domain_config.get(
        "primary_metric"
    )

    primary = metrics.get(
        "primary_metric"
    )

    if primary:

        observations.append(
            f"Total {primary_metric}: "
            f"{format_number(primary['total'])}."
        )

        observations.append(
            f"Average {primary_metric}: "
            f"{format_number(primary['average'])}."
        )

    record_count = metrics.get(
        "record_count"
    )

    if record_count is not None:

        observations.append(
            f"The dataset contains "
            f"{record_count:,} records."
        )

    unique_ids = metrics.get(
        "unique_id_count"
    )

    if unique_ids is not None:

        observations.append(
            f"There are approximately "
            f"{unique_ids:,} unique records based on "
            f"the detected ID column."
        )

    if inventory_risk:

        replenishment_count = (
            inventory_risk.get(
                "items_at_or_below_reorder_point"
            )
        )

        replenishment_percentage = (
            inventory_risk.get(
                "replenishment_percentage"
            )
        )

        if replenishment_count is not None:

            observations.append(
                f"{replenishment_count:,} items are at "
                f"or below their reorder point."
            )

        if replenishment_percentage is not None:

            observations.append(
                f"{replenishment_percentage:.2f}% of evaluated "
                f"items are at or below their reorder point."
            )

        demand_category = (
            inventory_risk.get(
                "highest_average_demand_category"
            )
        )

        if demand_category:

            observations.append(
                f"The category with the highest average "
                f"daily demand is "
                f"{demand_category['category']} at "
                f"{demand_category['average_daily_demand']:.2f} units per day."
            )

    for dimension, analysis in (
        dimension_analysis.items()
    ):

        top_values = analysis.get(
            "top_values",
            []
        )

        if not top_values:
            continue

        top = top_values[0]

        observations.append(
            f"The highest {primary_metric} contribution "
            f"among {dimension} values is "
            f"{top['value']} with "
            f"{format_number(top['total'])}."
        )

        if len(observations) >= 6:
            break

    if trend_analysis:

        trend_data = trend_analysis.get(
            "data",
            []
        )

        if len(trend_data) >= 2:

            first = trend_data[0]
            last = trend_data[-1]

            first_total = first["total"]
            last_total = last["total"]

            if first_total != 0:

                change = (
                    (
                        last_total
                        - first_total
                    )
                    / abs(first_total)
                ) * 100

                direction = (
                    "increased"
                    if change >= 0
                    else "decreased"
                )

                observations.append(
                    f"{primary_metric.capitalize()} "
                    f"{direction} by approximately "
                    f"{abs(change):.2f}% between the "
                    f"first and last observed periods."
                )

    return observations


def generate_domain_fallback(
    metrics,
    dimension_analysis,
    trend_analysis,
    domain_config,
    observations,
    inventory_risk=None
):
    domain = domain_config.get(
        "domain",
        ""
    )

    domain_label = domain_config.get(
        "domain_label",
        ""
    ).lower()

    if domain == "ecommerce_orders":

        insights = list(
            observations
        )

        status_distribution = metrics.get(
            "status_distribution",
            {}
        )

        if status_distribution:

            highest_status = max(
                status_distribution,
                key=status_distribution.get
            )

            insights.append(
                f"The most common order status is "
                f"{highest_status} with "
                f"{status_distribution[highest_status]:,} orders."
            )

        delivery_time = metrics.get(
            "delivery_time_days"
        )

        if delivery_time:

            insights.append(
                f"Average delivery time is "
                f"{delivery_time['average']:.2f} days, "
                f"based on "
                f"{delivery_time['orders_evaluated']:,} "
                f"orders with valid delivery dates."
            )

        on_time_rate = metrics.get(
            "on_time_delivery_rate"
        )

        if on_time_rate is not None:

            insights.append(
                f"{on_time_rate:.2f}% of evaluated orders "
                f"were delivered on or before the estimated "
                f"delivery date."
            )

        recommendations = []

        cancellation_rate = metrics.get(
            "cancellation_rate",
            0
        )

        if cancellation_rate > 0:

            recommendations.append(
                "Investigate canceled orders to identify "
                "recurring fulfillment or customer-service issues."
            )

        unavailable_rate = metrics.get(
            "unavailable_rate",
            0
        )

        if unavailable_rate > 0:

            recommendations.append(
                "Review unavailable orders to identify "
                "inventory or fulfillment availability problems."
            )

        on_time_rate = metrics.get(
            "on_time_delivery_rate"
        )

        if (
            on_time_rate is not None
            and on_time_rate < 90
        ):

            recommendations.append(
                "Review late deliveries and fulfillment "
                "processes to improve on-time performance."
            )

        else:

            recommendations.append(
                "Continue monitoring delivery performance "
                "against estimated delivery dates."
            )

        if trend_analysis:

            recommendations.append(
                "Monitor order volume trends to identify "
                "periods of unusually high or low demand."
            )

        recommendations.append(
            "Track order-status distribution regularly "
            "to identify changes in fulfillment health."
        )

        return {
            "status": "fallback",
            "insights": insights[:12],
            "recommendations": recommendations[:5],
        }

    if domain == "restaurant_sales":

        insights = list(
            observations
        )

        recommendations = [
            "Focus marketing and promotional efforts on "
            "the highest-revenue products.",
            "Review lower-performing products and purchase "
            "types for potential improvement.",
            "Monitor revenue trends to identify periods of "
            "strong and weak restaurant performance.",
            "Review payment methods and customer purchasing "
            "patterns to improve the ordering experience.",
            "Use revenue and quantity patterns to support "
            "menu and inventory planning.",
        ]

        return {
            "status": "fallback",
            "insights": insights[:12],
            "recommendations": recommendations[:5],
        }

    if domain == "saas_subscription":

        insights = list(
            observations
        )

        churn_rate = metrics.get(
            "churn_rate"
        )

        upgrade_rate = metrics.get(
            "upgrade_rate"
        )

        downgrade_rate = metrics.get(
            "downgrade_rate"
        )

        auto_renewal_rate = metrics.get(
            "auto_renewal_rate"
        )

        if (
            churn_rate is not None
            and upgrade_rate is not None
        ):

            if upgrade_rate > churn_rate:

                insights.append(
                    "The upgrade rate is higher than "
                    "the churn rate, indicating stronger "
                    "expansion activity than customer loss."
                )

            else:

                insights.append(
                    "The churn rate is at or above "
                    "the upgrade rate, indicating a need "
                    "to monitor customer retention."
                )

        if (
            downgrade_rate is not None
            and churn_rate is not None
        ):

            if downgrade_rate > churn_rate:

                insights.append(
                    "Downgrades occur more frequently "
                    "than churn, suggesting some customers "
                    "may be reducing usage rather than leaving."
                )

        if auto_renewal_rate is not None:

            insights.append(
                f"Auto-renewal is enabled for "
                f"{auto_renewal_rate:.2f}% of subscriptions."
            )

        recommendations = []

        if (
            churn_rate is not None
            and churn_rate >= 10
        ):

            recommendations.append(
                "Prioritize customer-retention initiatives "
                "for accounts showing churn risk."
            )

        else:

            recommendations.append(
                "Continue monitoring churn and retention "
                "patterns across subscription segments."
            )

        if (
            upgrade_rate is not None
            and upgrade_rate > 0
        ):

            recommendations.append(
                "Identify plans and customer segments with "
                "strong upgrade activity and use them to "
                "support expansion strategies."
            )

        if (
            downgrade_rate is not None
            and downgrade_rate > 0
        ):

            recommendations.append(
                "Review downgrade patterns to understand "
                "which plans or customer groups may be "
                "experiencing value or pricing concerns."
            )

        if auto_renewal_rate is not None:

            recommendations.append(
                "Monitor auto-renewal adoption and identify "
                "segments with lower renewal engagement."
            )

        if trend_analysis:

            recommendations.append(
                "Monitor MRR trends over time to identify "
                "periods of strong growth or declining recurring revenue."
            )

        return {
            "status": "fallback",
            "insights": insights[:12],
            "recommendations": recommendations[:5],
        }

    if (
        domain == "inventory"
        or "inventory" in domain_label
    ):

        insights = list(
            observations
        )

        secondary = metrics.get(
            "secondary_metrics",
            {}
        )

        if "daily_demand" in secondary:

            insights.append(
                f"Average daily demand is "
                f"{format_number(secondary['daily_demand']['average'])} "
                f"units."
            )

        if "reorder_point" in secondary:

            insights.append(
                f"Average reorder point is "
                f"{format_number(secondary['reorder_point']['average'])}."
            )

        if "lead_time_days" in secondary:

            insights.append(
                f"Average lead time is "
                f"{format_number(secondary['lead_time_days']['average'])} days."
            )

        if inventory_risk:

            replenishment_count = (
                inventory_risk.get(
                    "items_at_or_below_reorder_point"
                )
            )

            replenishment_percentage = (
                inventory_risk.get(
                    "replenishment_percentage"
                )
            )

            if replenishment_count is not None:

                insights.append(
                    f"{replenishment_count:,} items require "
                    f"replenishment based on their current "
                    f"stock and reorder point."
                )

            if replenishment_percentage is not None:

                insights.append(
                    f"{replenishment_percentage:.2f}% of evaluated "
                    f"items are currently at or below the reorder point."
                )

            demand_category = (
                inventory_risk.get(
                    "highest_average_demand_category"
                )
            )

            if demand_category:

                insights.append(
                    f"{demand_category['category']} has the highest "
                    f"average daily demand at "
                    f"{demand_category['average_daily_demand']:.2f} units per day."
                )

        recommendations = []

        if inventory_risk:

            replenishment_count = inventory_risk.get(
                "items_at_or_below_reorder_point",
                0
            )

            replenishment_percentage = inventory_risk.get(
                "replenishment_percentage",
                0
            )

            if replenishment_count > 0:

                recommendations.append(
                    f"Prioritize replenishment for the "
                    f"{replenishment_count:,} items currently "
                    f"at or below their reorder points."
                )

            if replenishment_percentage >= 20:

                recommendations.append(
                    "A significant portion of inventory is at or "
                    "below reorder points, so review replenishment "
                    "planning and safety-stock levels."
                )

            else:

                recommendations.append(
                    "Continue monitoring stock against reorder "
                    "points to identify replenishment needs early."
                )

            if (
                "daily_demand" in secondary
                and inventory_risk.get(
                    "highest_daily_demand_items"
                )
            ):

                recommendations.append(
                    "Prioritize high-demand items when allocating "
                    "replenishment resources because they can "
                    "deplete stock faster."
                )

            if (
                "demand_std_dev" in secondary
                and inventory_risk.get(
                    "highest_demand_variability_items"
                )
            ):

                recommendations.append(
                    "Review high demand-variability items and "
                    "consider additional safety stock where appropriate."
                )

            if (
                "lead_time_days" in secondary
                and inventory_risk.get(
                    "longest_lead_time_items"
                )
            ):

                recommendations.append(
                    "Plan earlier replenishment for items with "
                    "long supplier lead times."
                )

        else:

            recommendations = [
                "Monitor stock levels against reorder points "
                "to reduce stockout risk.",
                "Use daily demand and demand variability "
                "to prioritize inventory replenishment.",
                "Review items with longer lead times and "
                "plan replenishment earlier."
            ]

        return {
            "status": "fallback",
            "insights": insights[:12],
            "recommendations": recommendations[:5],
        }

    if (
        domain == "retail_sales"
        or "retail" in domain_label
        or "sales" in domain_label
    ):

        recommendations = [
            "Review the strongest sales dimensions "
            "identified by the analysis.",
            "Investigate weaker-performing segments "
            "for potential sales improvement.",
        ]

        if trend_analysis:

            recommendations.append(
                "Use the detected sales trend to identify "
                "periods requiring additional attention."
            )

        else:

            recommendations.append(
                "Track sales over time to identify future "
                "seasonal and performance trends."
            )

        return {
            "status": "fallback",
            "insights": observations,
            "recommendations": recommendations,
        }

    recommendations = [
        "Review the strongest-performing dimensions "
        "identified by the analysis.",
        "Investigate weaker-performing segments "
        "for potential improvement opportunities.",
    ]

    if trend_analysis:

        recommendations.append(
            "Use the detected time trend to identify "
            "periods requiring additional attention."
        )

    else:

        recommendations.append(
            "Collect time-based data where possible to "
            "support future trend analysis."
        )

    return {
        "status": "fallback",
        "insights": observations,
        "recommendations": recommendations,
    }


def generate_ai_insights(
    metrics,
    dimension_analysis,
    trend_analysis,
    domain_config,
    observations,
    inventory_risk=None
):
    api_key = os.getenv(
        "GROQ_API_KEY"
    )

    if not api_key:

        return generate_domain_fallback(
            metrics,
            dimension_analysis,
            trend_analysis,
            domain_config,
            observations,
            inventory_risk
        )

    try:

        model = ChatGroq(
            model="openai/gpt-oss-20b",
            temperature=0
        )

        prompt = f"""
You are a business intelligence analyst.

The dataset has already been cleaned and analyzed
by deterministic Python code.

Do NOT invent numbers.

Use ONLY the verified results provided below.

DOMAIN:
{json.dumps(domain_config, indent=2, default=str)}

VERIFIED METRICS:
{json.dumps(metrics, indent=2, default=str)}

DIMENSION ANALYSIS:
{json.dumps(dimension_analysis, indent=2, default=str)}

TIME TREND:
{json.dumps(trend_analysis, indent=2, default=str)}

INVENTORY RISK ANALYSIS:
{json.dumps(inventory_risk, indent=2, default=str)}

AUTOMATIC OBSERVATIONS:
{json.dumps(observations, indent=2, default=str)}

Return valid JSON with exactly these keys:

{{
    "insights": [
        "insight 1",
        "insight 2",
        "insight 3"
    ],
    "recommendations": [
        "recommendation 1",
        "recommendation 2",
        "recommendation 3"
    ]
}}

Requirements:
- Keep insights concise.
- Focus on the detected domain.
- Use domain-specific business terminology.
- For e-commerce orders, focus on order volume, order status, delivery completion, cancellation, unavailable orders, delivery time, late delivery, and on-time delivery.
- Do not discuss sales or revenue for e-commerce orders when those metrics are not present.
- For inventory data, focus on stock levels, reorder points, replenishment needs, demand, lead time, demand variability, and stockout risk.
- For retail sales data, focus on sales, profit, products, categories, customers, regions, and sales trends.
- For restaurant sales data, focus on revenue, quantity, price, products, purchase types, payment methods, managers, cities, and revenue trends.
- For restaurant sales data, revenue is derived from price multiplied by quantity.
- For SaaS or subscription data, focus on MRR, ARR, seats, plan tiers, billing frequency, churn, upgrades, downgrades, trials, auto-renewal, subscription growth, account growth, and recurring revenue trends.
- For SaaS data, MRR is the primary recurring-revenue metric when available.
- Use only verified calculations.
- Do not invent statistics.
- Do not repeat the entire dataset.
- Make recommendations actionable.
- Do not mention a time trend when no time trend exists.
"""

        response = model.invoke(
            prompt
        )

        content = response.content

        if not isinstance(
            content,
            str
        ):
            content = str(
                content
            )

        content = content.strip()

        if content.startswith("```"):

            content = content.replace(
                "```json",
                ""
            ).replace(
                "```",
                ""
            ).strip()

        parsed = json.loads(
            content
        )

        insights = parsed.get(
            "insights",
            []
        )

        recommendations = parsed.get(
            "recommendations",
            []
        )

        if not isinstance(
            insights,
            list
        ):
            insights = []

        if not isinstance(
            recommendations,
            list
        ):
            recommendations = []

        if (
            not insights
            or not recommendations
        ):

            return generate_domain_fallback(
                metrics,
                dimension_analysis,
                trend_analysis,
                domain_config,
                observations,
                inventory_risk
            )

        return {
            "status": "llm",
            "insights": insights,
            "recommendations": recommendations,
        }

    except Exception as e:

        print(
            f"\nAI insight generation failed: {e}"
        )

        fallback = generate_domain_fallback(
            metrics,
            dimension_analysis,
            trend_analysis,
            domain_config,
            observations,
            inventory_risk
        )

        fallback["error"] = str(e)

        return fallback


def analyze_dataset(
    cleaned_file,
    domain_config
):
    print("\n" + "=" * 60)
    print("ANALYSIS AGENT")
    print("=" * 60)

    print(
        f"\nInput file: {cleaned_file}"
    )

    try:

        df = pd.read_csv(
            cleaned_file
        )

    except Exception as e:

        print(
            f"\nFailed to load cleaned dataset: {e}"
        )

        return {
            "status": "failed",
            "error": str(e),
        }

    if df.empty:

        return {
            "status": "failed",
            "error": "Cleaned dataset is empty.",
        }

    print(
        f"Rows    : {len(df)}"
    )

    print(
        f"Columns : {len(df.columns)}"
    )

    print(
        f"\nDetected domain: "
        f"{domain_config.get('domain_label', 'Unknown')}"
    )

    print(
        f"Primary metric: "
        f"{domain_config.get('primary_metric')}"
    )

    print(
        "\n[1] Calculating basic metrics..."
    )

    metrics = calculate_basic_metrics(
        df,
        domain_config
    )

    print(
        "Basic metrics calculated."
    )

    print(
        "\n[2] Analyzing dimensions..."
    )

    dimension_analysis = analyze_dimensions(
        df,
        domain_config
    )

    print(
        f"Dimensions analyzed: "
        f"{len(dimension_analysis)}"
    )

    print(
        "\n[3] Analyzing time trends..."
    )

    trend_analysis = analyze_time_trend(
        df,
        domain_config
    )

    if trend_analysis:

        print(
            f"Trend periods: "
            f"{trend_analysis['period_count']}"
        )

    else:

        print(
            "No usable time trend detected."
        )

    print(
        "\n[4] Identifying top/bottom performers..."
    )

    performer_analysis = identify_performers(
        df,
        domain_config
    )

    print(
        f"Performance groups analyzed: "
        f"{len(performer_analysis)}"
    )

    print(
        "\n[5] Analyzing inventory risk..."
    )

    inventory_risk = analyze_inventory_risk(
        df,
        domain_config
    )

    if inventory_risk:

        print(
            "Inventory risk analysis completed."
        )

        print(
            f"Items at/below reorder point: "
            f"{inventory_risk['items_at_or_below_reorder_point']}"
        )

        print(
            f"Replenishment percentage: "
            f"{inventory_risk['replenishment_percentage']:.2f}%"
        )

    else:

        print(
            "Inventory risk analysis not applicable."
        )

    print(
        "\n[6] Generating verified observations..."
    )

    observations = (
        generate_automatic_observations(
            metrics,
            dimension_analysis,
            trend_analysis,
            domain_config,
            inventory_risk
        )
    )

    for observation in observations:

        print(
            f"  • {observation}"
        )

    print(
        "\n[7] Generating business insights..."
    )

    ai_results = generate_ai_insights(
        metrics,
        dimension_analysis,
        trend_analysis,
        domain_config,
        observations,
        inventory_risk
    )

    print(
        f"Insight source: "
        f"{ai_results.get('status')}"
    )

    result = {
        "status": "success",

        "dataset": {
            "file": cleaned_file,
            "rows": int(
                len(df)
            ),
            "columns": int(
                len(df.columns)
            ),
        },

        "domain": domain_config,

        "metrics": metrics,

        "dimension_analysis": (
            dimension_analysis
        ),

        "trend_analysis": (
            trend_analysis
        ),

        "performer_analysis": (
            performer_analysis
        ),

        "inventory_risk_analysis": (
            inventory_risk
        ),

        "observations": observations,

        "insights": ai_results.get(
            "insights",
            []
        ),

        "recommendations": ai_results.get(
            "recommendations",
            []
        ),

        "ai_source": ai_results.get(
            "status"
        ),
    }

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)

    print(
        f"Records analyzed : "
        f"{len(df):,}"
    )

    print(
        f"Primary metric   : "
        f"{domain_config.get('primary_metric')}"
    )

    print(
        f"Dimensions       : "
        f"{len(dimension_analysis)}"
    )

    print(
        f"AI insights      : "
        f"{len(result['insights'])}"
    )

    print(
        f"Recommendations  : "
        f"{len(result['recommendations'])}"
    )

    return result


if __name__ == "__main__":
    from domain_config_agent import configure_domain

    input_file = (
        "test-datasets/"
        "cleaned_saas_subscriptions.csv"
    )

    raw_file = (
        "test-datasets/"
        "saas_subscriptions.csv"
    )

    config = configure_domain(
        raw_file
    )

    result = analyze_dataset(
        input_file,
        config
    )

    print(
        "\nFINAL ANALYSIS RESULT:"
    )

    print(
        json.dumps(
            result,
            indent=2,
            default=str
        )
    )