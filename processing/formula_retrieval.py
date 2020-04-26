import argparse
import os
import resource
from processing.process_posts import posts_processing
from processing.process_comments import comments_processing
from processing.extract_formulas import formula_processing
import time

def processing_main(dir_name, database_name):
    start = time.process_time()
    print("max memory usage in GB: ", format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f"))

    posts_processing(dir_name, database_name)
    time_posts = time.process_time()
    print("time processing posts: ", format(time_posts-start, ".2f"), "s")
    print("max memory usage in GB: ", format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f"))

    comments_processing(dir_name, database_name)
    time_comments = time.process_time()
    print("time processing posts: ", format(time_comments-time_posts, ".2f"), "s")
    print("max memory usage in GB: ", format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f"))

    formula_processing(database_name)
    time_formulas = time.process_time()
    print("time processing posts: ", format(time_formulas-time_comments, ".2f"), "s")
    print("max memory usage in GB: ", format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f"))

    print("total execution time: ", format(time_formulas-start, ".2f"), "s")
    print("total execution time: ", format(time_formulas-start/60, ".2f"), "min")
    print("max memory usage in byte: ", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    print("max memory usage in GB: ", format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i","--input",default= "../dataset/mathematics", help = "input directory of stackexchange dump *.xml files")
    parser.add_argument("-d", "--database", default='../output/dataset.db', help="database output")
    args = parser.parse_args()
    processing_main(args.input, args.database)
