# PTST Data Processing + Visualiser

2 uses:
- Data Processing: `process.py`
- Data Visualisation: `app.py`

## Data Processing
Script for processing the output of PTST. 

It analyses the files to find the tests that are usable. 

Usable tests are tests containing all the expected data files. 

The script will then take these usable tests and summarise them meaning that it will take the pub and sub `.csv` files and put all the data into one single file per test.

### Usage
```bash
python process.py <raw_dir> <usable_dir> <summaries_dir>
```

`<raw_dir>`: Path pointing to dir containing all test folders.

`<usable_dir>`: Path pointing to dir where all usable test data will be copied to. Folder will be created if it doesn't exist.

`<summaries_dir>`: Path pointing to dir where test summaries will be placed. Folder will be created if it doesn't exist.

## Data Visualisation
Dash web application that let's you visualise test data dynamically.

### Usage
```bash
python app.py
```

You can also pass in a path to the tests folder like so:

```bash
python app.py <summaries_dir>
```

`<summaries_dirs>`: Path pointing to dir where all the test summaries are.

This will automatically fill in the value of the input.