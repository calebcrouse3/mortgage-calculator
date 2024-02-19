import requests

# Set your API key and endpoint URL here
api_key = 'YOUR_API_KEY'
endpoint = 'https://api.zillow.com/example_endpoint'  # This is a placeholder URL

# Specify parameters for your request (e.g., property ID, address)
parameters = {
    'zpid': '123456',  # Example Zillow Property ID
    'address': '123 Main St',
    'citystatezip': 'City, State, ZIP'
}

# Add your API key to the request headers or parameters as required by the API
headers = {
    'Authorization': f'Bearer {api_key}'
}

# Make the API request
response = requests.get(endpoint, params=parameters, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Process the JSON response
    data = response.json()
    print(data)
else:
    print('Failed to retrieve data:', response.status_code)
