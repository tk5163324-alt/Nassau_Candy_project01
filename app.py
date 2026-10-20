from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Nassau Candy Profitability", page_icon="🍬", layout="wide")
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

st.title("🍬 Nassau Candy Distributor")
st.subheader("Product Line Profitability & Margin Performance Analysis")
st.caption("Interactive dashboard: product profitability, division performance, cost diagnostics, Pareto and data validation.")

FACTORIES = pd.DataFrame([
    {"Factory":"Lot's O' Nuts","Latitude":32.881893,"Longitude":-111.768036},
    {"Factory":"Wicked Choccy's","Latitude":32.076176,"Longitude":-81.088371},
    {"Factory":"Sugar Shack","Latitude":48.119140,"Longitude":-96.181150},
    {"Factory":"Secret Factory","Latitude":41.446333,"Longitude":-90.565487},
    {"Factory":"The Other Factory","Latitude":35.117500,"Longitude":-89.971107},
])
MAPPING = pd.DataFrame([
    ("Chocolate","Nutty Crunch Surprise","Lot's O' Nuts"),
    ("Chocolate","Fudge Mallows","Lot's O' Nuts"),
    ("Chocolate","Scrumdiddlyumptious","Lot's O' Nuts"),
    ("Chocolate","Milk Chocolate","Wicked Choccy's"),
    ("Chocolate","Triple Dazzle Caramel","Wicked Choccy's"),
    ("Sugar","Laffy Taffy","Sugar Shack"),("Sugar","SweeTARTS","Sugar Shack"),
    ("Sugar","Nerds","Sugar Shack"),("Sugar","Fun Dip","Sugar Shack"),
    ("Other","Fizzy Lifting Drinks","Sugar Shack"),
    ("Sugar","Everlasting Gobstopper","Secret Factory"),
    ("Sugar","Hair Toffee","The Other Factory"),
    ("Other","Lickable Wallpaper","Secret Factory"),
    ("Other","Wonka Gum","Secret Factory"),("Other","Kazookles","The Other Factory"),
], columns=["Mapped Division","Mapped Product","Factory"])
ALIASES = {
    "order date":"Order Date","ship date":"Ship Date","division":"Division",
    "product name":"Product Name","sales":"Sales","units":"Units",
    "gross profit":"Gross Profit","cost":"Cost","region":"Region",
    "state/province":"State/Province","city":"City","order id":"Order ID",
    "row id":"Row ID","customer id":"Customer ID","product id":"Product ID",
    "ship mode":"Ship Mode","country/region":"Country/Region","postal code":"Postal Code"
}


def find_csv():
    files = list(DATA.glob("*.csv")) + list(ROOT.glob("*.csv"))

    if not files:
        return None

    preferred = [
        p for p in files
        if "nassau candy distributor" in p.name.lower()
    ]

    if not preferred:
        return files[0]

    # Prefer the original dataset with the most rows.
    for path in preferred:
        try:
            if len(pd.read_csv(path, usecols=[0])) == 10194:
                return path
        except Exception:
            continue

    return preferred[0]


@st.cache_data
def load_data(path, modified):
    df = pd.read_csv(path)
    rename = {}
    for c in df.columns:
        key = str(c).strip().lower().replace("_", " ")
        if key in ALIASES:
            rename[c] = ALIASES[key]
    df = df.rename(columns=rename)
    required = ["Order Date","Division","Product Name","Sales","Units","Gross Profit","Cost"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError("Required column(s) missing: " + ", ".join(missing))
    original_rows = len(df)
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce", dayfirst=True)
    if "Ship Date" in df.columns:
        df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce", dayfirst=True)
    for c in ["Sales","Units","Gross Profit","Cost"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["Division","Product Name"]:
        df[c] = df[c].astype("string").str.strip()
    duplicates = int(df.duplicated().sum())
    df = df.drop_duplicates()
    before = len(df)
    df = df.dropna(subset=["Order Date","Division","Product Name","Sales","Gross Profit","Cost"])
    df = df[(df["Sales"] > 0) & (df["Cost"] >= 0) &
            (df["Units"].isna() | (df["Units"] > 0)) & (df["Gross Profit"] <= df["Sales"])]
    invalid_removed = before - len(df)
    df["Calculated Profit"] = df["Sales"] - df["Cost"]
    df["Profit Difference"] = df["Gross Profit"] - df["Calculated Profit"]
    df["Gross Margin (%)"] = df["Gross Profit"] / df["Sales"] * 100
    df["Profit per Unit"] = (df["Gross Profit"] / df["Units"]).where(df["Units"] > 0)
    df["Cost Ratio (%)"] = df["Cost"] / df["Sales"] * 100
    df["Month"] = df["Order Date"].dt.to_period("M").dt.to_timestamp()
    checks = {
        "Original rows": original_rows, "Rows after cleaning": len(df),
        "Duplicate rows removed": duplicates, "Invalid/missing rows removed": invalid_removed,
        "Gross Profit vs Sales-Cost mismatches (>$0.01)": int((df["Profit Difference"].abs() > .01).sum()),
        "Missing Units remaining": int(df["Units"].isna().sum())
    }
    return df, checks

csv = find_csv()
if csv is None:
    st.error("Dataset not found. Copy your Nassau Candy CSV into this project's data folder.")
    st.code("Nassau_Candy_Complete_Project/data/Nassau Candy Distributor.csv")
    st.stop()
try:
    df, checks = load_data(str(csv), csv.stat().st_mtime)
except Exception as e:
    st.error(f"Dataset loading error: {e}")
    st.stop()

st.sidebar.header("Dashboard Filters")
dmin, dmax = df["Order Date"].min().date(), df["Order Date"].max().date()
dates = st.sidebar.date_input("Select Order Date Range", (dmin,dmax), min_value=dmin, max_value=dmax)
divisions = sorted(df["Division"].dropna().unique().tolist())
chosen_divisions = st.sidebar.multiselect("Select Division", divisions, default=divisions)
search = st.sidebar.text_input("Search Product")
chosen_products = st.sidebar.multiselect("Select Products", sorted(df["Product Name"].dropna().unique()))
threshold = st.sidebar.slider("Minimum acceptable gross margin (%)",0,100,40,5)
f = df.copy()
if isinstance(dates,(tuple,list)) and len(dates)==2:
    f = f[f["Order Date"].between(pd.Timestamp(dates[0]),pd.Timestamp(dates[1])+pd.Timedelta(days=1)-pd.Timedelta(microseconds=1))]
f = f[f["Division"].isin(chosen_divisions)]
if search.strip():
    f = f[f["Product Name"].str.contains(search.strip(), case=False, na=False)]
if chosen_products:
    f = f[f["Product Name"].isin(chosen_products)]
if f.empty:
    st.warning("No records match these filters. Change the filters in the sidebar.")
    st.stop()

sales, gp, cost, units = f["Sales"].sum(), f["Gross Profit"].sum(), f["Cost"].sum(), f["Units"].sum()
margin = gp/sales*100 if sales else 0
st.caption(f"Dataset: {csv.name} | {len(f):,} rows | {f['Product Name'].nunique()} products")
k = st.columns(5)
for col,label,value in zip(k,["Total Sales","Gross Profit","Gross Margin","Units Sold","Total Cost"],
                           [f"${sales:,.2f}",f"${gp:,.2f}",f"{margin:.2f}%",f"{units:,.0f}",f"${cost:,.2f}"]):
    col.metric(label,value)

p = f.groupby(["Division","Product Name"],as_index=False).agg(
    Sales=("Sales","sum"), Gross_Profit=("Gross Profit","sum"), Cost=("Cost","sum"), Units=("Units","sum"))
p["Gross Margin (%)"] = p["Gross_Profit"]/p["Sales"]*100
p["Profit per Unit"] = (p["Gross_Profit"]/p["Units"]).where(p["Units"]>0)
p["Revenue Contribution (%)"] = p["Sales"]/p["Sales"].sum()*100
p["Profit Contribution (%)"] = p["Gross_Profit"]/p["Gross_Profit"].sum()*100 if p["Gross_Profit"].sum() else 0
p["Cost Ratio (%)"] = p["Cost"]/p["Sales"]*100
div = f.groupby("Division",as_index=False).agg(Sales=("Sales","sum"),Gross_Profit=("Gross Profit","sum"),Cost=("Cost","sum"),Units=("Units","sum"))
div["Gross Margin (%)"] = div["Gross_Profit"]/div["Sales"]*100
div["Revenue Contribution (%)"] = div["Sales"]/div["Sales"].sum()*100
div["Profit Contribution (%)"] = div["Gross_Profit"]/div["Gross_Profit"].sum()*100 if div["Gross_Profit"].sum() else 0
tabs = st.tabs(["Product Profitability","Division Performance","Cost & Margin Risks","Pareto Analysis","Region & Factories","Data Validation"])

with tabs[0]:
    a,b = st.columns(2)
    a.plotly_chart(px.bar(p.sort_values("Gross_Profit"),x="Gross_Profit",y="Product Name",color="Division",orientation="h",title="Gross profit by product"),use_container_width=True)
    b.plotly_chart(px.bar(p.sort_values("Gross Margin (%)"),x="Gross Margin (%)",y="Product Name",color="Division",orientation="h",title="Gross margin by product"),use_container_width=True)
    st.dataframe(p.sort_values("Gross_Profit",ascending=False),use_container_width=True,hide_index=True)
    risky = p[(p["Sales"]>=p["Sales"].median())&(p["Gross Margin (%)"]<threshold)]
    st.markdown("#### High-sales / below-threshold-margin products")
    st.dataframe(risky.sort_values("Sales",ascending=False),use_container_width=True,hide_index=True)
    st.download_button("Download product profitability CSV",p.to_csv(index=False).encode(), "product_profitability.csv","text/csv")
with tabs[1]:
    a,b = st.columns(2)
    a.plotly_chart(px.bar(div,x="Division",y="Sales",title="Sales by division"),use_container_width=True)
    b.plotly_chart(px.bar(div,x="Division",y="Gross_Profit",title="Gross profit by division"),use_container_width=True)
    st.plotly_chart(px.bar(div,x="Division",y="Gross Margin (%)",title="Gross margin by division"),use_container_width=True)
    st.dataframe(div,use_container_width=True,hide_index=True)
    st.download_button("Download division summary CSV",div.to_csv(index=False).encode(),"division_summary.csv","text/csv")
with tabs[2]:
    st.plotly_chart(px.scatter(f,x="Sales",y="Cost",color="Division",size="Units",hover_name="Product Name",hover_data=["Gross Profit","Gross Margin (%)"],title="Cost versus sales"),use_container_width=True)
    st.markdown("#### Highest cost-ratio products")
    st.dataframe(p.sort_values("Cost Ratio (%)",ascending=False).head(10),use_container_width=True,hide_index=True)
    st.markdown("#### Products below the selected margin threshold")
    st.dataframe(p[p["Gross Margin (%)"]<threshold].sort_values("Gross Margin (%)"),use_container_width=True,hide_index=True)
with tabs[3]:
    rev = p.sort_values("Sales",ascending=False).copy()
    rev["Cumulative Revenue (%)"] = rev["Sales"].cumsum()/rev["Sales"].sum()*100
    prof = p.sort_values("Gross_Profit",ascending=False).copy()
    prof["Cumulative Profit (%)"] = prof["Gross_Profit"].cumsum()/prof["Gross_Profit"].sum()*100 if prof["Gross_Profit"].sum() else 0
    a,b = st.columns(2)
    a.plotly_chart(px.bar(rev,x="Product Name",y="Sales",color="Division",title="Revenue Pareto"),use_container_width=True)
    b.plotly_chart(px.bar(prof,x="Product Name",y="Gross_Profit",color="Division",title="Profit Pareto"),use_container_width=True)
    st.markdown("Revenue ranked with cumulative contribution")
    st.dataframe(rev,use_container_width=True,hide_index=True)
    st.markdown("Profit ranked with cumulative contribution")
    st.dataframe(prof,use_container_width=True,hide_index=True)
with tabs[4]:
    if "Region" in f.columns:
        region = f.groupby("Region",as_index=False).agg(Sales=("Sales","sum"),Gross_Profit=("Gross Profit","sum"))
        region["Gross Margin (%)"] = region["Gross_Profit"]/region["Sales"]*100
        st.plotly_chart(px.bar(region,x="Region",y="Sales",title="Sales by region"),use_container_width=True)
        st.dataframe(region.sort_values("Sales",ascending=False),use_container_width=True,hide_index=True)
    if "State/Province" in f.columns:
        state = f.groupby("State/Province",as_index=False).agg(Sales=("Sales","sum"),Gross_Profit=("Gross Profit","sum"))
        st.markdown("Top states by sales")
        st.dataframe(state.sort_values("Sales",ascending=False).head(15),use_container_width=True,hide_index=True)
    st.markdown("#### Factory coordinates provided in the assignment")
    st.plotly_chart(px.scatter_geo(FACTORIES,lat="Latitude",lon="Longitude",hover_name="Factory",projection="natural earth",title="Factory locations"),use_container_width=True)
    st.dataframe(FACTORIES,use_container_width=True,hide_index=True)
    st.markdown("#### Product-to-factory mapping")
    def norm(s):
        return str(s).lower().replace("wonka bar -","").replace("wonka bar-","").strip()
    actual = p[["Division","Product Name","Sales","Gross_Profit","Gross Margin (%)"]].copy()
    actual["_key"] = actual["Product Name"].map(norm)
    mapping = MAPPING.copy()
    mapping["_key"] = mapping["Mapped Product"].map(norm)
    mapping = mapping.merge(actual,left_on="_key",right_on="_key",how="left")
    mapping["Mapping status"] = mapping["Product Name"].notna().map({True:"Matched",False:"Not found in current CSV"})
    st.dataframe(mapping.drop(columns="_key"),use_container_width=True,hide_index=True)
    st.download_button("Download factory mapping CSV",mapping.drop(columns="_key").to_csv(index=False).encode(),"product_factory_mapping.csv","text/csv")
with tabs[5]:
    st.dataframe(pd.DataFrame({"Validation check":list(checks.keys()),"Result":list(checks.values())}),use_container_width=True,hide_index=True)
    st.dataframe(f.isna().sum().rename("Missing values").reset_index().rename(columns={"index":"Column"}),use_container_width=True,hide_index=True)
    st.dataframe(f.head(100),use_container_width=True,hide_index=True)
    st.download_button("Download filtered cleaned data CSV",f.to_csv(index=False).encode(),"filtered_cleaned_data.csv","text/csv")

st.markdown("---")
st.header("Monthly Performance & Findings")
monthly = f.groupby("Month",as_index=False).agg(Sales=("Sales","sum"),Gross_Profit=("Gross Profit","sum"))
monthly["Gross Margin (%)"] = monthly["Gross_Profit"]/monthly["Sales"]*100
a,b = st.columns(2)
a.plotly_chart(px.line(monthly,x="Month",y="Sales",markers=True,title="Monthly sales trend"),use_container_width=True)
b.plotly_chart(px.line(monthly,x="Month",y="Gross Margin (%)",markers=True,title="Monthly gross margin trend"),use_container_width=True)
st.metric("Monthly gross-margin volatility (standard deviation)",f"{monthly['Gross Margin (%)'].std():.2f} percentage points" if len(monthly)>1 else "N/A")
if not p.empty:
    top = p.sort_values("Gross_Profit", ascending=False).iloc[0]
    best = p.sort_values("Gross Margin (%)", ascending=False).iloc[0]
    worst = p.sort_values("Gross Margin (%)", ascending=True).iloc[0]
    st.write(f"**Highest gross-profit product:** {top['Product Name']} (${top['Gross_Profit']:,.2f}).")
    st.write(f"**Highest-margin product:** {best['Product Name']} ({best['Gross Margin (%)']:.2f}%).")
    st.write(f"**Lowest-margin product:** {worst['Product Name']} ({worst['Gross Margin (%)']:.2f}%).")
st.caption("Regional concentration is descriptive. The transaction dataset alone does not prove factory-level route efficiency or shipping congestion.")
