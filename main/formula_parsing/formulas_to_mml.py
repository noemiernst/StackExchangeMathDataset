import sqlite3
import pandas as pd
import os
import sys
import time
import platform
import subprocess
from dump_processing.helper import write_table

def formulas_to_cmml(database, table, site):
    DB = sqlite3.connect(database)
    formulas = pd.read_sql('select tex.FormulaId, tex.LaTeXBody from "'+ table +'" tex LEFT JOIN "' + table + 'MathML" ml ON ml.FormulaId = tex.FormulaId WHERE ml.FormulaId IS NULL AND tex.Site="'+site+'"', DB)
    DB.close()

    cmml = {}
    sites = []
    for formula, body in zip(formulas["FormulaId"], formulas["LaTeXBody"]):
        use_shell = ('Windows' in platform.system())
        p2 = subprocess.Popen(
                ['latexmlmath', '--cmml=-', #'--preload=amsmath', '--preload=amsfonts',
                 '-'], shell=use_shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

        output, error = p2.communicate(input=body.encode())
        if error == b'':
            cmml[formula] = output
        else:
            cmml[formula] = ""
        sites.append(site)

        if len(sites) > 10:
            df = pd.DataFrame({"FormulaId": list(cmml.keys()), "Site": site, "ContentMathML": list(cmml.values())})
            write_table(database, table+"MathML", df)
            cmml = {}
            sites = []
    df = pd.DataFrame({"FormulaId": cmml.keys(), "Site": site, "ContentMathML": cmml.values()})
    write_table(database, table+"MathML", df)
    return cmml


#formulas_to_cmml("../../output/database.db", "FormulasPosts", "ai")
