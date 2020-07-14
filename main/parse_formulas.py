import argparse
from formula_parsing.formulas_to_mml import formulas_to_cmml
from formula_parsing.formulas_to_mml import formulas_to_pmml
from formula_parsing.formulas_to_mml import formulas_to_both_ml
from dump_processing.helper import log
import sys
import time
import sqlite3
import resource

def create_mathml_tables(database):
    DB = sqlite3.connect(database)
    cursor = DB.cursor()

    cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='FormulasPostsMathML' ")

    #if the count is 1, then table exists
    if cursor.fetchone()[0]!=1 :
        cursor.execute('CREATE TABLE "FormulasPostsMathML"("FormulaId" INTEGER PRIMARY KEY, "Site" TEXT, "ContentMathML" TEXT, "PresentationMathML" TEXT)')
    DB.commit()

    cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='FormulasCommentsMathML' ")
    if cursor.fetchone()[0]!=1 :
        cursor.execute('CREATE TABLE "FormulasCommentsMathML"("FormulaId" INTEGER PRIMARY KEY, "Site" TEXT, "ContentMathML" TEXT, "PresentationMathML" TEXT)')
    DB.commit()

    DB.close()

def main(filename_dumps, database, mode, threads):
    start = time.time()
    log("../output/statistics.log", "#################################################")
    log("../output/statistics.log", "parse_formulas.py")
    log("../output/statistics.log", "input: " + database + ", mode: " + mode + ", " + threads + " threads")
    log("../output/statistics.log", "output: "+ database + ", ../output/statistics.log")


    with open(filename_dumps) as f:
        sites = [line.rstrip() for line in f if line is not ""]

    log("../output/statistics.log", "dumps: " + str(sites))
    log("../output/statistics.log", "-------------------------")

    try:
        threads = int(threads)
    except:
        print("An Error occured parsing --threads argument " + threads)
    create_mathml_tables(database)

    for site in sites:
        start = time.time()
        if mode == "cmml":
            formulas_to_cmml(database, "FormulasPosts", site, threads)
            sys.stdout.write('\n')
            formulas_to_cmml(database, "FormulasComments", site, threads)
        if mode == "pmml":
            formulas_to_pmml(database, "FormulasPosts", site, threads)
            sys.stdout.write('\n')
            formulas_to_pmml(database, "FormulasComments", site, threads)
        if mode == "both":
            formulas_to_both_ml(database, "FormulasPosts", site, threads)
            sys.stdout.write('\n')
            formulas_to_both_ml(database, "FormulasComments", site, threads)
        sys.stdout.write('\n' + site + ' finished. Time: ' + str(int((time.time()-start)/60)) +"min " + str(int((time.time()-start)%60)) + "sec")

    log("../output/statistics.log", "-------------------------")
    log("../output/statistics.log", "total execution time: "+ str(int((time.time()-start)/60)) +"min " + str(int((time.time()-start)%60)) + "sec")
    log("../output/statistics.log", "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")
    log("../output/statistics.log", "#################################################")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dumps",default="test_dumps", help="File containing stackexchange dump sites names to be processed")
    parser.add_argument("--database", default='../output/database.db', help="database")
    parser.add_argument("-m", "--mode", default='both', help="options: cmml, pmml, both (ContentMathML, PresentationMathMl, Both)")
    parser.add_argument("-t", "--threads", default="20", help="Number of threads to run parallel. One thread used to convert a single formula in MathML. options: integer")
    args = parser.parse_args()
    main(args.dumps, args.database, args.mode, args.threads)
