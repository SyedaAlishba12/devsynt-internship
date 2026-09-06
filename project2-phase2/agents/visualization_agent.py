import os
import pandas as pd
import matplotlib.pyplot as plt


def create_visualizations(input_path, output_dir="assets"):
    """
    Create simple visualizations from the cleaned Superstore dataset.
    """

    print("\n" + "=" * 60)
    print("VISUALIZATION AGENT")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. Load cleaned dataset
    # ---------------------------------------------------------
    print("\n[1] Loading cleaned dataset...")

    df = pd.read_csv(input_path)

    if "order_date" in df.columns:
        df["order_date"] = pd.to_datetime(
            df["order_date"],
            errors="coerce"
        )

    os.makedirs(output_dir, exist_ok=True)

    # ---------------------------------------------------------
    # 2. Sales by Category
    # ---------------------------------------------------------
    print("\n[2] Creating category sales chart...")

    category_sales = (
        df.groupby("category")["sales"]
        .sum()
        .sort_values(ascending=False)
    )

    plt.figure(figsize=(8, 5))
    category_sales.plot(kind="bar")
    plt.title("Sales by Category")
    plt.xlabel("Category")
    plt.ylabel("Sales ($)")
    plt.xticks(rotation=0)
    plt.tight_layout()

    category_path = os.path.join(
        output_dir,
        "sales-by-category.png"
    )

    plt.savefig(category_path, dpi=150)
    plt.close()

    # ---------------------------------------------------------
    # 3. Sales by Region
    # ---------------------------------------------------------
    print("[3] Creating region sales chart...")

    region_sales = (
        df.groupby("region")["sales"]
        .sum()
        .sort_values(ascending=False)
    )

    plt.figure(figsize=(8, 5))
    region_sales.plot(kind="bar")
    plt.title("Sales by Region")
    plt.xlabel("Region")
    plt.ylabel("Sales ($)")
    plt.xticks(rotation=0)
    plt.tight_layout()

    region_path = os.path.join(
        output_dir,
        "sales-by-region.png"
    )

    plt.savefig(region_path, dpi=150)
    plt.close()

    # ---------------------------------------------------------
    # 4. Monthly Sales
    # ---------------------------------------------------------
    print("[4] Creating monthly sales chart...")

    monthly_sales = (
        df.dropna(subset=["order_date"])
        .set_index("order_date")
        .resample("ME")["sales"]
        .sum()
    )

    plt.figure(figsize=(10, 5))
    monthly_sales.plot(kind="line")
    plt.title("Monthly Sales Trend")
    plt.xlabel("Date")
    plt.ylabel("Sales ($)")
    plt.tight_layout()

    monthly_path = os.path.join(
        output_dir,
        "monthly-sales.png"
    )

    plt.savefig(monthly_path, dpi=150)
    plt.close()

    # ---------------------------------------------------------
    # 5. Complete
    # ---------------------------------------------------------
    print("\n" + "=" * 60)
    print("VISUALIZATION COMPLETE")
    print("=" * 60)

    print("\nCharts created:")
    print(category_path)
    print(region_path)
    print(monthly_path)

    return {
        "category_chart": category_path,
        "region_chart": region_path,
        "monthly_chart": monthly_path,
    }


if __name__ == "__main__":
    input_file = "data/cleaned_superstore.csv"

    create_visualizations(input_file)

