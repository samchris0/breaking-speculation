import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback, Input, Output, State

from dash_app.utils.google_news_feed import get_top_headlines

dash.register_page(__name__, path="/")

layout = dbc.Container([
            dbc.Row([
                    dbc.Col(html.H1("The Speculative Times", className="text-left my-4"))
                ]),

            dbc.Navbar(
                dbc.Container([
                    dbc.Nav([
                        dbc.NavItem(dbc.NavLink("Business", href="#")),
                        dbc.NavItem(dbc.NavLink("Nation", href="#")),
                        dbc.NavItem(dbc.NavLink("World", href="#")),
                        dbc.NavItem(dbc.NavLink("Technology", href="#")),
                        dbc.NavItem(dbc.NavLink("Entertainment", href="#")),
                        dbc.NavItem(dbc.NavLink("Science", href="#")),
                        dbc.NavItem(dbc.NavLink("Sports", href="#")),
                        dbc.NavItem(dbc.NavLink("Health", href="#")),
                    ], navbar=True, className="w-100 justify-content-evenly")
                ], fluid=True),
                color="black",
                className="mb-4"
            ),

            html.Div([ 
                    dcc.Store(id='initial-load',data=True),

                    dcc.Loading(id='headline-container', children=[html.Div(id = 'headline-container-out')], type='circle')
                ])
        ])

@callback(
    Output('headline-container-out', 'children'),
    Output('initial-load', 'data'),
    Input('headline-container', 'children'),
    State('initial-load', 'data')
)
def load_headlines(headlines_container, initial_load):
    if initial_load == True:
        headlines = get_top_headlines()
        
        headlines_container = []
        
        for headline in headlines:
            
            text = f"Title: {headline.title} \n \
                    Link: {headline.link} \n \
                    Description: {headline.description} \n \
                    Source {headline.source} \n"

            headlines_container.append(dcc.Markdown(text))

        return headlines_container, False
    
    else:
        return dash.no_update, False


