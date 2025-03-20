import fastf1
import plotly.graph_objects as go
import pandas as pd
import fastf1.plotting
from dash import Dash, dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import os
import plotly.express as px

# Create cache directory if it doesn't exist
cache_dir = os.path.join(os.getcwd(), 'cache')
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

# Enable cache to speed up data loading
fastf1.Cache.enable_cache(cache_dir)

# Custom CSS for styling dropdowns
custom_css = """
/* Improve dropdown text visibility */
.Select-control, .Select-menu-outer, .Select-value-label, .Select-input > input {
    color: black !important;
    background-color: white !important;
}

/* Style for dropdown options when open */
.VirtualizedSelectOption {
    color: black !important;
    background-color: white !important;
}

/* Style for selected option in dropdown */
.Select--single > .Select-control .Select-value, .Select-placeholder {
    color: black !important;
}

/* Style for dropdown when focused/hovered */
.is-focused:not(.is-open) > .Select-control {
    border-color: #5c6ac4 !important;
}

/* Style for dropdown with dark theme checklist items */
.dash-checklist label {
    color: white !important;
}
"""

# Create the Dash app
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    # Add custom CSS to improve dropdown readability
    suppress_callback_exceptions=True
)

# Add custom CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
''' + custom_css + '''
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Define layout components
season_options = [{'label': str(year), 'value': year} for year in range(2018, 2025)]
event_options = []  # Will be populated based on selected season

# App layout
app.layout = html.Div([
    html.H1("Formula 1 Dashboard", className="text-center my-4"),

    dbc.Row([
        dbc.Col([
            html.H4("Settings"),
            html.Label("Select Season:"),
            dcc.Dropdown(
                id='season-dropdown',
                options=season_options,
                value=2023,
                className="mb-3",
                # Add explicit styling for better readability
                style={'color': 'black', 'background-color': 'white'}
            ),

            html.Label("Select Event:"),
            dcc.Dropdown(
                id='event-dropdown',
                options=event_options,
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
                # Radio items with better contrast
                labelStyle={'color': 'white'}
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

            html.Div(id='plot-style-container', children=[
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
                    labelStyle={'color': 'white'}
                )
            ]),

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
                    labelStyle={'color': 'white'}
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
                    labelStyle={'color': 'white', 'margin-right': '10px'}
                )
            ])
        ], width=3),

        dbc.Col([
            dcc.Loading(
                id="loading-visualization",
                type="circle",
                children=[html.Div(id='visualization-container')]
            )
        ], width=9)
    ])
])

# Callback to update event options when season changes
@app.callback(
    Output('event-dropdown', 'options'),
    Output('event-dropdown', 'value'),
    Input('season-dropdown', 'value')
)
def update_events(selected_season):
    if not selected_season:
        return [], None

    # Get all events for the selected season
    events = fastf1.get_event_schedule(selected_season)
    event_options = [{'label': f"{event['EventName']} - {event['EventDate'].strftime('%d %b')}",
                      'value': event['EventName']}
                     for _, event in events.iterrows()]

    # Return the options and select the first event
    return event_options, event_options[0]['value'] if event_options else None

# Callback to update driver options when event/session changes
@app.callback(
    Output('driver-dropdown', 'options'),
    Output('driver-dropdown', 'value'),
    Input('season-dropdown', 'value'),
    Input('event-dropdown', 'value'),
    Input('session-dropdown', 'value')
)
def update_drivers(selected_season, selected_event, selected_session):
    if not (selected_season and selected_event and selected_session):
        return [], []

    try:
        # Load session data
        session = fastf1.get_session(selected_season, selected_event, selected_session)
        session.load()

        # Get driver information
        drivers = session.results['Abbreviation'].tolist() if 'Abbreviation' in session.results else []

        # If no results, try getting from laps
        if not drivers and hasattr(session, 'laps'):
            drivers = session.laps['Driver'].unique().tolist()

        driver_options = [{'label': driver, 'value': driver} for driver in drivers]

        # Select first two drivers by default
        default_selected = drivers[:2] if len(drivers) >= 2 else drivers

        return driver_options, default_selected
    except Exception as e:
        print(f"Error loading drivers: {e}")
        return [], []

# Callback to update team options when event/session changes
@app.callback(
    Output('team-dropdown', 'options'),
    Output('team-dropdown', 'value'),
    Input('season-dropdown', 'value'),
    Input('event-dropdown', 'value'),
    Input('session-dropdown', 'value')
)
def update_teams(selected_season, selected_event, selected_session):
    if not (selected_season and selected_event and selected_session):
        return [], []

    try:
        # Load session data
        session = fastf1.get_session(selected_season, selected_event, selected_session)
        session.load()

        # Get team information
        teams = []
        if 'Team' in session.results:
            teams = session.results['Team'].unique().tolist()
        elif hasattr(session, 'laps') and 'Team' in session.laps:
            teams = session.laps['Team'].unique().tolist()

        team_options = [{'label': team, 'value': team} for team in teams]

        # Select first two teams by default
        default_selected = teams[:2] if len(teams) >= 2 else teams

        return team_options, default_selected
    except Exception as e:
        print(f"Error loading teams: {e}")
        return [], []

# Callback to show/hide container based on visualization type
@app.callback(
    Output('team-selection-container', 'style'),
    Output('driver-selection-container', 'style'),
    Output('telemetry-options-container', 'style'),
    Output('compound-filter-container', 'style'),
    Input('viz-type', 'value')
)
def toggle_selection_containers(viz_type):
    # Default all to hidden
    team_style = {'display': 'none'}
    driver_style = {'display': 'none'}
    telemetry_style = {'display': 'none'}
    compound_style = {'display': 'none'}

    # Show appropriate containers based on visualization type
    if viz_type == 'team_comparison':
        team_style = {'display': 'block'}
    elif viz_type in ['laptimes', 'telemetry']:
        driver_style = {'display': 'block'}

    if viz_type == 'telemetry':
        telemetry_style = {'display': 'block'}

    if viz_type in ['laptimes', 'lap_distribution', 'team_comparison']:
        compound_style = {'display': 'block'}

    return team_style, driver_style, telemetry_style, compound_style

# Main callback to update visualization
@app.callback(
    Output('visualization-container', 'children'),
    Input('season-dropdown', 'value'),
    Input('event-dropdown', 'value'),
    Input('session-dropdown', 'value'),
    Input('viz-type', 'value'),
    Input('driver-dropdown', 'value'),
    Input('team-dropdown', 'value'),
    Input('plot-style', 'value'),
    Input('telemetry-channel', 'value'),
    Input('telemetry-track-map', 'value'),
    Input('compound-filter', 'value')
)
def update_visualization(season, event, session_type, viz_type, selected_drivers,
                         selected_teams, plot_style, telemetry_channel, telemetry_track_map,
                         compound_filter):
    if not (season and event and session_type and viz_type):
        return html.Div("Please select all required options")

    try:
        # Load session data
        session = fastf1.get_session(season, event, session_type)
        session.load()

        if viz_type == 'laptimes':
            if not selected_drivers:
                return html.Div("Please select at least one driver")
            return create_laptimes_chart(session, selected_drivers, plot_style, compound_filter)

        elif viz_type == 'team_comparison':
            if not selected_teams or len(selected_teams) < 1:
                return html.Div("Please select at least one team")
            return create_team_comparison(session, selected_teams, plot_style, compound_filter)

        elif viz_type == 'telemetry':
            if not selected_drivers:
                return html.Div("Please select at least one driver")
            return create_telemetry_visualization(session, selected_drivers, telemetry_channel,
                                                  telemetry_track_map, plot_style)

        elif viz_type == 'lap_distribution':
            return create_lap_distribution(session, compound_filter, plot_style)

    except Exception as e:
        return html.Div(f"Error: {str(e)}")

def create_laptimes_chart(session, drivers, plot_style='line', compound_filter=None):
    if plot_style == 'line' or plot_style == 'scatter':
        fig = go.Figure()

        for driver in drivers:
            # Get laps for the driver
            driver_laps = session.laps.pick_drivers(driver)

            # Apply compound filter if provided
            if compound_filter and len(compound_filter) > 0:
                driver_laps = driver_laps[driver_laps['Compound'].isin(compound_filter)]

            # Filter for valid laps with times
            valid_laps = driver_laps[driver_laps['LapTime'].notna()]

            if len(valid_laps) > 0:
                # Get team for the driver
                team = valid_laps.iloc[0]['Team'] if 'Team' in valid_laps.columns else None

                # Convert lap times to seconds for plotting
                lap_times = valid_laps['LapTime'].dt.total_seconds()
                lap_numbers = valid_laps['LapNumber']

                # Get team color if available
                try:
                    team_color = fastf1.plotting.get_team_color(team) if team else None
                except:
                    team_color = None

                # Create trace based on plot style
                if plot_style == 'line':
                    fig.add_trace(go.Scatter(
                        x=lap_numbers,
                        y=lap_times,
                        mode='lines+markers',
                        name=f"{driver} ({team})" if team else driver,
                        marker=dict(color=team_color),
                        line=dict(color=team_color),
                        hovertemplate='Lap %{x}<br>Time: %{text}<extra></extra>',
                        text=[str(time) for time in valid_laps['LapTime']]
                    ))
                else:  # scatter
                    # Group by compound if available
                    if 'Compound' in valid_laps.columns:
                        compounds = valid_laps['Compound'].unique()
                        for compound in compounds:
                            compound_laps = valid_laps[valid_laps['Compound'] == compound]
                            if len(compound_laps) > 0:
                                c_lap_times = compound_laps['LapTime'].dt.total_seconds()
                                c_lap_numbers = compound_laps['LapNumber']

                                # Use compound color as primary, team color as secondary
                                compound_color = fastf1.plotting.COMPOUND_COLORS.get(compound, team_color)

                                fig.add_trace(go.Scatter(
                                    x=c_lap_numbers,
                                    y=c_lap_times,
                                    mode='markers',
                                    name=f"{driver} - {compound}",
                                    marker=dict(
                                        size=10,
                                        symbol='circle',
                                        color=compound_color
                                    ),
                                    hovertemplate='Lap %{x}<br>Time: %{text}<br>Compound: ' + compound + '<extra></extra>',
                                    text=[str(time) for time in compound_laps['LapTime']]
                                ))
                    else:
                        fig.add_trace(go.Scatter(
                            x=lap_numbers,
                            y=lap_times,
                            mode='markers',
                            name=f"{driver} ({team})" if team else driver,
                            marker=dict(color=team_color, size=10),
                            hovertemplate='Lap %{x}<br>Time: %{text}<extra></extra>',
                            text=[str(time) for time in valid_laps['LapTime']]
                        ))

        fig.update_layout(
            title='Lap Times Comparison',
            xaxis_title='Lap Number',
            yaxis_title='Lap Time (seconds)',
            template='plotly_dark',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )

    elif plot_style == 'box' or plot_style == 'violin':
        # Prepare data for box or violin plot
        all_data = []

        for driver in drivers:
            driver_laps = session.laps.pick_drivers(driver)

            # Apply compound filter if provided
            if compound_filter and len(compound_filter) > 0:
                driver_laps = driver_laps[driver_laps['Compound'].isin(compound_filter)]

            valid_laps = driver_laps[driver_laps['LapTime'].notna()]

            if len(valid_laps) > 0:
                lap_times = valid_laps['LapTime'].dt.total_seconds()
                team = valid_laps.iloc[0]['Team'] if 'Team' in valid_laps.columns else 'Unknown'

                # For each lap, add its details
                for i, time in enumerate(lap_times):
                    compound = valid_laps.iloc[i]['Compound'] if 'Compound' in valid_laps.columns else 'Unknown'

                    all_data.append({
                        'Driver': driver,
                        'Team': team,
                        'Compound': compound,
                        'LapTime': time
                    })

        # Convert to DataFrame for plotting
        df = pd.DataFrame(all_data)

        if len(df) > 0:
            # Create team color mapping
            team_colors = {}
            for team in df['Team'].unique():
                try:
                    team_colors[team] = fastf1.plotting.get_team_color(team)
                except:
                    team_colors[team] = '#333333'

            if plot_style == 'box':
                if 'Compound' in df.columns and len(df['Compound'].unique()) > 1:
                    # Use compound as color if available
                    fig = px.box(df, x='Driver', y='LapTime', color='Compound',
                                 title='Lap Time Distribution by Driver',
                                 template='plotly_dark',
                                 color_discrete_map=fastf1.plotting.COMPOUND_COLORS)
                else:
                    # Use team as color
                    fig = px.box(df, x='Driver', y='LapTime', color='Team',
                                 title='Lap Time Distribution by Driver',
                                 template='plotly_dark',
                                 color_discrete_map=team_colors)
            else:  # violin
                if 'Compound' in df.columns and len(df['Compound'].unique()) > 1:
                    # Use compound as color if available
                    fig = px.violin(df, x='Driver', y='LapTime', color='Compound',
                                    title='Lap Time Distribution by Driver',
                                    box=True, points="all", template='plotly_dark',
                                    color_discrete_map=fastf1.plotting.COMPOUND_COLORS)
                else:
                    # Use team as color
                    fig = px.violin(df, x='Driver', y='LapTime', color='Team',
                                    title='Lap Time Distribution by Driver',
                                    box=True, points="all", template='plotly_dark',
                                    color_discrete_map=team_colors)

            fig.update_layout(
                xaxis_title='Driver',
                yaxis_title='Lap Time (seconds)',
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
            )
        else:
            return html.Div("No valid lap data available for the selected drivers and compound filter")

    else:
        return html.Div("Unsupported plot style")

    return dcc.Graph(figure=fig)

def create_team_comparison(session, teams, plot_style='box', compound_filter=None):
    # Get all laps by team
    team_laps = {}
    team_colors = {}

    for team in teams:
        # Get all drivers from this team
        team_drivers = []

        if 'Team' in session.results:
            team_drivers = session.results.loc[session.results['Team'] == team, 'Abbreviation'].tolist()

        # If no drivers found in results, try from laps
        if not team_drivers and hasattr(session, 'laps') and 'Team' in session.laps.columns:
            team_drivers = session.laps.loc[session.laps['Team'] == team, 'Driver'].unique().tolist()

        # Collect laps from all team drivers
        all_team_laps = []
        for driver in team_drivers:
            driver_laps = session.laps.pick_drivers(driver)

            # Apply compound filter if provided
            if compound_filter and len(compound_filter) > 0:
                driver_laps = driver_laps[driver_laps['Compound'].isin(compound_filter)]

            # Filter for valid laps
            valid_laps = driver_laps[driver_laps['LapTime'].notna()]

            if len(valid_laps) > 0:
                all_team_laps.append(valid_laps)

                # Get team color if not already set
                if team not in team_colors:
                    try:
                        team_colors[team] = fastf1.plotting.get_team_color(team)
                    except:
                        team_colors[team] = '#333333'

        if all_team_laps:
            team_laps[team] = pd.concat(all_team_laps, ignore_index=True)

    if not team_laps:
        return html.Div("No valid lap data available for the selected teams")

    # Prepare data based on plot style
    if plot_style == 'box' or plot_style == 'violin':
        # Prepare data for box/violin plot
        all_data = []

        for team, laps in team_laps.items():
            lap_times = laps['LapTime'].dt.total_seconds()

            # For each lap, add to dataset
            for i, time in enumerate(lap_times):
                compound = laps.iloc[i]['Compound'] if 'Compound' in laps.columns else 'Unknown'
                driver = laps.iloc[i]['Driver'] if 'Driver' in laps.columns else 'Unknown'

                all_data.append({
                    'Team': team,
                    'Driver': driver,
                    'LapTime': time,
                    'Compound': compound
                })

        # Convert to DataFrame for plotting
        df = pd.DataFrame(all_data)

        if len(df) > 0:
            # If multiple compounds are available, use them for color
            if 'Compound' in df.columns and len(df['Compound'].unique()) > 1:
                if plot_style == 'box':
                    fig = px.box(df, x='Team', y='LapTime', color='Compound',
                                 title='Lap Time Distribution by Team',
                                 template='plotly_dark',
                                 color_discrete_map=fastf1.plotting.COMPOUND_COLORS)
                else:  # violin
                    fig = px.violin(df, x='Team', y='LapTime', color='Compound',
                                    box=True, points="all",
                                    title='Lap Time Distribution by Team',
                                    template='plotly_dark',
                                    color_discrete_map=fastf1.plotting.COMPOUND_COLORS)
            else:
                # Use team colors
                if plot_style == 'box':
                    fig = px.box(df, x='Team', y='LapTime', color='Team',
                                 title='Lap Time Distribution by Team',
                                 template='plotly_dark',
                                 color_discrete_map=team_colors)
                else:  # violin
                    fig = px.violin(df, x='Team', y='LapTime', color='Team',
                                    box=True, points="all",
                                    title='Lap Time Distribution by Team',
                                    template='plotly_dark',
                                    color_discrete_map=team_colors)
        else:
            return html.Div("No valid lap data for plotting")

    else:  # line or scatter
        fig = go.Figure()

        for team, laps in team_laps.items():
            team_color = team_colors.get(team, '#333333')

            if plot_style == 'line':
                # Calculate lap time statistics per lap number
                lap_stats = laps.groupby('LapNumber')['LapTime'].agg(['mean', 'min', 'max']).reset_index()

                # Convert timedeltas to seconds
                lap_stats['mean'] = lap_stats['mean'].dt.total_seconds()
                lap_stats['min'] = lap_stats['min'].dt.total_seconds()
                lap_stats['max'] = lap_stats['max'].dt.total_seconds()

                # Add trace for mean lap time
                fig.add_trace(go.Scatter(
                    x=lap_stats['LapNumber'],
                    y=lap_stats['mean'],
                    mode='lines+markers',
                    name=f"{team} (Mean)",
                    line=dict(color=team_color),
                    marker=dict(color=team_color)
                ))

                # Add range fill for min-max
                fig.add_trace(go.Scatter(
                    x=lap_stats['LapNumber'],
                    y=lap_stats['min'],
                    mode='lines',
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo='skip'
                ))

                fig.add_trace(go.Scatter(
                    x=lap_stats['LapNumber'],
                    y=lap_stats['max'],
                    mode='lines',
                    line=dict(width=0),
                    fill='tonexty',
                    fillcolor=f"rgba{(*hex_to_rgb(team_color), 0.2)}",
                    showlegend=False,
                    hoverinfo='skip'
                ))

            else:  # scatter
                # Group by compound if available
                if 'Compound' in laps.columns:
                    compounds = laps['Compound'].unique()
                    for compound in compounds:
                        compound_laps = laps[laps['Compound'] == compound]
                        if len(compound_laps) > 0:
                            lap_times = compound_laps['LapTime'].dt.total_seconds()
                            lap_numbers = compound_laps['LapNumber']

                            # Use compound color instead of team color
                            compound_color = fastf1.plotting.COMPOUND_COLORS.get(compound, team_color)

                            fig.add_trace(go.Scatter(
                                x=lap_numbers,
                                y=lap_times,
                                mode='markers',
                                name=f"{team} - {compound}",
                                marker=dict(
                                    size=10,
                                    symbol='circle',
                                    color=compound_color
                                ),
                                hovertemplate='Lap %{x}<br>Time: %{y:.3f}s<br>Compound: ' + compound + '<extra></extra>'
                            ))
                else:
                    lap_times = laps['LapTime'].dt.total_seconds()
                    lap_numbers = laps['LapNumber']

                    fig.add_trace(go.Scatter(
                        x=lap_numbers,
                        y=lap_times,
                        mode='markers',
                        name=team,
                        marker=dict(color=team_color, size=10),
                        hovertemplate='Lap %{x}<br>Time: %{y:.3f}s<extra></extra>'
                    ))

    fig.update_layout(
        title='Team Lap Times Comparison',
        xaxis_title='Lap Number' if plot_style in ['line', 'scatter'] else 'Team',
        yaxis_title='Lap Time (seconds)',
        template='plotly_dark',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )

    return dcc.Graph(figure=fig)

def create_telemetry_visualization(session, drivers, channel, track_map='no', plot_style='line'):
    if len(drivers) < 1:
        return html.Div("Please select at least one driver")

    if track_map == 'yes':
        # Create track map visualization with telemetry data
        fig = go.Figure()

        for driver in drivers:
            try:
                # Get fastest lap for driver
                driver_laps = session.laps.pick_drivers(driver)

                if len(driver_laps) == 0:
                    continue

                fastest_lap = driver_laps.pick_fastest()

                # Get telemetry data
                if hasattr(fastest_lap, 'get_telemetry'):
                    telemetry = fastest_lap.get_telemetry()

                    # Check if required channels exist
                    if 'X' in telemetry.columns and 'Y' in telemetry.columns and channel in telemetry.columns:
                        # Get team for the driver
                        team = driver_laps.iloc[0]['Team'] if 'Team' in driver_laps.columns else None

                        # Get team color if available
                        try:
                            team_color = fastf1.plotting.get_team_color(team) if team else None
                        except:
                            team_color = None

                        # Create scatter plot colored by the selected channel
                        fig.add_trace(go.Scatter(
                            x=telemetry['X'],
                            y=telemetry['Y'],
                            mode='markers',
                            marker=dict(
                                size=5,
                                color=telemetry[channel],
                                colorscale='Viridis',
                                showscale=True,
                                colorbar=dict(title=channel)
                            ),
                            name=f"{driver} ({team})" if team else driver,
                            hovertemplate=f"X: %{{x:.1f}}<br>Y: %{{y:.1f}}<br>{channel}: %{{marker.color}}<extra>{driver}</extra>"
                        ))
            except Exception as e:
                print(f"Error plotting telemetry for {driver}: {e}")

        fig.update_layout(
            title=f'{channel} Telemetry on Track Map - {session.event["EventName"]} {session.name}',
            template='plotly_dark',
            showlegend=True,
            yaxis=dict(
                scaleanchor="x",
                scaleratio=1
            )
        )

    else:
        # Regular telemetry plot
        fig = go.Figure()

        for driver in drivers:
            try:
                # Get fastest lap for driver
                driver_laps = session.laps.pick_drivers(driver)

                if len(driver_laps) == 0:
                    continue

                fastest_lap = driver_laps.pick_fastest()

                # Get telemetry data
                if hasattr(fastest_lap, 'get_telemetry'):
                    telemetry = fastest_lap.get_telemetry()

                    # Check if selected channel exists
                    if channel in telemetry.columns:
                        # Get distance or time for x-axis
                        x_data = telemetry['Distance'] if 'Distance' in telemetry.columns else telemetry.index

                        # Get team for the driver
                        team = driver_laps.iloc[0]['Team'] if 'Team' in driver_laps.columns else None

                        # Get team color if available
                        try:
                            team_color = fastf1.plotting.get_team_color(team) if team else None
                        except:
                            team_color = None

                        # Add to plot based on style
                        if plot_style == 'line':
                            fig.add_trace(go.Scatter(
                                x=x_data,
                                y=telemetry[channel],
                                mode='lines',
                                name=f"{driver} ({team})" if team else driver,
                                line=dict(color=team_color),
                                hovertemplate=f"{channel}: %{{y}}<br>Distance: %{{x:.0f}}m<extra>{driver}</extra>"
                                if 'Distance' in telemetry.columns else
                                f"{channel}: %{{y}}<extra>{driver}</extra>"
                            ))
                        elif plot_style == 'scatter':
                            fig.add_trace(go.Scatter(
                                x=x_data,
                                y=telemetry[channel],
                                mode='markers',
                                name=f"{driver} ({team})" if team else driver,
                                marker=dict(size=5, color=team_color),
                                hovertemplate=f"{channel}: %{{y}}<br>Distance: %{{x:.0f}}m<extra>{driver}</extra>"
                                if 'Distance' in telemetry.columns else
                                f"{channel}: %{{y}}<extra>{driver}</extra>"
                            ))
                        # Box and violin don't make sense for telemetry over distance
            except Exception as e:
                print(f"Error plotting telemetry for {driver}: {e}")

        x_title = 'Distance (m)' if len(fig.data) > 0 and 'Distance' in telemetry.columns else 'Time'

        fig.update_layout(
            title=f'{channel} Telemetry Comparison',
            xaxis_title=x_title,
            yaxis_title=channel,
            template='plotly_dark',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
        )

    return dcc.Graph(figure=fig)

def create_lap_distribution(session, compound_filter=None, plot_style='violin'):
    # Prepare data
    all_data = []

    # Get all laps with valid lap times
    laps = session.laps[session.laps['LapTime'].notna()]

    # Apply compound filter if provided
    if compound_filter and len(compound_filter) > 0:
        laps = laps[laps['Compound'].isin(compound_filter)]

    # Skip if no valid laps
    if len(laps) == 0:
        return html.Div("No valid lap data available")

    # Prepare data structure for plotting
    for i, lap in laps.iterrows():
        driver = lap['Driver']
        team = lap['Team'] if 'Team' in lap else 'Unknown'
        compound = lap['Compound'] if 'Compound' in lap else 'Unknown'
        lap_time = lap['LapTime'].total_seconds()

        all_data.append({
            'Driver': driver,
            'Team': team,
            'Compound': compound,
            'LapTime': lap_time
        })

    # Convert to DataFrame
    df = pd.DataFrame(all_data)

    # Create team color mapping
    team_colors = {}
    for team in df['Team'].unique():
        try:
            team_colors[team] = fastf1.plotting.get_team_color(team)
        except:
            team_colors[team] = '#333333'

    # Create visualization based on plot style
    if plot_style == 'violin':
        # Always prioritize compound colors for violin plots
        fig = px.violin(df, x='Driver', y='LapTime', color='Compound',
                        box=True, points="all",
                        title='Lap Time Distribution by Driver and Compound',
                        template='plotly_dark',
                        color_discrete_map=fastf1.plotting.COMPOUND_COLORS)
    elif plot_style == 'box':
        # Always prioritize compound colors for box plots
        fig = px.box(df, x='Driver', y='LapTime', color='Compound',
                     title='Lap Time Distribution by Driver and Compound',
                     template='plotly_dark',
                     color_discrete_map=fastf1.plotting.COMPOUND_COLORS)
    elif plot_style == 'line' or plot_style == 'scatter':
        # For line/scatter, we'll create a grouped visualization

        if plot_style == 'line':
            # Group data by driver and compound, calculate statistics
            driver_stats = df.groupby(['Driver', 'Compound', 'Team']).agg({
                'LapTime': ['mean', 'min', 'max', 'std']
            }).reset_index()

            # Flatten the multi-index columns
            driver_stats.columns = ['Driver', 'Compound', 'Team', 'Mean', 'Min', 'Max', 'Std']

            # Sort by mean lap time
            driver_stats = driver_stats.sort_values('Mean')

            fig = go.Figure()

            for compound in df['Compound'].unique():
                compound_data = driver_stats[driver_stats['Compound'] == compound]

                # Use compound colors for different compounds
                compound_color = fastf1.plotting.COMPOUND_COLORS.get(compound, '#333333')

                fig.add_trace(go.Scatter(
                    x=compound_data['Driver'],
                    y=compound_data['Mean'],
                    mode='lines+markers',
                    name=compound,
                    line=dict(color=compound_color),
                    marker=dict(color=compound_color, size=8),
                    error_y=dict(
                        type='data',
                        array=compound_data['Std'],
                        visible=True
                    )
                ))
        else:  # scatter
            fig = go.Figure()

            for compound in df['Compound'].unique():
                compound_data = df[df['Compound'] == compound]

                # Use compound colors
                compound_color = fastf1.plotting.COMPOUND_COLORS.get(compound, '#333333')

                fig.add_trace(go.Scatter(
                    x=compound_data['Driver'],
                    y=compound_data['LapTime'],
                    mode='markers',
                    name=compound,
                    marker=dict(
                        color=compound_color,
                        size=8
                    ),
                    hovertemplate='Driver: %{x}<br>Time: %{y:.3f}s<br>Compound: ' + compound + '<extra></extra>'
                ))

    fig.update_layout(
        xaxis_title='Driver',
        yaxis_title='Lap Time (seconds)',
        template='plotly_dark',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )

    return dcc.Graph(figure=fig)

# Helper function to convert hex color to RGB tuple
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Run the app
if __name__ == '__main__':
    app.run(debug=True)