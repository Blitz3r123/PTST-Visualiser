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
    html.Div(id="combinations-container"),
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
    [
        Output("test-dropdown", "options"),    
        Output("combinations-container", "children"),    
    ],
    Input("testdir-input", "value")
)
def populate_dropdown(testpath):
    output = []
    comb_output = []
    
    if os.path.exists(testpath):
        output = [os.path.join(testpath, x) for x in os.listdir(testpath)]
        comb_output = get_comb_output(output)
    else:
        output = []
        
    return output, comb_output

@app.callback(
    [
        Output("latency-summary-output", "children"),
        Output("latency-boxplot-output", "children"),
        Output("latency-dotplot-output", "children"),
        Output("latency-lineplot-output", "children"),
        Output("latency-histogram-output", "children"),
        Output("latency-cdf-output", "children"),
        Output("latency-transient-output", "children"),
        
        Output("throughput-summary-output", "children"),
        Output("throughput-boxplot-output", "children"),
        Output("throughput-dotplot-output", "children"),
        Output("throughput-lineplot-output", "children"),
        Output("throughput-histogram-output", "children"),
        Output("throughput-cdf-output", "children"),
        Output("throughput-transient-output", "children"),
        
        Output("sample-rate-summary-output", "children"),
        Output("sample-rate-boxplot-output", "children"),
        Output("sample-rate-dotplot-output", "children"),
        Output("sample-rate-lineplot-output", "children"),
        Output("sample-rate-histogram-output", "children"),
        Output("sample-rate-cdf-output", "children"),
        Output("sample-rate-transient-output", "children"),
        
        Output("total-samples-summary-output", "children"),
        Output("total-samples-boxplot-output", "children"),
        Output("total-samples-dotplot-output", "children"),
        Output("total-samples-lineplot-output", "children"),
        Output("total-samples-histogram-output", "children"),
        Output("total-samples-cdf-output", "children"),
        Output("total-samples-transient-output", "children"),
        
        Output("lost-samples-summary-output", "children"),
        Output("lost-samples-boxplot-output", "children"),
        Output("lost-samples-dotplot-output", "children"),
        Output("lost-samples-lineplot-output", "children"),
        Output("lost-samples-histogram-output", "children"),
        Output("lost-samples-cdf-output", "children"),
        Output("lost-samples-transient-output", "children"),
        
        Output("log-timeline-output", "children")
    ],
    Input("test-dropdown", "value")
)
def populate_summary(tests):
    
    if tests is None:
        return "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""
    
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
    lat_boxplot = get_plot("box", lat_dfs, "Test", "Latency (ms)") if lat_dfs else None
    lat_dotplot = get_plot("dot", lat_dfs, "Number of Observations", "Latency (ms)") if lat_dfs else None
    lat_lineplot = get_plot("line", lat_dfs, "Number of Observations", "Latency (ms)") if lat_dfs else None
    lat_histogram = get_plot("histogram", lat_dfs, "Latency (ms)", "Number of Observations") if lat_dfs else None
    lat_cdf = get_plot("cdf", lat_dfs, "Latency (ms)", "F(x)") if lat_dfs else None
    lat_transient = get_transient_analysis(lat_dfs , "Latency (ms)")

    tp_summary_table = generate_summary_table(tp_summaries)
    tp_boxplot = get_plot("box", tp_dfs, "Test", "Total Throughput (mbps)") if tp_dfs else None
    tp_dotplot = get_plot("dot", tp_dfs, "Increasing Time In Seconds", "Total Throughput (mbps)") if tp_dfs else None
    tp_lineplot = get_plot("line", tp_dfs, "Increasing Time In Seconds", "Total Throughput (mbps)") if tp_dfs else None
    tp_histogram = get_plot("histogram", tp_dfs, "Total Throughput (mbps)", "Number of Observations") if tp_dfs else None
    tp_cdf = get_plot("cdf", tp_dfs, "Total Throughput (mbps)", "F(x)") if tp_dfs else None
    tp_transient = None
    
    sample_rate_summary_table = generate_summary_table(sample_rate_summaries)
    sr_boxplot = get_plot("box", sr_dfs, "Test", "Sample Rate (samples/s)") if sr_dfs else None
    sr_dotplot = get_plot("dot", sr_dfs, "Increasing Time In Seconds", "Sample Rate (samples/s)") if sr_dfs else None
    sr_lineplot = get_plot("line", sr_dfs, "Increasing Time In Seconds", "Sample Rate (samples/s)") if sr_dfs else None
    sr_histogram = get_plot("histogram", sr_dfs, "Sample Rate (samples/s)", "Number of Observations") if sr_dfs else None
    sr_cdf = get_plot("cdf", sr_dfs, "Sample Rate (sample/s)", "F(x)") if sr_dfs else None
    sr_transient = None
    
    total_samples_summary_table = generate_summary_table(total_samples_summaries)
    # total_samples_boxplot = get_plot("box", total_samples_dfs, "Test", "Total Samples") if total_samples_dfs else None
    total_samples_boxplot = ""
    total_samples_dotplot = get_plot("dot", total_samples_dfs, "Increasing Time In Seconds", "Total Samples") if total_samples_dfs else None
    total_samples_lineplot = get_plot("line", total_samples_dfs, "Increasing Time", "Total Samples") if total_samples_dfs else None
    total_samples_histogram = get_plot("histogram", total_samples_dfs, "Total Samples", "Number of Observations") if total_samples_dfs else None
    total_samples_cdf = get_plot("cdf", total_samples_dfs, "Total Samples", "F(x)") if total_samples_dfs else None
    total_samples_transient = None
    
    lost_samples_summary_table = generate_summary_table(lost_samples_summaries)
    # lost_samples_boxplot = get_plot("box", lost_samples_dfs, "Test", "Lost Samples") if lost_samples_dfs else None
    lost_samples_boxplot = ""
    lost_samples_dotplot = get_plot("dot", lost_samples_dfs, "Increasing Time In Seconds", "Lost Samples") if lost_samples_dfs else None
    lost_samples_lineplot = get_plot("line", lost_samples_dfs, "Increasing Time In Seconds", "Lost Samples") if lost_samples_dfs else None
    lost_samples_histogram = get_plot("histogram", lost_samples_dfs, "Lost Samples", "Number of Observations") if lost_samples_dfs else None
    lost_samples_cdf = get_plot("cdf", lost_samples_dfs, "Lost Samples", "F(x)") if lost_samples_dfs else None
    lost_samples_transient = None
    
    log_timelines = html.Div(log_timelines)
        
    return lat_summary_table, lat_boxplot, lat_dotplot, lat_lineplot, lat_histogram, lat_cdf, lat_transient, tp_summary_table, tp_boxplot, tp_dotplot, tp_lineplot, tp_histogram, tp_cdf, tp_transient, sample_rate_summary_table, sr_boxplot, sr_dotplot, sr_lineplot, sr_histogram, sr_cdf, sr_transient, total_samples_summary_table, total_samples_boxplot, total_samples_dotplot, total_samples_lineplot, total_samples_histogram, total_samples_cdf, total_samples_transient, lost_samples_summary_table, lost_samples_boxplot, lost_samples_dotplot, lost_samples_lineplot, lost_samples_histogram, lost_samples_cdf, lost_samples_transient, log_timelines

if __name__ == "__main__": 
    app.run_server(debug=True, host="127.0.0.1", port="6745")