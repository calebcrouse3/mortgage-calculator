"""
For whatever reason, the acs5 2019 dataset gives state and zip codes which can be used
as a mapping
"""


import requests
import csv

API_KEY = '89d7f2e8a5581f6421d8f4a16e6486cd86e46f6a'

url = f'https://api.census.gov/data/2019/acs/acs5'

params = {
    'get': 'STATE',
    'for': 'zip code tabulation area:*',  # Get data for all ZCTAs
    'key': API_KEY
}

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()

    with open('../data/state_zip_map.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["state", "state_repeated", "zip_code"])
        writer.writerows(data[1:])


else:
    print('Failed to retrieve data:', response.status_code, response.text)
