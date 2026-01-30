import plotly.graph_objects as go


def build_market_figure(market_data):
    fig = go.Figure()
    
    yes_data = market_data["outcomes"].get("Yes",[])
    no_data = market_data["outcomes"].get("No",[])

    if yes_data:
        yes_history = yes_data.get("history",[])
        if yes_history:
            fig.add_trace(
                go.Scatter(x=yes_history["t"],y=yes_history["h"],name="Yes",mode="lines",line_color="darkgreen")
            )
    if no_data:
        no_history = no_data.get("history",[])
        if no_history:
            fig.add_trace(
                go.Scatter(x=no_history["t"],y=no_history["h"],name="Yes",mode="lines",line_color="firebrick")
            )

    return fig