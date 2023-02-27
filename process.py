from process_functions import *

args = sys.argv[1:]

if len(args) < 3:
    console.print(f"Missing some args: {args}.\nExpected 3: <tests_dir>, <output_dir>, <summary_dir>", style="bold red")
    sys.exit(0)
else:
    testsdir = args[0]
    outputdir = args[1]
    summarydir = args[2]
    
# ? Check the paths given are valid
validate_args(testsdir, outputdir, summarydir)

if "-delete" in args or "--delete" in args:
    with console.status(f"Deleting everything in {outputdir}..."):
        shutil.rmtree(outputdir)

# ? Find what data is usable and copy it over to outputdir
analyse_tests(testsdir, outputdir)

# ? Summarise the test results into the summarydir
summarise_tests(outputdir, summarydir)