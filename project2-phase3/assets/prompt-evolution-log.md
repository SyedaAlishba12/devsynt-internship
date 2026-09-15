# Prompt Evolution Log

## Purpose

The analysis prompt was improved during Phase 3 as the pipeline was tested with different business datasets.

The main focus was to make the AI understand the detected domain, use the calculated results correctly, and produce useful insights without making up numbers.

## Version 1 - Generic Business Analysis

The first version used a general business-analysis prompt.

It asked the AI to look at the analysis results and provide business insights and recommendations.

### Problems noticed

* The prompt was too general for different types of datasets.
* It did not clearly distinguish between sales, inventory, restaurant, and subscription data.
* The AI could focus on metrics that were not relevant to the dataset.
* Different domains needed different business terminology.

## Version 2 - Domain-Aware Analysis

The prompt was then updated with separate instructions for the five supported domains:

* Retail sales
* E-commerce orders
* Inventory
* Restaurant sales
* SaaS/subscriptions

### Changes made

For example:

* E-commerce analysis focuses on order status, delivery, cancellation, unavailable orders, and delivery performance.
* Inventory analysis focuses on stock levels, reorder points, demand, lead time, and replenishment.
* Retail analysis focuses on sales, profit, products, categories, customers, regions, and trends.
* Restaurant analysis focuses on revenue, quantity, price, products, purchase types, payment methods, managers, and cities.
* SaaS analysis focuses on MRR, ARR, seats, plans, churn, upgrades, downgrades, trials, and auto-renewal.

This made the generated insights more relevant to the dataset being analyzed.

## Version 3 - Verified Metrics

The next change was to make sure the AI relied on the results calculated by the Python analysis code.

The prompt was updated to tell the AI to:

* Use only verified metrics.
* Avoid inventing numbers.
* Avoid discussing metrics that were not available.
* Keep insights focused on the actual analysis.
* Avoid mentioning a time trend if no usable trend was found.
* Give practical recommendations.

The Analysis Agent also creates verified observations before sending the results to the AI. These observations give the AI a clear set of calculated facts to work with.

## Version 4 - Fallback and Reliability

The final version added stronger fallback behavior.

If the Groq API is unavailable or the AI request fails, the pipeline uses deterministic fallback logic instead of stopping the entire process.

This allows the system to:

* Continue running without the AI service.
* Generate the dashboard normally.
* Keep the output based on calculated results.
* Maintain the same general output structure across different datasets.

During testing, domain aliases were also normalized to stable internal domain names. For example, an AI response using `e-commerce` is normalized to the internal `ecommerce_orders` key so that the correct E-commerce analysis functions are still used.

## Testing

The updated prompt and pipeline were tested with:

1. Retail sales - Superstore
2. E-commerce orders - Brazilian E-Commerce/Olist
3. Inventory - Logistics Warehouse Dataset
4. Restaurant sales - Restaurant Sales Dataset
5. SaaS/subscriptions - SaaS subscription dataset

A malformed dataset was also tested to check how the pipeline handles incomplete or unexpected input.

## Current Prompt Version

**Version 4**

The current version combines:

* Domain-aware instructions
* Verified deterministic metrics
* Domain-specific terminology
* Restrictions against unsupported statistics
* Actionable recommendations
* AI fallback behavior
* Consistent output handling
* Domain alias normalization
