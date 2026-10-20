# Nassau Candy Distributor — Research / EDA Report

## Objective
Assess product and division profitability, margins, cost structure, concentration, and potential margin risks.

## Method
Source file: `Nassau Candy Distributor.csv`. Original rows: 10,194; rows after cleaning: 10,194. Dates were parsed with day-first interpretation. Exact duplicate rows and records with missing required fields, non-positive sales, negative cost, invalid units, or gross profit greater than sales were excluded. Negative gross profit was retained as a potential loss. Source profit is compared with Sales minus Cost and mismatches are reported.

## Overall results
- Total Sales: $141,783.63
- Gross Profit: $93,442.80
- Overall Gross Margin: 65.91%
- Total Cost: $48,340.83
- Units: 38,654
- Monthly gross-margin standard deviation: 0.53 percentage points.

## Product findings
- Highest gross-profit product: **Wonka Bar -Scrumdiddlyumptious** (Chocolate), $19,357.50.
- Highest-margin product: **Everlasting Gobstopper**, 80.00%.
- Lowest-margin product: **Kazookles**, 7.69%.

## Division, Pareto and risk analysis
See `division_summary.csv`, `revenue_pareto.csv`, `profit_pareto.csv`, and `product_profitability.csv`. Pareto tables rank products and calculate cumulative contribution to identify the group crossing 80%.

## Recommendations
1. Protect pricing and availability for products with strong gross profit and margin.
2. Investigate pricing, cost and promotion assumptions for high-sales / low-margin products.
3. Monitor monthly margin changes and investigate unusual declines.
4. Use Pareto contribution to monitor dependence on a small group of products.
5. Review product/factory mapping matches before operational use.

## Limitations
The transaction dataset does not contain factory-level transaction links, route distance, freight cost, capacity or delivery performance. Factory coordinates and product-to-factory mapping are provided separately by the assignment. Region/state concentration does not prove shipping congestion or route inefficiency.
