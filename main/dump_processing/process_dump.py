import resource
from dump_processing.process_posts import posts_processing
from dump_processing.process_comments import comments_processing
from dump_processing.formula_processing import formula_processing
from dump_processing.process_badges import badge_processing
from dump_processing.process_postlinks import postlinks_processing
from dump_processing.process_users import users_processing
from dump_processing.process_tags import tags_processing
import time
from dump_processing.helper import log
import os
from pathlib import Path

def processing_main(site_name, dir_name, database_name, context_length):
    #statistics_file = os.path.join(Path(database).parent, "statistics.log")
    start = time.process_time()

    posts_processing(site_name, dir_name, database_name)
    time_posts = time.process_time()
    print("time processing posts: ", format(time_posts-start, ".2f"), "s")
    #log(statistics_file, "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")

    comments_processing(site_name, dir_name, database_name)
    time_comments = time.process_time()
    print("time processing comments: ", format(time_comments-time_posts, ".2f"), "s")
    #log(statistics_file, "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")

    formula_processing(site_name, database_name, dir_name, context_length)
    time_formulas = time.process_time()
    print("time processing formulas: ", format(time_formulas-time_comments, ".2f"), "s")
    #log(statistics_file, "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")

    badge_processing(site_name, dir_name, database_name)
    time_badge = time.process_time()
    print("time processing badges: ", format(time_badge-time_formulas, ".2f"), "s")
    #log(statistics_file, "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")

    postlinks_processing(site_name, dir_name, database_name)
    time_postlinks = time.process_time()
    print("time processing postlinks: ", format(time_postlinks-time_badge, ".2f"), "s")
    #log(statistics_file, "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")

    users_processing(site_name, dir_name, database_name)
    time_users = time.process_time()
    print("time processing users: ", format(time_users-time_postlinks, ".2f"), "s")
    #log(statistics_file, "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")

    tags_processing(site_name, dir_name, database_name)
    time_tags = time.process_time()
    print("time processing tags: ", format(time_tags - time_users, ".2f"), "s")
    #log(statistics_file, "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")

