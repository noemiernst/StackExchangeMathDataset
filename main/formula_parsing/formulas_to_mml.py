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
    formulas = pd.read_sql('select tex.FormulaId, tex.LaTeXBody from "'+ table +'" tex LEFT JOIN "' + table + 'MathML" ml ON ml.FormulaId = tex.FormulaId WHERE ml.ContentMathML IS NULL AND tex.Site="'+site+'"', DB)
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

        if len(sites) > 9:
            df = pd.DataFrame({"FormulaId": list(cmml.keys()), "Site": site, "ContentMathML": list(cmml.values())})
            write_table(database, table+"MathML", df)
            cmml = {}
            sites = []
    df = pd.DataFrame({"FormulaId": cmml.keys(), "Site": site, "ContentMathML": cmml.values()})
    write_table(database, table+"MathML", df)
    return cmml


def formulas_to_pmml(database, table, site):
    DB = sqlite3.connect(database)
    formulas = pd.read_sql('select tex.FormulaId, tex.LaTeXBody from "'+ table +'" tex LEFT JOIN "' + table + 'MathML" ml ON ml.FormulaId = tex.FormulaId WHERE ml.PresentationMathML IS NULL AND tex.Site="'+site+'"', DB)
    DB.close()

    pmml = {}
    sites = []
    for formula, body in zip(formulas["FormulaId"], formulas["LaTeXBody"]):
        use_shell = ('Windows' in platform.system())
        p2 = subprocess.Popen(
                ['latexmlmath', '--pmml=-', #'--preload=amsmath', '--preload=amsfonts',
                 '-'], shell=use_shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

        output, error = p2.communicate(input=body.encode())
        if error == b'':
            pmml[formula] = output
        else:
            pmml[formula] = ""
        sites.append(site)

        if len(sites) > 9:
            df = pd.DataFrame({"FormulaId": list(pmml.keys()), "Site": site, "PresentationMathML": list(pmml.values())})
            write_table(database, table+"MathML", df)
            pmml = {}
            sites = []
    df = pd.DataFrame({"FormulaId": pmml.keys(), "Site": site, "ContentMathML": pmml.values()})
    write_table(database, table+"MathML", df)
    return pmml

def formulas_to_both_ml(database, table, site):
    DB = sqlite3.connect(database)
    formulas = pd.read_sql('select tex.FormulaId, tex.LaTeXBody from "'+ table +'" tex LEFT JOIN "' + table + 'MathML" ml ON ml.FormulaId = tex.FormulaId WHERE ml.ContentMathML IS NULL AND ml.PresentationMathML IS NULL AND tex.Site="'+site+'"', DB)
    DB.close()

    ids = []
    cmml = []
    pmml = []
    sites = []
    for formula, body in zip(formulas["FormulaId"], formulas["LaTeXBody"]):
        use_shell = ('Windows' in platform.system())
        p2 = subprocess.Popen(
                ['latexmlmath', '--cmml=-', #'--preload=amsmath', '--preload=amsfonts',
                 '-'], shell=use_shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        output_c, error = p2.communicate(input=body.encode())
        if error != b'':
            output_c = ""

        p2 = subprocess.Popen(
                ['latexmlmath', '--pmml=-', #'--preload=amsmath', '--preload=amsfonts',
                 '-'], shell=use_shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        output_p, error = p2.communicate(input=body.encode())
        if error != b'':
            output_p = ""

        ids.append(formula)
        cmml.append(output_c)
        pmml.append(output_p)
        sites.append(site)

        if len(sites) > 9:
            df = pd.DataFrame({"FormulaId": ids, "Site": site, "ContentMathML": cmml, "PresentationMathML": pmml})
            write_table(database, table+"MathML", df)
            ids = []
            cmml = []
            pmml = []
            sites = []
    df = pd.DataFrame({"FormulaId": ids, "Site": site, "ContentMathML": cmml, "PresentationMathML": pmml})
    write_table(database, table+"MathML", df)
    return cmml
