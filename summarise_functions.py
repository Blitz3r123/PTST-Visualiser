import os
import sys
import re
import shutil
import pandas as pd

from pprint import pprint
from rich.console import Console
from rich.progress import track

console = Console()

def get_latencies(pubfile):
    try:
        df = pd.read_csv(pubfile, on_bad_lines="skip", skiprows=2, skipfooter=5, engine="python")
    except Exception as e:
        console.print(f"Error looking at {pubfile}:", style="bold red")
        console.print(e, style="bold red")
        return
    
    try:
        lat_header = [_ for _ in df.columns if "latency" in _.lower()][0]
        df = df[lat_header]
    except Exception as e:
        print(e)
        return

    return df

def get_metric_per_sub(sub_file, metric):
    df = pd.read_csv(sub_file, on_bad_lines='skip', skiprows=2, skipfooter=3, engine='python')
    sub_head = [x for x in df.columns if metric in x.lower()][0]
    df = df[sub_head]
    df.rename(os.path.basename(sub_file).replace(".csv", ""), inplace=True)
    # ? Take off the last number because its an average produced by perftest
    df = df[:-2]
    
    return df

def get_total_sub_metric(sub_files, metric):
    sub_dfs = []
    
    for file in sub_files:
        df = pd.read_csv(file, on_bad_lines="skip", skiprows=2, skipfooter=3, engine="python")
        sub_head = [x for x in df.columns if metric in x.lower()][0]
        df = df[sub_head]
        df.rename(os.path.basename(file).replace(".csv", ""), inplace=True)
        sub_dfs.append(df)
        
    sub_df = pd.concat(sub_dfs, axis=1)
    
    # ? Add up all columns to create total column
    sub_df["total_" + metric] = sub_df[list(sub_df.columns)].sum(axis=1)
    
    # ? Take off the last number because its an average produced by perftest
    sub_df = sub_df[:-2]
    
    return sub_df["total_" + metric][:-1]

def test_summary_exists(test, summarydir):
    testname = os.path.basename(test)
    summary_path = os.path.join(summarydir, f"{testname}_summary.csv")
    return os.path.exists(summary_path)