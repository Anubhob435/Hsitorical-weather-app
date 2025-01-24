import os
from dotenv import load_dotenv
import mysql.connector

# Load environment variables
load_dotenv()

# Database connection details
db_config = {
    "host": os.getenv('MYSQL_HOST'),
    "user": os.getenv('MYSQL_USER'),
    "password": os.getenv('MYSQL_PASSWORD'),
    "database": os.getenv('MYSQL_DATABASE')
}

# Test the connection
try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    print("Successfully connected to the database!")
    conn.close()
except mysql.connector.Error as err:
    print(f"Error: {err}")


def query_weather_data():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Fetch last 5 records
        query = "SELECT * FROM weather ORDER BY timestamp DESC LIMIT 5"
        cursor.execute(query)
        rows = cursor.fetchall()

        print("Last 5 weather records:")
        for row in rows:
            print(row)

        conn.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")

# Run the query function
query_weather_data()
