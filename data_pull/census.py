import requests
import csv

api_key = "89d7f2e8a5581f6421d8f4a16e6486cd86e46f6a"
dataset = 'acs/acs5'
year = '2019'
base_url = f'https://api.census.gov/data/{year}/{dataset}'

variable_names = ["total_population", "median_home_value", "median_gross_rent", "state", "zip_code"]

variables = [
    "B01003_001E",  # Total Population
    "B25077_001E",  # Median Value of Owner-Occupied Housing Units
    "B19013_001E",  # Median Household Income
    #"B25064_001E",  # Median Gross Rent
    #"B25001_001E",  # Total Housing Units
    #"B25001_002E",  # Occupied Housing Units
    #"B25001_003E",  # Vacant Housing Units
    #"B25002_001E",  # Occupancy Status
    #"B25003_001E",  # Total Housing Units
    #"B25003_002E",  # Owner-Occupied Units
    #"B25003_003E",  # Renter-Occupied Units
]

variables = ','.join(variables)

# request all zip codes
geography = 'zip code tabulation area:*'


url = f'{base_url}?get={variables}&for={geography}&key={api_key}'
response = requests.get(url)

if response.status_code == 200:
    data = response.json()

    with open('../data/census_data.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(variable_names)
        # exclude first line of data. Its just malformed column names
        writer.writerows(data[1:])

else:
    print('Failed to retrieve data:', response.status_code)
