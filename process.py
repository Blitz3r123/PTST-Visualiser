from process_functions import *

args = sys.argv[1:]

if len(args) > 2:
    console.print(f"Too many args given: {args}", style="bold red")
    sys.exit(0)
elif len(args) < 2:
    console.print(f"Missing some args: {args}.\nExpected 2: <tests_dir>, <output_dir>", style="bold red")
    sys.exit(0)
else:
    testsdir = args[0]
    outputdir = args[1]
    
# ? Check the paths given are valid
validate_args(testsdir, outputdir)

# ? Find what data is usable and copy it over to outputdir
analyse_tests(testsdir, outputdir)

