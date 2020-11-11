import argparse
from formula_parsing.formulas_to_mml import formulas_to_cmml
from formula_parsing.formulas_to_mml import formulas_to_pmml
from formula_parsing.formulas_to_mml import formulas_to_both_ml
from dump_processing.helper import log
import sys
import time
import sqlite3
import resource
import os
from pathlib import Path

def create_mathml_tables(database):
    DB = sqlite3.connect(database, timeout=60000)
    cursor = DB.cursor()

    cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='FormulasPostsMathML' ")

    #if the count is 1, then table exists
    if cursor.fetchone()[0]!=1 :
        cursor.execute('CREATE TABLE "FormulasPostsMathML"("FormulaId" INTEGER PRIMARY KEY, "Site" TEXT, "ContentMathML" TEXT, "OPT" TEXT, "PresentationMathML" TEXT, "SLT" TEXT)')
    DB.commit()

    cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='FormulasCommentsMathML' ")
    if cursor.fetchone()[0]!=1 :
        cursor.execute('CREATE TABLE "FormulasCommentsMathML"("FormulaId" INTEGER PRIMARY KEY, "Site" TEXT, "ContentMathML" TEXT, "OPT" TEXT, "PresentationMathML" TEXT, "SLT" TEXT)')
    DB.commit()

    DB.close()

def main(filename_dumps, database, mode, threads, tree, comments, offset, total_formulas, output_database):
    statistics_file = os.path.join(Path(database).parent, "statistics.log")
    start = time.time()
    log(statistics_file, "#################################################")
    log(statistics_file, "parse_formulas.py")
    log(statistics_file, "input: " + database + ", mode: " + mode + ", " + threads + " threads")
    log(statistics_file, "output: "+ output_database + ", " + statistics_file)


    with open(filename_dumps) as f:
        sites = [line.rstrip() for line in f if line != ""]

    log(statistics_file, "dumps: " + str(sites))
    log(statistics_file, "-------------------------")

    try:
        threads = int(threads)
    except:
        print("An Error occured parsing --threads argument " + threads)
    create_mathml_tables(output_database)

    if tree == "yes":
        tree = True
    else:
        tree = False

    if comments == "yes":
        comments = True
    else:
        comments = False

    for site in sites:
        start = time.time()
        if mode == "cmml":
            formulas_to_cmml(database, "FormulasPosts", site, threads, tree, offset, total_formulas, output_database)
            sys.stdout.write('\n')
            if(comments):
                formulas_to_cmml(database, "FormulasComments", site, threads, tree, offset, total_formulas, output_database)
        if mode == "pmml":
            formulas_to_pmml(database, "FormulasPosts", site, threads, tree, offset, total_formulas, output_database)
            sys.stdout.write('\n')
            if(comments):
                formulas_to_pmml(database, "FormulasComments", site, threads, tree, offset, total_formulas, output_database)
        if mode == "both":
            formulas_to_both_ml(database, "FormulasPosts", site, threads, tree, offset, total_formulas, output_database)
            sys.stdout.write('\n')
            if(comments):
                formulas_to_both_ml(database, "FormulasComments", site, threads, tree, offset, total_formulas, output_database)
        sys.stdout.write('\n' + site + ' finished. Time: ' + str(int((time.time()-start)/60)) +"min " + str(int((time.time()-start)%60)) + "sec")

    log(statistics_file, "\n-------------------------")
    log(statistics_file, "total execution time: "+ str(int((time.time()-start)/60)) +"min " + str(int((time.time()-start)%60)) + "sec")
    log(statistics_file, "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")
    log(statistics_file, "#################################################")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dumps",default="test_dumps", help="File containing stackexchange dump sites names to be processed")
    parser.add_argument("--database", default='../output/database.db', help="database")
    parser.add_argument("-m", "--mode", default='both', help="options: cmml, pmml, both (ContentMathML, PresentationMathMl, Both)")
    parser.add_argument("--tree", default="yes", help="options: yes, no. Whether or not to calculate slt trees from pmml and opt from cmml ")
    parser.add_argument("-t", "--threads", default="20", help="Number of threads to run parallel. One thread used to convert a single formula in MathML. options: integer")
    parser.add_argument("-c", "--comments", default="no", help="options: yes, no. Whether or not to parse comment formulas in addition to the post formulas.")
    parser.add_argument("--offset", default=0, help="Offset of start formula")
    parser.add_argument("--totalformulas", default=1000000, help="Number of total formulas (limit)")
    parser.add_argument("--output", default='../output/database.db', help="database to write to")

    args = parser.parse_args()
    main(args.dumps, args.database, args.mode, args.threads, args.tree, args.comments, args.offset, args.totalformulas, args.output)
