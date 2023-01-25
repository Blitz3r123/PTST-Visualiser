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
    html.Div([dbc.ListGroup(
        generate_toc()
    )]),
    html.Div([
        html.H1("Latency Summary Stats", id="latency-summary-title"),
        html.Div(id="latency-summary-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
    ]),
    html.Div([
        html.H1("Throughput Summary Stats", id="throughput-summary-title"),
        html.Div(id="throughput-summary-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
    ]),
    html.Div([
        html.H1("Sample Rate Summary Stats", id="sample-rate-summary-title"),
        html.Div(id="sample-rate-summary-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
    ]),
    html.Div([
        html.H1("Total Samples Summary Stats", id="total-samples-summary-title"),
        html.Div(id="total-samples-summary-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
    ]),
    html.Div([
        html.H1("Lost Samples Summary Stats", id="lost-samples-summary-title"),
        html.Div(id="lost-samples-summary-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
    ]),
    html.Div([
        html.H1("Logs Timeline", id="summary-title"),
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
        Output("sample-rate-summary-output", "children"),
        Output("total-samples-summary-output", "children"),
        Output("lost-samples-summary-output", "children"),
        Output("log-timeline-output", "children")
    ],
    Input("test-dropdown", "value")
)
def populate_summary(tests):
    
    if tests is None:
        return "", "", "", "", "", ""
    
    lat_summaries = []
    tp_summaries = []
    sample_rate_summaries = []
    total_samples_summaries = []
    lost_samples_summaries = []
    log_timelines = []
    
    for test in tests:
        lat_df = get_lat_df(test)
        lat_summary_stats = get_summary_stats(lat_df, test)
        lat_summaries.append(lat_summary_stats)
        
        tp_df = get_df_from_subs("mbps", test)
        tp_summary_stats = get_summary_stats(tp_df, test)
        tp_summaries.append(tp_summary_stats)
        
        sample_rate_df = get_df_from_subs("samples/s", test)
        sample_rate_summary_stats = get_summary_stats(sample_rate_df, test)
        sample_rate_summaries.append(sample_rate_summary_stats)
        
        total_samples_df = get_df_from_subs("total samples", test)
        total_samples_summary_stats = get_summary_stats(total_samples_df, test)
        total_samples_summaries.append(total_samples_summary_stats)
        
        lost_samples_df = get_df_from_subs("lost samples", test)
        lost_samples_summary_stats = get_summary_stats(lost_samples_df, test)
        lost_samples_summaries.append(lost_samples_summary_stats)
        
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
        
    lat_summary_table = generate_summary_table(lat_summaries)
    tp_summary_table = generate_summary_table(tp_summaries)
    sample_rate_summary_table = generate_summary_table(sample_rate_summaries)
    total_samples_summary_table = generate_summary_table(total_samples_summaries)
    lost_samples_summary_table = generate_summary_table(lost_samples_summaries)
        
    log_timelines = html.Div(log_timelines)
        
    return lat_summary_table, tp_summary_table, sample_rate_summary_table, total_samples_summary_table, lost_samples_summary_table, log_timelines

if __name__ == "__main__": 
    app.run_server(debug=True, host="127.0.0.1", port="6745")