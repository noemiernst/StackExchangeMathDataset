import latex2mathml
import argparse
import sqlite3
import pandas as pd
from helper import log
import re

def analyze_posts(database, table):
    DB = sqlite3.connect(database)
    posts = (pd.read_sql('select Body from "'+ table+'"', DB))["Body"].to_list()
    DB.close()

    log("../output/analysis.log", "# posts: "+ str(len(posts)))

    inline = re.compile("`.+?`")
    count = 0
    for post in posts:
        count += len(re.findall(inline, post))
        if len(re.findall(inline, post))>0:
            print(re.findall(inline, post))

    inline = re.compile("(( {4}).+)+")
    count = 0
    for post in posts:
        count += len(re.findall(inline, post))
        if len(re.findall(inline, post))>0:
            print(re.findall(inline, post))

    print(count)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d","--database",default= "../output/physics.db", help = "input database with LaTeX formulas")
    parser.add_argument("-t", "--table", default="QuestionsText", help= "name of table in database")
    #parser.add_argument("-d","--database",default= "../output/mathematics.db", help = "input database with LaTeX formulas")
    #parser.add_argument("-t", "--table", default="FormulasPosts", help= "name of table in database")
    args = parser.parse_args()

    analyze_posts(args.database, args.table)
