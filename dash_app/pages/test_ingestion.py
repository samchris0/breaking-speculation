import json

import dash
from dash import html, dcc, callback, Input, Output, State, MATCH
from dash.exceptions import PreventUpdate

from dash_app.utils.ingestion_request import ingestion_request
from dash_app.utils.result_query import result_query

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
    
    #Save task_ids
    html.Div(id="store-task-ids",
             children=[
                html.Div([
                    dcc.Interval(id={'type': 'result-polling', 'index':'init'}, interval=100000, disabled=False),
                    dcc.Store(id={'type': 'task-storage', 'index':'init'}, data=[]) #type:ignore
             ])
            ]     
        ),

    html.Div(id='display-results',
             children=[html.Div(id={'type': 'result-container', 'index': 'init'}, children=[])])
])

#Build search options radio buttons based on provider selected
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
        Output('store-task-ids','children'),
        Output('display-results','children'),
        Input('make-query','n_clicks'),
        State('provider','value'),
        State('search-term','value'),
        State('provider-search-options', 'value'),
        State('store-task-ids','children'),
        State('display-results','children'),
        prevent_initial_call=True
)
def make_query(_, provider, search_term, search, storage, results):

    request = ingestion_request(provider=provider,search_term=search_term,search=search)

    print(request["task_id"])

    new_query = html.Div([
        
        # Add max interval?
        dcc.Interval(id={'type': 'result-polling', 'index':f'{request["task_id"]}'}, interval=500, disabled=False),
        dcc.Store(id={'type': 'task-storage', 'index':f'{request["task_id"]}'}, data=request["task_id"])
    
    ])
    
    result_container = html.Div(id={'type':'result-container', 'index':f'{request["task_id"]}'})

    return storage+[new_query], results+[result_container]


@callback(
    Output({'type': 'result-container', 'index':MATCH},'children'),
    Output({'type': 'result-polling', 'index': MATCH}, 'disabled'),
    Input({'type': 'result-polling', 'index': MATCH}, 'n_intervals'),
    State({'type': 'task-storage', 'index': MATCH}, 'data'),
    prevent_initial_call=True
)
def return_query(_, task_id):
    
    if not task_id:
        raise PreventUpdate

    results = result_query(task_id)
    status = results.get("status")
    
    continue_polling = False
    disable_polling = True

    if status == "pending":
        return dash.no_update, continue_polling

    if status == "in_progress":
        data = results["data"]

        update_result = html.Div(
            html.Ul(
                    [html.Pre(json.dumps(item, indent=2)) for item in data]
            )
        ) 
        return update_result, continue_polling
    
    if status == "success":
        data = results["data"]

        final_result = html.Div(
            html.Ul(
                    [html.Pre(json.dumps(item, indent=2)) for item in data]
            )
        ) 
        return final_result, disable_polling

    if status == "failure":
        disable_polling = True
        error = results.get("error", "Unknown error")

        return [f"Error in fetching data: {error}"], disable_polling

    return [f"Unknown task status: {status}"], disable_polling
