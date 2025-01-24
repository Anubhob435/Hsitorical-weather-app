import requests
import json
import time
from datetime import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv('OPENWEATHER_API_KEY')
CITIES = ['california', 'delhi', 'kolkata', 'london', 'toronto']
URL = 'http://api.openweathermap.org/data/2.5/weather'
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('MONGO_DB_NAME')

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def get_weather_data(city):
    params = {
        'q': city,
        'appid': API_KEY,
        'units': 'metric'
    }
    response = requests.get(URL, params=params)
    return response.json()

def update_weather_records():
    for city in CITIES:
        data = get_weather_data(city)
        record = {
            'timestamp': datetime.now().isoformat()
        }
        if 'main' in data and 'weather' in data:
            record.update({
                'temperature': data['main']['temp'],
                'description': data['weather'][0]['description']
            })
        else:
            record['error'] = 'Could not retrieve data'
        
        # Get the collection for this city and insert the record
        collection = db[city.replace(' ', '_')]  # Replace spaces with underscores for collection names
        collection.insert_one(record)
        print(f"Data inserted for {city}")

if __name__ == '__main__':
    while True:
        try:
            update_weather_records()
            print(f"Updated all cities at {datetime.now().isoformat()}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(600)  # Sleep for 15 minutes