import os
import sys
import pandas as pd
import re
import dash_bootstrap_components as dbc
import plotly.express as px

from pprint import pprint
from functions import *
from dash import Dash, html, dcc, Output, Input, State

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
                    id="testdir-input",
                    style={"border-color": "#28a745"}
                ),
                dcc.Dropdown(
                    [], 
                    multi=True, 
                    id="test-dropdown", 
                    placeholder="Select one or more tests",
                    style={"marginTop": "1vh"}
                ),
                html.Div(
                    html.P("You can look for specific settings and plot it using the below:", style={"color": "grey", "margin-top": "1vh", "font-size": "8pt"})
                ),
                html.Div(id="setting-selection-container", style={"margin-top": "1vh"}),
                html.Div(
                    dbc.Button("Add Plot", color="primary", style={"width": "100%"}, id="setting-selector-button")
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
                html.Div(id="participant-allocation-container"),
                generate_metric_output_content("Latency", "latency"),
                generate_metric_output_content("Throughput", "throughput"),
                generate_metric_output_content("Sample Rate", "sample-rate"),
                generate_metric_output_content("Total Samples", "total-samples-received"),
                generate_metric_output_content("Lost Samples", "lost-samples")
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
        Output("alert-container", "children"),
        Output("setting-selection-container", "children")
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
    
    return test_summaries, comb_output, testpath, alert_output, generate_setting_selection(testpath)

@app.callback(
    Output("test-dropdown", "value"),
    [
        Input("setting-selector-button", "n_clicks"),    
        Input("test-dropdown", "value")    
    ],
    [
        State("testdir", "children"),
        State("setting-selection-container", "children")
    ]
)
def get_test_selection(n_clicks, tests, testdir, children):
    
    if n_clicks is None:
        return tests
    else:
        values = []
        
        children = children['props']['children']
        
        for child in children:
            if child['type'] == 'Col':
                dropdowns = child['props']['children']
                for dropdown in dropdowns:
                    if dropdown['type'] == 'Dropdown':
                        values.append(dropdown['props']['value'])
        
        test_selection = "_".join(values)
        
        if 'vary' in test_selection:
            regex_pattern = re.sub(r'vary', r'.*', test_selection)
            
            test_data = [_.replace("_summary.csv", "") for _ in os.listdir(testdir)]
            
            matched_tests = [test for test in test_data if re.match(regex_pattern, test)]
            
            if len(matched_tests) > 0:
                if tests:
                    tests.extend(matched_tests)
                else:
                    tests = matched_tests
            
            return tests
            
        else:
            # ? Check if test_selection exists
            test_selection_exists = len([_ for _ in os.listdir(testdir) if test_selection in _]) > 0
        
            if test_selection_exists:
                if tests:
                    tests.append(test_selection)
                else:
                    tests = [test_selection]
        
            return tests

@app.callback(
    [
        Output("participant-allocation-container", "children"),
        
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
        
        Output("total-samples-received-barchart-output", "children"),
        
        Output("lost-samples-barchart-output", "children"),
        
    ],
    [
        Input("test-dropdown", "value"),
        Input("testdir", "children")
    ]
)
def populate_summary(tests, testdir):

    if tests is None:
        return "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""
    
    lat_summaries = []
    tp_summaries = []
    sample_rate_summaries = []
    
    lat_dfs = []
    tp_dfs = []
    sr_dfs = []
    total_samples_received_dfs = []
    lost_samples_dfs = []
    participant_allocation_dfs = []
    
    for test in tests:
        summary_file = os.path.join(testdir, f"{test}_summary.csv")
        if not os.path.exists(summary_file):
            console.print(f"Summmary file doesn't exist for {test}.", style="bold red")
            continue
        
        # ! Limit file reading to 10,000 rows or Dash will break
        summary_df = pd.read_csv(summary_file, nrows=10000)
        
        testname = test
        test = os.path.join(testdir, test)
        
        participant_allocation_dfs.append({
            testname: get_participant_allocation_df(summary_df)
        })
        
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
        
        total_samples_received_df = get_total_samples_received_per_sub(summary_df)
        total_samples_received_dfs.append(total_samples_received_df.rename(testname))
        
        lost_samples_df = get_lost_samples_received_per_sub(summary_df)
        lost_samples_dfs.append(lost_samples_df.rename(testname))

    participant_allocation_output = get_participant_allocation_output(participant_allocation_dfs)

    lat_summary_table = generate_summary_table(lat_summaries)
    lat_boxplot = get_plot("box", lat_dfs, "Test", "Latency (ms)") if lat_dfs is not None else None
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
    
    total_samples_received_barchart = get_plot("bar", total_samples_received_dfs, "sub_n", "# of samples")
    
    lost_samples_received_barchart = get_plot("bar", lost_samples_dfs, "sub_n", "# of samples")
        
    return participant_allocation_output, lat_summary_table, lat_boxplot, lat_dotplot, lat_lineplot, lat_histogram, lat_cdf, lat_transient, tp_summary_table, tp_boxplot, tp_dotplot, tp_lineplot, tp_histogram, tp_cdf, tp_transient, sample_rate_summary_table, sr_boxplot, sr_dotplot, sr_lineplot, sr_histogram, sr_cdf, sr_transient, total_samples_received_barchart, lost_samples_received_barchart

if __name__ == "__main__": 
    app.run_server(debug=True, host="127.0.0.1", port="6745")