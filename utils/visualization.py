import pandas as pd
import fastf1
import fastf1.plotting
import plotly.graph_objects as go
import plotly.express as px
from dash import html, dcc, dash_table

# Helper function to convert hex color to RGB tuple
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_laptimes_table(session, drivers, compound_filter):
    # Collect lap data for the selected drivers
    all_laps = []

    for driver in drivers:
        driver_laps = session.laps.pick_drivers(driver)

        # Apply compound filter if provided
        if compound_filter and len(compound_filter) > 0:
            driver_laps = driver_laps[driver_laps['Compound'].isin(compound_filter)]

        # Filter for valid laps with times
        valid_laps = driver_laps[driver_laps['LapTime'].notna()]

        if len(valid_laps) > 0:
            all_laps.append(valid_laps)

    if not all_laps:
        return html.Div("No lap data available for the selected drivers and filters")

    # Combine all laps
    combined_laps = pd.concat(all_laps)

    # Select and format columns for display
    display_columns = ['Driver', 'LapNumber', 'LapTime', 'Compound', 'TyreLife', 'FreshTyre', 'Team']
    display_df = combined_laps[display_columns].copy()

    # Format lap times to strings
    display_df['LapTime'] = display_df['LapTime'].apply(lambda x: str(x))

    # Sort by driver and lap number
    display_df = display_df.sort_values(['Driver', 'LapNumber'])

    # Create data table
    return dash_table.DataTable(
        id='lap-times-table',
        columns=[{"name": col, "id": col} for col in display_df.columns],
        data=display_df.to_dict('records'),
        style_table={'overflowX': 'auto'},
        style_header={
            'backgroundColor': '#2c3e50',
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'left'
        },
        style_cell={
            'backgroundColor': '#1e2130',
            'color': 'white',
            'textAlign': 'left',
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '14px',
            'padding': '8px'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#283747'
            }
        ],
        page_size=10,
        filter_action="native",
        sort_action="native",
    )

# Function to create a data table for team comparison
def create_team_comparison_table(session, teams, compound_filter):
    # Collect all team drivers
    all_team_laps = []

    for team in teams:
        # Get all drivers from this team
        team_drivers = []

        if 'Team' in session.results:
            team_drivers = session.results.loc[session.results['Team'] == team, 'Abbreviation'].tolist()

        # If no drivers found in results, try from laps
        if not team_drivers and hasattr(session, 'laps') and 'Team' in session.laps.columns:
            team_drivers = session.laps.loc[session.laps['Team'] == team, 'Driver'].unique().tolist()

        # Collect laps from all team drivers
        for driver in team_drivers:
            driver_laps = session.laps.pick_drivers(driver)

            # Apply compound filter if provided
            if compound_filter and len(compound_filter) > 0:
                driver_laps = driver_laps[driver_laps['Compound'].isin(compound_filter)]

            # Filter for valid laps
            valid_laps = driver_laps[driver_laps['LapTime'].notna()]

            if len(valid_laps) > 0:
                all_team_laps.append(valid_laps)

    if not all_team_laps:
        return html.Div("No lap data available for the selected teams and filters")

    # Combine all laps
    combined_laps = pd.concat(all_team_laps)

    # Select and format columns for display
    display_columns = ['Team', 'Driver', 'LapNumber', 'LapTime', 'Compound', 'TyreLife', 'FreshTyre']
    display_df = combined_laps[display_columns].copy()

    # Format lap times to strings
    display_df['LapTime'] = display_df['LapTime'].apply(lambda x: str(x))

    # Sort by team, driver and lap number
    display_df = display_df.sort_values(['Team', 'Driver', 'LapNumber'])

    # Create data table
    return dash_table.DataTable(
        id='team-comparison-table',
        columns=[{"name": col, "id": col} for col in display_df.columns],
        data=display_df.to_dict('records'),
        style_table={'overflowX': 'auto'},
        style_header={
            'backgroundColor': '#2c3e50',
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'left'
        },
        style_cell={
            'backgroundColor': '#1e2130',
            'color': 'white',
            'textAlign': 'left',
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '14px',
            'padding': '8px'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#283747'
            }
        ],
        page_size=10,
        filter_action="native",
        sort_action="native",
    )

# Function to create a data table for telemetry data
def create_telemetry_table(session, drivers, channel):
    if len(drivers) < 1:
        return html.Div("Please select at least one driver")

    all_telemetry = []

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

                # Add driver info
                telemetry['Driver'] = driver
                telemetry['Team'] = driver_laps.iloc[0]['Team'] if 'Team' in driver_laps.columns else 'Unknown'
                telemetry['LapNumber'] = fastest_lap['LapNumber']

                all_telemetry.append(telemetry)
        except Exception as e:
            print(f"Error getting telemetry for {driver}: {e}")

    if not all_telemetry:
        return html.Div("No telemetry data available for the selected drivers")

    # Combine all telemetry data
    combined_telemetry = pd.concat(all_telemetry)

    # Select relevant columns
    display_columns = ['Driver', 'Team', 'LapNumber', 'Distance', channel, 'Time', 'SessionTime']
    display_df = combined_telemetry[display_columns].copy()

    # Format time columns
    display_df['Time'] = display_df['Time'].apply(lambda x: str(x))
    display_df['SessionTime'] = display_df['SessionTime'].apply(lambda x: str(x))

    # Sample data to keep table manageable (every 10th point)
    display_df = display_df.iloc[::10, :]

    # Create data table
    return dash_table.DataTable(
        id='telemetry-table',
        columns=[{"name": col, "id": col} for col in display_df.columns],
        data=display_df.to_dict('records'),
        style_table={'overflowX': 'auto'},
        style_header={
            'backgroundColor': '#2c3e50',
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'left'
        },
        style_cell={
            'backgroundColor': '#1e2130',
            'color': 'white',
            'textAlign': 'left',
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '14px',
            'padding': '8px'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#283747'
            }
        ],
        page_size=10,
        filter_action="native",
        sort_action="native",
    )

# Function to create a data table for lap distribution
def create_lap_distribution_table(session, compound_filter):
    # Get all laps with valid lap times
    laps = session.laps[session.laps['LapTime'].notna()]

    # Apply compound filter if provided
    if compound_filter and len(compound_filter) > 0:
        laps = laps[laps['Compound'].isin(compound_filter)]

    # Skip if no valid laps
    if len(laps) == 0:
        return html.Div("No valid lap data available")

    # Select and format columns for display
    display_columns = ['Driver', 'Team', 'LapNumber', 'LapTime', 'Compound', 'TyreLife', 'Stint', 'TrackStatus']
    display_df = laps[display_columns].copy()

    # Format lap times to strings
    display_df['LapTime'] = display_df['LapTime'].apply(lambda x: str(x))

    # Sort by driver and lap time
    display_df = display_df.sort_values(['Driver', 'LapTime'])

    # Create data table
    return dash_table.DataTable(
        id='lap-distribution-table',
        columns=[{"name": col, "id": col} for col in display_df.columns],
        data=display_df.to_dict('records'),
        style_table={'overflowX': 'auto'},
        style_header={
            'backgroundColor': '#2c3e50',
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'left'
        },
        style_cell={
            'backgroundColor': '#1e2130',
            'color': 'white',
            'textAlign': 'left',
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '14px',
            'padding': '8px'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#283747'
            }
        ],
        page_size=10,
        filter_action="native",
        sort_action="native",
    )

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
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=40, r=40, t=60, b=40),
            height=600
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
                                 color_discrete_map=fastf1.plotting.COMPOUND_COLORS,
                                 height=600)
                else:
                    # Use team as color
                    fig = px.box(df, x='Driver', y='LapTime', color='Team',
                                 title='Lap Time Distribution by Driver',
                                 template='plotly_dark',
                                 color_discrete_map=team_colors,
                                 height=600)
            else:  # violin
                if 'Compound' in df.columns and len(df['Compound'].unique()) > 1:
                    # Use compound as color if available
                    fig = px.violin(df, x='Driver', y='LapTime', color='Compound',
                                    title='Lap Time Distribution by Driver',
                                    box=True, points="all", template='plotly_dark',
                                    color_discrete_map=fastf1.plotting.COMPOUND_COLORS,
                                    height=600)
                else:
                    # Use team as color
                    fig = px.violin(df, x='Driver', y='LapTime', color='Team',
                                    title='Lap Time Distribution by Driver',
                                    box=True, points="all", template='plotly_dark',
                                    color_discrete_map=team_colors,
                                    height=600)

            fig.update_layout(
                xaxis_title='Driver',
                yaxis_title='Lap Time (seconds)',
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                margin=dict(l=40, r=40, t=60, b=40)
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

                # Get team color if not already set - FIXED METHOD
                if team not in team_colors:
                    try:
                        team_colors[team] = fastf1.plotting.team_color(team) # Corrected method
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
                                 color_discrete_map=fastf1.plotting.COMPOUND_COLORS,
                                 height=600)
                else:  # violin
                    fig = px.violin(df, x='Team', y='LapTime', color='Compound',
                                    box=True, points="all",
                                    title='Lap Time Distribution by Team',
                                    template='plotly_dark',
                                    color_discrete_map=fastf1.plotting.COMPOUND_COLORS,
                                    height=600)
            else:
                # Use team colors
                if plot_style == 'box':
                    fig = px.box(df, x='Team', y='LapTime', color='Team',
                                 title='Lap Time Distribution by Team',
                                 template='plotly_dark',
                                 color_discrete_map=team_colors,
                                 height=600)
                else:  # violin
                    fig = px.violin(df, x='Team', y='LapTime', color='Team',
                                    box=True, points="all",
                                    title='Lap Time Distribution by Team',
                                    template='plotly_dark',
                                    color_discrete_map=team_colors,
                                    height=600)
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
                    line=dict(color=team_color, width=3),  # Increased line width for better visibility
                    marker=dict(color=team_color, size=8)
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

    # Additional layout improvements for better readability - FIXED GRID LINES
    fig.update_layout(
        title=dict(
            text='Team Lap Times Comparison',
            font=dict(size=22)
        ),
        xaxis=dict(
            title=dict(
                text='Lap Number' if plot_style in ['line', 'scatter'] else 'Team',
                font=dict(size=16)
            ),
            gridcolor='#333',  # Correct way to set grid line color
            zerolinecolor='#333'
        ),
        yaxis=dict(
            title=dict(
                text='Lap Time (seconds)',
                font=dict(size=16)
            ),
            gridcolor='#333',  # Correct way to set grid line color
            zerolinecolor='#333'
        ),
        template='plotly_dark',
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            font=dict(size=14)
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        height=600,
        plot_bgcolor='#1a1a1a',  # Darker background for better contrast
        paper_bgcolor='#1a1a1a'
    )

    # If we're using line plot, add markers to distinguish lines better
    if plot_style == 'line':
        marker_symbols = ['circle', 'square', 'diamond', 'triangle-up', 'star']
        for i, trace in enumerate(fig.data):
            if hasattr(trace, 'mode') and trace.mode == 'lines+markers':
                fig.data[i].marker.symbol = marker_symbols[i % len(marker_symbols)]

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
            ),
            margin=dict(l=40, r=40, t=60, b=40),
            height=700
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
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            margin=dict(l=40, r=40, t=60, b=40),
            height=600
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
                        color_discrete_map=fastf1.plotting.COMPOUND_COLORS,
                        height=600)
    elif plot_style == 'box':
        # Always prioritize compound colors for box plots
        fig = px.box(df, x='Driver', y='LapTime', color='Compound',
                     title='Lap Time Distribution by Driver and Compound',
                     template='plotly_dark',
                     color_discrete_map=fastf1.plotting.COMPOUND_COLORS,
                     height=600)
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
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        height=600
    )

    return dcc.Graph(figure=fig)