from functions import *

testdir = "./data"

tests = [os.path.join(testdir, folder) for folder in os.listdir(testdir)]

# TODO: Remove list limiter on tests
for test in tests[:3]:
    lat_summary = get_latency_summary(test)
    pprint(lat_summary)
