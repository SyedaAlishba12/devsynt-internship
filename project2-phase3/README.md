# Project 2 - Phase 3

## Production-Grade Dynamic Dashboard and Domain-Aware Agents

This phase builds on the Phase 2 analysis pipeline and makes it work with different types of business datasets.

The system first looks at the incoming CSV file and identifies its domain, important columns, and main metrics. It then cleans the data, performs the relevant analysis, and generates an HTML dashboard based on the available data.

The main goal of this phase was to make the pipeline flexible enough to work with different domains instead of being designed for only one type of dataset.

## Architecture

```text
Input CSV
   |
   v
Domain Configuration Agent
   |
   v
Orchestrator
   |
   +--> Clean Agent
   |
   +--> Analysis Agent
   |
   +--> Dashboard Agent
            |
            v
     Generated Dashboard
```

## Main Components

### Domain Configuration Agent

This agent examines the dataset before the main pipeline starts. It identifies:

* The dataset domain
* The primary metric
* Date column
* ID column
* Numeric columns
* Useful dimensions
* Success metrics
* Recommended analysis areas

The configuration is then passed to the other agents so they can perform analysis according to the dataset.

### Clean Agent

The Clean Agent prepares the dataset for analysis. It handles:

* CSV loading
* Column name standardization
* Data type detection
* Numeric conversion
* Missing values
* Duplicate rows
* Infinite values
* Date validation
* Cleaning reports

The cleaning process is designed to avoid removing values just because they look unusual. For example, negative values are not automatically removed because they can be valid business values such as losses or adjustments.

### Analysis Agent

The Analysis Agent performs the main calculations and then generates business insights.

Depending on the detected domain, it can perform:

* Domain-specific metric calculations
* Dimension analysis
* Time-trend analysis
* Top and bottom performer analysis
* Inventory risk analysis
* Automatic observations
* Business insights
* Recommendations

The numerical results are calculated using Python first. The AI is then given these verified results to generate the final insights, which helps reduce unsupported or invented statistics.

### Dashboard Agent

The Dashboard Agent creates the final HTML dashboard from the analysis results.

The dashboard is generated according to the available data, so different datasets can produce different:

* KPI cards
* Charts
* Performance sections
* Insights
* Recommendations

This allows the same dashboard agent to be used for different business domains.

## Supported Domains

The pipeline was tested using five different types of business datasets.

| Domain            | Dataset                    | Main Focus                                   |
| ----------------- | -------------------------- | -------------------------------------------- |
| Retail Sales      | Superstore                 | Sales, profit, products, categories, regions |
| E-Commerce Orders | Brazilian E-Commerce/Olist | Orders, status, delivery, cancellation       |
| Inventory         | Logistics Warehouse        | Stock, reorder points, demand, replenishment |
| Restaurant Sales  | Restaurant Sales           | Revenue, products, quantity, payment methods |
| SaaS/Subscription | SaaS Subscription Dataset  | MRR, ARR, churn, plans, subscriptions        |

## Testing

The complete pipeline was run on all five datasets.

### Retail Sales

* 9,994 records
* Sales and profit analysis
* 48 monthly trend periods
* Product, category, customer, and regional analysis
* Dynamic dashboard generated successfully

### Inventory

* 3,204 records
* Stock and reorder analysis
* 240 items were at or below their reorder point
* 7.49% replenishment percentage
* Inventory dimension analysis
* Dynamic dashboard generated successfully

### E-Commerce Orders

* 99,441 records
* 99,441 unique orders
* 99,441 unique customers
* 96,478 delivered orders
* 97.02% delivery completion rate
* 0.63% cancellation rate
* 0.61% unavailable-order rate
* 12.56-day average delivery time
* 91.89% on-time delivery rate
* 25 time-trend periods
* Order status analysis
* Dynamic dashboard generated successfully

### Restaurant Sales

* 254 records
* Revenue calculated using price × quantity
* Product analysis
* Purchase type and payment method analysis
* Manager and city analysis
* Monthly revenue trends
* Dynamic dashboard generated successfully

### SaaS/Subscription

* 5,000 records
* MRR and ARR analysis
* Seat and subscription analysis
* Churn, upgrade, and downgrade analysis
* Trial and auto-renewal analysis
* Plan and billing-frequency analysis
* Dynamic dashboard generated successfully

## Malformed Data Handling

A separate malformed dataset was also tested to see how the pipeline behaves when the input contains incomplete or unexpected data.

The pipeline handled the dataset without crashing and still generated an output dashboard.

This was included to make sure that an imperfect dataset does not completely stop the pipeline.

## AI and Fallback Behavior

The Analysis Agent uses Groq for generating business insights when the API is available.

The API key is loaded through the `GROQ_API_KEY` environment variable.

If the API is unavailable or the AI generation fails, the system uses predefined deterministic fallback logic to generate domain-specific insights and recommendations.

This means the dashboard can still be generated even when the external AI service is unavailable.

## Project Structure

```text
project2-phase3/
|
+-- agents/
|   +-- domain_config_agent.py
|   +-- clean_agent.py
|   +-- analysis_agent.py
|   +-- dashboard_agent.py
|
+-- test-datasets/
|   +-- Sample - Superstore.csv
|   +-- inventory_warehouse.csv
|   +-- ecommerce_orders.csv
|   +-- restaurant_sales.csv
|   +-- saas_subscriptions.csv
|   +-- cleaned_*.csv
|
+-- generated-dashboard/
|
+-- assets/
|   +-- prompt-evolution-log.md
|   +-- flow-diagram.png
|   +-- dataset1-result.png
|   +-- dataset2-result.png
|   +-- dataset3-result.png
|   +-- dataset4-result.png
|   +-- dataset5-result.png
|
+-- main.py
+-- requirements.txt
+-- README.md
```

## Running the Project

Open PowerShell in the `project2-phase3` folder.

Install the required packages:

```powershell
pip install -r requirements.txt
```

Run the pipeline:

```powershell
python main.py
```

A specific dataset can also be provided:

```powershell
python main.py "test-datasets/ecommerce_orders.csv"
```

The generated dashboards are saved in:

```text
generated-dashboard/
```

## Prompt Evolution

The analysis prompt was improved during development as more datasets were tested.

The main stages were:

1. Generic business analysis
2. Adding domain-specific instructions
3. Using verified metrics and reducing unsupported claims
4. Adding fallback behavior when AI is unavailable

The details are documented in:

```text
assets/prompt-evolution-log.md
```

## Production-Grade Features

The Phase 3 implementation includes:

* Automatic domain detection
* Domain-specific configuration
* Dynamic analysis
* Dynamic dashboard generation
* Verified metric calculations
* AI-generated insights
* AI fallback behavior
* Handling of malformed data
* Consistent output structure
* Testing across five different domains
* Prompt version tracking
* Domain alias normalization for more reliable domain routing

## Output

For a dataset, the pipeline produces:

1. A cleaned CSV file
2. Domain configuration
3. Cleaning results
4. Verified analysis results
5. Business insights
6. Recommendations
7. A generated HTML dashboard
