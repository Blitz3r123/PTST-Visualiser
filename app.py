import os
import pandas as pd
import dash_bootstrap_components as dbc

from pprint import pprint
from dash import Dash, html, dcc, Output, Input

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Input(
        value="C:/Users/acwh025/Documents/Software Dev/ML/data", 
        placeholder="Enter path to tests", 
        id="testdir-input"
    ),
    dcc.Dropdown([], multi=True, id="test-dropdown", placeholder="Select one or more tests"),
    html.Div(id="latency-summary-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
    html.Div(id="throughput-summary-output")
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
        Output("throughput-summary-output", "children")
    ],
    Input("test-dropdown", "value")
)
def populate_summary(tests):
    
    if tests is None:
        return "", ""
    
    lat_summaries = []
    stat_headers = []
    for test in tests:
        rundir = os.path.join(test, "run_1")
        
        if not os.path.exists(rundir):
            return "", ""
        
        csv_files = [file for file in os.listdir(rundir) if ".csv" in file]
        
        if len(csv_files) == 0:
            return "", ""
        
        if "pub_0.csv" not in csv_files:
            return "", ""
        
        pubdir = os.path.join(rundir, "pub_0.csv")
        
        lat_df = pd.read_csv(pubdir, on_bad_lines="skip", skiprows=2, skipfooter=3)
        
        try:
            lat_head = [col for col in lat_df.columns if "latency" in col.lower()][0]
            lat_df = lat_df[lat_head]
        except Exception as e:
            return "", ""
        
        count = len(lat_df.index)
        mean = lat_df.mean()
        median = lat_df.median()
        variance = lat_df.var()
        std = lat_df.std()
        skew = lat_df.skew()
        df_range = lat_df.max() - lat_df.min()
        lower_quartile = lat_df.quantile(.25)
        upper_quartile = lat_df.quantile(.75)
        interquartile_range = upper_quartile - lower_quartile
        df_min = lat_df.min()
        df_max = lat_df.max()
        
        lat_summary_stats =  {
            "test": test, 
            "count": count, 
            "mean": mean, 
            "median": median, 
            "variance": variance, 
            "std": std, 
            "skew": skew, 
            "range": df_range, 
            "lower_quartile": lower_quartile, 
            "upper_quartile": upper_quartile, 
            "interquartile_range": interquartile_range, 
            "min": df_min,
            "max": df_max
        }
        
        lat_summaries.append(lat_summary_stats)
        
        for key, value in lat_summary_stats.items():
            stat_headers.append(key)
        
    lat_summary_table = dbc.Table([
        html.Thead(
            html.Tr(
                [html.Th("Stat")] + [html.Th( os.path.basename(lat_summary["test"]) ) for lat_summary in lat_summaries]
            )
        ),
        html.Tbody([
            html.Tr(
                [html.Td("Count")] + [html.Td(summary["count"]) for summary in lat_summaries]
            ),
            html.Tr(
                [html.Td("mean")] + [html.Td(summary["mean"]) for summary in lat_summaries]
            ),
            html.Tr(
                [html.Td("median")] + [html.Td(summary["median"]) for summary in lat_summaries]
            ),
            html.Tr(
                [html.Td("variance")] + [html.Td(summary["variance"]) for summary in lat_summaries]
            ),
            html.Tr(
                [html.Td("std")] + [html.Td(summary["std"]) for summary in lat_summaries]
            ),
            html.Tr(
                [html.Td("skew")] + [html.Td(summary["skew"]) for summary in lat_summaries]
            ),
            html.Tr(
                [html.Td("range")] + [html.Td(summary["range"]) for summary in lat_summaries]
            ),
            html.Tr(
                [html.Td("lower_quartile")] + [html.Td(summary["lower_quartile"]) for summary in lat_summaries]
            ),
            html.Tr(
                [html.Td("upper_quartile")] + [html.Td(summary["upper_quartile"]) for summary in lat_summaries]
            ),
            html.Tr(
                [html.Td("interquartile_range")] + [html.Td(summary["interquartile_range"]) for summary in lat_summaries]
            ),
            html.Tr(
                [html.Td("min")] + [html.Td(summary["min"]) for summary in lat_summaries]
            ),
            html.Tr(
                [html.Td("max")] + [html.Td(summary["max"]) for summary in lat_summaries]
            )
        ])
    ], bordered=True)
    
    return lat_summary_table, ""
    
    # if test:
    #     if os.path.exists(os.path.join(test, "run_1")):
    #         csv_files = [file for file in os.listdir(os.path.join(test, "run_1")) if ".csv" in file]
        
    #         if len(csv_files) == 0:
    #             lat_summary = f"{test} has no csv files."
    #             tp_summary = f"{test} has no csv files."
        
    #         if "pub_0.csv" not in csv_files:
    #             raise Exception(f"{test} has no pub_0.csv file.")
            
    #         pub = os.path.join(test, "run_1", "pub_0.csv")
            
    #         lat_df = pd.read_csv(pub, on_bad_lines="skip", skiprows=2)
            
    #         lat_header = [col for col in lat_df.columns if "latency" in col.lower()][0]
            
    #         lat_df = lat_df[lat_header]
            
    #         lat_summary = dcc.Markdown(lat_df.describe().to_frame().to_markdown())
            
    #         sub_files = [file for file in csv_files if "sub" in file]
            
    #         if len(sub_files) == 0:
    #             tp_summary = f"No sub csv files found for {test}."
    #         else:
    #             tp_children = []
    #             for file in sub_files:
    #                 file = os.path.join(test, "run_1", file)
    #                 df = pd.read_csv(file, on_bad_lines="skip", skiprows=2, skipfooter=3)
    #                 tp_header = [col for col in df.columns if "mbps" in col.lower()][0]
                    
    #                 tp_df = df[tp_header].to_frame()
                    
    #                 for col in tp_df.columns:
    #                     tp_df[col] = tp_df[col].astype(float)
                    
    #                 tp_df = tp_df.rename(columns={ tp_header: os.path.basename(file) })
                    
    #                 tp_children.append(html.Td(dcc.Markdown(tp_df.describe().to_markdown())))
                    
    #             tp_summary = dbc.Table(html.Tr(tp_children), bordered=True, hover=True)
            
    #     else:
    #         lat_summary, tp_summary = f"run_1 folder not found for {test}."

if __name__ == "__main__": 
    app.run_server(debug=True, host="127.0.0.1", port="6745")