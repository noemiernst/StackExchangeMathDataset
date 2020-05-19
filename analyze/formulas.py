import latex2mathml
import argparse
import sqlite3
import pandas as pd
from Histogram import Histogram
from helper import log

def equations(formulas):
    count = 0
    for formula in formulas:
        if '=' in formula:
            count += 1
    log("../output/analysis.log", '# equations: '+ str(count)+ ', '+ format(100*count/len(formulas), ".2f")+ '%'+ "  (formulas containing '=')")

def length(formulas, length):
    count = 0
    for formula in formulas:
        if len(formula) == length:
            count += 1
    log("../output/analysis.log", '# formulas of length '+ str(length)+ ': '+ str(count)+ ', '+ format(100*count/len(formulas), ".2f")+ '%')

def min_length(formulas, length):
    count = 0
    for formula in formulas:
        if len(formula) >= length:
            count += 1
    log("../output/analysis.log", '# formulas of length >= '+ str(length)+ ': '+ str(count)+ ', '+ format(100*count/len(formulas), ".2f")+ '%')

def greek_letters(formulas):
    count = 0
    symbols = [r'\alpha', r'\beta', r'\gamma', r'\delta', r'\epsilon', r'\zeta', r'\eta', r'\theta', r'\iota',
               r'\kappa', r'\lambda', r'\mu', r'\nu', r'\xi', r'\omicron', r'\pi', r'\rho', r'\sigma', r'\tau',
               r'\upsilon', r'\phi', r'\chi', r'\psi', r'\omega']
    for formula in formulas:
        f = formula.lower()
        if any(sym in f for sym in symbols):
            count += 1
    log("../output/analysis.log", '# formulas containing greek letters: '+ str(count)+ ', '+ format(100*count/len(formulas), ".2f")+ '%')


def super_subscripts(formulas):
    super_count = 0
    sub_count = 0
    for formula in formulas:
        if '^' in formula:
            super_count += 1
        if '_' in formula[0]:
            sub_count += 1
    log("../output/analysis.log", '# formulas containing superscripts (^): '+ str(super_count)+ ', '+ format(100*super_count/len(formulas), ".2f")+ '%')
    log("../output/analysis.log", '# formulas containing subscripts (_): '+ str(sub_count)+ ', '+ format(100*sub_count/len(formulas), ".2f")+ '%')

def sum_integral(formulas):
    sum_count = 0
    integral_count = 0
    other_count = 0
    symbols = [r'\prod', r'\bigcup', r'\bigcap', r'\iint', r'\iiint', r'\iiiint', r'\iiiiint', r'\idotsint']
    for formula in formulas:
        if r'\sum' in formula:
            sum_count += 1
        if r'\int' in formula:
            integral_count += 1
        if any(sym in formula for sym in symbols):
            other_count += 1

    log("../output/analysis.log", r'# formulas containing sums (\sum): '+ str(sum_count)+ ', '+ format(100*sum_count/len(formulas), ".2f")+ '%')
    log("../output/analysis.log", r'# formulas containing integrals (\int): '+ str(integral_count)+ ', '+ format(100*integral_count/len(formulas), ".2f")+ '%')
    log("../output/analysis.log", r'# formulas containing others (\prod, \bigcup,\bigcup, \iint, ...): '+ str(other_count)+ ', '+ format(100*other_count/len(formulas), ".2f")+ '%')

def fractions(formulas):
    count = 0
    symbols = [r'\frac', r'\over', r'\cfrac']
    for formula in formulas:
        if any(sym in formula for sym in symbols):
            count += 1
    log("../output/analysis.log", '# formulas containing fractions: '+ str(count)+ ', '+ format(100*count/len(formulas), ".2f")+ '%')

def analyze_formulas(database, table):
    DB = sqlite3.connect(database)
    formulas = (pd.read_sql('select Body from "'+ table+'"', DB))["Body"].to_list()
    DB.close()

    log("../output/analysis.log", "# formulas: "+ str(len(formulas))+ ', '+ format(100*len(formulas)/len(formulas), ".2f")+ '%')

    equations(formulas)
    #length(formulas, 0)
    #length(formulas, 1)
    #length(formulas, 2)
    #length(formulas, 3)
    #length(formulas, 4)
    #length(formulas, 5)
    #length(formulas, 6)
    #min_length(formulas, 7)
    greek_letters(formulas)
    super_subscripts(formulas)
    sum_integral(formulas)
    fractions(formulas)

    Histogram.create_length_distribution(Histogram, formulas)
    Histogram.create_token_length_distribution(Histogram, formulas)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d","--database",default= "../output/physics.db", help = "input database with LaTeX formulas")
    parser.add_argument("-t", "--table", default="FormulasPosts", help= "name of table in database")
    #parser.add_argument("-d","--database",default= "../output/mathematics.db", help = "input database with LaTeX formulas")
    #parser.add_argument("-t", "--table", default="FormulasPosts", help= "name of table in database")
    args = parser.parse_args()

    analyze_formulas(args.database, args.table)
