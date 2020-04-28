import argparse
import resource
from process_posts import posts_processing
from process_comments import comments_processing
from extract_formulas import formula_processing
from process_votes import bounty_processing
from process_badges import badge_processing
import time
from helper import log

def processing_main(dir_name, database_name):
    log("../output/statistics.log", "#################################################")
    log("../output/statistics.log", "# formula_retrieval.py")
    log("../output/statistics.log", "# input: " + dir_name)
    log("../output/statistics.log", "# output: "+ database_name)
    log("../output/statistics.log", "# -------------------------")

    start = time.process_time()

    posts_processing(dir_name, database_name)
    time_posts = time.process_time()
    print("# time processing posts: ", format(time_posts-start, ".2f"), "s")

    comments_processing(dir_name, database_name)
    time_comments = time.process_time()
    print("# time processing comments: ", format(time_comments-time_posts, ".2f"), "s")

    formula_processing(database_name)
    time_formulas = time.process_time()
    print("# time processing formulas: ", format(time_formulas-time_comments, ".2f"), "s")

    bounty_processing(dir_name, database_name)
    time_bounty = time.process_time()
    print("# time processing bounty: ", format(time_bounty-time_formulas, ".2f"), "s")

    badge_processing(dir_name, database_name)
    time_badge = time.process_time()
    print("# time processing badges: ", format(time_badge-time_bounty, ".2f"), "s")

    log("../output/statistics.log", "# -------------------------")
    log("../output/statistics.log", "# total execution time: "+ str(int((time_badge-start)/60)) +"min " + str(int((time_badge-start)%60)) + "sec")
    log("../output/statistics.log", "# max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")
    log("../output/statistics.log", "#################################################")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    #parser.add_argument("-i","--input",default= "../dataset/mathematics", help = "input directory of stackexchange dump *.xml files")
    #parser.add_argument("-d", "--database", default='../output/dataset.db', help="database output")
    parser.add_argument("-i","--input",default= "../dataset/physics", help = "input directory of stackexchange dump *.xml files")
    parser.add_argument("-d", "--database", default='../output/physics.db', help="database output")
    args = parser.parse_args()
    processing_main(args.input, args.database)
