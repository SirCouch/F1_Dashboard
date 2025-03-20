from dash import Output, Input, html, dcc
import fastf1
from utils.data_loader import load_session, get_events_for_season
from utils.visualization import (
    create_laptimes_chart, create_team_comparison, create_telemetry_visualization,
    create_lap_distribution, create_laptimes_table, create_team_comparison_table,
    create_telemetry_table, create_lap_distribution_table
)

def register_callbacks(app):
    """Register all callbacks for the Dash app."""

    # Callback to update event options when season changes
    @app.callback(
        Output('event-dropdown', 'options'),
        Output('event-dropdown', 'value'),
        Input('season-dropdown', 'value')
    )
    def update_events(selected_season):
        if not selected_season:
            return [], None

        event_options = get_events_for_season(selected_season)
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
            session = load_session(selected_season, selected_event, selected_session)

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
            session = load_session(selected_season, selected_event, selected_session)

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

    # Main callback to update visualization and data table
    @app.callback(
        [Output('visualization-container', 'children'),
         Output('data-table-container', 'children')],
        [Input('season-dropdown', 'value'),
         Input('event-dropdown', 'value'),
         Input('session-dropdown', 'value'),
         Input('viz-type', 'value'),
         Input('driver-dropdown', 'value'),
         Input('team-dropdown', 'value'),
         Input('plot-style', 'value'),
         Input('telemetry-channel', 'value'),
         Input('telemetry-track-map', 'value'),
         Input('compound-filter', 'value')]
    )
    def update_visualization_and_table(season, event, session_type, viz_type, selected_drivers,
                                       selected_teams, plot_style, telemetry_channel, telemetry_track_map,
                                       compound_filter):
        if not (season and event and session_type and viz_type):
            return html.Div("Please select all required options"), html.Div("No data to display")

        try:
            # Load session data
            session = load_session(season, event, session_type)

            # Prepare data for visualization
            visualization = None
            data_table = None

            if viz_type == 'laptimes':
                if not selected_drivers:
                    return html.Div("Please select at least one driver"), html.Div("No data to display")
                visualization = create_laptimes_chart(session, selected_drivers, plot_style, compound_filter)
                data_table = create_laptimes_table(session, selected_drivers, compound_filter)

            elif viz_type == 'team_comparison':
                if not selected_teams or len(selected_teams) < 1:
                    return html.Div("Please select at least one team"), html.Div("No data to display")
                visualization = create_team_comparison(session, selected_teams, plot_style, compound_filter)
                data_table = create_team_comparison_table(session, selected_teams, compound_filter)

            elif viz_type == 'telemetry':
                if not selected_drivers:
                    return html.Div("Please select at least one driver"), html.Div("No data to display")
                visualization = create_telemetry_visualization(session, selected_drivers, telemetry_channel,
                                                               telemetry_track_map, plot_style)
                data_table = create_telemetry_table(session, selected_drivers, telemetry_channel)

            elif viz_type == 'lap_distribution':
                visualization = create_lap_distribution(session, compound_filter, plot_style)
                data_table = create_lap_distribution_table(session, compound_filter)

            return visualization, data_table

        except Exception as e:
            return html.Div(f"Error: {str(e)}"), html.Div("Error loading data")