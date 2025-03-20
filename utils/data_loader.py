import os
import fastf1

def setup_fastf1_cache():
    """Create and configure the fastf1 cache."""
    # Create cache directory if it doesn't exist
    cache_dir = os.path.join(os.getcwd(), 'cache')
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    # Enable cache to speed up data loading
    fastf1.Cache.enable_cache(cache_dir)

    return cache_dir

def get_events_for_season(season):
    """Get all events for a specific F1 season.

    Args:
        season (int): Year of the season

    Returns:
        list: List of event options for dropdown
    """
    # Get all events for the selected season
    events = fastf1.get_event_schedule(season)
    event_options = [{'label': f"{event['EventName']} - {event['EventDate'].strftime('%d %b')}",
                      'value': event['EventName']}
                     for _, event in events.iterrows()]

    return event_options

def load_session(season, event, session_type):
    """Load a specific F1 session.

    Args:
        season (int): Year of the season
        event (str): Name of the event
        session_type (str): Session type (e.g., 'FP1', 'Q', 'R')

    Returns:
        fastf1.Session: Loaded session object
    """
    session = fastf1.get_session(season, event, session_type)
    session.load()
    return session