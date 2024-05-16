import os
import requests
import pandas as pd
from datetime import datetime, timedelta

# Define constants
START_DATE = "1980-01-01"
TIMEZONE = "Europe/Paris"
DATA_DIR = "weather_data"

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_weather_data(lat, lon, start_date, end_date, timezone):
    print(f"Fetching data for lat={lat}, lon={lon}")

    base_url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "precipitation",
        "timezone": timezone,
    }
    response = requests.get(base_url, params=params)
    response.raise_for_status()  # Check for errors
    return response.json()

def process_data(data):
    df = pd.DataFrame(data["hourly"])
    df["datetime"] = pd.to_datetime(df["time"])
    df["date"] = df["datetime"].dt.date
    df["month"] = df["datetime"].dt.month
    df["day_of_week"] = df["datetime"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"] >= 5
    return df

def get_weather_data(city_name, lat, lon):
    file_path = os.path.join(DATA_DIR, f"{city_name.lower()}_weather_data.csv")
    
    if os.path.exists(file_path):
        print(f"Loading existing data for {city_name}")
        return pd.read_csv(file_path)
    else:
        print(f"Fetching new data for {city_name}")


        # Set end date to today
        end_date = datetime.now().strftime("%Y-%m-%d")

        weather_data = fetch_weather_data(lat, lon, START_DATE, end_date, TIMEZONE)
        weather_df = process_data(weather_data)
        weather_df.to_csv(file_path, index=False)
        return weather_df

# Example usage
# city_name = "Limoges"
# lat, lon = 45.8333, 1.25
# weather_df = get_weather_data(city_name, lat, lon)
# print(weather_df.head())
