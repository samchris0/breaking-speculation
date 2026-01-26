import json

import dash
from dash import html, dcc, callback, Input, Output, State, MATCH
from dash.exceptions import PreventUpdate

from dash_app.utils.ingestion_request import ingestion_request
from dash_app.utils.merge_tree_deltas import merge_tree_deltas
from dash_app.utils.render_tree import render_tree
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
    html.Div(id="store-tasks",
             children=[
                html.Div([
                    dcc.Interval(id={'type': 'result-polling', 'index':'init'}, interval=100000, disabled=True),
                    dcc.Store(id={'type': 'task-storage', 'index':'init'}, data=[]), #type:ignore
                    dcc.Store(id={'type': 'task-index-counter', 'index':'init'}, data=0),
                    dcc.Store(id={'type': 'result-tree', 'index':'init'}, data={}),
                ])
            ]     
        ),
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
        Output('store-tasks','children'),
        Input('make-query','n_clicks'),
        State('provider','value'),
        State('search-term','value'),
        State('provider-search-options', 'value'),
        State('store-tasks','children'),
        prevent_initial_call=True
)
def make_query(_, provider, search_term, search, queries):

    request = ingestion_request(provider=provider,search_term=search_term,search=search)

    print(request["task_id"])

    new_query = html.Div(
        [
            # Add max interval?
            dcc.Interval(id={'type': 'result-polling', 'index':f'{request["task_id"]}'}, interval=750, disabled=False),
            dcc.Store(id={'type': 'task-id-storage', 'index':f'{request["task_id"]}'}, data=request["task_id"]),
            dcc.Store(id={'type': 'task-index-counter', 'index':f'{request["task_id"]}'}, data=0),
            dcc.Store(id={'type': 'result-tree', 'index':f'{request["task_id"]}'}, data={}),

            html.Div(
                id={'type':'result-container', 'index':f'{request["task_id"]}'},
                className = "result-output"
                ),
        ],
    className="query"
    )
    
    return queries+[new_query]


@callback(
    Output({'type': 'result-container', 'index':MATCH},'children'),
    Output({'type': 'result-polling', 'index': MATCH}, 'disabled'),
    Output({'type': 'task-index-counter', 'index': MATCH}, 'data'),
    Output({'type': 'result-tree', 'index': MATCH}, 'data'),
    Input({'type': 'result-polling', 'index': MATCH}, 'n_intervals'),
    State({'type': 'task-id-storage', 'index': MATCH}, 'data'),
    State({'type': 'task-index-counter', 'index': MATCH}, 'data'),
    State({'type': 'result-tree', 'index': MATCH}, 'data'),
    prevent_initial_call=True
)
def return_query(_, task_id, index, tree):
    
    if not task_id:
        raise PreventUpdate

    # Get new data and update meta information
    request = result_query(task_id)
    status = request.get("status")
    
    continue_polling = False
    polling_disabled = True

    if status == "pending":
        return dash.no_update, continue_polling, index, tree

    if status == "failure":
        error = request.get("error", "Unknown error")

        return [f"Error in fetching data: {error}"], polling_disabled, index, tree

    deltas = request["data"]
    if deltas:
        new_deltas = deltas[index:]
        new_index = len(deltas)
        new_tree = merge_tree_deltas(tree, new_deltas)
        html_tree = render_tree(new_tree)

        if status == "in_progress":
            return html_tree, continue_polling, new_index, new_tree
        
        if status == "success":
            return html_tree, polling_disabled, new_index, new_tree

    return [f"Status: {status}"], continue_polling, index, tree
