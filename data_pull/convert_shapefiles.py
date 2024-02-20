"""
This script converts the shapefiles to a geojson file and simplifies the geometry to reduce the file size.
It also adds the zip code as the id for each feature in the geojson file which is required for the 
mapbox choropleth map.
"""


import geopandas as gpd
import json

gdf = gpd.read_file("../data/shapefiles/tl_2020_us_zcta520.shp")

tolerance = .001  # Adjust as needed
simplified_geometry = gdf.simplify(tolerance)
simplified_gdf = gpd.GeoDataFrame(geometry=simplified_geometry, crs=gdf.crs)
simplified_gdf = simplified_gdf.merge(gdf.drop(columns='geometry'), left_index=True, right_index=True)
simplified_gdf.to_file("../data/simplified_zipcode_geo.json", driver='GeoJSON')

def load_geo_json(path):
    with open(path) as geo:
        return json.load(geo)

zip_geo = load_geo_json("../data/simplified_zipcode_geo.json")

for i in range(len(zip_geo["features"])):
   shape = zip_geo["features"][i]
   shape["id"] = shape["properties"]["ZCTA5CE20"]

with open("../data/simplified_zipcode_geo.json", "w") as f:
    json.dump(zip_geo, f, indent=2)
