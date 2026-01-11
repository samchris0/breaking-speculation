import asyncio
import atexit
import httpx

import dash
from dash import Dash, html, dcc

from app.dash.utils.http_client import async_client

# Initialize the app
app = Dash(__name__, use_pages=True, suppress_callback_exceptions=True)

# App layout
app.layout = html.Div([
                        dash.page_container
                    ])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050)