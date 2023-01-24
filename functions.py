import os
import dash_bootstrap_components as dbc
import pandas as pd

from pprint import pprint
from rich.console import Console
from dash import Dash, html, dcc, Output, Input

console = Console()

def get_summary_stats(type, df, test):
    if "latency" in type or "throughput" in type:
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

def get_tp_df(test):
    rundir = os.path.join(test, "run_1")
    csv_files = [file for file in os.listdir(rundir) if ".csv" in file]
    sub_files = [file for file in csv_files if "sub" in file]
    sub_files = [os.path.join(rundir, file) for file in sub_files]
        
    sub_dfs = []
    
    for file in sub_files:
        df = pd.read_csv(file, on_bad_lines="skip", skiprows=2, skipfooter=3, engine="python")
        sub_dfs.append(df)
        
    sub_df = pd.concat(sub_dfs, axis=0, ignore_index=True)
    
    tp_head = [x for x in sub_df.columns if "mbps" in x.lower()][0]
    
    tp_df = sub_df[tp_head]
    
    return tp_df

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