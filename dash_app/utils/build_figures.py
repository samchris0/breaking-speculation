from datetime import datetime

import plotly.graph_objects as go


def build_market_figure(market_data):
    fig = go.Figure()#config={"displayModeBar":False})
    
    yes_data = market_data["outcomes"].get("Yes",[])
    no_data = market_data["outcomes"].get("No",[])

    if no_data:
        no_history = no_data.get("history",[])
        if no_history:
            
            no_price = [price*100 for price in no_history["p"]]
            no_dates = [datetime.fromtimestamp(ts) for ts in no_history["t"]]

            fig.add_trace(
                go.Scatter(x=no_dates,y=no_price,name="No",mode="lines",line_color="firebrick")
            )

    if yes_data:
        yes_history = yes_data.get("history",[])
        if yes_history:

            yes_price = [price*100 for price in yes_history["p"]]
            yes_dates = [datetime.fromtimestamp(ts) for ts in yes_history["t"]]

            fig.add_trace(
                go.Scatter(x=yes_dates,y=yes_price,name="Yes",mode="lines",line_color="darkgreen")
            )
            fig.update_layout(    
                title=f"{round(yes_price[-1])}% Chance"
            )

    fig.update_layout(    
        xaxis=dict(
            showspikes=True,
            fixedrange=True,
            spikemode="across",  
            spikesnap="cursor",  
            spikecolor="black",
            spikedash="dash",
        ),
        yaxis=dict(
            fixedrange=True
        ),
        hovermode="x"
    )

    return fig