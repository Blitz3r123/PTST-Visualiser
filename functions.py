import os
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from pprint import pprint
from plotly.subplots import make_subplots
from rich.console import Console
from statistics import NormalDist
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
    
    lat_df = lat_df.loc[:].div(1000)
    
    return lat_df

def get_df_from_subs(metric_heading, test):
    if "total samples received" in metric_heading:
        metric_heading = "total samples"
    rundir = os.path.join(test, "run_1")
    csv_files = [file for file in os.listdir(rundir) if ".csv" in file]
    sub_files = [file for file in csv_files if "sub" in file]
    sub_files = [os.path.join(rundir, file) for file in sub_files]
        
    sub_dfs = []
    
    for file in sub_files:
        df = pd.read_csv(file, on_bad_lines="skip", skiprows=2, skipfooter=3, engine="python")
        sub_head = [x for x in df.columns if metric_heading in x.lower()][0]
        df = df[sub_head]
        df.rename(os.path.basename(file).replace(".csv", ""), inplace=True)
        sub_dfs.append(df)
        
    sub_df = pd.concat(sub_dfs, axis=1)
    
    # ? Add up all columns to create total column
    sub_df["total_" + metric_heading] = sub_df[list(sub_df.columns)].sum(axis=1)
    
    # ? Take off the last number because its an average produced by perftest
    sub_df = sub_df[:-2]
    return sub_df["total_" + metric_heading][:-1]

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
    if "lost-samples" in metric:
        summary_link = ""
    else:
        summary_link = dbc.ListGroupItem(
            title + " Summary Stats",
            href="#" +metric+ "-summary-title",
            external_link=True,
            style={"marginTop": "0.5vh"},   
        )

    if "total-samples-received" in metric:
        boxplot_link = ""
    elif "lost-samples" in metric:
        boxplot_link = ""
    else:
        boxplot_link = dbc.ListGroupItem(
            title + " Box Plots",
            href="#" +metric+ "-boxplot-title",
            external_link=True,
            style={"marginTop": "0.5vh"}
        )
    
    dotplot_link = dbc.ListGroupItem(
        title + " Dot Plots",
        href="#" +metric+ "-dotplot-title",
        external_link=True,
        style={"marginTop": "0.5vh"},
    )
    
    lineplot_link = dbc.ListGroupItem(
        title + " Line Plots",
        href="#" +metric+ "-lineplot-title",
        external_link=True,
        style={"marginTop": "0.5vh"}
    )
    
    histogram_link = dbc.ListGroupItem(
        title + " Histograms",
        href="#" +metric+ "-histogram-title",
        external_link=True,
        style={"marginTop": "0.5vh"}
    )
    
    cdf_link = dbc.ListGroupItem(
        title + " Empirical Cumulative Distribution Functions",
        href="#" +metric+ "-cdf-title",
        external_link=True,
        style={"marginTop": "0.5vh"}
    )
    
    if "total-samples-received" in metric:
        transient_link = ""
    elif "lost-samples" in metric:
        transient_link = ""
    else:
        transient_link = dbc.ListGroupItem(
            title + " Transient Analyses",
            href="#" +metric+ "-transient-title",
            external_link=True,
            style={"marginTop": "0.5vh"}
        )
    
    output = [
        html.H5(title, style={"marginTop": "1vh"}),
        summary_link,
        boxplot_link,
        dotplot_link,
        lineplot_link,
        histogram_link,
        cdf_link,
        transient_link
    ]
    return output

def generate_toc():
    lists = []
    lists.append(generate_toc_section("Latency", "latency"))
    lists.append(generate_toc_section("Throughput", "throughput"))
    lists.append(generate_toc_section("Sample Rate", "sample-rate"))
    lists.append(generate_toc_section("Total Samples Received", "total-samples-received"))
    lists.append(generate_toc_section("Lost Samples", "lost-samples"))
    
    output = []
    for item in lists:
        output = output + item 
        
    output = output + [html.H5("Logs"), html.A(dbc.ListGroupItem("Log Timeline"), href="#log-timeline-title", style={"paddingBottom": "3vh"})]
        
    return output

def generate_metric_output_content(title, metric):
    if "lost-samples" in metric:
        summary_output = html.Div(id=metric + "-summary-output", style={"maxWidth": "100vw", "overflowX": "scroll"})
    else:
        summary_output = html.Div([
            html.H3(title + " Summary Stats", id=metric + "-summary-title"),
            html.Div(id=metric + "-summary-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
        ])
    
    if "total-samples-received" in metric:
        boxplot_output = html.Div(id=metric + "-boxplot-output", style={"maxWidth": "100vw", "overflowX": "scroll"})
    elif "lost-samples" in metric:
        boxplot_output = html.Div(id=metric + "-boxplot-output", style={"maxWidth": "100vw", "overflowX": "scroll"})
    else:
        boxplot_output = html.Div([
            html.H3(title + " Box Plots", id=metric + "-boxplot-title"),
            html.Div(id=metric + "-boxplot-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
        ])
    
    lineplot_output = html.Div([
        html.H3(title + " Line Plots", id=metric + "-lineplot-title"),
        html.Div(id=metric + "-lineplot-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
    ])
    
    dotplot_output = html.Div([
        html.H3(title + " Dot Plots", id=metric + "-dotplot-title"),
        html.Div(id=metric + "-dotplot-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
    ])
    
    histogram_output = html.Div([
        html.H3(title + " Histograms", id=metric + "-histogram-title"),
        html.Div(id=metric + "-histogram-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
    ])
    
    cdf_output = html.Div([
        html.H3(title + " Empirical Cumulative Distribution Functions", id=metric + "-cdf-title"),
        html.Div(id=metric + "-cdf-output", style={"maxWidth": "100vw", "overflowX": "scroll"}),
    ])
    
    if "total-samples-received" in metric:
        transient_output = html.Div(id=metric + "-transient-output", style={"maxWidth": "100vw", "overflowX": "scroll"})
    elif "lost-samples" in metric:
        transient_output = html.Div(id=metric + "-transient-output", style={"maxWidth": "100vw", "overflowX": "scroll"})
    else:
        transient_output = html.Div([
            html.H3(title + " Transient Analyses", id=metric + "-transient-title"),
            html.Div(id=metric + "-transient-output", style={"maxWidth": "100vw", "overflowX": "scroll"})
        ])
    
    return html.Div([
        summary_output,
        boxplot_output,
        lineplot_output,
        dotplot_output,
        histogram_output,
        cdf_output,
        transient_output
    ])
    
def confidence_interval(data, confidence=0.95):
  dist = NormalDist.from_samples(data)
  z = NormalDist().inv_cdf((1 + confidence) / 2.)
  h = dist.stdev * z / ((len(data) - 1) ** .5)
  return h
    
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

def get_transient_analysis(dfs, metric):
    figs = []
    
    for df in dfs:
        fig = make_subplots(
            rows=2, 
            cols=6, 
            specs=[
                [{"colspan": 4, "rowspan": 2}, None, None, None, None, {}],
                [None, None, None, None, None, {}]
            ],
            start_cell="top-left",
            horizontal_spacing=0,
            subplot_titles=("Line Plot", "Histograms", "CDFs")
        )
        
        fig.add_trace(
            go.Scatter(y=df, x=df.index),
            row=1, col=1
        )
        fig.add_vline(x=len(df.index) / 2, row=1, col=1, line_dash="dash", line_width=3)
        # ? Big "A"
        fig.add_annotation(
            x=len(df.index) * .25, 
            y=df.max() * .5, 
            text="A", 
            row=1, col=1, 
            showarrow=False
        )
        # ? Big "B"
        fig.add_annotation(
            x=len(df.index) * .75, 
            y=df.max() * .5, 
            text="B", 
            row=1, col=1, 
            showarrow=False
        )
        fig.update_annotations(font_size=40, selector={"text": "A"})
        fig.update_annotations(font_size=40, selector={"text": "B"})
        fig['layout']['xaxis'].update(title_text="Number of Observations")
        fig['layout']['yaxis'].update(title_text=metric)
        
        mid_point = int(len(df.index) *.5)
        
        df_a = df.iloc[:mid_point].rename("A").reset_index(drop=True)
        df_b = df.iloc[mid_point:].rename("B").reset_index(drop=True)
        
        combined_df = pd.concat([df_a, df_b], axis=1).reset_index().iloc[:, 1:]
                
        fig.add_trace(
            go.Histogram(x=df_a, name="A"),
            row=1, col=6
        ),
        fig.add_trace(
            go.Histogram(x=df_b, name="B"),
            row=1, col=6
        )
        fig['layout']['xaxis2'].update(title_text=metric)
        fig['layout']['yaxis2'].update(title_text="Number of Observations")
        
        fig.add_traces(
            [
                px.ecdf(combined_df).data[0],
                px.ecdf(combined_df).data[1]
            ],
            rows=[2, 2], cols=[6, 6]
        )
        fig['layout']['xaxis3'].update(title_text=metric)
        fig['layout']['yaxis3'].update(title_text="F(x)")
        
        fig.update_layout(
            title=df.name
        )
        
        figs.append(fig)
    
    return html.Div([dcc.Graph(figure=fig, style={"width": "100%", "height": "100%"}) for fig in figs], style={"maxWidth": "100vw", "overflowX" : "scroll", "height": "100vh"})

def get_comb_output(tests):
    durations = []
    datalens = []
    pubs = []
    subs = []
    reliabilities = []
    unicasts = []
    durabilities = []
    lat_counts = []
    
    for test in tests:
        test = os.path.basename(test)
        
        test = test.split("_")
        durations.append(test[0])
        datalens.append(test[1])
        pubs.append(test[2])
        subs.append(test[3])
        reliabilities.append(test[4])
        unicasts.append(test[5])
        durabilities.append(test[6])
        lat_counts.append(test[7])

    durations = list(set(durations))
    datalens = list(set(datalens))
    pubs = list(set(pubs))
    subs = list(set(subs))
    reliabilities = list(set(reliabilities))
    unicasts = list(set(unicasts))
    durabilities = list(set(durabilities))
    lat_counts = list(set(lat_counts))

    table_header = [
        html.Thead(html.Tr([
            html.Th("Variable"),
            html.Th("Values"),
            html.Th("# of Values")
        ]))
    ]
    
    durations = html.Tr(
        [html.Td("Durations")] + 
        [ html.Td(", ".join(durations)) ] + 
        [ html.Td( str(len(durations)) ) ]
    )
    datalens = html.Tr(
        [html.Td("Data Lengths")] + 
        [ html.Td(", ".join(datalens)) ] + 
        [ html.Td( str(len(datalens)) ) ]
    )
    pubs = html.Tr(
        [html.Td("Publishers")] + 
        [ html.Td(", ".join(pubs)) ] + 
        [ html.Td( str(len(pubs)) ) ]
    )
    subs = html.Tr(
        [html.Td("Subscribers")] + 
        [ html.Td(", ".join(subs)) ] + 
        [ html.Td( str(len(subs)) ) ]
    )
    reliabilities = html.Tr(
        [html.Td("Reliabilities")] + 
        [ html.Td(", ".join(reliabilities)) ] + 
        [ html.Td( str(len(reliabilities)) ) ]
    )
    unicasts = html.Tr(
        [html.Td("Communication Patterns")] + 
        [ html.Td(", ".join(unicasts)) ] + 
        [ html.Td( str(len(unicasts)) ) ]
    )
    durabilities = html.Tr(
        [html.Td("Durabilities")] + 
        [ html.Td(", ".join(durabilities)) ] + 
        [ html.Td( str(len(durabilities)) ) ]
    )
    lat_counts = html.Tr(
        [html.Td("Latency Counts")] + 
        [ html.Td(", ".join(lat_counts)) ] + 
        [ html.Td( str(len(lat_counts)) ) ]
    )
    
    total_combs = len(durations) * len(datalens) * len(pubs) * len(subs) * len(reliabilities) * len(durabilities) * len(lat_counts)
    total_combs = "{:,.0f}".format(total_combs)
    
    total_row = html.Tr([html.Td("Multiplied Total"), html.Td(""), html.Td(total_combs)])
    
    table_body = [
        html.Tbody([durations, datalens, pubs, subs, reliabilities, unicasts, durabilities, lat_counts, total_row])
    ]
    
    return html.Div([
        html.H3("Captured Settings", style={"marginTop": "2vh"}),
        dbc.Table(table_header + table_body, bordered=True)
    ])
    
def get_total_samples_per_sub(test):
    rundir = os.path.join("./", test, "run_1")
    sub_csvs = [os.path.join(rundir, file) for file in os.listdir(rundir) if "sub" in file and ".csv" in file]
    
    test_df = pd.DataFrame(columns=["sub", "total_samples"])
    
    for sub_csv in sub_csvs:
        df = pd.read_csv(sub_csv, on_bad_lines="skip", skiprows=2, skipfooter=3, engine="python")
        total_samples_col = [col for col in df.columns if "total" in col.lower()]
        total_samples_df = df[total_samples_col]
        
        sub_name = os.path.basename(sub_csv).replace(".csv", "")
        total_samples = int(total_samples_df.max())
        
        sub_df = pd.DataFrame([[sub_name, total_samples]], columns=test_df.columns)
        
        test_df = pd.concat([test_df, sub_df], ignore_index=True)
    
    return test_df
    
    
def get_total_samples_received_summary_table(tests, testdir, total_dfs, lost_dfs):
    """
    For each test:
    1. Get the df containing the total samples per sub
        How?
            - For each sub get the max total samples value
            - Concat vertically with 2 columns: sub, total samples
                - So it looks like:
                    sub_0   12045
                    sub_1   231432
                    sub_2   45545
                    ...
                    sub_n   124234
    2. Plot the bar chart of it
    """
        
    barchart_output = ""
    summary_table_output = ""
    
    if len(tests) == 0:
        return ""
        
    bar_data = []
        
    for test in tests:
        testpath = os.path.join(testdir, test)
        total_samples_df = get_total_samples_per_sub(testpath)
        
        bar_data.append(
            go.Bar(x=total_samples_df["sub"], y=total_samples_df["total_samples"], name=test)
        )
        
    fig = go.Figure(data=bar_data)
    fig.update_layout(barmode="group", title="Total Samples Per Subscriber")
        
    barchart_output = dcc.Graph(figure=fig)
        
    if len(total_dfs) == 0:
        return ""
    
    test_names = [df.name for df in total_dfs]
    
    total_df = pd.concat(total_dfs, axis=1)
    lost_df = pd.concat(lost_dfs, axis=1)
    
    table_header = [
        html.Thead(html.Tr([
            html.Th("Test"),
            html.Th("Total Samples Received"),
            html.Th("Lost Samples"),
            html.Th("Total Samples"),
            html.Th("Lost Samples (%)")
        ]))
    ]
    
    rows = []
    
    for test in test_names:
        total_samples_received = total_df[test].max()
        lost_samples = lost_df[test].max()
        total_samples = lost_samples + total_samples_received
        lost_sample_percent = (lost_samples / total_samples) * 100
        
        
        rows.append(html.Tr([
            html.Td(test),
            html.Td("{:,.0f}".format(total_samples_received)),
            html.Td("{:,.0f}".format(lost_samples)),
            html.Td("{:,.0f}".format(total_samples)),
            html.Td("{:,.0f}".format(lost_sample_percent)),
        ]))
        
    table_body = [html.Tbody(rows)]
    
    summary_table_output = dbc.Table(table_header + table_body, bordered=True)
    
    return html.Div([ summary_table_output, barchart_output ])