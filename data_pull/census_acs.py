"""
This script pulls data from the US Census American Community Survey and writes it to a CSV file.
"""

import requests
import csv

API_KEY = '89d7f2e8a5581f6421d8f4a16e6486cd86e46f6a'

url = f'https://api.census.gov/data/2022/acs/acs5'

variables_dict = {
    'B01001_001E': "Total Population",
    'B01003_001E': "Population Density",
    'B01002_001E': "Median Age",
    'B19013_001E': "Median Household Income",
    'B25064_001E': "Median Gross Rent",
    'B25077_001E': "Median Home Value",
    'B25003_002E': "Percentage of Owner-occupied Housing Units",
    'B25002_003E': "Percentage of Vacant Housing Units",
    'B15003_001E': "Educational Attainment - Total Population",
    'B15003_002E': "Educational Attainment - High School Diploma",
    'B15003_022E': "Educational Attainment - Bachelor's Degree",
    'B15003_023E': "Educational Attainment - Advanced Degree",
    'B01001_003E': "Age Distribution - Under 18 Years",
    'B01001_004E': "Age Distribution - 18 to 24 Years",
    'B01001_005E': "Age Distribution - 25 to 34 Years",
    'B01001_006E': "Age Distribution - 35 to 44 Years",
    'B01001_007E': "Age Distribution - 45 to 54 Years",
    'B01001_008E': "Age Distribution - 55 to 64 Years",
    'B01001_009E': "Age Distribution - 65 to 74 Years",
    'B01001_010E': "Age Distribution - 75 to 84 Years",
    'B01001_011E': "Age Distribution - 85 Years and Over",
    'B11001_001E': "Household Type - Total Households",
    'B11001_002E': "Household Type - Family Households",
    'B11001_007E': "Household Type - Non-family Households",
    'B23025_001E': "Employment Status - Total Population",
    'B23025_003E': "Employment Status - In Labor Force",
    'B23025_004E': "Employment Status - Civilian Labor Force Unemployed",
    #'STATE': "state" this is returning none for somereason. Use state zip map instead from acs5 2019
}

variables_string = ','.join(list(variables_dict.keys()))

variable_names = list(variables_dict.values()) + ["zip_code"]

params = {
    'get': variables_string,  # Variables to retrieve
    'for': 'zip code tabulation area:*',  # Get data for all zip codes
    'key': API_KEY
}

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()

    with open('../data/census_data.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(variable_names)
        # exclude first line of data. Its just malformed column names
        writer.writerows(data[1:])

else:
    print('Failed to retrieve data:', response.status_code, response.text)
