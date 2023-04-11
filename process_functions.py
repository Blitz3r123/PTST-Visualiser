from analyse_functions import *
from summarise_functions import *

import pandas as pd

def validate_args(testsdir, outputdir, summarydir):
    testsdir_exists_and_isdir = os.path.exists(testsdir) and os.path.isdir(testsdir)
    
    if not testsdir_exists_and_isdir:
        console.print(f"{testsdir} does not exist or is not a folder.", style="bold red")
        sys.exit(0)
    
    if not os.path.exists(outputdir):
        os.mkdir(outputdir)
        
    if not os.path.exists(summarydir):
        os.mkdir(summarydir)

def analyse_tests(testsdir, outputdir):
    testdirs = get_testdirs(testsdir)

    progress_log_tests = get_progress_log_tests(testsdir)

    if len(progress_log_tests) < len(testdirs):
        console.print(f"Mismatch in number of tests found in the progress.log and the test folders found in {testsdir}", style="bold red")
        console.print(f'\tprogress.log has {len(progress_log_tests)} tests while there are {len(testdirs)} test folders in {testsdir}', style="bold white")
        sys.exit(0)
    
    
    test_reports = []
    successful_tests = []
    
    for i in track( range( len(testdirs) ), description="Analysing tests...", update_period=1 ):
        test = testdirs[i]
            
        reports = []
        
        try:
            progress_test = [progress_test for progress_test in progress_log_tests if progress_test["test"] in test][0]
        except Exception as e:
            console.print(e, style="bold red")
            
        # ? Get expected test duration
        expected_test_duration_s = get_expected_duration_s(test)
        
        # ? Get actual test duration
        try:
            actual_test_duration_s = parse_log_duration_to_s(progress_test["duration"])
        except KeyError as e:
            actual_test_duration_s = calculate_duration_s(progress_test['start_time'], progress_test['end_time'])
        
        # ? Compare expected to actual test duration
        if actual_test_duration_s < expected_test_duration_s:
            reports.append(f"Test ran shorter than expected. {actual_test_duration_s} seconds instead of {expected_test_duration_s} seconds.")
        
        # ? Get expected csv files
        expected_csv_files = get_expected_csv_files(test)
        # ? Get actual csv files
        actual_csv_files = get_actual_csv_files(test)
        
        run_path = os.path.join(test, 'run_1')
        if not os.path.exists(run_path):
            actual_csv_filepaths = [os.path.join(test, _) for _ in actual_csv_files]
        else:
            actual_csv_filepaths = [os.path.join(test, "run_1", _) for _ in actual_csv_files]
        
        empty_files = []
        for file in actual_csv_filepaths:
            filesize = os.path.getsize(file)
            if filesize == 0:
                empty_files.append(file)
                continue
            
        if len(empty_files) > 0:
            empty_files = [os.path.basename(file) for file in empty_files]
            reports.append("Empty Files: " + ", ".join(empty_files))
        
        if len(expected_csv_files) == 0:
            console.print(f"{test} expects no csv files?!", style="bold red")
            sys.exit(0)
        
        if len(actual_csv_files) == 0:
            reports.append(f"Test has no csv files.")
            
        if len(actual_csv_files) < len(expected_csv_files):
            reports.append(f"Missing {len(expected_csv_files) - len(actual_csv_files)} csv files.")
        
        # ? Copy over leftover files from the test that happened after
        found_csv_files = copy_leftover_csv_files_if_found(test, actual_csv_files, expected_csv_files)
        
        # ? Get actual logs
        actual_logs = get_actual_logs(test)
        
        if not actual_logs:
            reports.append(f"No logs found.")
            
        if len(reports) == 0:
            successful_tests.append(test)
        else:
            test_reports.append({
                "test": test,
                "reports": reports
            })

    test_reports_df = pd.DataFrame(test_reports)
    test_reports_df.to_csv("./test_report.csv")
    console.print(f"Test issues written to test_report.csv.", style="bold green")
                
    for i in track( range( len(successful_tests) ), description="Copying usable tests...", update_period=1 ):
        test = successful_tests[i]
        src_dir = test
        dest_dir = os.path.join(outputdir, os.path.basename(test))
        if not os.path.exists(dest_dir):
            shutil.copytree(src_dir, dest_dir)
                
def summarise_tests(outputdir, summarydir):
    
    if not os.path.exists(outputdir):
        console.print(f"{outputdir} doesn't exist.", style="bold red")
        sys.exit()

    if not os.path.exists(summarydir):
        console.print(f"{summarydir} doesn't exist.", style="bold red")
        sys.exit()

    tests = [ os.path.join(outputdir, _) for _ in os.listdir(outputdir) ]
    
    for i in track( range( len(tests) ), description="Summarising tests...", update_period=1 ):
        test = tests[i]
        
        if test_summary_exists(test, summarydir):
            continue
        
        testpath = os.path.join(test, "run_1")
        pub_files = [(os.path.join( testpath, _ )) for _ in os.listdir(testpath) if "pub" in _]
        
        if len(pub_files) == 0:
            console.print(f"{test} has no pub files.", style="bold red")
            continue

        pub0_csv = pub_files[0]
        
        sub_files = [(os.path.join( testpath, _ )) for _ in os.listdir(testpath) if "sub" in _]

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

        test_df = pd.concat([
            latencies,
            total_throughput_mbps,
            total_sample_rate,
            total_samples_received,    
            total_samples_lost    
        ], axis=1)
        
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

        if not os.path.exists(summarydir):
            os.mkdir(summarydir)

        summary_csv_path = os.path.join(summarydir, f"{os.path.basename(test)}_summary.csv")
        
        if not os.path.exists(summary_csv_path):
            test_df.to_csv(summary_csv_path, sep=",")