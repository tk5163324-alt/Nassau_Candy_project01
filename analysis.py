from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)
ALIASES = {"order date":"Order Date","ship date":"Ship Date","division":"Division","product name":"Product Name",
"sales":"Sales","units":"Units","gross profit":"Gross Profit","cost":"Cost","region":"Region",
"state/province":"State/Province","city":"City","order id":"Order ID","row id":"Row ID",
"customer id":"Customer ID","product id":"Product ID","ship mode":"Ship Mode","country/region":"Country/Region","postal code":"Postal Code"}

def main():
    files = list(DATA.glob("*.csv")) + list(ROOT.glob("*.csv"))
    if not files:
        raise FileNotFoundError("Put the Nassau Candy CSV in the project's data folder.")
    csv = next((p for p in files if "nassau candy distributor" in p.name.lower()), files[0])
    df = pd.read_csv(csv)
    df = df.rename(columns={c:ALIASES[str(c).strip().lower().replace("_"," ")] for c in df.columns if str(c).strip().lower().replace("_"," ") in ALIASES})
    required = ["Order Date","Division","Product Name","Sales","Units","Gross Profit","Cost"]
    missing = [c for c in required if c not in df.columns]
    if missing: raise ValueError(f"Missing required columns: {missing}")
    original = len(df)
    df["Order Date"] = pd.to_datetime(df["Order Date"],errors="coerce",dayfirst=True)
    for c in ["Sales","Units","Gross Profit","Cost"]: df[c] = pd.to_numeric(df[c],errors="coerce")
    for c in ["Division","Product Name"]: df[c] = df[c].astype("string").str.strip()
    duplicates = int(df.duplicated().sum()); df = df.drop_duplicates()
    before = len(df)
    df = df.dropna(subset=["Order Date","Division","Product Name","Sales","Gross Profit","Cost"])
    df = df[(df["Sales"]>0)&(df["Cost"]>=0)&(df["Units"].isna()|(df["Units"]>0))&(df["Gross Profit"]<=df["Sales"])]
    removed = before-len(df)
    df["Calculated Profit"] = df["Sales"]-df["Cost"]
    df["Profit Difference"] = df["Gross Profit"]-df["Calculated Profit"]
    df["Gross Margin (%)"] = df["Gross Profit"]/df["Sales"]*100
    df["Profit per Unit"] = (df["Gross Profit"]/df["Units"]).where(df["Units"]>0)
    df["Cost Ratio (%)"] = df["Cost"]/df["Sales"]*100
    df["Month"] = df["Order Date"].dt.to_period("M").dt.to_timestamp()
    product = df.groupby(["Division","Product Name"],as_index=False).agg(Sales=("Sales","sum"),Gross_Profit=("Gross Profit","sum"),Cost=("Cost","sum"),Units=("Units","sum"))
    product["Gross Margin (%)"] = product["Gross_Profit"]/product["Sales"]*100
    product["Profit per Unit"] = (product["Gross_Profit"]/product["Units"]).where(product["Units"]>0)
    product["Revenue Contribution (%)"] = product["Sales"]/product["Sales"].sum()*100
    product["Profit Contribution (%)"] = product["Gross_Profit"]/product["Gross_Profit"].sum()*100 if product["Gross_Profit"].sum() else 0
    product["Cost Ratio (%)"] = product["Cost"]/product["Sales"]*100
    product = product.sort_values("Gross_Profit",ascending=False)
    division = df.groupby("Division",as_index=False).agg(Sales=("Sales","sum"),Gross_Profit=("Gross Profit","sum"),Cost=("Cost","sum"),Units=("Units","sum"))
    division["Gross Margin (%)"] = division["Gross_Profit"]/division["Sales"]*100
    division["Revenue Contribution (%)"] = division["Sales"]/division["Sales"].sum()*100
    division["Profit Contribution (%)"] = division["Gross_Profit"]/division["Gross_Profit"].sum()*100 if division["Gross_Profit"].sum() else 0
    monthly = df.groupby("Month",as_index=False).agg(Sales=("Sales","sum"),Gross_Profit=("Gross Profit","sum"))
    monthly["Gross Margin (%)"] = monthly["Gross_Profit"]/monthly["Sales"]*100
    revenue = product.sort_values("Sales",ascending=False).copy()
    revenue["Cumulative Revenue (%)"] = revenue["Sales"].cumsum()/revenue["Sales"].sum()*100
    profit = product.sort_values("Gross_Profit",ascending=False).copy()
    profit["Cumulative Profit (%)"] = profit["Gross_Profit"].cumsum()/profit["Gross_Profit"].sum()*100 if profit["Gross_Profit"].sum() else 0
    checks = pd.DataFrame([
        ("Original rows",original),
        ("Rows after cleaning",len(df)),
        ("Duplicate rows removed",duplicates),
        ("Invalid/missing rows removed",removed),
        ("Profit mismatches > $0.01",int((df["Profit Difference"].abs()>.01).sum())),
        ("Missing Units remaining",int(df["Units"].isna().sum()))
    ],
    columns=["Check","Result"])
    for name,table in [("cleaned_data",df),
        ("product_profitability",product),
        ("division_summary",division),
        ("monthly_trends",monthly),
        ("revenue_pareto",revenue),
        ("profit_pareto",profit),
        ("data_validation",checks)]:
        table.to_csv(OUT/f"{name}.csv",index=False)
    sales,gp,cost,units = df["Sales"].sum(),df["Gross Profit"].sum(),df["Cost"].sum(),df["Units"].sum()
    top = product.iloc[0]
    best = product.sort_values("Gross Margin (%)", ascending=False).iloc[0]
    worst = product.sort_values("Gross Margin (%)", ascending=True).iloc[0]
    vol = monthly["Gross Margin (%)"].std() if len(monthly)>1 else 0
    report = f"""# Nassau Candy Distributor — Research / EDA Report


## Method
Source file: `{csv.name}`. Original rows: {original:,}; rows after cleaning: {len(df):,}. Dates were parsed with day-first interpretation. Exact duplicate rows and records with missing required fields, non-positive sales, negative cost, invalid units, or gross profit greater than sales were excluded. Negative gross profit was retained as a potential loss. Source profit is compared with Sales minus Cost and mismatches are reported.

## Overall results
- Total Sales: ${sales:,.2f}
- Gross Profit: ${gp:,.2f}
- Overall Gross Margin: {gp/sales*100 if sales else 0:.2f}%
- Total Cost: ${cost:,.2f}
- Units: {units:,.0f}
- Monthly gross-margin standard deviation: {vol:.2f} percentage points.

## Product findings
- Highest gross-profit product: **{top['Product Name']}** ({top['Division']}), ${top['Gross_Profit']:,.2f}.
- Highest-margin product: **{best['Product Name']}**, {best['Gross Margin (%)']:.2f}%.
- Lowest-margin product: **{worst['Product Name']}**, {worst['Gross Margin (%)']:.2f}%.


"""
    (OUT/"research_eda_report.md").write_text(report,encoding="utf-8")
    summary = f"""# Executive Summary — Nassau Candy Profitability Analysis

## Performance snapshot
- **Sales:** ${sales:,.2f}
- **Gross Profit:** ${gp:,.2f}
- **Gross Margin:** {gp/sales*100 if sales else 0:.2f}%
- **Cost:** ${cost:,.2f}
- **Units sold:** {units:,.0f}

## Key products
- **Gross-profit leader:** {top['Product Name']} — ${top['Gross_Profit']:,.2f}.
- **Margin leader:** {best['Product Name']} — {best['Gross Margin (%)']:.2f}%.
- **Margin review candidate:** {worst['Product Name']} — {worst['Gross Margin (%)']:.2f}%.
"""
    (OUT/"executive_summary.md").write_text(summary,encoding="utf-8")
    print(f"Loaded {csv.name}; original rows={original:,}; cleaned rows={len(df):,}")
    print(f"Sales=${sales:,.2f}; Gross Profit=${gp:,.2f}; Margin={gp/sales*100 if sales else 0:.2f}%")
    print(f"Reports and CSV outputs saved to {OUT}")

if __name__ == "__main__":
    main()
