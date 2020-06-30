import argparse
from formula_parsing.formulas_to_mml import formulas_to_cmml
from formula_parsing.formulas_to_mml import formulas_to_pmml
from formula_parsing.formulas_to_mml import formulas_to_both_ml
import sys
import time

def main(filename_dumps, database, mode):
    with open(filename_dumps) as f:
        sites = [line.rstrip() for line in f if line is not ""]

    for site in sites:
        start = time.time()
        if mode == "cmml":
            formulas_to_cmml(database, "FormulasPosts", site)
            sys.stdout.write('\n')
            formulas_to_cmml(database, "FormulasComments", site)
        if mode == "pmml":
            formulas_to_pmml(database, "FormulasPosts", site)
            sys.stdout.write('\n')
            formulas_to_pmml(database, "FormulasComments", site)
        if mode == "both":
            formulas_to_both_ml(database, "FormulasPosts", site)
            sys.stdout.write('\n')
            formulas_to_both_ml(database, "FormulasComments", site)
        sys.stdout.write('\n' + site + ' finished. Time: ' + str(int((time.time()-start)/60)) +"min " + str(int((time.time()-start)%60)) + "sec")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dumps",default="test_dumps", help="File containing stackexchange dump sites names to be processed")
    parser.add_argument("--database", default='../output/database.db', help="database")
    parser.add_argument("-m", "--mode", default='both', help="options: cmml, pmml, both (ContentMathML, PresentationMathMl, Both)")
    args = parser.parse_args()
    main(args.dumps, args.database, args.mode)
