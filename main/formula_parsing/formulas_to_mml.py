import sqlite3
import pandas as pd
import os
import sys
import time
import platform
import subprocess
from dump_processing.helper import write_table
from dump_processing.helper import update_table
from dump_processing.helper import progress_bar


def formulas_to_cmml(database, table, site):
    DB = sqlite3.connect(database)
    formulas = pd.read_sql('select tex.FormulaId, tex.LaTeXBody from "'+ table +'" tex LEFT JOIN "' + table + 'MathML" ml ON ml.FormulaId = tex.FormulaId WHERE ml.ContentMathML IS NULL AND tex.Site="'+site+'"', DB)
    DB.close()

    cmml = {}
    sites = []
    count = 0
    for formula, body in zip(formulas["FormulaId"], formulas["LaTeXBody"]):
        count += 1
        use_shell = ('Windows' in platform.system())
        p2 = subprocess.Popen(
                ['latexmlmath', '--cmml=-', #'--preload=amsmath', '--preload=amsfonts',
                 '-'], shell=use_shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

        output, error = p2.communicate(input=body.encode())
        if error == b'':
            cmml[formula] = output.decode("utf-8")
        else:
            cmml[formula] = ""
        sites.append(site)

        if len(sites) > 9:
            df = pd.DataFrame({"FormulaId": list(cmml.keys()), "Site": site, "ContentMathML": list(cmml.values())})
            update_table(database, table+"MathML", df, "FormulaId")
            cmml = {}
            sites = []
            progress_bar(count, len(formulas["FormulaId"]), "Formulas", 40)
    df = pd.DataFrame({"FormulaId": list(cmml.keys()), "Site": site, "ContentMathML": list(cmml.values())})
    update_table(database, table+"MathML", df, "FormulaId")
    progress_bar(count, len(formulas["FormulaId"]), "Formulas", 40)
    return cmml


def formulas_to_pmml(database, table, site):
    DB = sqlite3.connect(database)
    formulas = pd.read_sql('select tex.FormulaId, tex.LaTeXBody from "'+ table +'" tex LEFT JOIN "' + table + 'MathML" ml ON ml.FormulaId = tex.FormulaId WHERE ml.PresentationMathML IS NULL AND tex.Site="'+site+'"', DB)
    DB.close()

    pmml = {}
    sites = []
    count = 0
    for formula, body in zip(formulas["FormulaId"], formulas["LaTeXBody"]):
        count += 1
        use_shell = ('Windows' in platform.system())
        p2 = subprocess.Popen(
                ['latexmlmath', '--pmml=-', #'--preload=amsmath', '--preload=amsfonts',
                 '-'], shell=use_shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

        output, error = p2.communicate(input=body.encode())
        if error == b'':
            pmml[formula] = output.decode("utf-8")
        else:
            pmml[formula] = ""
        sites.append(site)

        if len(sites) > 9:
            df = pd.DataFrame({"FormulaId": list(pmml.keys()), "Site": site, "PresentationMathML": list(pmml.values())})
            update_table(database, table+"MathML", df, "FormulaId")
            pmml = {}
            sites = []
            progress_bar(count, len(formulas["FormulaId"]), "Formulas", 40)
    df = pd.DataFrame({"FormulaId": list(pmml.keys()), "Site": site, "PresentationMathML": list(pmml.values())})
    update_table(database, table+"MathML", df, "FormulaId")
    progress_bar(count, len(formulas["FormulaId"]), "Formulas", 40)
    return pmml

def formulas_to_both_ml(database, table, site):
    DB = sqlite3.connect(database)
    formulas = pd.read_sql('select tex.FormulaId, tex.LaTeXBody from "'+ table +'" tex LEFT JOIN "' + table + 'MathML" ml ON ml.FormulaId = tex.FormulaId WHERE (ml.ContentMathML IS NULL OR ml.PresentationMathML IS NULL) AND tex.Site="'+site+'"', DB)
    DB.close()

    ids = []
    cmml = []
    pmml = []
    sites = []
    count = 0
    for formula, body in zip(formulas["FormulaId"], formulas["LaTeXBody"]):
        count += 1
        use_shell = ('Windows' in platform.system())
        p2 = subprocess.Popen(
                ['latexmlmath', '--cmml=-', #'--preload=amsmath', '--preload=amsfonts',
                 '-'], shell=use_shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        output_c, error = p2.communicate(input=body.encode())
        if error != b'':
            output_c = ""
        else:
            output_c = output_c.decode("utf-8")

        p2 = subprocess.Popen(
                ['latexmlmath', '--pmml=-', #'--preload=amsmath', '--preload=amsfonts',
                 '-'], shell=use_shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        output_p, error = p2.communicate(input=body.encode())
        if error != b'':
            output_p = ""
        else:
            output_p = output_p.decode("utf-8")

        ids.append(formula)
        cmml.append(output_c)
        pmml.append(output_p)
        sites.append(site)

        if len(sites) > 9:
            df = pd.DataFrame({"FormulaId": ids, "Site": site, "ContentMathML": cmml, "PresentationMathML": pmml})
            update_table(database, table+"MathML", df, "FormulaId")
            ids = []
            cmml = []
            pmml = []
            sites = []
            progress_bar(count, len(formulas["FormulaId"]), "Formulas", 40)
    df = pd.DataFrame({"FormulaId": ids, "Site": site, "ContentMathML": cmml, "PresentationMathML": pmml})
    update_table(database, table+"MathML", df, "FormulaId")
    progress_bar(count, len(formulas["FormulaId"]), "Formulas", 40)
    return cmml
