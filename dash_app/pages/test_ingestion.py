import dash
from dash import html, dcc, callback, Input, Output, State

from dash_app.utils.ingestion_request import ingestion_request

dash.register_page(__name__, path="/test")

providers = {'Polymarket':'polymarket', 'Kalshi':'kalshi'}

provider_searches = {
    'polymarket': {'keyword':'keyword', 'event_slug':'exact'},
    'kalshi': []
}

layout = html.Div([
    html.Title(title='Test Page'),

    html.Div(["Select a provider: ",

            dcc.RadioItems(
                options=[{'label': k, 'value': v} for k, v in providers.items()],
                id = "provider"
            )
    ]),

    html.Div(["Select a search option: ",
            
            dcc.RadioItems(
                id = "provider-search-options"
            )
    ]),

    html.Div([
        html.H2('Enter search term'),
        dcc.Input(id='search-term', type='text')
    ]),

    html.Button('Make Query', id='make-query'),
    
    html.Div(id='display-results')
])

@callback(
    Output('provider-search-options','options'),
    Input('provider','value')
)
def display_search_options(provider):
    options = provider_searches.get(provider)

    if isinstance(options, dict):
        return [{'label': k, 'value': v} for k,v in options.items()]
    else:
        return []

@callback(
        Output('display-results','children'),
        Input('make-query','n_clicks'),
        State('provider','value'),
        State('search-term','value'),
        State('provider-search-options', 'value'),
        prevent_initial_call=True
)
def make_query(_, provider, search_term, search):

    task = ingestion_request(provider=provider,search_term=search_term,search=search)


    if not task:
        return "No results found"

    return [
        html.H3("Results"),
        html.Div(
            html.Ul(
                [html.Li(item) for item in task],
                className = "results-list"
            )
        )
    ]