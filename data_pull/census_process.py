"""This does some light processing of the data downloaded from the US Census Bureau. And writes
the processed data to the data/processed_census_data.csv file."""

import pandas as pd

df = pd.read_csv("../data/census_data.csv", dtype={"zip_code": str})
df = df.loc[df["Total Population"] > 0]
mask_columns = [x for x in  df.columns if x not in ["zip_code"]]

df[mask_columns] = df[mask_columns].mask(df[mask_columns] < 0)
df.to_csv("../data/processed_census_data.csv", index=False)