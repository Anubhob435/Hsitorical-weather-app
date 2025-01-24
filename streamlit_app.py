import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import mysql.connector
import requests
import json
from datetime import datetime
import pytz
import time
from pymongo import MongoClient
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database and API configurations
db_config = {
    "host": os.getenv('MYSQL_HOST'),
    "user": os.getenv('MYSQL_USER'),
    "password": os.getenv('MYSQL_PASSWORD'),
    "database": os.getenv('MYSQL_DATABASE')
}

api_key = os.getenv('OPENWEATHER_API_KEY')

# Add MongoDB configurations
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('MONGO_DB_NAME')

# Initialize MongoDB connection
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client[DB_NAME]

def get_current_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            "temperature": round(data["main"]["temp"] - 273.15, 2),
            "humidity": data["main"]["humidity"],
            "description": data["weather"][0]["description"]
        }
    return None

def get_coordinates(city):
    """Get latitude and longitude for a city"""
    geocoding_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={api_key}"
    response = requests.get(geocoding_url)
    if response.status_code == 200:
        data = response.json()
        if data:
            return {
                'lat': data[0]['lat'],
                'lon': data[0]['lon']
            }
    return None

def get_historical_weather(lat, lon, start_date, end_date):
    """Fetch historical weather data for given coordinates and date range"""
    historical_data = []
    current_date = start_date
    
    while current_date <= end_date:
        timestamp = int(datetime.combine(current_date, datetime.min.time()).timestamp())
        url = f"https://api.openweathermap.org/data/3.0/onecall/timemachine?lat={lat}&lon={lon}&dt={timestamp}&appid={api_key}"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            temp_celsius = round(data['data'][0]['temp'] - 273.15, 2)
            humidity = data['data'][0]['humidity']
            
            historical_data.append({
                'timestamp': current_date,
                'temperature_celsius': temp_celsius,
                'humidity': humidity
            })
        
        current_date += timedelta(days=1)
        time.sleep(1)  # Avoid API rate limiting
    
    return historical_data

def save_to_json(data, city):
    try:
        # Read existing records
        try:
            with open('records.json', 'r') as f:
                records = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            records = {}
        
        # Update records
        if city not in records:
            records[city] = []
        records[city].append({
            **data,
            "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Keep only last 100 records per city
        records[city] = records[city][-100:]
        
        # Save updated records
        with open('records.json', 'w') as f:
            json.dump(records, f, indent=4)
    except Exception as e:
        st.error(f"Error saving to JSON: {e}")

def fetch_weather_data():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM weather ORDER BY timestamp"
        cursor.execute(query)
        data = cursor.fetchall()
        conn.close()
        return data
    except mysql.connector.Error as err:
        st.error(f"Database Error: {err}")
        return None

def fetch_mongo_data(city):
    """Fetch all weather data from MongoDB for a specific city"""
    collection = mongo_db[city.replace(' ', '_')]
    data = list(collection.find({}, {'_id': 0}).sort('timestamp', 1))  # Sort by timestamp ascending
    return data

# Set page config
st.set_page_config(page_title="Weather Dashboard", layout="wide")

# Add custom CSS for margins
st.markdown("""
    <style>
        .main > div {
            padding-left: 100px;
            padding-right: 100px;
        }
    </style>
""", unsafe_allow_html=True)

# Create a container for the main content
main_container = st.container()

with main_container:
    st.title("Weather Monitoring Dashboard")

    # Get available cities from MongoDB
    available_cities = [coll for coll in mongo_db.list_collection_names()]

    # City selection dropdown
    city_input = st.selectbox("Select City", available_cities)
    update_button = st.button("Update Weather Data")

    if update_button or 'last_update' not in st.session_state:
        with st.spinner('Fetching current weather...'):
            current_weather = get_current_weather(city_input)
            if current_weather:
                st.session_state.last_update = current_weather
                save_to_json(current_weather, city_input)
            else:
                st.error(f"Could not fetch current weather for {city_input}")

    # Display current weather
    st.header("Current Weather")
    if 'last_update' in st.session_state:
        current_weather = st.session_state.last_update
        # Display last update time
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime("%Y-%m-%d %I:%M:%S %p IST")
        st.write(f"Last Updated: {current_time}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Temperature", f"{current_weather['temperature']}°C")
        with col2:
            st.metric("Humidity", f"{current_weather['humidity']}%")
        with col3:
            st.metric("Condition", current_weather['description'])

    # Historical Data Section
    st.header("Historical Weather Data")

    # Fetch and display MongoDB historical data
    with st.spinner('Fetching historical data...'):
        mongo_data = fetch_mongo_data(city_input)
        
        if mongo_data:
            # Temperature trend
            fig_temp = go.Figure()
            fig_temp.add_trace(go.Scatter(
                x=[record['timestamp'] for record in mongo_data],
                y=[record['temperature'] for record in mongo_data],
                mode='lines+markers',
                name='Temperature'
            ))
            fig_temp.update_layout(
                title=f'Historical Temperature Trends for {city_input}',
                xaxis_title='Timestamp',
                yaxis_title='Temperature (°C)'
            )
            st.plotly_chart(fig_temp)

            # Show recent records
            st.subheader("Recent Weather Records")
            st.table(mongo_data[:5])
        else:
            st.info("No historical data available for this city")
