import latex2mathml
import argparse
import sqlite3
import pandas as pd

def equations(formulas):
    count = 0
    for formula in zip(formulas["Body"]):
        if '=' in formula[0]:
            count += 1
    print('# equations: ', count, ', ', format(100*count/len(formulas["Body"]), ".2f"), '%', "  (formulas containing '=')")

def length(formulas, length):
    count = 0
    for formula in zip(formulas["Body"]):
        if len(formula[0]) == length:
            count += 1
    print('# formulas of length ', length, ': ', count, ', ', format(100*count/len(formulas["Body"]), ".2f"), '%')

def min_length(formulas, length):
    count = 0
    for formula in zip(formulas["Body"]):
        if len(formula[0]) >= length:
            count += 1
    print('# formulas of length >= ', length, ': ', count, ', ', format(100*count/len(formulas["Body"]), ".2f"), '%')

def greek_letters(formulas):
    count = 0
    symbols = [r'\alpha', r'\beta', r'\gamma', r'\delta', r'\epsilon', r'\zeta', r'\eta', r'\theta', r'\iota',
               r'\kappa', r'\lambda', r'\mu', r'\nu', r'\xi', r'\omicron', r'\pi', r'\rho', r'\sigma', r'\tau',
               r'\upsilon', r'\phi', r'\chi', r'\psi', r'\omega']
    for formula in zip(formulas["Body"]):
        f = (formula[0]).lower()
        if any(sym in f for sym in symbols):
            count += 1
    print('# formulas containing greek letters: ', count, ', ', format(100*count/len(formulas["Body"]), ".2f"), '%')


def super_subscripts(formulas):
    super_count = 0
    sub_count = 0
    for formula in zip(formulas["Body"]):
        if '^' in formula[0]:
            super_count += 1
        if '_' in formula[0]:
            sub_count += 1
    print('# formulas containing superscripts (^): ', super_count, ', ', format(100*super_count/len(formulas["Body"]), ".2f"), '%')
    print('# formulas containing subscripts (_): ', sub_count, ', ', format(100*sub_count/len(formulas["Body"]), ".2f"), '%')

def sum_integral(formulas):
    sum_count = 0
    integral_count = 0
    other_count = 0
    symbols = [r'\prod', r'\bigcup', r'\bigcap', r'\iint', r'\iiint', r'\iiiint', r'\iiiiint', r'\idotsint']
    for formula in zip(formulas["Body"]):
        if r'\sum' in formula[0]:
            sum_count += 1
        if r'\int' in formula[0]:
            integral_count += 1
        if any(sym in formula[0] for sym in symbols):
            other_count += 1

    print(r'# formulas containing sums (\sum): ', sum_count, ', ', format(100*sum_count/len(formulas["Body"]), ".2f"), '%')
    print(r'# formulas containing integrals (\int): ', integral_count, ', ', format(100*integral_count/len(formulas["Body"]), ".2f"), '%')
    print(r'# formulas containing others (\prod, \bigcup,\bigcup, \iint, ...): ', other_count, ', ', format(100*other_count/len(formulas["Body"]), ".2f"), '%')

def fractions(formulas):
    count = 0
    symbols = [r'\frac', r'\over', r'\cfrac']
    for formula in zip(formulas["Body"]):
        if any(sym in formula[0] for sym in symbols):
            count += 1
    print('# formulas containing fractions: ', count, ', ', format(100*count/len(formulas["Body"]), ".2f"), '%')

def analyze_formulas(database, table):
    DB = sqlite3.connect(database)
    formulas = pd.read_sql('select Body from "'+ table+'"', DB)
    DB.close()

    print("# formulas: ", len(formulas["Body"]), ', ', format(100*len(formulas["Body"])/len(formulas["Body"]), ".2f"), '%')

    equations(formulas)
    length(formulas, 0)
    length(formulas, 1)
    length(formulas, 2)
    length(formulas, 3)
    length(formulas, 4)
    length(formulas, 5)
    length(formulas, 6)
    min_length(formulas, 7)
    greek_letters(formulas)
    super_subscripts(formulas)
    sum_integral(formulas)
    fractions(formulas)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    #parser.add_argument("-d","--database",default= "../output/physics.db", help = "input database with LaTeX formulas")
    #parser.add_argument("-t", "--table", default="Formulas_Posts", help= "name of table in database")
    parser.add_argument("-d","--database",default= "../output/mathematics.db", help = "input database with LaTeX formulas")
    parser.add_argument("-t", "--table", default="Formulas_Posts", help= "name of table in database")
    args = parser.parse_args()

    analyze_formulas(args.database, args.table)
