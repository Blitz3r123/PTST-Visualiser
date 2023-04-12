import os
import shutil
import sys

from pprint import pprint
from rich.console import Console
from rich.progress import track

console = Console()

args = sys.argv[1:]

if len(args) != 3:
    console.print(f"Expected 3 args but found {len(args)}. Refer to the readme for help.", style="bold red")
    sys.exit()

raw_dir = args[0]
usable_dir = args[1]
summaries_dir = args[2]

if not os.path.exists(raw_dir):
    console.print(f"The path {raw_dir} doesn't exist.", style="bold red")
    sys.exit()

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

# ? 2. Copy usable tests over to usable_dir.
for i in track(range(len(usable_test_dirs)), description="Copying over usable tests..."):
    usable_test_dir = usable_test_dirs[i]
    src = usable_test_dir
    dest = os.path.join(usable_dir, os.path.basename(usable_test_dir))
    
    if not os.path.exists(dest):
        os.makedirs(dest)
    
    try:
        shutil.copytree(src, dest)
    except FileExistsError as e:
        continue

# ? 3. Summarise tests in usable_dir.
