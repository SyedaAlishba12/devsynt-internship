import os
import pandas as pd
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate


# Load environment variables from .env
load_dotenv()


def generate_ai_insights(
    total_sales,
    total_profit,
    total_quantity,
    total_orders,
    average_sales,
    average_profit,
    top_products,
    sales_by_region,
    sales_by_category,
    profit_by_category,
    output_dir="assets"
):
    """
    Use LangChain + Groq to generate a short AI-powered
    business insight summary from the calculated EDA results.
    """

    print("\n[9] Generating AI-powered business insights...")

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("GROQ_API_KEY not found in .env")
        print("Skipping AI insights.")
        return None

    try:
        # Initialize Groq LLM through LangChain
        llm = ChatGroq(
            model="openai/gpt-oss-20b",
            temperature=0.2,
            api_key=api_key
        )

        # Prepare a compact summary for the LLM
        top_product = top_products.index[0]
        top_product_sales = top_products.iloc[0]

        top_region = sales_by_region.index[0]
        top_region_sales = sales_by_region.iloc[0]

        top_category = sales_by_category.index[0]
        top_category_sales = sales_by_category.iloc[0]

        most_profitable_category = profit_by_category.index[0]
        most_profitable_category_profit = profit_by_category.iloc[0]

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
You are a retail business analyst.

Analyze the provided sales statistics and produce a short,
beginner-friendly business insight report.

Include:
1. Overall performance
2. Best-performing product
3. Best-performing region
4. Best-performing category
5. Most profitable category
6. Two practical recommendations

Keep the response concise and easy to understand.
Do not invent statistics that are not provided.
"""
            ),
            (
                "human",
                """
Retail Sales Statistics:

Total Sales: ${total_sales:,.2f}
Total Profit: ${total_profit:,.2f}
Total Quantity Sold: {total_quantity:,}
Total Orders: {total_orders:,}
Average Sale: ${average_sales:,.2f}
Average Profit: ${average_profit:,.2f}

Top Product:
{top_product}
Sales: ${top_product_sales:,.2f}

Top Region:
{top_region}
Sales: ${top_region_sales:,.2f}

Top Category:
{top_category}
Sales: ${top_category_sales:,.2f}

Most Profitable Category:
{most_profitable_category}
Profit: ${most_profitable_category_profit:,.2f}
"""
            )
        ])

        chain = prompt | llm

        response = chain.invoke({
            "total_sales": total_sales,
            "total_profit": total_profit,
            "total_quantity": total_quantity,
            "total_orders": total_orders,
            "average_sales": average_sales,
            "average_profit": average_profit,
            "top_product": top_product,
            "top_product_sales": top_product_sales,
            "top_region": top_region,
            "top_region_sales": top_region_sales,
            "top_category": top_category,
            "top_category_sales": top_category_sales,
            "most_profitable_category": most_profitable_category,
            "most_profitable_category_profit": most_profitable_category_profit,
        })

        ai_insights = response.content

        print("\nAI Business Insights:")
        print("-" * 60)
        print(ai_insights)
        print("-" * 60)

        os.makedirs(output_dir, exist_ok=True)

        with open(
            os.path.join(output_dir, "ai_business_insights.txt"),
            "w",
            encoding="utf-8"
        ) as file:
            file.write(ai_insights)

        print("\nAI insights saved to:")
        print(os.path.join(output_dir, "ai_business_insights.txt"))

        return ai_insights

    except Exception as e:
        print(f"AI insight generation failed: {e}")
        print("The rest of the analysis will continue normally.")
        return None


def analyze_dataset(input_path, output_dir="assets"):
    """
    Analyze the cleaned Superstore dataset and generate
    EDA results required for the project.
    """

    print("\n" + "=" * 60)
    print("ANALYSIS / EDA AGENT")
    print("=" * 60)

    # ---------------------------------------------------------
    # 1. Load cleaned dataset
    # ---------------------------------------------------------
    print("\n[1] Loading cleaned dataset...")

    df = pd.read_csv(input_path)

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    # Convert dates again because CSV does not preserve
    # pandas datetime types.
    if "order_date" in df.columns:
        df["order_date"] = pd.to_datetime(
            df["order_date"],
            errors="coerce"
        )

    # ---------------------------------------------------------
    # 2. Basic summary statistics
    # ---------------------------------------------------------
    print("\n[2] Calculating overall statistics...")

    total_sales = df["sales"].sum()
    total_profit = df["profit"].sum()
    total_quantity = df["quantity"].sum()
    total_orders = df["order_id"].nunique()

    average_sales = df["sales"].mean()
    average_profit = df["profit"].mean()

    print(f"Total Sales     : ${total_sales:,.2f}")
    print(f"Total Profit    : ${total_profit:,.2f}")
    print(f"Total Quantity  : {total_quantity:,}")
    print(f"Total Orders    : {total_orders:,}")
    print(f"Average Sale    : ${average_sales:,.2f}")
    print(f"Average Profit  : ${average_profit:,.2f}")

    # ---------------------------------------------------------
    # 3. Best-selling products
    # ---------------------------------------------------------
    print("\n[3] Finding best-selling products...")

    top_products = (
        df.groupby("product_name")["sales"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    print("\nTop 10 Products by Sales:")
    print(top_products.to_string())

    # ---------------------------------------------------------
    # 4. Sales by region
    # ---------------------------------------------------------
    print("\n[4] Calculating sales by region...")

    sales_by_region = (
        df.groupby("region")["sales"]
        .sum()
        .sort_values(ascending=False)
    )

    print("\nSales by Region:")
    print(sales_by_region.to_string())

    # ---------------------------------------------------------
    # 5. Sales by category
    # ---------------------------------------------------------
    print("\n[5] Calculating sales by category...")

    sales_by_category = (
        df.groupby("category")["sales"]
        .sum()
        .sort_values(ascending=False)
    )

    print("\nSales by Category:")
    print(sales_by_category.to_string())

    # ---------------------------------------------------------
    # 6. Monthly sales
    # ---------------------------------------------------------
    print("\n[6] Calculating monthly sales...")

    monthly_sales = (
        df.dropna(subset=["order_date"])
        .set_index("order_date")
        .resample("ME")["sales"]
        .sum()
    )

    print("\nMonthly Sales:")
    print(monthly_sales.to_string())

    # ---------------------------------------------------------
    # 7. Category profit
    # ---------------------------------------------------------
    print("\n[7] Calculating profit by category...")

    profit_by_category = (
        df.groupby("category")["profit"]
        .sum()
        .sort_values(ascending=False)
    )

    print("\nProfit by Category:")
    print(profit_by_category.to_string())

    # ---------------------------------------------------------
    # 8. Save analysis results
    # ---------------------------------------------------------
    print("\n[8] Saving analysis results...")

    os.makedirs(output_dir, exist_ok=True)

    # Overall summary
    summary = pd.DataFrame({
        "Metric": [
            "Total Sales",
            "Total Profit",
            "Total Quantity",
            "Total Orders",
            "Average Sale",
            "Average Profit"
        ],
        "Value": [
            total_sales,
            total_profit,
            total_quantity,
            total_orders,
            average_sales,
            average_profit
        ]
    })

    summary.to_csv(
        os.path.join(output_dir, "analysis_summary.csv"),
        index=False
    )

    # Other analysis results
    top_products.to_csv(
        os.path.join(output_dir, "top_products.csv"),
        header=["Sales"]
    )

    sales_by_region.to_csv(
        os.path.join(output_dir, "sales_by_region.csv"),
        header=["Sales"]
    )

    sales_by_category.to_csv(
        os.path.join(output_dir, "sales_by_category.csv"),
        header=["Sales"]
    )

    monthly_sales.to_csv(
        os.path.join(output_dir, "monthly_sales.csv"),
        header=["Sales"]
    )

    profit_by_category.to_csv(
        os.path.join(output_dir, "profit_by_category.csv"),
        header=["Profit"]
    )

    # ---------------------------------------------------------
    # 9. Generate AI-powered insights using LangChain + Groq
    # ---------------------------------------------------------
    ai_insights = generate_ai_insights(
        total_sales=total_sales,
        total_profit=total_profit,
        total_quantity=total_quantity,
        total_orders=total_orders,
        average_sales=average_sales,
        average_profit=average_profit,
        top_products=top_products,
        sales_by_region=sales_by_region,
        sales_by_category=sales_by_category,
        profit_by_category=profit_by_category,
        output_dir=output_dir
    )

    # ---------------------------------------------------------
    # 10. Final report
    # ---------------------------------------------------------
    results = {
        "total_sales": total_sales,
        "total_profit": total_profit,
        "total_quantity": total_quantity,
        "total_orders": total_orders,
        "average_sales": average_sales,
        "average_profit": average_profit,
        "top_products": top_products,
        "sales_by_region": sales_by_region,
        "sales_by_category": sales_by_category,
        "monthly_sales": monthly_sales,
        "profit_by_category": profit_by_category,
        "ai_insights": ai_insights,
    }

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)

    print("\nAnalysis files saved in:")
    print(output_dir)

    return results


if __name__ == "__main__":
    input_file = "data/cleaned_superstore.csv"

    analyze_dataset(input_file)
