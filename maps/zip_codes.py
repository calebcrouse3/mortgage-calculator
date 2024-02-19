import folium

# Initialize the map centered at a geographic location
m = folium.Map(location=[40.7128, -74.0060], zoom_start=10)

# Path to the GeoJSON file (replace with the path to your GeoJSON file)
geojson_path = 'path/to/your/zipcodes.geojson'

# Example data: A dictionary where the key is the zip code and the value is the data metric
# Replace this with your actual data
zip_code_data = {
    '10001': {'Population': 21102, 'MedianHomePrice': 500000},
    # Add more zip codes and metrics here
}

# Function to style the GeoJSON layers
def style_function(feature):
    zip_code = feature['properties']['ZIPCODE']
    data = zip_code_data.get(zip_code, {})
    # You can adjust the fill color based on one of your metrics here, for example
    return {
        'fillColor': '#green' if data else '#gray',
        'color': 'black',
        'weight': 1.5,
        'fillOpacity': 0.5,
    }

# Add the GeoJSON layer to the map
folium.GeoJson(
    geojson_path,
    style_function=style_function,
    # Optional: Add a tooltip or popup to display data on click/hover
    tooltip=folium.GeoJsonTooltip(fields=['ZIPCODE'], aliases=['ZIP Code']),
).add_to(m)

# Save the map to an HTML file
m.save('index.html')