import os
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.express as px

from pprint import pprint
from functions import *
from dash import Dash, html, dcc, Output, Input

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Input(
        value="C:/Users/acwh025/Documents/Software Dev/ML/data", 
        placeholder="Enter path to tests", 
        id="testdir-input"
    ),
    dcc.Dropdown([], multi=True, id="test-dropdown", placeholder="Select one or more tests"),
    html.Div([
        html.H1("Latency Summary Stats"),    
        html.Div(id="latency-summary-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
    ]),
    html.Div([
        html.H1("Throughput Summary Stats"),    
        html.Div(id="throughput-summary-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
    ]),
    html.Div([
        html.H1("Logs Timeline"),
        html.Div(id="log-timeline-output", style={"maxWidth": "100vw", "overflowX": "scroll"})
    ])
], style={"marginTop": "2vh"}, fluid=True)

@app.callback(
    Output("test-dropdown", "options"),
    Input("testdir-input", "value")
)
def populate_dropdown(testpath):
    if os.path.exists(testpath):
        return [os.path.join(testpath, x) for x in os.listdir(testpath)]
    else:
        return []

@app.callback(
    [
        Output("latency-summary-output", "children"),
        Output("throughput-summary-output", "children"),
        Output("log-timeline-output", "children")
    ],
    Input("test-dropdown", "value")
)
def populate_summary(tests):
    
    if tests is None:
        return "", "", ""
    
    lat_summaries = []
    tp_summaries = []
    log_timelines = []
    for test in tests:
        lat_df = get_lat_df(test)
        lat_summary_stats = get_summary_stats("latency", lat_df, test)
        lat_summaries.append(lat_summary_stats)
        
        tp_df = get_tp_df(test)
        tp_summary_stats = get_summary_stats("throughput", tp_df, test)
        tp_summaries.append(tp_summary_stats)
        
        cpu_log_df = get_cpu_log_df(test)
        
        fig = px.timeline(cpu_log_df, x_start="start", x_end="end", y="vm", color="vm")
        fig.update_layout(xaxis=dict(
            title="Log Timestamp",
            tickformat="%H:%M:%S"
        ))
            
        log_timeline = html.Div([
            html.H5(os.path.basename(test)),
            dcc.Graph(figure=fig)
        ])
        log_timelines.append(log_timeline)
        
    lat_summary_table = dbc.Table([
        html.Thead(
            html.Tr(
                [html.Th("Stat")] + [html.Th( os.path.basename(lat_summary["test"]) ) for lat_summary in lat_summaries]
            )
        ),
        html.Tbody([
            html.Tr([html.Td("Count")] + [html.Td("{0:,.2f}".format(summary["count"])) for summary in lat_summaries]),
            html.Tr([html.Td("mean")] + [html.Td("{0:,.2f}".format(summary["mean"])) for summary in lat_summaries]),
            html.Tr([html.Td("median")] + [html.Td("{0:,.2f}".format(summary["median"])) for summary in lat_summaries]),
            html.Tr([html.Td("variance")] + [html.Td("{0:,.2f}".format(summary["variance"])) for summary in lat_summaries]),
            html.Tr([html.Td("std")] + [html.Td("{0:,.2f}".format(summary["std"])) for summary in lat_summaries]),
            html.Tr([html.Td("skew")] + [html.Td("{0:,.2f}".format(summary["skew"])) for summary in lat_summaries]),
            html.Tr([html.Td("range")] + [html.Td("{0:,.2f}".format(summary["range"])) for summary in lat_summaries]),
            html.Tr([html.Td("lower_quartile")] + [html.Td("{0:,.2f}".format(summary["lower_quartile"])) for summary in lat_summaries]),
            html.Tr([html.Td("upper_quartile")] + [html.Td("{0:,.2f}".format(summary["upper_quartile"])) for summary in lat_summaries]),
            html.Tr([html.Td("interquartile_range")] + [html.Td("{0:,.2f}".format(summary["interquartile_range"])) for summary in lat_summaries]),
            html.Tr([html.Td("min")] + [html.Td("{0:,.2f}".format(summary["min"])) for summary in lat_summaries]),
            html.Tr([html.Td("max")] + [html.Td("{0:,.2f}".format(summary["max"])) for summary in lat_summaries])
        ])
    ], bordered=True, hover=True)
    
    tp_summary_table = dbc.Table([
        html.Thead(
            html.Tr(
                [html.Th("Stat")] + [html.Th( os.path.basename(tp_summary["test"]) ) for tp_summary in tp_summaries]
            )
        ),
        html.Tbody([
            html.Tr([html.Td("Count")] + [html.Td("{0:,.2f}".format(summary["count"])) for summary in tp_summaries]),
            html.Tr([html.Td("mean")] + [html.Td("{0:,.2f}".format(summary["mean"])) for summary in tp_summaries]),
            html.Tr([html.Td("median")] + [html.Td("{0:,.2f}".format(summary["median"])) for summary in tp_summaries]),
            html.Tr([html.Td("variance")] + [html.Td("{0:,.2f}".format(summary["variance"])) for summary in tp_summaries]),
            html.Tr([html.Td("std")] + [html.Td("{0:,.2f}".format(summary["std"])) for summary in tp_summaries]),
            html.Tr([html.Td("skew")] + [html.Td("{0:,.2f}".format(summary["skew"])) for summary in tp_summaries]),
            html.Tr([html.Td("range")] + [html.Td("{0:,.2f}".format(summary["range"])) for summary in tp_summaries]),
            html.Tr([html.Td("lower_quartile")] + [html.Td("{0:,.2f}".format(summary["lower_quartile"])) for summary in tp_summaries]),
            html.Tr([html.Td("upper_quartile")] + [html.Td("{0:,.2f}".format(summary["upper_quartile"])) for summary in tp_summaries]),
            html.Tr([html.Td("interquartile_range")] + [html.Td("{0:,.2f}".format(summary["interquartile_range"])) for summary in tp_summaries]),
            html.Tr([html.Td("min")] + [html.Td("{0:,.2f}".format(summary["min"])) for summary in tp_summaries]),
            html.Tr([html.Td("max")] + [html.Td("{0:,.2f}".format(summary["max"])) for summary in tp_summaries])
        ])
    ], bordered=True, hover=True)
        
    log_timelines = html.Div(log_timelines)
        
    return lat_summary_table, tp_summary_table, log_timelines

if __name__ == "__main__": 
    app.run_server(debug=True, host="127.0.0.1", port="6745")