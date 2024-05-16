import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dotenv import load_dotenv
import os
from fetch_data import get_weather_data, get_fetched_cities

load_dotenv()

# Load city list
cities_df = pd.read_csv('cities.csv')

# Capitalize the city labels
cities_df['label'] = cities_df['label'].str.title()

city_options = [{'label': city, 'value': city} for city in cities_df['label']]

# Define analyze_rainy_days function
def analyze_rainy_days(df, rain_threshold=0.1, min_rainy_hours=1, selected_months=None):
    if 'month' not in df.columns:
        df['month'] = pd.to_datetime(df['datetime']).dt.month
        
    if selected_months is not None:
        df = df[df['month'].isin(selected_months)]
    
    df['is_rainy'] = df['precipitation'] > rain_threshold
    daily_rainy_hours = df.groupby(['date', 'is_weekend']).agg({'is_rainy': 'sum'}).reset_index()
    daily_rainy_hours['is_rainy_day'] = daily_rainy_hours['is_rainy'] >= min_rainy_hours

    weekend_rainy_days = daily_rainy_hours[daily_rainy_hours['is_weekend'] == True]['is_rainy_day']
    weekday_rainy_days = daily_rainy_hours[daily_rainy_hours['is_weekend'] == False]['is_rainy_day']

    summary_stats = pd.DataFrame({
        'Weekday': [weekday_rainy_days.mean()],
        'Weekend': [weekend_rainy_days.mean()]
    }, index=['Rainy Day Frequency'])

    n_iterations = 10000
    n_size = min(len(weekend_rainy_days), len(weekday_rainy_days))
    weekday_frequencies = np.empty(n_iterations)
    weekend_frequencies = np.empty(n_iterations)

    for i in range(n_iterations):
        weekday_sample = np.random.choice(weekday_rainy_days, n_size, replace=True)
        weekend_sample = np.random.choice(weekend_rainy_days, n_size, replace=True)
        weekday_frequencies[i] = weekday_sample.mean()
        weekend_frequencies[i] = weekend_sample.mean()

    t_stat, p_value = stats.ttest_ind(weekend_frequencies, weekday_frequencies, equal_var=False)

    fig_box = px.box(pd.DataFrame({'Weekday': weekday_frequencies, 'Weekend': weekend_frequencies}),
                     title='Frequency of Rainy Days: Weekends vs Weekdays',
                     labels={'value': 'Rainy Day Frequency', 'variable': 'Day Type'},
                     color_discrete_map={'Weekday': 'rgb(34, 163, 192)', 'Weekend': 'rgb(255, 99, 132)'},
                     template='plotly_dark')
    fig_box.update_layout(xaxis_title='Day Type', yaxis_title='Rainy Day Frequency', margin=dict(l=20, r=20, t=50, b=20))

    bootstrap_df = pd.DataFrame({'Weekday': weekday_frequencies, 'Weekend': weekend_frequencies})
    fig_bootstrap = px.histogram(bootstrap_df, barmode='overlay',
                                 title='Bootstrapped Frequencies of Rainy Days: Weekends vs Weekdays',
                                 labels={'value': 'Rainy Day Frequency', 'variable': 'Day Type'},
                                 color_discrete_sequence=['rgb(34, 163, 192)', 'rgb(255, 99, 132)'],
                                 template='plotly_dark')
    fig_bootstrap.update_layout(margin=dict(l=20, r=20, t=50, b=20))

    return summary_stats, t_stat, p_value, fig_box, fig_bootstrap

# Initialize Dash app with a Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
server = app.server

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Rainy Day Analysis", className="text-center text-primary mb-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("City", className="card-title"),
                    dcc.Dropdown(
                        id='city-dropdown',
                        options=city_options,
                        placeholder='Enter city name',
                        value=None,
                        searchable=True,
                        clearable=True,
                        persistence=True,
                        persistence_type='session'
                    )
                ])
            ], className="mb-4")
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Rain Threshold (mm)", className="card-title"),
                    dcc.Slider(
                        id='rain-threshold-slider',
                        min=0,
                        max=10,
                        step=0.1,
                        value=0.1,
                        marks={i: str(i) for i in range(0, 11)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    )
                ])
            ], className="mb-4")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Minimum Rainy Hours", className="card-title"),
                    dbc.Input(
                        id='min-rainy-hours-input',
                        type='number',
                        min=1,
                        max=24,
                        step=1,
                        value=1,
                    )
                ])
            ], className="mb-4")
        ], width=6)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Select Months", className="card-title"),
                    dcc.Dropdown(
                        id='month-dropdown',
                        options=[{'label': month, 'value': i} for i, month in enumerate(['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'], 1)],
                        value=list(range(1, 13)),
                        multi=True
                    )
                ])
            ], className="mb-4")
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Summary Statistics", className="card-title"),
                dcc.Loading(id='loading-summary', type='default', children=html.Div(id='summary-stats', className="card-text"))
            ])
        ], className="mb-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                dcc.Loading(id='loading-box-plot', type='default', children=dcc.Graph(id='box-plot'))
            ])
        ], className="mb-4"), width=12)
    ]),
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                dcc.Loading(id='loading-bootstrap-plot', type='default', children=dcc.Graph(id='bootstrap-plot'))
            ])
        ], className="mb-4"), width=12)
    ])
], fluid=True)

@app.callback(
    [Output('summary-stats', 'children'),
     Output('box-plot', 'figure'),
     Output('bootstrap-plot', 'figure')],
    [Input('city-dropdown', 'value'),
     Input('rain-threshold-slider', 'value'),
     Input('min-rainy-hours-input', 'value'),
     Input('month-dropdown', 'value')]
)
def update_output(city, rain_threshold, min_rainy_hours, selected_months):
    if not city:
        raise dash.exceptions.PreventUpdate

    try:
        weather_df = get_weather_data(city)
    except ValueError as e:
        return [html.P(str(e), className="text-danger")], {}, {}

    summary_stats, t_stat, p_value, fig_box, fig_bootstrap = analyze_rainy_days(
        weather_df, rain_threshold, min_rainy_hours, selected_months)
    
    summary_text = [
        html.P(f"Weekday Rainy Day Frequency: {summary_stats['Weekday'][0]:.2f}", className="mb-2"),
        html.P(f"Weekend Rainy Day Frequency: {summary_stats['Weekend'][0]:.2f}", className="mb-2"),
        html.P(f"T-statistic: {t_stat:.2f}", className="mb-2"),
        html.P(f"P-value: {p_value:.2e}", className="mb-2")
    ]

    return summary_text, fig_box, fig_bootstrap

if __name__ == '__main__':
    app.run_server(debug=True)
