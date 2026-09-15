import json
import os
import re

import pandas as pd
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

load_dotenv()


def normalize_column_name(column_name):
    name = str(column_name).strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


def normalize_columns(df):
    df = df.copy()
    df.columns = [normalize_column_name(column) for column in df.columns]
    return df


def find_column_by_alias(columns, aliases):
    normalized_columns = {
        normalize_column_name(column): column
        for column in columns
    }

    for alias in aliases:
        alias_normalized = normalize_column_name(alias)

        if alias_normalized in normalized_columns:
            return normalized_columns[alias_normalized]

    return None


def detect_date_column(df):
    date_aliases = [
        "order_date",
        "order_purchase_timestamp",
        "purchase_date",
        "transaction_date",
        "invoice_date",
        "sale_date",
        "sales_date",
        "date",
        "start_date",
        "created_at",
        "created_date",
        "timestamp",
        "datetime",
        "end_date",
    ]

    exact_match = find_column_by_alias(
        df.columns,
        date_aliases
    )

    if exact_match:
        return exact_match

    for column in df.columns:
        if (
            "date" in column
            or "timestamp" in column
            or "datetime" in column
        ):
            sample = df[column].dropna().head(100)

            if len(sample) == 0:
                continue

            parsed = pd.to_datetime(
                sample,
                errors="coerce",
                format="mixed"
            )

            if parsed.notna().mean() >= 0.8:
                return column

    return None


def detect_id_column(df):
    preferred_ids = [
        "order_id",
        "transaction_id",
        "invoice_id",
        "item_id",
        "product_id",
        "customer_id",
        "subscription_id",
        "account_id",
        "user_id",
        "record_id",
        "id",
    ]

    for preferred in preferred_ids:
        column = find_column_by_alias(
            df.columns,
            [preferred]
        )

        if column:
            return column

    for column in df.columns:
        if column.endswith("_id") and column != "row_id":
            return column

    return None


def detect_numeric_columns(df):
    excluded_columns = {
        "id",
        "row_id",
        "order_id",
        "transaction_id",
        "invoice_id",
        "item_id",
        "product_id",
        "customer_id",
        "subscription_id",
        "account_id",
        "user_id",
        "record_id",
        "postal_code",
        "zip",
        "zip_code",
    }

    numeric_columns = []

    for column in df.columns:
        if column in excluded_columns:
            continue

        if pd.api.types.is_numeric_dtype(df[column]):
            numeric_columns.append(column)

    return numeric_columns


def detect_metric_columns(df):
    metric_aliases = [
        "sales",
        "revenue",
        "amount",
        "price",
        "profit",
        "income",
        "cost",
        "quantity",
        "units",
        "stock",
        "stock_level",
        "stock_quantity",
        "inventory",
        "inventory_level",
        "reorder_point",
        "reorder_frequency_days",
        "lead_time_days",
        "daily_demand",
        "demand_std_dev",
        "popularity_score",
        "item_popularity_score",
        "discount",
        "rating",
        "spend",
        "expenses",
        "expense",
        "orders",
        "customers",
        "users",
        "subscriptions",
        "churn",
        "mrr",
        "mrr_amount",
        "arr",
        "arr_amount",
        "balance",
        "payment",
        "total",
        "seats",
        "upgrade_flag",
        "downgrade_flag",
        "churn_flag",
        "auto_renew_flag",
        "is_trial",
    ]

    excluded_metric_columns = {
        "id",
        "row_id",
        "order_id",
        "transaction_id",
        "invoice_id",
        "item_id",
        "product_id",
        "customer_id",
        "subscription_id",
        "account_id",
        "user_id",
        "record_id",
        "postal_code",
        "zip",
        "zip_code",
    }

    metric_columns = []

    for alias in metric_aliases:
        column = find_column_by_alias(
            df.columns,
            [alias]
        )

        if (
            column
            and column not in metric_columns
            and column not in excluded_metric_columns
        ):
            if pd.api.types.is_numeric_dtype(df[column]):
                metric_columns.append(column)

    return metric_columns


def detect_dimension_columns(df, date_column, id_column):
    dimensions = []

    for column in df.columns:
        if column == date_column or column == id_column:
            continue

        if column.endswith("_id"):
            continue

        if pd.api.types.is_object_dtype(df[column]):
            unique_count = df[column].nunique(
                dropna=True
            )

            if 2 <= unique_count <= 100:
                dimensions.append(column)

        elif isinstance(
            df[column].dtype,
            pd.CategoricalDtype
        ):
            unique_count = df[column].nunique(
                dropna=True
            )

            if 2 <= unique_count <= 100:
                dimensions.append(column)

    return dimensions


def detect_domain_heuristically(df):
    columns = set(df.columns)

    def has_any(names):
        return bool(columns.intersection(names))

    if has_any(
        {
            "stock",
            "stock_level",
            "stock_quantity",
            "inventory",
            "inventory_level",
            "reorder_point",
            "daily_demand",
            "lead_time_days",
        }
    ) and has_any(
        {
            "item",
            "item_id",
            "product",
            "product_id",
            "sku",
        }
    ):
        return "inventory"

    if has_any(
        {
            "order_status",
        }
    ) and has_any(
        {
            "order_purchase_timestamp",
            "order_date",
            "purchase_date",
        }
    ) and has_any(
        {
            "order_estimated_delivery_date",
            "order_delivered_customer_date",
            "order_delivered_carrier_date",
        }
    ):
        return "ecommerce_orders"

    if has_any(
        {
            "product",
            "item",
            "item_name",
            "menu_item",
            "dish",
        }
    ) and has_any(
        {
            "quantity",
            "price",
            "amount",
            "sales",
            "revenue",
        }
    ) and has_any(
        {
            "purchase_type",
            "payment_method",
            "manager",
            "city",
        }
    ):
        return "restaurant_sales"

    if has_any(
        {
            "subscription",
            "subscription_id",
            "plan",
            "plan_tier",
            "billing_frequency",
        }
    ) or has_any(
        {
            "mrr",
            "mrr_amount",
            "arr",
            "arr_amount",
            "churn",
            "churn_flag",
        }
    ):
        return "saas_subscription"

    if has_any(
        {
            "sales",
            "revenue",
        }
    ) and has_any(
        {
            "product",
            "product_name",
            "category",
            "quantity",
        }
    ):
        return "retail_sales"

    if has_any(
        {
            "order_id",
            "customer_id",
        }
    ) and has_any(
        {
            "product_id",
            "product_name",
        }
    ) and has_any(
        {
            "price",
            "amount",
            "sales",
            "revenue",
        }
    ):
        return "ecommerce_orders"

    if has_any(
        {
            "customer_id",
            "customer",
            "customer_name",
        }
    ) and has_any(
        {
            "sales",
            "revenue",
            "spend",
            "amount",
        }
    ):
        return "customer_analytics"

    return "general_business_data"


def create_fallback_domain_config(df):
    date_column = detect_date_column(df)
    id_column = detect_id_column(df)
    numeric_columns = detect_numeric_columns(df)
    metric_columns = detect_metric_columns(df)

    dimensions = detect_dimension_columns(
        df,
        date_column,
        id_column
    )

    domain = detect_domain_heuristically(df)

    if domain == "restaurant_sales":
        restaurant_dimensions = [
            "product",
            "purchase_type",
            "payment_method",
            "manager",
            "city",
        ]

        dimensions = [
            column
            for column in restaurant_dimensions
            if column in df.columns
        ]

    primary_metric = None

    if domain == "inventory":
        inventory_priority_metrics = [
            "stock_level",
            "stock_quantity",
            "inventory_level",
            "inventory",
            "stock",
            "daily_demand",
            "reorder_point",
        ]

        for preferred in inventory_priority_metrics:
            if preferred in metric_columns:
                primary_metric = preferred
                break

        if primary_metric is None:
            primary_metric = "stock_level"

    elif domain == "restaurant_sales":
        primary_metric = "revenue"

        secondary_metrics = [
            metric
            for metric in [
                "price",
                "quantity",
            ]
            if metric in metric_columns
        ]

    elif domain == "saas_subscription":
        saas_priority_metrics = [
            "mrr_amount",
            "mrr",
            "arr_amount",
            "arr",
            "seats",
        ]

        for preferred in saas_priority_metrics:
            if preferred in metric_columns:
                primary_metric = preferred
                break

    elif domain == "ecommerce_orders":
        ecommerce_priority_metrics = [
            "sales",
            "revenue",
            "amount",
            "order_count",
        ]

        for preferred in ecommerce_priority_metrics:
            if preferred in metric_columns:
                primary_metric = preferred
                break

        if primary_metric is None:
            primary_metric = "order_count"

    else:
        generic_priority_metrics = [
            "revenue",
            "sales",
            "amount",
            "profit",
            "price",
            "quantity",
            "stock",
            "inventory",
            "mrr",
            "mrr_amount",
            "arr",
            "arr_amount",
            "cost",
        ]

        for preferred in generic_priority_metrics:
            if preferred in metric_columns:
                primary_metric = preferred
                break

    if domain != "restaurant_sales":
        secondary_metrics = [
            metric
            for metric in metric_columns
            if metric != primary_metric
        ][:5]

    success_metrics = secondary_metrics[:4]

    recommended_charts = []

    if domain == "ecommerce_orders":
        success_metrics = [
            "order_status",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
            "order_delivered_carrier_date",
        ]

        recommended_charts = [
            {
                "type": "line",
                "x": date_column,
                "y": None,
                "title": "Order Volume Trend",
            },
            {
                "type": "bar",
                "x": "order_status",
                "y": None,
                "title": "Orders by Status",
            },
        ]

    elif domain == "restaurant_sales":
        secondary_metrics = [
            metric
            for metric in [
                "price",
                "quantity",
            ]
            if metric in metric_columns
        ]

        success_metrics = [
            "revenue",
            "quantity",
            "price",
        ]

        recommended_charts = []

        if date_column:
            recommended_charts.append(
                {
                    "type": "line",
                    "x": date_column,
                    "y": "revenue",
                    "title": "Restaurant Revenue Trend",
                }
            )

        for dimension in dimensions[:4]:
            recommended_charts.append(
                {
                    "type": "bar",
                    "x": dimension,
                    "y": "revenue",
                    "title": (
                        f"Revenue by "
                        f"{dimension.replace('_', ' ').title()}"
                    ),
                }
            )

    elif domain == "saas_subscription":
        secondary_metrics = [
            metric
            for metric in [
                "arr_amount",
                "seats",
            ]
            if metric in metric_columns
        ]

        success_metrics = [
            "mrr_amount",
            "arr_amount",
            "churn_flag",
            "upgrade_flag",
            "downgrade_flag",
            "auto_renew_flag",
        ]

        recommended_charts = []

        if date_column:
            recommended_charts.append(
                {
                    "type": "line",
                    "x": date_column,
                    "y": "mrr_amount",
                    "title": "MRR Trend",
                }
            )

        for dimension in dimensions[:3]:
            recommended_charts.append(
                {
                    "type": "bar",
                    "x": dimension,
                    "y": "mrr_amount",
                    "title": (
                        f"MRR by "
                        f"{dimension.replace('_', ' ').title()}"
                    ),
                }
            )

    elif date_column and primary_metric:
        recommended_charts.append(
            {
                "type": "line",
                "x": date_column,
                "y": primary_metric,
                "title": (
                    f"{primary_metric.replace('_', ' ').title()} Trend"
                ),
            }
        )

        for dimension in dimensions[:3]:
            recommended_charts.append(
                {
                    "type": "bar",
                    "x": dimension,
                    "y": primary_metric,
                    "title": (
                        f"{primary_metric.replace('_', ' ').title()} by "
                        f"{dimension.replace('_', ' ').title()}"
                    ),
                }
            )

    if not recommended_charts and primary_metric:
        recommended_charts.append(
            {
                "type": "bar",
                "x": dimensions[0] if dimensions else None,
                "y": primary_metric,
                "title": (
                    f"{primary_metric.replace('_', ' ').title()} Overview"
                ),
            }
        )

    domain_labels = {
        "retail_sales": "Retail Sales",
        "ecommerce_orders": "E-Commerce Orders",
        "inventory": "Inventory Management",
        "restaurant_sales": "Restaurant Sales",
        "saas_subscription": "SaaS / Subscription",
        "customer_analytics": "Customer Analytics",
        "general_business_data": "General Business Data",
    }

    available_metrics = list(metric_columns)

    if domain == "ecommerce_orders":
        available_metrics = [
            "order_count",
            "delivery_time_days",
            "on_time_delivery_rate",
            "cancellation_rate",
            "status_distribution",
        ] + available_metrics

    elif domain == "restaurant_sales":
        available_metrics = [
            "revenue",
            "price",
            "quantity",
        ] + [
            metric
            for metric in metric_columns
            if metric not in {
                "price",
                "quantity",
            }
        ]

    elif domain == "saas_subscription":
        available_metrics = [
            "mrr_amount",
            "arr_amount",
            "seats",
            "churn_rate",
            "upgrade_rate",
            "downgrade_rate",
            "auto_renewal_rate",
        ] + [
            metric
            for metric in metric_columns
            if metric not in {
                "mrr_amount",
                "arr_amount",
                "seats",
            }
        ]

    return {
        "domain": domain,
        "domain_label": domain_labels.get(
            domain,
            "General Business Data"
        ),
        "primary_metric": primary_metric,
        "secondary_metrics": secondary_metrics,
        "date_column": date_column,
        "id_column": id_column,
        "dimension_columns": dimensions,
        "numeric_columns": numeric_columns,
        "metric_semantics": {
            "primary_metric": primary_metric,
            "available_metrics": available_metrics,
        },
        "success_metrics": success_metrics,
        "recommended_charts": recommended_charts,
        "source": "heuristic_fallback",
    }


def build_llm_domain_config(df):
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return None

    sample = df.head(10).to_dict(
        orient="records"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are a domain configuration agent for a production data analytics pipeline.

Inspect the dataset schema and sample records.

Choose the most appropriate domain from:
- retail sales
- e-commerce
- inventory
- restaurant sales
- SaaS/subscriptions
- customer analytics
- another business domain

Return valid JSON only.

The JSON must contain:
domain
domain_label
primary_metric
secondary_metrics
date_column
id_column
dimension_columns
numeric_columns
metric_semantics
success_metrics
recommended_charts

Important rules:

Only use physical dataset columns for:
- date_column
- id_column
- dimension_columns
- numeric_columns

Derived metrics may be used for:
- primary_metric
- secondary_metrics
- success_metrics
- metric_semantics
- recommended chart y values

For e-commerce order lifecycle datasets, recognize:
- order ID
- customer ID
- order status
- purchase timestamp
- approval timestamp
- delivery carrier date
- delivery customer date
- estimated delivery date

For e-commerce order lifecycle datasets, useful derived metrics include:
- order_count
- delivery_time_days
- on_time_delivery_rate
- cancellation_rate
- status_distribution

For inventory datasets, look specifically for:
- item ID
- product ID
- stock level
- reorder point
- reorder frequency
- lead time
- daily demand
- demand variability
- popularity score

For restaurant sales datasets, look specifically for:
- order ID
- date
- product or menu item
- price
- quantity
- purchase type
- payment method
- manager
- city

For restaurant sales datasets, revenue may be a derived metric:
revenue = price * quantity

For SaaS or subscription datasets, look specifically for:
- subscription ID
- account ID
- start date
- end date
- plan tier
- seats
- MRR
- ARR
- trial status
- upgrade flag
- downgrade flag
- churn flag
- billing frequency
- auto-renewal flag

For SaaS datasets, MRR should generally be the primary metric
when mrr_amount or mrr is available.

Useful SaaS success metrics may include:
- mrr_amount
- arr_amount
- churn_rate
- upgrade_rate
- downgrade_rate
- auto_renewal_rate
""",
            ),
            (
                "human",
                """
Dataset columns:
{columns}

Dataset sample:
{sample}
""",
            ),
        ]
    )

    try:
        llm = ChatGroq(
            model="openai/gpt-oss-20b",
            temperature=0,
            api_key=api_key,
        )

        chain = prompt | llm

        response = chain.invoke(
            {
                "columns": list(df.columns),
                "sample": json.dumps(
                    sample,
                    default=str
                ),
            }
        )

        content = response.content.strip()

        if content.startswith("```"):
            content = re.sub(
                r"^```(?:json)?",
                "",
                content
            )

            content = re.sub(
                r"```$",
                "",
                content
            )

            content = content.strip()

        return json.loads(content)

    except Exception:
        return None


def validate_domain_config(config, df):
    domain_aliases = {
        "e-commerce": "ecommerce_orders",
        "ecommerce": "ecommerce_orders",
        "e-commerce orders": "ecommerce_orders",
        "ecommerce orders": "ecommerce_orders",
        "e-commerce order lifecycle": "ecommerce_orders",
    }

    domain = str(
        config.get("domain", "")
    ).strip().lower()

    if domain in domain_aliases:
        config["domain"] = domain_aliases[domain]

    required_fields = [
        "domain",
        "domain_label",
        "primary_metric",
        "secondary_metrics",
        "date_column",
        "id_column",
        "dimension_columns",
        "numeric_columns",
        "metric_semantics",
        "success_metrics",
        "recommended_charts",
    ]

    for field in required_fields:
        if field not in config:
            return False

    physical_columns = set(df.columns)

    derived_metrics = {
        "order_count",
        "delivery_time_days",
        "on_time_delivery_rate",
        "cancellation_rate",
        "status_distribution",
        "revenue",
        "churn_rate",
        "upgrade_rate",
        "downgrade_rate",
        "auto_renewal_rate",
    }

    allowed_metric_names = physical_columns.union(
        derived_metrics
    )

    primary_metric = config.get(
        "primary_metric"
    )

    if primary_metric not in allowed_metric_names:
        return False

    for metric in config.get(
        "secondary_metrics",
        []
    ):
        if metric not in allowed_metric_names:
            return False

    for metric in config.get(
        "success_metrics",
        []
    ):
        if metric not in allowed_metric_names:
            return False

    date_column = config.get(
        "date_column"
    )

    if (
        date_column is not None
        and date_column not in physical_columns
    ):
        return False

    id_column = config.get(
        "id_column"
    )

    if (
        id_column is not None
        and id_column not in physical_columns
    ):
        return False

    for column in config.get(
        "dimension_columns",
        []
    ):
        if column not in physical_columns:
            return False

    for column in config.get(
        "numeric_columns",
        []
    ):
        if column not in physical_columns:
            return False

    for chart in config.get(
        "recommended_charts",
        []
    ):
        x_column = chart.get("x")
        y_column = chart.get("y")

        if (
            x_column is not None
            and x_column not in physical_columns
        ):
            return False

        if (
            y_column is not None
            and y_column not in allowed_metric_names
        ):
            return False

    return True

def configure_domain(input_file):
    try:
        df = pd.read_csv(input_file)

    except UnicodeDecodeError:
        df = pd.read_csv(
            input_file,
            encoding="latin1"
        )

    df = normalize_columns(df)

    print("DOMAIN CONFIGURATION AGENT")
    print(
        f"Rows detected    : {len(df)}"
    )
    print(
        f"Columns detected : {len(df.columns)}"
    )

    heuristic_domain = detect_domain_heuristically(
        df
    )

    print(
        "Detected domain:",
        heuristic_domain.replace(
            "_",
            " "
        ).title()
    )

    fallback_config = create_fallback_domain_config(
        df
    )

    llm_config = build_llm_domain_config(
        df
    )

    if (
        llm_config
        and validate_domain_config(
            llm_config,
            df
        )
    ):
        config = llm_config
        config["source"] = "llm"

    else:
        config = fallback_config
        config["source"] = "heuristic_fallback"

        if not os.getenv("GROQ_API_KEY"):
            print(
                "GROQ_API_KEY not found."
            )
            print(
                "Using deterministic domain configuration."
            )

    print(
        "Primary metric:",
        config.get(
            "primary_metric"
        )
    )

    print(
        "Date column:",
        config.get(
            "date_column"
        )
    )

    print(
        "ID column:",
        config.get(
            "id_column"
        )
    )

    return config


if __name__ == "__main__":
    input_file = "test-datasets/restaurant_sales.csv"

    result = configure_domain(
        input_file
    )

    print(
        "\nFINAL DOMAIN CONFIGURATION:"
    )

    print(
        json.dumps(
            result,
            indent=2,
            default=str
        )
    )