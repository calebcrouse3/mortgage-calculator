from math import *

import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from mortgage_calculator.utils import fig_display
from state_fips import state_fips_codes

st.set_page_config(layout="wide")

@st.cache_data
def load_zip_data(path):
    zip_data = pd.read_csv(path, dtype={'zip_code': str})
    return zip_data

@st.cache_data
def load_geo_json(path):
    with open(path) as geo:
        return json.load(geo)

zip_geo = load_geo_json("./data/simplified_zipcode_geo.json")
zip_data = load_zip_data("./data/processed_census_data.csv")
zip_states = load_zip_data("./data/state_zip_map.csv")

# join the zip data with the state data
zip_data = zip_data.merge(zip_states, on="zip_code")

def get_filtered_geo(zip_codes):
    filtered_geo = {}
    filtered_geo["type"] = zip_geo["type"]
    filtered_geo["crs"] = zip_geo["crs"]
    filtered_geo["features"] = []

    for i in range(len(zip_geo["features"])):
        shape = zip_geo["features"][i]
        if shape["id"] in zip_codes:
            filtered_geo["features"].append(shape)

    return filtered_geo


with st.sidebar:
    with st.form(key="form"):
        st.title("Zip Code Data")
        st.write("This app displays zip code data for the USA")
        st.write("Select the states you want to display data for")
        target_states = st.multiselect("Select States", options=state_fips_codes.keys(), default=["Texas"])
        colored_value = st.selectbox("Select the value to color the map by", options=zip_data.columns, index=1)
        submit_button = st.form_submit_button(label="Submit")

target_state_codes = [int(state_fips_codes[state]) for state in target_states]

filtered_zip_data = zip_data[zip_data["state"].isin(target_state_codes)]
filtered_zip_codes = filtered_zip_data["zip_code"].values
filtered_geo = get_filtered_geo(filtered_zip_codes)


# Creating the choropleth map
fig = px.choropleth(filtered_zip_data,
                    geojson=filtered_geo,
                    locations='zip_code', # This column in your CSV should match the GeoJSON
                    color=colored_value, # Data column to display
                    color_continuous_scale="Viridis",
                    scope="usa",
                    height=800,
                    # make background transparent
                    )

fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(
    title_text='USA Zip Code Data',
    plot_bgcolor='rgba(0,0,0,0)',  # Set background color to transparent
    geo=dict(
        bgcolor='rgba(0,0,0,0)',  # Set map background color to transparent
    )
)

st.plotly_chart(fig, use_container_width=True)
