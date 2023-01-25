import os
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

from pprint import pprint
from rich.console import Console
from dash import Dash, html, dcc, Output, Input

console = Console()

def get_summary_stats(df, test):
    count = len(df.index)
    mean = df.mean()
    median = df.median()
    variance = df.var()
    std = df.std()
    skew = df.skew()
    df_range = df.max() - df.min()
    lower_quartile = df.quantile(.25)
    upper_quartile = df.quantile(.75)
    interquartile_range = upper_quartile - lower_quartile
    df_min = df.min()
    df_max = df.max()
    
    summary_stats =  {
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
        
        
    return summary_stats

def get_lat_df(test):
    rundir = os.path.join(test, "run_1")
        
    if not os.path.exists(rundir):
        return
    
    csv_files = [file for file in os.listdir(rundir) if ".csv" in file]
    
    if len(csv_files) == 0:
        return
    
    if "pub_0.csv" not in csv_files:
        return
    
    sub_files = [file for file in csv_files if "sub" in file]
    
    pubdir = os.path.join(rundir, "pub_0.csv")
    
    lat_df = pd.read_csv(pubdir, on_bad_lines="skip", skiprows=2, skipfooter=3, engine="python")
    
    try:
        lat_head = [col for col in lat_df.columns if "latency" in col.lower()][0]
        lat_df = lat_df[lat_head]
    except Exception as e:
        return
    
    return lat_df

def get_df_from_subs(metric_heading, test):
    rundir = os.path.join(test, "run_1")
    csv_files = [file for file in os.listdir(rundir) if ".csv" in file]
    sub_files = [file for file in csv_files if "sub" in file]
    sub_files = [os.path.join(rundir, file) for file in sub_files]
        
    sub_dfs = []
    
    for file in sub_files:
        df = pd.read_csv(file, on_bad_lines="skip", skiprows=2, skipfooter=3, engine="python")
        sub_dfs.append(df)
        
    sub_df = pd.concat(sub_dfs, axis=0, ignore_index=True)
    
    sub_head = [x for x in sub_df.columns if metric_heading in x.lower()][0]
    
    sub_df = sub_df[sub_head]
    
    return sub_df

def get_cpu_log_df(test):
    logdir = os.path.join(test, "run_1", "logs")
    logs = [os.path.join(logdir, file) for file in os.listdir(logdir)]
    cpu_logs = [file for file in logs if "_cpu.log" in file]
    
    cpu_logs_data = []
    
    for log in cpu_logs:
        cpu_log_data = {
            "start": "",
            "end": "",
            "vm": os.path.basename(log).replace("_cpu.log", "").replace("csr-dds-", "").replace("app", "vm")
        }
        
        log_df = pd.read_csv(log, skiprows=1, skipfooter=1, engine="python", on_bad_lines="skip", delim_whitespace=True)
        
        # ? Pick the first column
        time_df = log_df.iloc[:,0]
        
        cpu_log_data["start"] = "1970-01-01 " + str(time_df.min())
        cpu_log_data["end"] = "1970-01-01 " + str(time_df.max())
        
        cpu_logs_data.append(cpu_log_data)
        
    return pd.DataFrame(cpu_logs_data)

def generate_summary_table(summaries):
    return dbc.Table([
        html.Thead(
            html.Tr(
                [html.Th("Stat")] + [html.Th( os.path.basename(summary["test"]) ) for summary in summaries]
            )
        ),
        html.Tbody([
            html.Tr([html.Td("Count")] + [html.Td("{0:,.2f}".format(summary["count"])) for summary in summaries]),
            html.Tr([html.Td("mean")] + [html.Td("{0:,.2f}".format(summary["mean"])) for summary in summaries]),
            html.Tr([html.Td("median")] + [html.Td("{0:,.2f}".format(summary["median"])) for summary in summaries]),
            html.Tr([html.Td("variance")] + [html.Td("{0:,.2f}".format(summary["variance"])) for summary in summaries]),
            html.Tr([html.Td("std")] + [html.Td("{0:,.2f}".format(summary["std"])) for summary in summaries]),
            html.Tr([html.Td("skew")] + [html.Td("{0:,.2f}".format(summary["skew"])) for summary in summaries]),
            html.Tr([html.Td("range")] + [html.Td("{0:,.2f}".format(summary["range"])) for summary in summaries]),
            html.Tr([html.Td("lower_quartile")] + [html.Td("{0:,.2f}".format(summary["lower_quartile"])) for summary in summaries]),
            html.Tr([html.Td("upper_quartile")] + [html.Td("{0:,.2f}".format(summary["upper_quartile"])) for summary in summaries]),
            html.Tr([html.Td("interquartile_range")] + [html.Td("{0:,.2f}".format(summary["interquartile_range"])) for summary in summaries]),
            html.Tr([html.Td("min")] + [html.Td("{0:,.2f}".format(summary["min"])) for summary in summaries]),
            html.Tr([html.Td("max")] + [html.Td("{0:,.2f}".format(summary["max"])) for summary in summaries])
        ])
    ], bordered=True, hover=True)
    
def generate_toc_section(title, metric):
    output = [
        html.H5(title),
        html.A(
            dbc.ListGroupItem(title + " Summary Stats"),
            href="#" +metric+ "-summary-title"
        ),
        html.A(
            dbc.ListGroupItem(title + " Box Plots"),
            href="#" +metric+ "-boxplot-title"
        ),
        html.A(
            dbc.ListGroupItem(title + " Dot Plots"),
            href="#" +metric+ "-dotplot-title"
        ),
        html.A(
            dbc.ListGroupItem(title + " Line Plots"),
            href="#" +metric+ "-lineplot-title"
        ),
        html.A(
            dbc.ListGroupItem(title + " Histograms"),
            href="#" +metric+ "-histogram-title"
        ),
        html.A(
            dbc.ListGroupItem(title + " Empirical Cumulative Distribution Functions"),
            href="#" +metric+ "-cdf-title"
        ),
        html.A(
            dbc.ListGroupItem(title + " Transient Analyses"),
            href="#" +metric+ "-transient-title"
        )
    ]
    return output

def generate_toc():
    lists = []
    lists.append(generate_toc_section("Latency", "latency"))
    lists.append(generate_toc_section("Throughput", "throughput"))
    lists.append(generate_toc_section("Sample Rate", "sample-rate"))
    lists.append(generate_toc_section("Total Samples", "total-samples"))
    lists.append(generate_toc_section("Lost Samples", "lost-samples"))
    
    output = []
    for item in lists:
        output = output + item 
        
    output = output + [html.H5("Logs"), html.A(dbc.ListGroupItem("Log Timeline"), href="#log-timeline-title")]
        
    return output

def generate_metric_output_content(title, metric):
    return html.Div([
        html.H3(title + " Summary Stats", id=metric + "-summary-title"),
        html.Div(id=metric + "-summary-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
        
        html.H3(title + " Box Plots", id=metric + "-boxplot-title"),
        html.Div(id=metric + "-boxplot-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
        
        html.H3(title + " Line Plots", id=metric + "-lineplot-title"),
        html.Div(id=metric + "-lineplot-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
        
        html.H3(title + " Dot Plots", id=metric + "-dotplot-title"),
        html.Div(id=metric + "-dotplot-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
        
        html.H3(title + " Histograms", id=metric + "-histogram-title"),
        html.Div(id=metric + "-histogram-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
        
        html.H3(title + " Empirical Cumulative Distribution Functions", id=metric + "-cdf-title"),
        html.Div(id=metric + "-cdf-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
        
        html.H3(title + " Transient Analyses", id=metric + "-transient-title"),
        html.Div(id=metric + "-transient-output", style={"maxWidth": "100vw", "overflowX": "scroll"})
    ])
    
def get_plot(type, dfs, x_title, y_title):
    df = pd.concat(dfs, axis=1)

    if "box" in type:
        fig = px.box(df, log_y=True)
    elif "dot" in type:
        fig = px.scatter(df)
    elif "line" in type:
        fig = px.line(df)
    elif "histogram" in type:
        fig = px.histogram(df)
    elif "cdf" in type:
        fig = px.ecdf(df)

    fig.update_layout(xaxis_title=x_title, yaxis_title=y_title)
    
    return dcc.Graph(figure=fig)