import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

from dash import Dash, html, dcc

import sys
sys.stdout.reconfigure(line_buffering=True) # type: ignore

# Initialize the app
app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.FLATLY])

# App layout

app.layout = dmc.MantineProvider(       
    children=html.Div([
        dash.page_container 
    ])
)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=True)