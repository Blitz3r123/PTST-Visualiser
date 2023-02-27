from analyse_functions import *

import pandas as pd

def validate_args(testsdir, outputdir):
    testsdir_exists_and_isdir = os.path.exists(testsdir) and os.path.isdir(testsdir)
    outputdir_exists_and_isdir = os.path.exists(outputdir) and os.path.isdir(outputdir)
    
    if not testsdir_exists_and_isdir:
        console.print(f"{testsdir} does not exist or is not a folder.", style="bold red")
        sys.exit(0)
    
    if not outputdir_exists_and_isdir:
        console.print(f"{outputdir} does not exist or is not a folder.", style="bold red")
        sys.exit(0)

def analyse_tests(testsdir, outputdir):
    testdirs = get_testdirs(testsdir)
    
    progress_log = get_progress_log(testsdir)
    
    progress_log_tests = get_progress_log_tests(progress_log)
    
    if len(progress_log_tests) < len(testdirs):
        console.print(f"Mismatch in number of tests found in the progress.log and the test folders found in {testsdir}", style="bold red")
        console.print(f'\tprogress.log has {len(progress_log_tests)} tests while there are {len(testdirs)} test folders in {testsdir}', style="bold white")
        sys.exit(0)
    
    test_reports = []
    successful_tests = []
    
    for test in testdirs:
        with console.status(f"[{testdirs.index(test) + 1}/{len(testdirs)}] Analysing {test}"):
            
            reports = []
            
            try:
                progress_test = [progress_test for progress_test in progress_log_tests if progress_test["test"] in test][0]
            except Exception as e:
                console.print(e, style="bold red")
                
            # ? Get expected test duration
            expected_test_duration_s = get_expected_duration_s(test)
            # ? Get actual test duration
            actual_test_duration_s = parse_log_duration_to_s(progress_test["duration"])
            
            # ? Compare expected to actual test duration
            if actual_test_duration_s < expected_test_duration_s:
                reports.append(f"Test ran shorter than expected. {actual_test_duration_s} seconds instead of {expected_test_duration_s} seconds.")
            
            # ? Get expected csv files
            expected_csv_files = get_expected_csv_files(test)
            # ? Get actual csv files
            actual_csv_files = get_actual_csv_files(test)
            
            if len(expected_csv_files) == 0:
                console.print(f"{test} expects no csv files?!", style="bold red")
                sys.exit(0)
            
            if len(actual_csv_files) == 0:
                reports.append(f"Test has no csv files.")
            
            # ? Copy over leftover files from the test that happened after
            found_csv_files = copy_leftover_csv_files_if_found(test, actual_csv_files, expected_csv_files)
            
            # ? Get actual logs
            actual_logs = get_actual_logs(test)
            
            if len(actual_logs) == 0:
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
    console.print(f"Test issues written to test_report.csv", style="bold white")
                
    for test in successful_tests:
        with console.status(f"[{successful_tests.index(test) + 1}/{len(successful_tests)}] Copying {os.path.basename(test)}..."):
            src_dir = test
            dest_dir = os.path.join(outputdir, os.path.basename(test))
            if not os.path.exists(dest_dir):
                shutil.copytree(src_dir, dest_dir)