# Multi-Agent Retail Sales Analytics Pipeline

## Project Overview

This project is a beginner-level multi-agent retail sales analytics pipeline built using **Python, LangChain, LangGraph, Groq, Pandas, Matplotlib, HTML, and CSS**.

The system takes a raw retail sales CSV file and processes it through multiple specialized agents. The final result is a static dashboard containing key sales metrics, charts, and business insights.

The pipeline demonstrates how multiple agents can work together through a LangGraph workflow while using an LLM to assist with orchestration and business insight generation.

---

## Project Objectives

The main objectives of this project are to:

* Process a raw retail sales dataset.
* Clean and validate the dataset.
* Perform exploratory data analysis.
* Generate useful sales and profit statistics.
* Use an LLM to assist the orchestration process.
* Generate AI-powered business insights.
* Create visualizations from the analyzed data.
* Present the results through a simple static dashboard.

---

## Technologies Used

| Technology  | Purpose                                   |
| ----------- | ----------------------------------------- |
| Python      | Main programming language                 |
| Pandas      | Data cleaning and analysis                |
| LangGraph   | Multi-agent workflow and state management |
| LangChain   | LLM integration and prompt handling       |
| Groq        | Free LLM API provider                     |
| GPT-OSS-20B | LLM used for orchestration and insights   |
| Matplotlib  | Data visualization                        |
| HTML        | Dashboard structure                       |
| CSS         | Dashboard styling                         |

---

## Dataset

The project uses the **Sample - Superstore** retail sales dataset.

The raw dataset contains:

* **9,994 rows**
* **21 columns**

The dataset contains information such as:

* Order ID
* Order Date
* Customer
* Region
* Category
* Product
* Sales
* Quantity
* Discount
* Profit

The original dataset is stored in:

```text
data/Sample - Superstore.csv
```

The raw dataset is kept unchanged. The cleaned version is generated separately at:

```text
data/cleaned_superstore.csv
```

---

# Multi-Agent Architecture

The project contains four main agents:

```text
Raw Retail Sales CSV
        |
        v
+---------------------+
|  Orchestrator Agent |
|   LangChain + Groq  |
+----------+----------+
           |
           v
     +-----------+
     | Clean     |
     | Agent     |
     +-----+-----+
           |
           v
     +-----------+
     | Analysis  |
     | Agent     |
     +-----+-----+
           |
           v
     +-----------+
     |Visualization|
     |   Agent    |
     +-----+------+
           |
           v
   Static Dashboard
```

The workflow is implemented using **LangGraph nodes, edges, and shared state**.

---

# 1. Orchestrator Agent

File:

```text
agents/orchestrator.py
```

The Orchestrator Agent is responsible for controlling the overall workflow.

It receives information about the input dataset and uses **LangChain with the Groq LLM** to decide the appropriate initial processing route.

For the raw Superstore dataset, the LLM determines that the dataset should be cleaned first.

The decision is then passed to LangGraph, which routes the workflow to the appropriate agent.

Example decision:

```text
LLM Orchestrator Decision:
Route selected: clean_first
```

After the selected step, LangGraph continues the pipeline through the remaining agents.

This demonstrates the **agent → state → edge → next agent** workflow pattern.

---

# 2. Clean Agent

File:

```text
agents/clean_agent.py
```

The Clean Agent prepares the raw dataset for analysis.

It performs the following tasks:

* Loads the raw CSV.
* Standardizes column names.
* Checks for missing values.
* Corrects data types.
* Converts date columns.
* Converts numeric columns.
* Checks for duplicate rows.
* Checks for invalid records.
* Removes invalid rows when necessary.
* Saves the cleaned dataset.

For this dataset, the cleaning process found:

```text
Original rows       : 9994
Final rows          : 9994
Rows removed        : 0
Missing values      : 0
Duplicates removed  : 0
Invalid rows removed: 0
```

The cleaned dataset is saved as:

```text
data/cleaned_superstore.csv
```

---

# 3. Analysis / EDA Agent

File:

```text
agents/analysis_agent.py
```

The Analysis Agent performs exploratory data analysis on the cleaned dataset.

It calculates:

* Total sales
* Total profit
* Total quantity
* Total orders
* Average sale
* Average profit
* Top-selling products
* Sales by region
* Sales by category
* Monthly sales
* Profit by category

The calculated results are saved as CSV files inside:

```text
assets/
```

### Overall Results

| Metric         |        Result |
| -------------- | ------------: |
| Total Sales    | $2,297,200.86 |
| Total Profit   |   $286,397.02 |
| Total Quantity |        37,873 |
| Total Orders   |         5,009 |
| Average Sale   |       $229.86 |
| Average Profit |        $28.66 |

### Top Product

The highest-selling product was:

**Canon imageCLASS 2200 Advanced Copier**

with approximately:

```text
$61,599.82
```

in sales.

### Sales by Region

```text
West       $725,457.82
East       $678,781.24
Central    $501,239.89
South      $391,721.91
```

### Sales by Category

```text
Technology         $836,154.03
Furniture          $741,999.80
Office Supplies    $719,047.03
```

### Profit by Category

```text
Technology         $145,454.95
Office Supplies    $122,490.80
Furniture           $18,451.27
```

---

## AI-Powered Business Insights

The Analysis Agent also uses **LangChain + Groq** to interpret the calculated statistics.

The LLM receives the verified statistics produced by Pandas and generates a short business insight report.

The AI identifies:

* Overall business performance
* Best-performing product
* Best-performing region
* Best-performing category
* Most profitable category
* Practical business recommendations

The generated report is saved to:

```text
assets/ai_business_insights.txt
```

The LLM does not calculate the original sales statistics. Those calculations are performed deterministically using Pandas, while the LLM is used to interpret the results and provide recommendations.

---

# 4. Visualization Agent

File:

```text
agents/visualization_agent.py
```

The Visualization Agent creates charts from the cleaned dataset.

It generates three charts:

### Sales by Category

```text
assets/sales-by-category.png
```

### Sales by Region

```text
assets/sales-by-region.png
```

### Monthly Sales Trend

```text
assets/monthly-sales.png
```

These visualizations are then displayed on the static dashboard.

---

# LangGraph Workflow

The workflow uses LangGraph's `StateGraph`.

The shared pipeline state contains information such as:

```text
input_file
cleaned_file
cleaning_report
analysis_results
visualization_results
status
route_decision
```

The workflow begins with the Orchestrator:

```text
START
  |
  v
Orchestrator
  |
  | LLM decision
  v
Clean Agent
  |
  v
Analysis Agent
  |
  v
Visualization Agent
  |
  v
END
```

The Orchestrator uses a conditional LangGraph edge to determine the first processing route.

For the current raw Superstore dataset:

```text
Orchestrator
     |
     | clean_first
     v
Clean Agent
     |
     v
Analysis Agent
     |
     v
Visualization Agent
```

---

# Complete Data Flow

The complete project flow is:

```text
Raw CSV
   |
   v
Orchestrator Agent
   |
   v
Clean Agent
   |
   v
Cleaned Dataset
   |
   v
Analysis / EDA Agent
   |
   +----> Analysis CSV Results
   |
   +----> AI Business Insights
   |
   v
Visualization Agent
   |
   +----> Category Chart
   +----> Region Chart
   +----> Monthly Sales Chart
   |
   v
Static Dashboard
```

---

# Static Dashboard

The final results are presented through a static dashboard built using:

* HTML
* CSS

Files:

```text
dashboard.html
dashboard.css
```

The dashboard contains:

* Navigation bar
* Project introduction
* Key performance metrics
* Sales by category
* Sales by region
* Monthly sales trend
* Business insights
* Multi-agent processing pipeline
* Footer

The dashboard uses a green/sage color palette for a clean analytics-style interface.

---

# Project Evidence

The `assets` directory contains screenshots demonstrating the project's execution and results.

### Flow Diagram

```text
assets/flow-diagram.png
```

Shows the overall multi-agent processing workflow.

### Cleaning Result

```text
assets/cleaning-result.png
```

Shows the Clean Agent's terminal output and data-cleaning results.

### Analysis Output

```text
assets/analysis-output.png
```

Shows the Analysis Agent's calculated statistics and AI-generated business insights.

### Dashboard Preview

```text
assets/dashboard-preview.png
```

Shows the completed static retail analytics dashboard.

---

# Case Study Walkthrough

## Step 1 — Raw Data

The pipeline starts with the original Sample - Superstore CSV containing 9,994 records.

```text
data/Sample - Superstore.csv
```

## Step 2 — Orchestration

The Orchestrator Agent examines the input and uses the Groq LLM through LangChain to determine that the raw dataset should be cleaned first.

```text
Route selected: clean_first
```

## Step 3 — Data Cleaning

The Clean Agent processes the raw dataset.

In this case, the dataset was already relatively clean, so no rows needed to be removed.

The resulting cleaned dataset contains all 9,994 original records.

## Step 4 — Analysis

The Analysis Agent calculates sales, profit, order, product, category, region, and monthly statistics.

It also sends a compact version of the verified statistics to the Groq LLM through LangChain to generate business recommendations.

## Step 5 — Visualization

The Visualization Agent converts the analysis into three charts:

* Category sales
* Regional sales
* Monthly sales

## Step 6 — Dashboard

The generated results and charts are presented through the static HTML/CSS dashboard.

The final dashboard provides a simple view of the retail business performance.

---

# Project Structure

```text
project2-phase2/
│
├── agents/
│   ├── __init__.py
│   ├── clean_agent.py
│   ├── analysis_agent.py
│   ├── visualization_agent.py
│   └── orchestrator.py
│
├── data/
│   ├── Sample - Superstore.csv
│   └── cleaned_superstore.csv
│
├── assets/
│   ├── flow-diagram.png
│   ├── cleaning-result.png
│   ├── analysis-output.png
│   ├── dashboard-preview.png
│   ├── sales-by-category.png
│   ├── sales-by-region.png
│   ├── monthly-sales.png
│   ├── ai_business_insights.txt
│   ├── analysis_summary.csv
│   ├── top_products.csv
│   ├── sales_by_region.csv
│   ├── sales_by_category.csv
│   ├── monthly_sales.csv
│   └── profit_by_category.csv
│
├── dashboard.html
├── dashboard.css
├── main.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

# How to Run

## 1. Create and activate the virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure the Groq API key

Create a `.env` file in the project root:

```text
GROQ_API_KEY=your_groq_api_key_here
```

The `.env` file is excluded from Git using `.gitignore`.

## 4. Run the complete pipeline

From the project root:

```bash
python main.py
```

The pipeline will:

```text
Orchestrator
     ↓
Clean Agent
     ↓
Analysis Agent
     ↓
Visualization Agent
```

## 5. View the dashboard

Open:

```text
dashboard.html
```

You can use VS Code Live Server to view the dashboard in a browser.

---

# Conclusion

This project demonstrates a complete beginner-level multi-agent retail analytics workflow.

Instead of having one program perform every task, the pipeline separates responsibilities between specialized agents:

* The **Orchestrator Agent** manages the workflow and uses an LLM to make the initial routing decision.
* The **Clean Agent** prepares the dataset.
* The **Analysis Agent** performs EDA and uses an LLM to generate business insights.
* The **Visualization Agent** creates charts.
* The **Dashboard** presents the final results.

The project combines deterministic data processing with LLM-based reasoning to create a practical and understandable multi-agent sales analytics system.
