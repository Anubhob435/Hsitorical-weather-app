import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Get API key from environment variables
api_key = os.getenv('OPENWEATHER_API_KEY')

# Define the API link
api_link = f"https://api.openweathermap.org/data/3.0/onecall/overview?lon=-11.8092&lat=51.509865&appid=8f595392e9c2431cc79b082bda23c905"

# Fetch data from the API
response = requests.get(api_link)

# Check if the request was successful
if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=4))  # Pretty print the JSON response
else:
    print(f"Error fetching data from API: {response.status_code}")