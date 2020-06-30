import argparse
from formula_parsing.formulas_to_mml import formulas_to_cmml

def main(filename_dumps, database):
    with open(filename_dumps) as f:
        sites = [line.rstrip() for line in f if line is not ""]

    for site in sites:
        formulas_to_cmml(database, "FormulasPosts", site)
        formulas_to_cmml(database, "FormulasComments", site)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dumps",default="test_dumps", help="File containing stackexchange dump sites names to be processed")
    parser.add_argument("--database", default='../output/database.db', help="database")
    args = parser.parse_args()
    main(args.dumps, args.database)
