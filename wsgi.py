import sys
import os

from dash import Dash
from my_app import app  # Adjust this line to import your Dash app

# Set the path to your app
sys.path.insert(0, '/weather.hectorb.fr/main')

# Create the application instance
application = app.server