import requests
import pandas as pd
from datetime import datetime, timedelta

# Define constants
CITY_NAME = "Limoges"
LATITUDE = 45.8333
LONGITUDE = 1.25
START_DATE = "1980-01-01"
END_DATE = "2024-05-15"
TIMEZONE = "Europe/Paris"

# Fetch weather data
def fetch_weather_data(latitude, longitude, start_date, end_date, timezone):
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={latitude}&longitude={longitude}&start_date={start_date}&end_date={end_date}&hourly=precipitation&timezone={timezone}"
    response = requests.get(url)
    data = response.json()
    return data

# Function to parse data and filter by time
def parse_and_filter_data(data):
    hourly_data = data['hourly']
    dates = hourly_data['time']
    precipitations = hourly_data['precipitation']

    # Convert to DataFrame
    df = pd.DataFrame({
        'datetime': pd.to_datetime(dates),
        'precipitation': precipitations
    })

    # Filter data between 7 AM and 9 PM
    df = df[(df['datetime'].dt.hour >= 7) & (df['datetime'].dt.hour < 21)]

    return df

# Fetch data
weather_data = fetch_weather_data(LATITUDE, LONGITUDE, START_DATE, END_DATE, TIMEZONE)
weather_df = parse_and_filter_data(weather_data)

# Adding additional columns for analysis
weather_df['date'] = weather_df['datetime'].dt.date
weather_df['day_of_week'] = weather_df['datetime'].dt.dayofweek
weather_df['is_weekend'] = weather_df['day_of_week'] >= 5

# Save the data to a CSV file
weather_df.to_csv('limoges_weather_data.csv', index=False)

# Group by date and check if it rained on weekends vs weekdays
grouped_df = weather_df.groupby(['date', 'is_weekend']).agg({'precipitation': 'sum'}).reset_index()

# Separate data for weekends and weekdays
weekend_rain = grouped_df[grouped_df['is_weekend'] == True]
weekday_rain = grouped_df[grouped_df['is_weekend'] == False]

# Average rain on weekends and weekdays
avg_weekend_rain = weekend_rain['precipitation'].mean()
avg_weekday_rain = weekday_rain['precipitation'].mean()

# Print average precipitation
print(f"Average weekend rain: {avg_weekend_rain} mm")
print(f"Average weekday rain: {avg_weekday_rain} mm")
