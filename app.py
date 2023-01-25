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
    generate_metric_output_content("Latency", "latency"),
    generate_metric_output_content("Throughput", "throughput"),
    generate_metric_output_content("Sample Rate", "sample-rate"),
    generate_metric_output_content("Total Samples", "total-samples"),
    generate_metric_output_content("Lost Samples", "lost-samples"),
    html.Div([
        html.H3("Logs Timeline", id="log-timeline-title"),
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
        Output("latency-boxplot-output", "children"),
        Output("throughput-summary-output", "children"),
        Output("throughput-boxplot-output", "children"),
        Output("sample-rate-summary-output", "children"),
        Output("sample-rate-boxplot-output", "children"),
        Output("total-samples-summary-output", "children"),
        Output("total-samples-boxplot-output", "children"),
        Output("lost-samples-summary-output", "children"),
        Output("lost-samples-boxplot-output", "children"),
        Output("log-timeline-output", "children")
    ],
    Input("test-dropdown", "value")
)
def populate_summary(tests):
    
    if tests is None:
        return "", "", "", "", "", "", "", "", "", "", ""
    
    lat_summaries = []
    tp_summaries = []
    sample_rate_summaries = []
    total_samples_summaries = []
    lost_samples_summaries = []
    log_timelines = []
    
    lat_dfs = []
    tp_dfs = []
    sr_dfs = []
    total_samples_dfs = []
    lost_samples_dfs = []
    
    for test in tests:
        lat_df = get_lat_df(test)
        lat_dfs.append(lat_df.rename(os.path.basename(test)))
        lat_summary_stats = get_summary_stats(lat_df, test)
        lat_summaries.append(lat_summary_stats)
        
        tp_df = get_df_from_subs("mbps", test)
        tp_dfs.append(tp_df.rename(os.path.basename(test)))
        tp_summary_stats = get_summary_stats(tp_df, test)
        tp_summaries.append(tp_summary_stats)
        
        sample_rate_df = get_df_from_subs("samples/s", test)
        sr_dfs.append(sample_rate_df.rename(os.path.basename(test)))
        sample_rate_summary_stats = get_summary_stats(sample_rate_df, test)
        sample_rate_summaries.append(sample_rate_summary_stats)
        
        total_samples_df = get_df_from_subs("total samples", test)
        total_samples_dfs.append(total_samples_df.rename(os.path.basename(test)))
        total_samples_summary_stats = get_summary_stats(total_samples_df, test)
        total_samples_summaries.append(total_samples_summary_stats)
        
        lost_samples_df = get_df_from_subs("lost samples", test)
        lost_samples_dfs.append(lost_samples_df.rename(os.path.basename(test)))
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
    lat_boxplot_fig = get_boxplot(lat_dfs, "Latency (us)") if lat_dfs else None
    if lat_boxplot_fig is None:
        lat_boxplot = ""
    else:
        lat_boxplot = dcc.Graph(figure=lat_boxplot_fig)
    
    tp_summary_table = generate_summary_table(tp_summaries)
    tp_boxplot_fig = get_boxplot(tp_dfs, "Throughput (mbps)") if tp_dfs else None
    if tp_boxplot_fig is None:
        tp_boxplot = ""
    else:
        tp_boxplot = dcc.Graph(figure=tp_boxplot_fig)
    
    sample_rate_summary_table = generate_summary_table(sample_rate_summaries)
    sr_boxplot_fig = get_boxplot(sr_dfs, "Sample Rate (samples/s)") if sr_dfs else None
    if sr_boxplot_fig is None:
        sr_boxplot = ""
    else:
        sr_boxplot = dcc.Graph(figure=sr_boxplot_fig)
    
    total_samples_summary_table = generate_summary_table(total_samples_summaries)
    total_samples_boxplot_fig = get_boxplot(total_samples_dfs, "Total Samples") if total_samples_dfs else None
    if total_samples_boxplot_fig is None:
        total_samples_boxplot = ""
    else:
        total_samples_boxplot = dcc.Graph(figure=total_samples_boxplot_fig)
    
    lost_samples_summary_table = generate_summary_table(lost_samples_summaries)
    lost_samples_boxplot_fig = get_boxplot(lost_samples_dfs, "Lost Samples") if lost_samples_dfs else None
    if lost_samples_boxplot_fig is None:
        lost_samples_boxplot = ""
    else:
        lost_samples_boxplot = dcc.Graph(figure=lost_samples_boxplot_fig)
    
    log_timelines = html.Div(log_timelines)
        
    return lat_summary_table, lat_boxplot, tp_summary_table, tp_boxplot, sample_rate_summary_table, sr_boxplot, total_samples_summary_table, total_samples_boxplot, lost_samples_summary_table, lost_samples_boxplot, log_timelines

if __name__ == "__main__": 
    app.run_server(debug=True, host="127.0.0.1", port="6745")