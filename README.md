# Nassau Candy Distributor — Complete Project

## Structure
- `app.py`: interactive Streamlit dashboard
- `analysis.py`: data cleaning, calculations, CSV outputs and report generation
- `requirements.txt`: Python dependencies
- `data/`: put the provided Nassau Candy CSV here
- `outputs/`: generated analysis tables and reports

## Setup in PowerShell
Open this folder in VS Code and run:

```powershell
python -m pip install -r requirements.txt
python analysis.py
python -m streamlit run app.py
```

Open the local URL printed by Streamlit (usually `http://localhost:8501`).

## Dashboard sections
1. Product profitability overview
2. Division performance
3. Cost versus sales and margin risks
4. Revenue/profit Pareto analysis
5. Region/state concentration and factory mapping
6. Data validation and cleaned data preview
7. Monthly sales and gross-margin trends

## Metrics
- Gross Margin (%) = Gross Profit / Sales × 100
- Profit per Unit = Gross Profit / Units
- Revenue Contribution (%) = Product Sales / Total Sales × 100
- Profit Contribution (%) = Product Gross Profit / Total Gross Profit × 100
- Cost Ratio (%) = Cost / Sales × 100
- Margin volatility = standard deviation of monthly gross margins

## Notes
Column names with spaces or underscores are normalized. Dates use day-first parsing, matching the supplied date examples. Negative gross profit is retained as a possible loss. Profit mismatches are reported rather than silently overwritten. Factory coordinates and product mappings come from the assignment brief, not the transaction CSV. Regional concentration does not by itself prove shipping-route inefficiency.
