# PTST Data Processing + Visualiser

2 uses:
- Data Processing: `process.py`
- Data Visualisation: `app.py`

## Data Processing
Script for processing the output of PTST. 
It analyses the files to find the tests that are usable. 
Usable tests are tests containing all the expected data files. 
The script will then take these usable tests and summarise them meaning that it will take the pub and sub `.csv` files and put all the data into one single file per test.

## Data Visualisation

<!-- This tool basically takes the results of a test campaign from PTST and does the following:

1. Check which test results are usable (`analyse_functions.py`).
2. Summarise the usable results by putting all measurements into a single file (`summarise_functions.py`).

This is all for preparation to be used in the PTST Visualiser (`app.py`).

## Requirements
`set_dir` should point to a path that should follow something like:
```
📁 set_dir
    📁 test_one
        📄 pub_0.csv
        📄 sub_0.csv
        ...
        📄 sub_n.csv
    ...
    📁 test_n
    📄 progress.log
```

<span style="color: red;">**Make sure that there is a progress.log file or it won't work!**</span>

## How to use

### Data Processing
Run the following on the folder of a test set from PTST (where the folder contains folders - each folde corresponds to a single test):

```
python process.py <raw_dir> <usable_dir> <summary_dir>
```

Where `<raw_dir>` is the path to the test set results (a folder to all tests where each folder is a test) from PTST, `<usable_dir>` is the path to a folder where the usable test data will be copied to, and `<summary_dir>` is the folder where all the summaries will be stored.

You can use `-skip-analysis` to skip the test analysis and usable test copy process:

```
python process.py <raw_dir> <usable_dir> <summary_dir> -skip-analysis
```

### Visualiser

```
python app.py
```

## Todo
- [x] Add checks to see if the actual csv files have a data length greater than like 50 bytes i.e. they aren't empty.
- [ ] Show the total number of tests analysed, how many were usable, and how many were discarded
- [ ] Implement the case where multiple progress.log files are found. -->
