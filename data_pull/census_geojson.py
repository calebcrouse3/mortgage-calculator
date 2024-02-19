import requests
from zipfile import ZipFile
from io import BytesIO
import geopandas as gpd


DATA_PATH = '../data/shapefiles/'
shapefile_url = f"https://www2.census.gov/geo/tiger/TIGER2020/ZCTA520/tl_2020_us_zcta520.zip"
response = requests.get(shapefile_url)

if response.status_code == 200:
    with ZipFile(BytesIO(response.content)) as thezip:
        thezip.extractall(path=DATA_PATH)
    print("Shapefile downloaded successfully")
else:
    print(f"Failed to download the shapefile. Status code: {response.status_code}")
