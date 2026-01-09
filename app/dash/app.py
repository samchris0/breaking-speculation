import dash
from dash import Dash, html, dcc

# Initialize the app
app = Dash(__name__, use_pages=True)

# App layout
app.layout = html.Div([
                        dash.page_container
                    ])

if __name__ == "__main__":
    app.run_server(debug=True)