This tool basically takes the results of a test campaign from PTST and does the following:

1. Check which test results are usable (`analyse_functions.py`).
2. Summarise the usable results by putting all measurements into a single file (`summarise_functions.py`).

This is all for preparation to be used in the PTST Visualiser (`index.py`).

## How to use
Run the following on the folder of a test campaign from PTST:

```
python process.py <camp_dir> <output_dir> <summary_dir>
```

Where `<camp_dir>` is the path to the test campaign results (a folder to all tests where each folder is a test) from PTST, `<output_dir>` is the path to a folder where the usable test data will be copied to, and `<summary_dir>` is the folder where all the summaries will be stored.

## Todo
[ ] Add checks to see if the actual csv files have a data length greater than like 50 bytes i.e. they aren't empty.
[ ] Implement the case where multiple progress.log files are found.