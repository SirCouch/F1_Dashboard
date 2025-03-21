from dash import Dash
import dash_bootstrap_components as dbc

from components.layout import create_layout
from components.callbacks import register_callbacks
from utils.data_loader import setup_fastf1_cache

# Create cache directory if it doesn't exist
setup_fastf1_cache()

# Create the Dash app
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True
)

# Set up the app layout
app.layout = create_layout()

# Register all callbacks
register_callbacks(app)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)