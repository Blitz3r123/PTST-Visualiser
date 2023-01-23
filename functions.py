import os
import pandas as pd

from pprint import pprint
from rich.console import Console

console = Console()

def get_latency_summary(test):
    csv_files = [file for file in os.listdir(os.path.join(test, "run_1")) if ".csv" in file]
    
    if "pub_0.csv" not in csv_files:
        raise Exception(f"{test} has no pub_0.csv file.")
    
    pub = os.path.join(test, "run_1", "pub_0.csv")
    
    lat_df = pd.read_csv(pub, on_bad_lines="skip", skiprows=2)
    
    lat_header = [col for col in lat_df.columns if "latency" in col.lower()][0]
    
    lat_df = lat_df[lat_header]
    
    count = len(lat_df.index)
    mean = lat_df.mean()
    median = lat_df.median()
    variance = lat_df.var()
    std = lat_df.std()
    # cov = lat_df.cov()
    skew = lat_df.skew()
    df_range = lat_df.max() - lat_df.min()
    lower_quartile = lat_df.quantile(.25)
    upper_quartile = lat_df.quantile(.75)
    interquartile_range = upper_quartile - lower_quartile
    df_min = lat_df.min()
    df_max = lat_df.max()
    
    return [
        {"count": count},
        {"mean": mean},
        {"median": median},
        {"variance": variance},
        {"std": std},
        # {"cov": cov},
        {"skew": skew},
        {"range": df_range},
        {"lower_quartile": lower_quartile},
        {"upper_quartile": upper_quartile},
        {"interquartile_range": interquartile_range},
        {"min": df_min},
        {"max": df_max}
    ]