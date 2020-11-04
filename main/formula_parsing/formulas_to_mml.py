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
from threading import Thread
from formula_parsing.formulas_to_tree import slt
from formula_parsing.formulas_to_tree import opt


def threadFunc(call, body, cmml, id):
    p2 = subprocess.Popen(call, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    output, error = p2.communicate(input=body.encode())
    if error == b'':
        cmml[id] = output.decode("utf-8")
    else:
        cmml[id] = ""

def formulas_to_cmml(database, table, site, threads, tree):
    DB = sqlite3.connect(database)
    formulas = pd.read_sql('select tex.FormulaId, tex.LaTeXBody from "'+ table +'" tex LEFT JOIN "' + table + 'MathML" ml ON ml.FormulaId = tex.FormulaId WHERE ml.ContentMathML IS NULL AND tex.Site="'+site+'"', DB)
    DB.close()

    threaded = []
    cmml = {}
    count = 0
    th = {}
    for formula, body in zip(formulas["FormulaId"], formulas["LaTeXBody"]):
        count += 1
        th[formula] = Thread(target=threadFunc, args=(['latexmlmath', '--cmml=-', '-'], body, cmml, formula))
        threaded.append(formula)
        th[formula].start()

        if(len(threaded) >= threads):
            for formula in threaded:
                th[formula].join()
            threaded = []
            keys = [i[0] for i in sorted(cmml.items(), key=lambda item: item[0])]
            values = [i[1] for i in sorted(cmml.items(), key=lambda item: item[0])]
            if tree:
                opts = []
                for value in values:
                    opts.append(opt(value))
                df = pd.DataFrame({"FormulaId": keys, "Site": site, "ContentMathML": values, "OPT": opts})
            else:
                df = pd.DataFrame({"FormulaId": keys, "Site": site, "ContentMathML": values})
            update_table(database, table+"MathML", df, "FormulaId")
            cmml = {}
            progress_bar(count, len(formulas["FormulaId"]), "Formulas of " + table + " in " + site, 40)

    if count != 0:
        keys = [i[0] for i in sorted(cmml.items(), key=lambda item: item[0])]
        values = [i[1] for i in sorted(cmml.items(), key=lambda item: item[0])]
        if tree:
            opts = []
            for value in values:
                opts.append(opt(value))
            df = pd.DataFrame({"FormulaId": keys, "Site": site, "ContentMathML": values, "OPT": opts})
        else:
            df = pd.DataFrame({"FormulaId": keys, "Site": site, "ContentMathML": values})
        update_table(database, table+"MathML", df, "FormulaId")
        progress_bar(count, len(formulas["FormulaId"]), "Formulas of " + table + " in " + site, 40)
    return cmml


def formulas_to_pmml(database, table, site, threads, tree):
    DB = sqlite3.connect(database)
    formulas = pd.read_sql('select tex.FormulaId, tex.LaTeXBody from "'+ table +'" tex LEFT JOIN "' + table + 'MathML" ml ON ml.FormulaId = tex.FormulaId WHERE ml.PresentationMathML IS NULL AND tex.Site="'+site+'"', DB)
    DB.close()

    threaded = []
    pmml = {}
    count = 0
    th = {}
    for formula, body in zip(formulas["FormulaId"], formulas["LaTeXBody"]):
        count += 1
        th[formula] = Thread(target=threadFunc, args=(['latexmlmath', '--pmml=-', '-'], body, pmml, formula))
        threaded.append(formula)
        th[formula].start()

        if(len(threaded) >= threads):
            for formula in threaded:
                th[formula].join()
            threaded = []
            keys = [i[0] for i in sorted(pmml.items(), key=lambda item: item[0])]
            values = [i[1] for i in sorted(pmml.items(), key=lambda item: item[0])]
            if tree:
                slts = []
                for value in values:
                    slts.append(slt(value))
                df = pd.DataFrame({"FormulaId": keys, "Site": site, "PresentationMathML": values, "SLT": slts})
            else:
                df = pd.DataFrame({"FormulaId": keys, "Site": site, "PresentationMathML": values})
            update_table(database, table+"MathML", df, "FormulaId")
            pmml = {}
            progress_bar(count, len(formulas["FormulaId"]), "Formulas of " + table + " in " + site, 40)
    if count != 0:
        keys = [i[0] for i in sorted(pmml.items(), key=lambda item: item[0])]
        values = [i[1] for i in sorted(pmml.items(), key=lambda item: item[0])]
        if tree:
            slts = []
            for value in values:
                slts.append(slt(value))
            df = pd.DataFrame({"FormulaId": keys, "Site": site, "PresentationMathML": values, "SLT": slts})
        else:
            df = pd.DataFrame({"FormulaId": keys, "Site": site, "PresentationMathML": values})
        update_table(database, table+"MathML", df, "FormulaId")
        progress_bar(count, len(formulas["FormulaId"]), "Formulas of " + table + " in " + site, 40)
    return pmml

def formulas_to_both_ml(database, table, site, threads, tree):
    DB = sqlite3.connect(database)
    formulas = pd.read_sql('select tex.FormulaId, tex.LaTeXBody from "'+ table +'" tex LEFT JOIN "' + table + 'MathML" ml ON ml.FormulaId = tex.FormulaId WHERE (ml.ContentMathML IS NULL OR ml.PresentationMathML IS NULL) AND tex.Site="'+site+'"', DB)
    DB.close()

    ids = []
    threaded = []
    pmml = {}
    cmml = {}
    count = 0
    th_p = {}
    th_c = {}
    for formula, body in zip(formulas["FormulaId"], formulas["LaTeXBody"]):
        count += 1

        th_p[formula] = Thread(target=threadFunc, args=(['latexmlmath', '--cmml=-', '-'], body, cmml, formula))
        th_p[formula].start()

        th_c[formula] = Thread(target=threadFunc, args=(['latexmlmath', '--pmml=-', '-'], body, pmml, formula))
        th_c[formula].start()

        threaded.append(formula)
        ids.append(formula)

        if(len(threaded) >= (threads/2)):
            for formula in threaded:
                th_p[formula].join()
                th_c[formula].join()
            threaded = []
            cmml = [i[1] for i in sorted(cmml.items(), key=lambda item: item[0])]
            pmml = [i[1] for i in sorted(pmml.items(), key=lambda item: item[0])]
            ids = sorted(ids)
            if tree:
                slts = []
                for ml in pmml:
                    slts.append(slt(ml))
                opts = []
                for ml in cmml:
                    opts.append(opt(ml))
                df = pd.DataFrame({"FormulaId": ids, "Site": site, "ContentMathML": cmml, "OPT": opts, "PresentationMathML": pmml, "SLT": slts})
            else:
                df = pd.DataFrame({"FormulaId": ids, "Site": site, "ContentMathML": cmml, "PresentationMathML": pmml})
            update_table(database, table+"MathML", df, "FormulaId")
            ids = []
            pmml = {}
            cmml = {}
            progress_bar(count, len(formulas["FormulaId"]), "Formulas of " + table + " in " + site, 40)
    if count != 0:
        for formula in threaded:
            th_p[formula].join()
            th_c[formula].join()
        cmml = [i[1] for i in sorted(cmml.items(), key=lambda item: item[0])]
        pmml = [i[1] for i in sorted(pmml.items(), key=lambda item: item[0])]
        ids = sorted(ids)
        if tree:
            slts = []
            for ml in pmml:
                slts.append(slt(ml))
            opts = []
            for ml in cmml:
                opts.append(opt(ml))
            df = pd.DataFrame({"FormulaId": ids, "Site": site, "ContentMathML": cmml, "OPT": opts, "PresentationMathML": pmml, "SLT": slts})
        else:
            df = pd.DataFrame({"FormulaId": ids, "Site": site, "ContentMathML": cmml, "PresentationMathML": pmml})
        update_table(database, table+"MathML", df, "FormulaId")
        progress_bar(count, len(formulas["FormulaId"]), "Formulas of " + table + " in " + site, 40)
