import os
import pandas as pd

from dash import Dash, html, dcc, Output, Input

app = Dash(__name__)

app.layout = html.Div([
    dcc.Input(
        "C:/Users/acwh025/Documents/Software Dev/ML/data", 
        placeholder="Enter path to tests", 
        id="testdir-input"
    ),
    dcc.Dropdown([], multi=False, id="test-dropdown"),
    html.Div(id="latency-summary-output")
])

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
    Output("latency-summary-output", "children"),
    Input("test-dropdown", "value")
)
def populate_lat_summary(test):
    
    if test:
        if os.path.exists(os.path.join(test, "run_1")):
            csv_files = [file for file in os.listdir(os.path.join(test, "run_1")) if ".csv" in file]
        
            if len(csv_files) == 0:
                return f"{test} has no csv files."
        
            if "pub_0.csv" not in csv_files:
                raise Exception(f"{test} has no pub_0.csv file.")
            
            pub = os.path.join(test, "run_1", "pub_0.csv")
            
            lat_df = pd.read_csv(pub, on_bad_lines="skip", skiprows=2)
            
            lat_header = [col for col in lat_df.columns if "latency" in col.lower()][0]
            
            lat_df = lat_df[lat_header]
            
            return dcc.Markdown(lat_df.describe().to_frame().to_markdown())
        else:
            return f"run_1 folder not found for {test}."
    

if __name__ == "__main__": 
    app.run_server(debug=True, host="127.0.0.1", port="6745")