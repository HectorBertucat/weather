import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output

# Load the provided data
file_path = 'limoges_weather_data.csv'
weather_df = pd.read_csv(file_path)

# Convert 'datetime' column to datetime object
weather_df['datetime'] = pd.to_datetime(weather_df['datetime'])

# Adding additional columns for analysis
weather_df['date'] = weather_df['datetime'].dt.date
weather_df['day_of_week'] = weather_df['datetime'].dt.dayofweek
weather_df['is_weekend'] = weather_df['day_of_week'] >= 5

# Function to perform the analysis
def analyze_rainy_days(df, rain_threshold=0.1, min_rainy_hours=1):
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
    fig_box.update_layout(xaxis_title='Day Type', yaxis_title='Rainy Day Frequency')

    bootstrap_df = pd.DataFrame({'Weekday': weekday_frequencies, 'Weekend': weekend_frequencies})
    fig_bootstrap = px.histogram(bootstrap_df, barmode='overlay',
                                 title='Bootstrapped Frequencies of Rainy Days: Weekends vs Weekdays',
                                 labels={'value': 'Rainy Day Frequency', 'variable': 'Day Type'},
                                 color_discrete_sequence=['rgb(34, 163, 192)', 'rgb(255, 99, 132)'],
                                 template='plotly_dark')

    return summary_stats, t_stat, p_value, fig_box, fig_bootstrap

# Initialize Dash app with a Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Rainy Day Analysis in Limoges"), width=12, className="text-center my-4")
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Label("Rain Threshold (mm):"),
            dcc.Slider(
                id='rain-threshold-slider',
                min=0,
                max=10,
                step=0.1,
                value=0.1,
                marks={i: str(i) for i in range(0, 11)},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], width=6, className="mb-4"),
        dbc.Col([
            dbc.Label("Minimum Rainy Hours:"),
            dcc.Slider(
                id='min-rainy-hours-slider',
                min=1,
                max=24,
                step=1,
                value=1,
                marks={i: str(i) for i in range(1, 25)},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], width=6, className="mb-4"),
    ]),
    dbc.Row([
        dbc.Col(html.Div(id='summary-stats', className="alert alert-info"), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='box-plot'), width=12, className="my-4")
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='bootstrap-plot'), width=12, className="my-4")
    ]),
], fluid=True)

@app.callback(
    [Output('summary-stats', 'children'),
     Output('box-plot', 'figure'),
     Output('bootstrap-plot', 'figure')],
    [Input('rain-threshold-slider', 'value'),
     Input('min-rainy-hours-slider', 'value')]
)
def update_output(rain_threshold, min_rainy_hours):
    summary_stats, t_stat, p_value, fig_box, fig_bootstrap = analyze_rainy_days(
        weather_df, rain_threshold, min_rainy_hours)
    
    summary_text = [
        html.H4("Summary Statistics"),
        html.P(f"Weekday Rainy Day Frequency: {summary_stats['Weekday'][0]:.2f}", className="lead"),
        html.P(f"Weekend Rainy Day Frequency: {summary_stats['Weekend'][0]:.2f}", className="lead"),
        html.P(f"T-statistic: {t_stat:.2f}", className="lead"),
        html.P(f"P-value: {p_value:.2e}", className="lead")
    ]
    
    return summary_text, fig_box, fig_bootstrap

if __name__ == '__main__':
    app.run_server(debug=True)
