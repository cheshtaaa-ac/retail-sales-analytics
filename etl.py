import pandas as pd
from sqlalchemy import create_engine

# ---------- EXTRACT ----------
df = pd.read_csv(r"D:\Cheshta work\retail_project\Sample - Superstore.csv", encoding="latin-1")
print("Raw rows:", len(df))

# ---------- PROFILE ----------
print("\nNull counts:\n", df.isnull().sum())
print("Duplicate rows:", df.duplicated().sum())

# ---------- CLEAN ----------
df.columns = [c.strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
df = df.drop_duplicates()
df["order_date"] = pd.to_datetime(df["order_date"])  # if dates look wrong, add dayfirst=True
df["ship_date"] = pd.to_datetime(df["ship_date"])
df["postal_code"] = df["postal_code"].astype(str)
df = df.dropna(subset=["order_id", "customer_id", "product_id"])
print("Clean rows:", len(df))

# ---------- TRANSFORM: star schema ----------
dim_customer = df[["customer_id", "customer_name", "segment"]].drop_duplicates("customer_id")

# Some Product IDs map to more than one product name in this dataset
print("Product IDs with multiple names:",
      (df.groupby("product_id")["product_name"].nunique() > 1).sum())
dim_product = df[["product_id", "category", "sub_category", "product_name"]].drop_duplicates("product_id")

dim_location = (df[["country", "region", "state", "city", "postal_code"]]
                .drop_duplicates().reset_index(drop=True))
dim_location["location_key"] = dim_location.index + 1

dates = pd.date_range(df["order_date"].min(), df["order_date"].max())
dim_date = pd.DataFrame({"full_date": dates})
dim_date["date_key"] = dim_date["full_date"].dt.strftime("%Y%m%d").astype(int)
dim_date["order_year"] = dim_date["full_date"].dt.year
dim_date["order_quarter"] = dim_date["full_date"].dt.quarter
dim_date["order_month"] = dim_date["full_date"].dt.month
dim_date["month_name"] = dim_date["full_date"].dt.month_name()

fact = df.merge(dim_location, on=["country", "region", "state", "city", "postal_code"])
fact["order_date_key"] = fact["order_date"].dt.strftime("%Y%m%d").astype(int)
fact_sales = fact[["order_id", "order_date_key", "ship_date", "ship_mode",
                   "customer_id", "product_id", "location_key",
                   "sales", "quantity", "discount", "profit"]]

# ---------- LOAD ----------
engine = create_engine(
    "mssql+pyodbc://@localhost\\SQLEXPRESS/RetailDW"
    "?driver=ODBC+Driver+18+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes",
    fast_executemany=True)

for name, table in [("dim_customer", dim_customer), ("dim_product", dim_product),
                    ("dim_location", dim_location), ("dim_date", dim_date),
                    ("fact_sales", fact_sales)]:
    table.to_sql(name, engine, if_exists="replace", index=False)
    print(f"Loaded {name}: {len(table)} rows")
