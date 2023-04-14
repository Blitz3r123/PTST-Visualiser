import os
import sys
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.express as px

from pprint import pprint
from functions import *
from dash import Dash, html, dcc, Output, Input

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

if len(sys.argv[1:]) > 0:
    data_dir = sys.argv[1]
else:
    data_dir = ""

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(
            [
                html.Div(id="testdir", style={"display": "none"}),
                dbc.Input(
                    value=data_dir,
                    placeholder="Enter path to tests", 
                    id="testdir-input"
                ),
                dcc.Dropdown(
                    [], 
                    multi=True, 
                    id="test-dropdown", 
                    placeholder="Select one or more tests",
                    style={"marginTop": "1vh"}
                ),
                html.Div([dbc.ListGroup(
                    generate_toc()
                )]),
            ], 
            width=3,
            style={"maxHeight": "100vh", "overflowY": "scroll"}
        ),
        dbc.Col(
            [
                html.Div(id="alert-container"),
                html.Div(id="combinations-container"),
                generate_metric_output_content("Latency", "latency"),
                generate_metric_output_content("Throughput", "throughput"),
                generate_metric_output_content("Sample Rate", "sample-rate"),
                generate_metric_output_content("Total Samples", "total-samples-received"),
                generate_metric_output_content("Lost Samples", "lost-samples"),
                html.Div([
                    html.H3("Logs Timeline", id="log-timeline-title"),
                    html.Div(id="log-timeline-output", style={"maxWidth": "100vw", "overflowX": "scroll"})
                ])
            ], 
            width=9,
            style={"maxHeight": "100vh", "overflowY": "scroll"}
        )
    ]),
], style={"maxHeight": "100vh", "overflowY": "hidden", "paddingTop": "2vh"}, fluid=True)

@app.callback(
    [
        Output("test-dropdown", "options"),
        Output("combinations-container", "children"),
        Output("testdir", "children"),
        Output("alert-container", "children")
    ],
    Input("testdir-input", "value")
)
def populate_dropdown(testpath):
    test_summaries = []
    comb_output = []
    errors = []

    test_summaries, errors = get_test_summaries(testpath)
    
    comb_output = get_comb_output(test_summaries)
        
    if len(errors) > 0:
        alerts = []
        
        for error in errors:
            alerts.append(dbc.Alert(error, id="alert", color="danger", dismissable=True, is_open=True))

        alert_output = alerts
    else:
        alert_output = []
    
    return test_summaries, comb_output, testpath, alert_output

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
        
        Output("total-samples-received-summary-output", "children"),
        Output("total-samples-received-boxplot-output", "children"),
        Output("total-samples-received-dotplot-output", "children"),
        Output("total-samples-received-lineplot-output", "children"),
        Output("total-samples-received-histogram-output", "children"),
        Output("total-samples-received-cdf-output", "children"),
        Output("total-samples-received-transient-output", "children"),
        
        Output("lost-samples-summary-output", "children"),
        Output("lost-samples-boxplot-output", "children"),
        Output("lost-samples-dotplot-output", "children"),
        Output("lost-samples-lineplot-output", "children"),
        Output("lost-samples-histogram-output", "children"),
        Output("lost-samples-cdf-output", "children"),
        Output("lost-samples-transient-output", "children"),
        
        # Output("log-timeline-output", "children")
    ],
    [
        Input("test-dropdown", "value"),
        Input("testdir", "children"),
    ]
)
def populate_summary(tests, testdir):
    if tests is None:
        return "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""
    
    lat_summaries = []
    tp_summaries = []
    sample_rate_summaries = []
    total_samples_received_summaries = []
    lost_samples_summaries = []
    # log_timelines = []
    
    lat_dfs = []
    tp_dfs = []
    sr_dfs = []
    total_samples_received_dfs = []
    lost_samples_dfs = []
    
    for test in tests:
        summary_file = os.path.join(testdir, f"{test}_summary.csv")
        if not os.path.exists(summary_file):
            console.print(f"Summmary file doesn't exist for {test}.", style="bold red")
            continue
        
        # ! Limit file reading to 10,000 rows or Dash will break
        summary_df = pd.read_csv(summary_file, nrows=10000)
        
        testname = test
        test = os.path.join(testdir, test)
        lat_df = summary_df["latency_us"]
        # ? Convert microseconds to milliseconds
        lat_df = lat_df.loc[:].div(1000)
        lat_dfs.append(lat_df.rename(testname))
        lat_summary_stats = get_summary_stats(lat_df, test)
        lat_summaries.append(lat_summary_stats)
        
        tp_df = summary_df["total_throughput_mbps"].dropna()
        tp_dfs.append(tp_df.rename(testname))
        tp_summary_stats = get_summary_stats(tp_df, test)
        tp_summaries.append(tp_summary_stats)
        
        sample_rate_df = summary_df["total_sample_rate"].dropna()
        sr_dfs.append(sample_rate_df.rename(testname))
        sample_rate_summary_stats = get_summary_stats(sample_rate_df, test)
        sample_rate_summaries.append(sample_rate_summary_stats)
        
        total_samples_received_df = summary_df["total_samples_received"].dropna()
        total_samples_received_dfs.append(total_samples_received_df.rename(testname))
        total_samples_received_summary_stats = get_summary_stats(total_samples_received_df, test)
        total_samples_received_summaries.append(total_samples_received_summary_stats)
        
        
        lost_samples_df = summary_df["total_samples_lost"].dropna()
        lost_samples_dfs.append(lost_samples_df.rename(testname))
        lost_samples_summary_stats = get_summary_stats(lost_samples_df, test)
        lost_samples_summaries.append(lost_samples_summary_stats)
        
        # cpu_log_df = get_cpu_log_df(test)

        # fig = px.timeline(cpu_log_df, x_start="start", x_end="end", y="vm", color="vm")
        
        # fig.update_layout(xaxis=dict(
        #     title="Log Timestamp",
        #     tickformat="%H:%M:%S"
        # ))
            
        # log_timeline = html.Div([
        #     html.H5(os.path.basename(test)),
        #     dcc.Graph(figure=fig)
        # ])
        # log_timelines.append(log_timeline)
    
    
    lat_summary_table = generate_summary_table(lat_summaries)
    lat_boxplot = get_plot("box", lat_dfs, "Test", "Latency (ms)") if lat_dfs else None
    lat_dotplot = get_plot("dot", lat_dfs, "Number of Observations", "Latency (ms)") if lat_dfs else None
    lat_lineplot = get_plot("line", lat_dfs, "Number of Observations", "Latency (ms)") if lat_dfs else None
    lat_histogram = get_plot("histogram", lat_dfs, "Latency (ms)", "Number of Observations") if lat_dfs else None
    lat_cdf = get_plot("cdf", lat_dfs, "Latency (ms)", "F(x)") if lat_dfs else None
    lat_transient = get_transient_analysis(lat_dfs , "Latency (ms)")

    tp_summary_table = generate_summary_table(tp_summaries)
    tp_boxplot = get_plot("box", tp_dfs, "Test", "Total Throughput (Mbps)") if tp_dfs else None
    tp_dotplot = get_plot("dot", tp_dfs, "Increasing Time In Seconds", "Total Throughput (Mbps)") if tp_dfs else None
    tp_lineplot = get_plot("line", tp_dfs, "Increasing Time In Seconds", "Total Throughput (Mbps)") if tp_dfs else None
    tp_histogram = get_plot("histogram", tp_dfs, "Total Throughput (Mbps)", "Number of Observations") if tp_dfs else None
    tp_cdf = get_plot("cdf", tp_dfs, "Total Throughput (Mbps)", "F(x)") if tp_dfs else None
    tp_transient = get_transient_analysis(tp_dfs, "Total Throughput (Mbps)")
    
    sample_rate_summary_table = generate_summary_table(sample_rate_summaries)
    sr_boxplot = get_plot("box", sr_dfs, "Test", "Sample Rate (samples/s)") if sr_dfs else None
    sr_dotplot = get_plot("dot", sr_dfs, "Increasing Time In Seconds", "Sample Rate (samples/s)") if sr_dfs else None
    sr_lineplot = get_plot("line", sr_dfs, "Increasing Time In Seconds", "Sample Rate (samples/s)") if sr_dfs else None
    sr_histogram = get_plot("histogram", sr_dfs, "Sample Rate (samples/s)", "Number of Observations") if sr_dfs else None
    sr_cdf = get_plot("cdf", sr_dfs, "Sample Rate (samples/s)", "F(x)") if sr_dfs else None
    sr_transient = get_transient_analysis(sr_dfs, "Sample Rates (samples/s)")
    
    # total_samples_received_summary_table = get_total_samples_received_summary_table(tests, testdir, total_samples_received_dfs, lost_samples_dfs)
    total_samples_received_summary_table = ""
    # total_samples_received_boxplot = get_plot("box", total_samples_received_dfs, "Test", "Total Samples Received") if total_samples_received_dfs else None
    total_samples_received_boxplot = ""
    total_samples_received_dotplot = get_plot("dot", total_samples_received_dfs, "Increasing Time In Seconds", "Total Samples Received") if total_samples_received_dfs else None
    total_samples_received_lineplot = get_plot("line", total_samples_received_dfs, "Increasing Time", "Total Samples Received") if total_samples_received_dfs else None
    total_samples_received_histogram = get_plot("histogram", total_samples_received_dfs, "Total Samples Received", "Number of Observations") if total_samples_received_dfs else None
    total_samples_received_cdf = get_plot("cdf", total_samples_received_dfs, "Total Samples Received", "F(x)") if total_samples_received_dfs else None
    total_samples_received_transient = None
    
    # lost_samples_summary_table = generate_summary_table(lost_samples_summaries)
    lost_samples_summary_table = ""
    # lost_samples_boxplot = get_plot("box", lost_samples_dfs, "Test", "Lost Samples") if lost_samples_dfs else None
    lost_samples_boxplot = ""
    lost_samples_dotplot = get_plot("dot", lost_samples_dfs, "Increasing Time In Seconds", "Lost Samples") if lost_samples_dfs else None
    lost_samples_lineplot = get_plot("line", lost_samples_dfs, "Increasing Time In Seconds", "Lost Samples") if lost_samples_dfs else None
    lost_samples_histogram = get_plot("histogram", lost_samples_dfs, "Lost Samples", "Number of Observations") if lost_samples_dfs else None
    lost_samples_cdf = get_plot("cdf", lost_samples_dfs, "Lost Samples", "F(x)") if lost_samples_dfs else None
    lost_samples_transient = None
    
    # log_timelines = html.Div(log_timelines)
        
    return lat_summary_table, lat_boxplot, lat_dotplot, lat_lineplot, lat_histogram, lat_cdf, lat_transient, tp_summary_table, tp_boxplot, tp_dotplot, tp_lineplot, tp_histogram, tp_cdf, tp_transient, sample_rate_summary_table, sr_boxplot, sr_dotplot, sr_lineplot, sr_histogram, sr_cdf, sr_transient, total_samples_received_summary_table, total_samples_received_boxplot, total_samples_received_dotplot, total_samples_received_lineplot, total_samples_received_histogram, total_samples_received_cdf, total_samples_received_transient, lost_samples_summary_table, lost_samples_boxplot, lost_samples_dotplot, lost_samples_lineplot, lost_samples_histogram, lost_samples_cdf, lost_samples_transient

if __name__ == "__main__": 
    app.run_server(debug=True, host="127.0.0.1", port="6745")