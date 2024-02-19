from math import *

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import json

st.set_page_config(layout="wide")

st.write("make some maps")

# Load the population data
df_population = pd.read_csv('us_county_population.csv')

# Load your GeoJSON file (make sure the path is correct)
with open('counties_geojson.json') as geo:
    counties_geojson = json.load(geo)

# Creating the choropleth map
fig = px.choropleth(df_population,
                    geojson=counties_geojson,
                    locations='County', # This column in your CSV should match the GeoJSON
                    color='Population', # Data column to display
                    color_continuous_scale="Viridis",
                    scope="usa")

fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(title_text='USA County Population')
fig.show()