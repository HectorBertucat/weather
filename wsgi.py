import sys
import os
from dotenv import load_dotenv

from dash import Dash
from my_app import app  # Adjust this line to import your Dash app

load_dotenv()

MAIN_PATH = os.getenv('MAIN_PATH')

# Set the path to your app
sys.path.insert(0, MAIN_PATH)

# Create the application instance
application = app.server