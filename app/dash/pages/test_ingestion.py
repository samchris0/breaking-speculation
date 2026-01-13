import dash
from dash import html, dcc, callback, Input, Output, State

from app.dash.utils.ingestion_request import ingestion_request

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
                options=providers,
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
    Input('provider','value'),
    Output('provider_options','options')
)
def display_search_options(provider):
    return provider_searches.get(provider)

@callback(
        Output('display-results','children'),
        Input('make-query','n_clicks'),
        State('provider','value'),
        State('search-term','value'),
        State('provider-search-options', 'value')
)
def make_query(_, provider, search_term, search):

    data = ingestion_request(provider=provider,search_term=search_term,search=search)

    if not data:
        return "No results found"

    return [
        html.H3("Results"),
        html.Div(
            html.Ul(
                [html.Li(datum) for datum in data],
                className = "results-list"
            )
        )
    ]