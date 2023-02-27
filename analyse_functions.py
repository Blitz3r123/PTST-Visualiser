import os
import sys
import re
import shutil

from pprint import pprint
from rich.console import Console

console = Console()

def get_testdirs(testdir):
    testdir_contents = os.listdir(testdir)
    testdir_contents = [
        os.path.join(
            testdir, 
            testdir_content
        ) 
        for testdir_content in testdir_contents
    ]

    return [
        item 
        for item in testdir_contents
        if os.path.isdir(item)
    ]

def get_progress_log(testdir):
    testdir_contents = os.listdir(testdir)
    progress_logs = [file for file in testdir_contents if 'progress.log' in file]
    
    if len(progress_logs) == 0:
        console.print(f"No progress.log found in {testdir}", style="bold red")
        sys.exit(0)
    elif len(progress_logs) == 1:
        return os.path.join(testdir, progress_logs[0])
    else:
        # ? Combine multiple progress logs into one
        # TODO
        None
        
def get_progress_log_tests(progress_log):
    try:
        with open(progress_log, "r") as f:
            file_contents = f.readlines()
    except FileNotFoundError as e:
        console.print(f'{progress_log} does not exist.', style="bold red")
        sys.exit(0)
        
    file_contents = [line.strip() for line in file_contents]

    if len(file_contents) == 0:
        console.print(f"progress.log is empty for {progress_log}.", style="bold red")
        sys.exit(0)
    else:
        tests = []
        
        for line in file_contents:
            test = {
                "test": None,
                "start_time": None,
                "end_time": None,
                "duration": None
            }
            
            if 'TEST ' in line:
                line_index = file_contents.index(line)
                start_time_index = line_index + 1
                end_time_index = line_index + 2
                duration_index = line_index + 3
                
                test['test'] = re.sub('TEST #\d*: ', '', line)
                
                test["start_time"] = file_contents[start_time_index].replace(
                    "[1/1]: Started at ", 
                    ""
                )
                test["end_time"] = file_contents[end_time_index].replace(
                    "[1/1]: Finished at ", 
                    ""
                )
                try:
                    test["duration"] = file_contents[duration_index].replace(
                        "[1/1]: ", 
                        ""
                    ).replace(
                        ":", 
                        ""
                    )
                except IndexError as e:
                    test["duration"] = None
                    
                tests.append(test)
                
    return tests

def get_expected_duration_s(test):
    if "s_" not in test:
        return 0
    else:
        test_duration_string = re.findall("\d\d*s_\d*", test)[0].split("_")[0]
        duration_s = test_duration_string.replace("s", "")
        duration_s = int(duration_s)

        return duration_s
    
def parse_log_duration_to_s(duration):
    if duration is None:
        return 0
    
    duration_items = duration.split(" ")
    
    if len(duration_items) != 8:
        console.print(f"Error parsing test duration: {duration}", style="bold red")
        return 0
    
    days_amount = int(duration_items[0])
    hours_amount = int(duration_items[2])
    minutes_amount = int(duration_items[4])
    seconds_amount = int(duration_items[6])
    
    days_amount_s = days_amount * 24 * 60 * 60
    hours_amount_s = hours_amount * 60 * 60
    minutes_amount_s = minutes_amount * 60
    
    return days_amount_s + hours_amount_s + minutes_amount_s + seconds_amount

assert(parse_log_duration_to_s("01 Days 01 Hours 01 Minutes 01 Seconds") == 90061)

def get_expected_csv_files(test):
    test_name = os.path.basename(test)
    
    participants_in_title = re.findall(r'\d*[P]_\d*[S]', test_name)[0]
    
    _, subs = participants_in_title.split("_")
    
    sub_amount = int(re.findall(r'\d*', subs)[0])
    
    expected_csv_files = [
        os.path.join(test, "pub_0.csv")
    ]
    
    for i in range(sub_amount):
        expected_csv_files.append(os.path.join(test, f'sub_{i}.csv'))
        
    return expected_csv_files

def get_run_contents(test):
    if not os.path.exists(test):
        console.print(f'The test path {test} does not exist.', style="bold red")
        return
        
    if not os.path.isdir(test):
        console.print(f'The test path {test} is not a folder.', style="bold red")
        return
        
    test_files = os.listdir(test)
    
    if len(test_files) == 0:
        console.print(f'The test path {test} has nothing inside it.', style="bold red")
        return
    
    run_dir = os.path.join(test, "run_1")
    
    if not os.path.exists(run_dir):
        console.print(f'The test path {test} has no run_1 folder.', style="bold red")
        console.print(f"Here is what is inside {test}:", style="bold red")
        for item in os.listdir(test):
            console.print(f"\t{item}", style="bold white")
        return
    
    run_contents = os.listdir(run_dir)
    
    return run_contents

def get_actual_csv_files(test):
    run_contents = get_run_contents(test)
    
    if len(run_contents) == 0:
        console.print(f'The run_1 folder inside {test} is empty.', style="bold red")
        return

    csv_files = [file for file in run_contents if '.csv' in file]
    
    return csv_files

def copy_leftover_csv_files_if_found(test, actual_files, expected_files):
    expected_files = [file.replace("'", "") for file in expected_files]
    expected_files = [os.path.join(test, "run_1", file) for file in expected_files]
    
    missing_files = list(set(expected_files) - set(actual_files))
    
    data_dir = os.path.dirname(test)
    all_tests = [
        os.path.join(data_dir, folder) 
        for folder in os.listdir(data_dir) 
        if os.path.isdir(os.path.join(data_dir, folder))
    ]
    
    test_index = all_tests.index(test)
    try:
        next_test = all_tests[test_index + 1]
        leftover_dir = os.path.join(next_test, "run_1", "leftovers")
        if not os.path.exists(leftover_dir):
            return []
        
        leftover_files = [
            os.path.join(leftover_dir, file) 
            for file in os.listdir(leftover_dir)
        ]
        
        found_files = list( 
            set(
                [os.path.basename(file) for file in missing_files]
            ).intersection(
                set(
                    [os.path.basename(file) for file in leftover_files]
                )
            )
        )
        
        if len(found_files) > 0:
            source_files = [os.path.join(next_test, "run_1", "leftovers", file) for file in found_files]
            
            for source_file in source_files:
                destination = os.path.join(test, "run_1", os.path.basename(source_file))
                shutil.copy(source_file, destination)
                
            # console.print(f"Copied leftovers from {next_test} to {test}.", style="bold green")
            
        return found_files
    except IndexError as e:
        return []
    
def get_actual_logs(test):
    run_contents = get_run_contents(test)
    
    log_dirs = [_ for _ in run_contents if "logs" in _]
    
    if len(log_dirs) == 0:
        console.print(f"The run_1 folder inside {test} has no logs folder.", style="bold red")
        return
    
    log_dir = log_dirs[0]
    
    log_dir = os.path.join(test, "run_1", log_dir)
    
    if not os.path.isdir(log_dir):
        console.print(f"{log_dir} is not a folder.", style="bold red")
        return
    
    log_files = os.listdir(log_dir)
    log_files = [
        os.path.join(log_dir, file)
        for file in log_files
    ]
    
    return log_files