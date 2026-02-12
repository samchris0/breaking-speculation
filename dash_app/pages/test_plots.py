from collections import defaultdict

import dash
import dash_mantine_components as dmc
from dash import html, dcc, callback, Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate

from dash_app.utils.build_figures import build_market_figure
from dash_app.utils.ingestion_request import ingestion_request
from dash_app.utils.merge_tree_deltas import merge_tree_deltas
from dash_app.utils.render_tree import render_tree_keys
from dash_app.utils.result_query import result_query

dash.register_page(__name__, path="/test-plots")

providers = {'Polymarket':'polymarket'}

provider_searches = {
    'polymarket': {'keyword':'keyword', 'event_slug':'exact'},
    #'kalshi': []
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
    
    html.Div(id="accordion-container",
             children=[
                    html.Div(id={"type":"accordion", "index":"init"})     
                ] 
            ),

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
    ]
)


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
        Output('accordion-container', 'children'),
        Input('make-query','n_clicks'),
        State('provider','value'),
        State('search-term','value'),
        State('provider-search-options', 'value'),
        State('store-tasks','children'),
        State('accordion-container', 'children'),
        prevent_initial_call=True
)
def make_query(_, provider, search_term, search, queries, accordions):

    request = ingestion_request(provider=provider,search_term=search_term,search=search)

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

    new_accordion = html.Div(
        [
            html.Div(id={"type":"accordion", "index":f'{request["task_id"]}'})
        ]
    )

    return queries+[new_query], accordions+[new_accordion]


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

    if status == "complete":
        error = request.get("error", "Unknown error")

        return [f"Search complete, no markets available for this keyword"], polling_disabled, index, tree

    deltas = request["data"]
    
    if deltas:
        new_deltas = deltas[index:]
        new_index = len(deltas)
        new_tree = merge_tree_deltas(tree, new_deltas)
        

        if status == "in_progress":
            return ["New Data Added"], continue_polling, new_index, new_tree
        
        if status == "success":
            return ["Completed Successfully"], polling_disabled, new_index, new_tree

    return [f"Status: {status}"], continue_polling, index, tree


@callback(
    Output({"type": "accordion", "index": MATCH}, "children"),
    Input({"type": "result-tree", "index": MATCH}, "data"),
    prevent_initial_call=True
)
def create_accordion(tree):
    
    event_accordions = []

    for event_id, event_data in tree.items():
        
        market_list = list(event_data["markets"].items())
        show_toggle_button = len(market_list) > 5

        event_accordions.append(
            html.Div(
                key=f"event-{event_id}",
                children=[   
                    dcc.Store(
                        id={"type": "accordion-visibility", "event-id": event_id, },
                        data="collapsed",
                    ),

                    dmc.Stack(
                        children=[
                            dmc.Group(
                                children=[
                                    # Event image
                                    html.Img(
                                        src=event_data["event_image"], #type: ignore
                                        style={"width": "40px", "height": "40px", "object-fit": "cover"},
                                    ),

                                    # Event title
                                    dmc.Text(
                                        f"{event_data['event_title']}",
                                        size="lg",
                                        fw=600,
                                    ),
                                ],
                            ),
                        
                        # Build accordion
                        dmc.Accordion(
                            id = {"type": "event-accordion","event-id": event_id},
                            multiple=True,
                            children=[
                                dmc.AccordionItem(
                                    value=market_id, #type: ignore
                                    style={
                                        "display": "block" if i < 5 else "none"
                                    },
                                    children=[
                                        dmc.AccordionControl(
                                            f"{market_data['market_question']}"
                                        ),
                                        dmc.AccordionPanel(
                                            html.Div(
                                                id={"type": "market-graph-container","event-id": event_id,"market-id": market_id,},
                                            )
                                        ),
                                    ],
                                )
                                for i, (market_id, market_data) in enumerate(market_list) # type: ignore
                            ],
                        ),

                        dmc.Center(
                            dmc.Button(
                                "Show all markets",
                                id={"type": "accordion-toggle", "event-id": event_id},
                                variant="subtle",
                                size="sm",
                                style={"display": "block" if show_toggle_button else "none"}
                            )
                        ),
                        
                        # Space out accordions
                        dmc.Divider(my="sm"),
                    
                        ]
                    )
                ]
            )
        )

    return event_accordions


@callback(
    Output({"type": "market-graph-container", "event-id": MATCH, "market-id": ALL}, "children"),
    Input({"type": "event-accordion", "event-id": MATCH}, "value"),
    State({"type": "result-tree", "index": ALL}, "data"),
    prevent_initial_call=True
)
def render_plots(active_markets, results_trees):
    
    if isinstance(active_markets, str):
        active_markets = [active_markets]

    # Get output ids
    event_id = dash.ctx.outputs_list[0]["id"]["event-id"]
    market_ids = [output["id"]["market-id"] for output in dash.ctx.outputs_list]

    n_markets = len(market_ids)
    
    if not active_markets:
        return [dash.no_update] * n_markets

    # Find the tree containing this event
    tree = next((t for t in results_trees if event_id in t), None)
    
    if not tree:
        return [dash.no_update] * n_markets

    event_data = tree[event_id]
    markets_dict = event_data.get("markets", {})
    
    outputs = []

    for market_id in market_ids:
        
        # Check if active
        if market_id not in active_markets:
            outputs.append(dash.no_update)
            continue
        
        market_data = markets_dict.get(market_id)
        
        if market_data:
            outputs.append(dcc.Graph(figure=build_market_figure(market_data),
                                     config={'displayModeBar': False,
                                             'scrollZoom': False}
                                )
                            )
        else:
            outputs.append(dash.no_update)

    return outputs

@callback(
    Output({"type": "event-accordion", "event-id": MATCH},"children",),
    Output({"type": "accordion-toggle", "event-id": MATCH},"children",),
    Output({"type": "accordion-visibility", "event-id": MATCH},"data",),
    Input({"type": "accordion-toggle", "event-id": MATCH},"n_clicks",),
    State({"type": "event-accordion", "event-id": MATCH},"children",),
    State({"type": "accordion-visibility", "event-id": MATCH},"data",),
    prevent_initial_call=True,
)
def toggle_accordion(_, accordion_children, visibility):
    show_all = visibility == "collapsed"

    for i, item in enumerate(accordion_children):
        item["props"]["style"] = {
            "display": "block" if show_all or i < 5 else "none"
        }

    return (
        accordion_children,
        "Show fewer markets" if show_all else "Show all markets",
        "expanded" if show_all else "collapsed",
    )