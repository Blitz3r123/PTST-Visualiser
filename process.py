import json
import os
import pandas as pd
import shutil
import sys

from pprint import pprint
from rich.console import Console
from rich.progress import track

console = Console()

args = sys.argv[1:]

if len(args) < 3:
    console.print(f"Expected at least 3 args but found {len(args)}. Refer to the readme for help.", style="bold red")
    sys.exit()

raw_dir = args[0]
usable_dir = args[1]
summaries_dir = args[2]

console.print(f"Working on {os.path.basename(raw_dir)}...\n\n", style="bold white")

if not os.path.exists(raw_dir):
    console.print(f"The path {raw_dir} doesn't exist.", style="bold red")
    sys.exit()

if "debug" in args:
    try:
        shutil.rmtree(usable_dir)
        shutil.rmtree(summaries_dir)
    except FileNotFoundError as e:
        None

def get_expected_csv_count_from_testname(testname):
    split = testname.split("_")
    sub_split = [_ for _ in split if "S" in _]
    sub_value = sub_split[0].replace("S", "")
    sub_value = int(sub_value)
    
    return sub_value + 1

assert(get_expected_csv_count_from_testname("600s_32000B_25P_1S_rel_uc_1dur_100lc") == 2)
assert(get_expected_csv_count_from_testname("600s_32000B_25P_25S_rel_uc_1dur_100lc") == 26)

def get_actual_csv_count(testdir):
    csv_files = [_ for _ in os.listdir(testdir) if '.csv' in _]
    
    return len(csv_files)

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
        try:
            df = pd.read_csv(file, on_bad_lines="skip", skiprows=2, skipfooter=3, engine="python")
        except Exception as e:
            console.print(f"Error when getting data from {file}:", style="bold red")
            console.print(f"\t{e}", style="bold red")
            continue
        sub_head = [x for x in df.columns if metric in x.lower()][0]
        df = df[sub_head]
        df.rename(os.path.basename(file).replace(".csv", ""), inplace=True)
        sub_dfs.append(df)
        
    if sub_dfs:
        sub_df = pd.concat(sub_dfs, axis=1)
    
        # ? Add up all columns to create total column
        sub_df["total_" + metric] = sub_df[list(sub_df.columns)].sum(axis=1)
        
        # ? Take off the last number because its an average produced by perftest
        sub_df = sub_df[:-2]
        
        return sub_df["total_" + metric][:-1]
    else:
        console.print(f"Couldn't get any data from {sub_files}.", style="bold red")

def test_summary_exists(test, summaries_dir):
    testname = os.path.basename(test)
    summary_path = os.path.join(summaries_dir, f"{testname}_summary.csv")
    return os.path.exists(summary_path)

def get_participant_allocation_per_machine(type, test):
    config = os.path.join(test, 'config.json')
    
    if not os.path.exists(config):
        return []
    
    with open(config, 'r') as f:
        config = json.load(f)
        
    machines = config['machines']
    
    allocation_list = []
    
    for machine in machines:
        scripts = machine['scripts']
        allocation_list.append(scripts.count(f"-{type}"))
        
    return allocation_list

"""
1. Find usable tests.
2. Copy usable tests over to usable_dir.
3. Summarise tests in usable_dir.
"""

report = []

# ? 1. Find usable tests.
test_dirs = [f.path for f in os.scandir(raw_dir) if f.is_dir()]

usable_test_dirs = []

for test_dir in test_dirs:
    expected_csv_count = get_expected_csv_count_from_testname(os.path.basename(test_dir))
    actual_csv_count = get_actual_csv_count(test_dir)
    
    if expected_csv_count == actual_csv_count:
        usable_test_dirs.append(test_dir)
    else:
        report.append({
            "test": os.path.basename(test_dir),
            "issue": f"Expected {expected_csv_count} csv files and found {actual_csv_count} instead."
        })

usable_percentage = int(len(usable_test_dirs) / len(test_dirs) * 100)

# ? 2. Copy usable tests over to usable_dir.
for i in track(range(len(usable_test_dirs)), description=f"Copying over {len(usable_test_dirs)} usable tests out of {len(test_dirs)} ({usable_percentage}%) total tests...\n"):
    usable_test_dir = usable_test_dirs[i]
    src = usable_test_dir
    dest = os.path.join(usable_dir, os.path.basename(usable_test_dir))
    
    try:
        if not os.path.exists(dest):
            os.makedirs(dest)
            shutil.copytree(src, dest, dirs_exist_ok=True)
    except FileExistsError as e:
        continue

# ? 3. Summarise tests in usable_dir.
if not os.path.exists(summaries_dir):
    os.makedirs(summaries_dir)

usable_tests = [f.path for f in os.scandir(usable_dir) if f.is_dir()]

for i in track( range( len(usable_tests) ), description="Summarising tests...", update_period=1 ):
    test = usable_tests[i]
    
    if test_summary_exists(test, summaries_dir):
        continue
    
    log_dir = os.path.join(test, "logs")
    
    log_files = os.listdir(log_dir)
    logs = [os.path.join(log_dir, file) for file in log_files if '_cpu.log' in file or '_mem.log' in file or '_dev.log' in file or '_edev.log' in file]
    logs = sorted(logs)
    
    """
    CPU:
    - %user
    - %system
    - %iowait
    - %idle
    RAM:
    - kbmemfree
    - kbmemused
    - %memused
    Network:
    - DEV
        - rxpck/s
        - txpck/s
        - rxkB/s
        - txkB/s
        - rxmcst/s
    - EDEV
        - rxerr/s
        - txerr/s
        - coll/s
    """
    
    log_cols = []
    
    for log in logs:
        df = pd.read_csv(log, skiprows=1, delim_whitespace=True)
        
        log_name = os.path.basename(log).replace(".log", "")
        
        if "_cpu" in log:
            user_df = pd.Series(df['%user']).rename(f"{log_name}_user").dropna()
            system_df = pd.Series(df['%system']).rename(f"{log_name}_system").dropna()
            iowait_df = pd.Series(df['%iowait']).rename(f"{log_name}_iowait").dropna()
            idle_df = pd.Series(df['%idle']).rename(f"{log_name}_idle").dropna()
            
            log_cols.append(user_df)
            log_cols.append(system_df)
            log_cols.append(iowait_df)
            log_cols.append(idle_df)
        
        elif "_mem" in log:
            kbmemfree_df = pd.Series(df['kbmemfree']).rename(f"{log_name}_mem_kbmemfree").dropna()
            kbmemused_df = pd.Series(df['kbmemused']).rename(f"{log_name}_mem_kbmemused").dropna()
            percent_mem_used_df = pd.Series(df['%memused']).rename(f"{log_name}_mem_percentmemused").dropna()

            log_cols.append(kbmemfree_df)         
            log_cols.append(kbmemused_df)
            log_cols.append(percent_mem_used_df)
    
        elif "_dev" in log:
            rxpck_df = pd.Series(df['rxpck/s']).rename(f"{log_name}_rxpck").dropna()
            txpck_df = pd.Series(df['txpck/s']).rename(f"{log_name}_txpck").dropna()
            rxkB_df = pd.Series(df['rxkB/s']).rename(f"{log_name}_rxkB").dropna()
            txkB_df = pd.Series(df['txkB/s']).rename(f"{log_name}_txkB").dropna()
            rxmcst_df = pd.Series(df['rxmcst/s']).rename(f"{log_name}_rxmcst").dropna()
            
            log_cols.append(rxpck_df)
            log_cols.append(txpck_df)
            log_cols.append(rxkB_df)
            log_cols.append(txkB_df)
            log_cols.append(rxmcst_df)
            
        elif "_edev" in log:
            rxerr_df = pd.Series(df['rxerr/s']).rename(f"{log_name}_rxerr").dropna()
            txerr_df = pd.Series(df['txerr/s']).rename(f"{log_name}_txerr").dropna()
            coll_df = pd.Series(df['coll/s']).rename(f"{log_name}_coll").dropna()
            
            log_cols.append(rxerr_df)
            log_cols.append(txerr_df)
            log_cols.append(coll_df)
    
    pub_files = [(os.path.join( test, _ )) for _ in os.listdir(test) if "pub" in _]
    
    if len(pub_files) == 0:
        console.print(f"{test} has no pub files.", style="bold red")
        continue

    pub0_csv = pub_files[0]
    
    sub_files = [(os.path.join( test, _ )) for _ in os.listdir(test) if "sub" in _]

    test_df = pd.DataFrame()

    # ? Add the metrics for the entire test
    latencies = get_latencies(pub0_csv)
    if latencies is None:
        continue    

    latencies = latencies.rename("latency_us")
    total_throughput_mbps = get_total_sub_metric(sub_files, "mbps").rename("total_throughput_mbps")
    total_sample_rate = get_total_sub_metric(sub_files, "samples/s").rename("total_sample_rate")
    total_samples_received = pd.Series([get_total_sub_metric(sub_files, "total samples").max()]).rename("total_samples_received")
    total_samples_lost = pd.Series([get_total_sub_metric(sub_files, "lost samples").max()]).rename("total_samples_lost")
    pub_allocation_per_machine = pd.Series(get_participant_allocation_per_machine('pub', test)).rename("pub_allocation_per_machine")
    sub_allocation_per_machine = pd.Series(get_participant_allocation_per_machine('sub', test)).rename("sub_allocation_per_machine")

    test_df = pd.concat([
        latencies,
        total_throughput_mbps,
        total_sample_rate,
        total_samples_received,    
        total_samples_lost,
        pub_allocation_per_machine,
        sub_allocation_per_machine
    ] + [col for col in log_cols], axis=1)
    
    # ? Add the metrics for each sub
    for sub_file in sub_files:
        sub_i = sub_files.index(sub_file)
        
        throughput_mbps = get_metric_per_sub(sub_file, "mbps").rename(f"sub_{sub_i}_throughput_mbps")
        
        sample_rate = get_metric_per_sub(sub_file, "samples/s").rename(f"sub_{sub_i}_sample_rate")
        
        total_samples_received = pd.Series([get_metric_per_sub(sub_file, "total samples").max()])
        total_samples_received = total_samples_received.rename(f"sub_{sub_i}_total_samples_received")
        
        total_samples_lost = pd.Series([get_metric_per_sub(sub_file, "lost samples").max()])
        total_samples_lost = total_samples_lost.rename(f"sub_{sub_i}_total_samples_lost")
        
        test_df = pd.concat([
            test_df, 
            throughput_mbps,
            sample_rate,
            total_samples_received,
            total_samples_lost    
        ], axis=1)

    # ? Replace NaN with ""
    test_df = test_df.fillna("")

    if not os.path.exists(summaries_dir):
        os.mkdir(summaries_dir)

    summary_csv_path = os.path.join(summaries_dir, f"{os.path.basename(test)}_summary.csv")
    
    if not os.path.exists(summary_csv_path):
        test_df.to_csv(summary_csv_path, sep=",")