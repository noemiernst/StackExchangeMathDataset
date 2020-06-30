import sqlite3
import pandas as pd

def formulas_to_tex(database, table, site, filename):
    DB = sqlite3.connect(database)
    formulas = pd.read_sql('select LaTeXBody from "'+ table +'" where Site="'+site+'"', DB)
    DB.close()

    data = r""

    with open(filename, 'w') as f:
        for formula in formulas["Body"]:
            f.write(r"$$" + formula + r"$$" + "\n")


formulas_to_tex("../../output/database.db", "FormulasPosts", "ai", "formulas.tex")
