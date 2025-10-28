import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# 🔹 PostgreSQL connection (edit username, password, dbname accordingly)
engine = create_engine(DATABASE_URL)

# 🔹 Excel file path
file_path = "Product_List.xlsx"

df = pd.read_excel(file_path)

# 🔹 Clean column names (remove extra spaces)
df.columns = df.columns.str.strip()

# 🔹 Rename Excel columns to match PostgreSQL table
df = df.rename(columns={
    "Plant Name": "scientific_name",
    "Disease": "disease",
    "Scientific Name": "disease_scientific_name",
    "Product Link": "product_link",
    "Product Name": "product_name",
    "How to use": "how_to_use",
    "Product Image": "product_image"
})

df.to_sql("products", engine, if_exists="append", index=False)

print("✅ Data successfully imported into PostgreSQL 'products' table!")
