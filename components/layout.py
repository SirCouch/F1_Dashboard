from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc

def create_layout():
    """Create the main layout for the F1 dashboard."""

    # Define dropdown options for seasons
    season_options = [{'label': str(year), 'value': year} for year in range(2018, 2025)]

    # Main layout
    layout = html.Div([
        html.H1("Formula 1 Data Analysis Dashboard", className="text-center my-4"),

        html.Div([
            dbc.Row([
                # LEFT COLUMN - CONTROLS
                dbc.Col([
                    html.Div([
                        html.H4("Data Selection", className="section-title"),

                        html.Label("Select Season:"),
                        dcc.Dropdown(
                            id='season-dropdown',
                            options=season_options,
                            value=2023,
                            className="mb-3",
                            style={'color': 'black', 'background-color': 'white'}
                        ),

                        html.Label("Select Event:"),
                        dcc.Dropdown(
                            id='event-dropdown',
                            options=[],  # Will be populated based on selected season
                            className="mb-3",
                            style={'color': 'black', 'background-color': 'white'}
                        ),

                        html.Label("Select Session:"),
                        dcc.Dropdown(
                            id='session-dropdown',
                            options=[
                                {'label': 'Practice 1', 'value': 'FP1'},
                                {'label': 'Practice 2', 'value': 'FP2'},
                                {'label': 'Practice 3', 'value': 'FP3'},
                                {'label': 'Qualifying', 'value': 'Q'},
                                {'label': 'Sprint', 'value': 'S'},
                                {'label': 'Sprint Qualifying', 'value': 'SQ'},
                                {'label': 'Race', 'value': 'R'}
                            ],
                            value='Q',
                            className="mb-3",
                            style={'color': 'black', 'background-color': 'white'}
                        ),
                    ], className="controls-section"),

                    html.Div([
                        html.H4("Visualization Options", className="section-title"),

                        html.Label("Visualization Type:"),
                        dcc.RadioItems(
                            id='viz-type',
                            options=[
                                {'label': 'Lap Times', 'value': 'laptimes'},
                                {'label': 'Team Comparison', 'value': 'team_comparison'},
                                {'label': 'Telemetry', 'value': 'telemetry'},
                                {'label': 'Lap Distribution', 'value': 'lap_distribution'}
                            ],
                            value='laptimes',
                            className="mb-3",
                            labelStyle={'color': 'white', 'display': 'block', 'margin-bottom': '8px'}
                        ),

                        html.Div(id='driver-selection-container', children=[
                            html.Label("Select Drivers:"),
                            dcc.Dropdown(
                                id='driver-dropdown',
                                multi=True,
                                className="mb-3",
                                style={'color': 'black', 'background-color': 'white'}
                            )
                        ]),

                        html.Div(id='team-selection-container', style={'display': 'none'}, children=[
                            html.Label("Select Teams:"),
                            dcc.Dropdown(
                                id='team-dropdown',
                                multi=True,
                                className="mb-3",
                                style={'color': 'black', 'background-color': 'white'}
                            )
                        ]),

                        html.Label("Plot Style:"),
                        dcc.RadioItems(
                            id='plot-style',
                            options=[
                                {'label': 'Line', 'value': 'line'},
                                {'label': 'Scatter', 'value': 'scatter'},
                                {'label': 'Box Plot', 'value': 'box'},
                                {'label': 'Violin Plot', 'value': 'violin'}
                            ],
                            value='line',
                            className="mb-3",
                            labelStyle={'color': 'white', 'display': 'block', 'margin-bottom': '8px'}
                        ),

                        html.Div(id='telemetry-options-container', style={'display': 'none'}, children=[
                            html.Label("Telemetry Channel:"),
                            dcc.Dropdown(
                                id='telemetry-channel',
                                options=[
                                    {'label': 'Speed', 'value': 'Speed'},
                                    {'label': 'RPM', 'value': 'RPM'},
                                    {'label': 'Throttle', 'value': 'Throttle'},
                                    {'label': 'Brake', 'value': 'Brake'},
                                    {'label': 'DRS', 'value': 'DRS'}
                                ],
                                value='Speed',
                                className="mb-3",
                                style={'color': 'black', 'background-color': 'white'}
                            ),

                            html.Label("Show as Track Map:"),
                            dcc.RadioItems(
                                id='telemetry-track-map',
                                options=[
                                    {'label': 'Yes', 'value': 'yes'},
                                    {'label': 'No', 'value': 'no'}
                                ],
                                value='no',
                                className="mb-3",
                                labelStyle={'color': 'white', 'display': 'block', 'margin-bottom': '8px'}
                            )
                        ]),

                        html.Div(id='compound-filter-container', style={'display': 'none'}, children=[
                            html.Label("Filter by Compound:"),
                            dcc.Checklist(
                                id='compound-filter',
                                options=[
                                    {'label': 'Soft', 'value': 'SOFT'},
                                    {'label': 'Medium', 'value': 'MEDIUM'},
                                    {'label': 'Hard', 'value': 'HARD'},
                                    {'label': 'Intermediate', 'value': 'INTERMEDIATE'},
                                    {'label': 'Wet', 'value': 'WET'}
                                ],
                                value=['SOFT', 'MEDIUM', 'HARD'],
                                className="mb-3",
                                labelStyle={'color': 'white', 'display': 'inline-block', 'margin-right': '15px', 'margin-bottom': '5px'}
                            )
                        ])
                    ], className="controls-section"),
                ], width=3),

                # RIGHT COLUMN - VISUALIZATION
                dbc.Col([
                    html.Div([
                        # Visualization container
                        html.Div([
                            html.H4("Data Visualization", className="section-title"),
                            dcc.Loading(
                                id="loading-visualization",
                                type="circle",
                                children=[html.Div(id='visualization-container')]
                            )
                        ], className="mb-4"),

                        # Raw data table container
                        html.Div([
                            html.H4("Raw Data", className="section-title"),
                            html.Div(id='data-table-container')
                        ])
                    ], className="p-3")
                ], width=9)
            ])
        ], className="main-container")
    ])

    return layout