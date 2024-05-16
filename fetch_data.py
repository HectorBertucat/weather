import os
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

# Define constants
START_DATE = "1980-01-01"
END_DATE = "2024-05-15"
TIMEZONE = "Europe/Paris"
DATA_DIR = "weather_data"
CITY_LIST_PATH = "cities.csv"

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_weather_data(lat, lon, start_date, end_date, timezone):
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

def get_lat_lon(city_name):
    cities_df = pd.read_csv(CITY_LIST_PATH)
    city_row = cities_df[cities_df['label'].str.lower() == city_name.lower()]
    if city_row.empty:
        raise ValueError(f"City {city_name} not found.")
    lat = city_row.iloc[0]['latitude']
    lon = city_row.iloc[0]['longitude']
    return lat, lon

def get_weather_data(city_name):
    file_path = os.path.join(DATA_DIR, f"{city_name.lower().replace(' ', '_')}_weather_data.csv")
    
    if os.path.exists(file_path):
        print(f"Loading existing data for {city_name}")
        return pd.read_csv(file_path)
    else:
        print(f"Fetching new data for {city_name}")
        lat, lon = get_lat_lon(city_name)
        weather_data = fetch_weather_data(lat, lon, START_DATE, END_DATE, TIMEZONE)
        weather_df = process_data(weather_data)
        weather_df.to_csv(file_path, index=False)
        return weather_df

def get_fetched_cities():
    files = os.listdir(DATA_DIR)
    cities = [file.replace('_weather_data.csv', '').replace('_', ' ').title() for file in files if file.endswith('_weather_data.csv')]
    return cities
