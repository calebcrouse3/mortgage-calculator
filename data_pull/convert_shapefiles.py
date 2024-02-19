import geopandas as gpd

gdf = gpd.read_file("../data/shapefiles/tl_2020_us_zcta520.shp")

tolerance = .1  # Adjust as needed
simplified_geometry = gdf.simplify(tolerance)
simplified_gdf = gpd.GeoDataFrame(geometry=simplified_geometry, crs=gdf.crs)
simplified_gdf = simplified_gdf.merge(gdf.drop(columns='geometry'), left_index=True, right_index=True)

simplified_gdf.to_file("../data/simplified_zipcode_geo.json", driver='GeoJSON')
