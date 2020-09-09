try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import os.path
import sqlite3
import pandas as pd
from dump_processing.helper import write_table
from dump_processing.helper import log
import resource
from dump_processing.database import max_column_value
from dump_processing.LatexTokenizer import LatexTokenizer
from pathlib import Path
from dump_processing.DumpDownloader import DumpDownloader


def current_formula_id(database):
    return max(max_column_value(database, "FormulasPosts", "FormulaId"), max_column_value(database, "FormulasComments", "FormulaId")) + 1

def formula_token_length(formula):
    tokenizer = LatexTokenizer
    return len(tokenizer.tokenize(tokenizer, formula))

def formula_extr(text, site):
    if site in DumpDownloader.mhchem:
        mhchem = True
    else:
        mhchem = False
    formulas = []
    positions = []
    inline = []

    error = False
    if text.find('$') > -1:
        before,found,after = text.partition('$')
        position = len(before)
        while found:
            if after.find('$') > -1:
                while before.endswith('\\'):
                    before,found,after = after.partition('$')
                    position += len(before) + 1
                formula,found,after = after.partition('$')

                while formula.endswith('\\'):
                    formula_temp,found_temp,after = after.partition('$')
                    formula = formula + found + formula_temp
                if formula != '':
                    if found:
                        if mhchem:
                            if not formula.startswith(DumpDownloader.mhchem[site]):
                                formulas.append(formula)
                                positions.append(position)
                                inline.append(True)
                        else:
                            formulas.append(formula)
                            positions.append(position)
                            inline.append(True)
                    else:
                        error = True

                    before,found,after = after.partition('$')
                    position += len(formula) + len(before) + 2
                else:
                    formula,found,after = after.partition('$$')
                    while formula.endswith('\\'):
                        formula_temp,found_temp,after = ('$'+after).partition('$$')
                        formula = formula + "$" + formula_temp
                    if formula != '':
                        if found:
                            if mhchem:
                                if not formula.startswith(DumpDownloader.mhchem[site]):
                                    formulas.append(formula)
                                    positions.append(position)
                                    inline.append(False)
                            else:
                                formulas.append(formula)
                                positions.append(position)
                                inline.append(False)
                        else:
                            after = formula
                            error = True

                    before,found,after = after.partition('$')
                    position += len(formula) + len(before) + 4
            else:
                found = False
            if error:
                break
    return formulas, positions, inline, error
# operatoren: z.B. &amp, &lt, &gt

def formula_extr_special(text, delimiter):
    formulas = []
    positions = []
    inline = []

    error = False
    postion = 0

    if text.find(delimiter) > -1:
        before,found,after = text.partition(delimiter)
        position = len(before)
        while found:
            if text.find(delimiter) > -1:
                formula,found,after = after.partition(delimiter)

                if(formula.endswith('\\')):
                    formula_temp,found_temp,after = after.partition(delimiter)
                    formula = formula + found + formula_temp
                if formula != '':
                    if found:
                        formulas.append(formula)
                        positions.append(position)
                        inline.append(True)
                    else:
                        error = True

                    before,found,after = after.partition(delimiter)
                    position += len(formula) + len(before) + 2 * len(delimiter)

            if error:
                break
    return formulas, positions, inline, error

def questions_formula_processing(site_name, database, directory, context_length):
    DB = sqlite3.connect(database)
    questions = pd.read_sql('select * from "QuestionText" where Site="'+site_name+'"', DB)
    DB.close()

    Formulas = {"FormulaId": [], "Site": [], "PostId": [], "LaTeXBody":[], "TokenLength": [], "StartingPosition": [], "Inline": []}
    #formula_con={}
    error_count = 0
    starting_formula_index = current_formula_id(database)
    formula_index = 0

    # question processing (title and body)
    for question, title, body in zip(questions["QuestionId"], questions["Title"], questions["Body"]):
        if site_name not in DumpDownloader.special_delim:
            formulas_title, positions_title, _, error_title = formula_extr(title, site_name)
            formulas_body, positions_body, inline, error_body = formula_extr(body, site_name)
        else:
            formulas_title, positions_title, _, error_title = formula_extr_special(title, DumpDownloader.special_delim[site_name])
            formulas_body, positions_body, inline, error_body = formula_extr_special(body, DumpDownloader.special_delim[site_name])

        # parsing errors occur (total of ~6500) do not take formulas from "invalid" texts
        if not error_title and not error_body:
            for formula, position in zip(formulas_title, positions_title):
                Formulas["FormulaId"].append(starting_formula_index+formula_index)
                Formulas["Site"].append(site_name)
                Formulas["PostId"].append(int(question))
                Formulas["LaTeXBody"].append(formula)
                #Formulas["SLTBody"].append(get_mathml(formula))
                Formulas["TokenLength"].append(formula_token_length(formula))
                # position -1 for formulas in title
                Formulas["StartingPosition"].append(-1)
                Formulas["Inline"].append(True)
                #formula_con[starting_formula_index+formula_index] = [int(question), formula, position, inl]
                formula_index += 1
            for formula, position, inl in zip(formulas_body, positions_body, inline):
                Formulas["FormulaId"].append(starting_formula_index+formula_index)
                Formulas["Site"].append(site_name)
                Formulas["PostId"].append(int(question))
                Formulas["LaTeXBody"].append(formula)
                #Formulas["SLTBody"].append(get_mathml(formula))
                Formulas["TokenLength"].append(formula_token_length(formula))
                Formulas["StartingPosition"].append(position)
                Formulas["Inline"].append(inl)
                #formula_con[starting_formula_index+formula_index] = [int(question), formula, position, inl]
                formula_index += 1
        else:
            error_count += 1

        if(len(Formulas["FormulaId"])>1000000):
            df = pd.DataFrame({"FormulaId":Formulas["FormulaId"], "Site": Formulas["Site"], "PostId":Formulas["PostId"],"LaTeXBody":Formulas["LaTeXBody"], "TokenLength":Formulas["TokenLength"], "StartingPosition":Formulas["StartingPosition"], "Inline":Formulas["Inline"]})
            write_table(database, 'FormulasPosts', df)
            Formulas = {"FormulaId": [], "Site": [], "PostId": [], "LaTeXBody":[], "TokenLength": [], "StartingPosition": [], "Inline": []}
            df._clear_item_cache()

    df = pd.DataFrame({"FormulaId":Formulas["FormulaId"], "Site": Formulas["Site"], "PostId":Formulas["PostId"],"LaTeXBody":Formulas["LaTeXBody"], "TokenLength":Formulas["TokenLength"], "StartingPosition":Formulas["StartingPosition"], "Inline":Formulas["Inline"]})
    write_table(database, 'FormulasPosts', df)

    statistics_file = os.path.join(Path(database).parent, "statistics.log")
    log(statistics_file, str(formula_index) + " formulas parsed from questions")
    log(statistics_file, str(error_count) + " errors in parsing question formulas")
    log(statistics_file, "error rate parsing formulas from questions: " + format(error_count/(len(questions["QuestionId"]))*100, ".4f") + " %")


def answers_formula_processing(site_name, database, directory, context_length):
    DB = sqlite3.connect(database)
    answers = pd.read_sql('select * from "AnswerText" where Site="'+site_name+'"', DB)
    DB.close()

    Formulas = {"FormulaId": [], "Site": [], "PostId": [], "LaTeXBody":[], "TokenLength": [], "StartingPosition": [], "Inline": []}
    #formula_con = {}
    error_count = 0
    starting_formula_index = current_formula_id(database)
    formula_index = 0

    for answer, body in zip(answers["AnswerId"], answers["Body"]):
        if site_name not in DumpDownloader.special_delim:
            formulas, positions, inline, error = formula_extr(str(body), site_name)
        else:
            formulas, positions, inline, error = formula_extr_special(body, DumpDownloader.special_delim[site_name])
        if not error:
            for formula, position, inl in zip(formulas, positions, inline):
                Formulas["FormulaId"].append(int(starting_formula_index+formula_index))
                Formulas["Site"].append(site_name)
                Formulas["PostId"].append(int(answer))
                Formulas["LaTeXBody"].append(formula)
                #Formulas["SLTBody"].append(get_mathml(formula))
                Formulas["TokenLength"].append(formula_token_length(formula))
                Formulas["StartingPosition"].append(position)
                Formulas["Inline"].append(inl)
                #formula_con[starting_formula_index+formula_index] = [int(answer), formula, position, inl]
                formula_index += 1
        else:
            error_count += 1

        if(len(Formulas["FormulaId"])>1000000):
            df = pd.DataFrame({"FormulaId":Formulas["FormulaId"], "Site": Formulas["Site"], "PostId":Formulas["PostId"],"LaTeXBody":Formulas["LaTeXBody"], "TokenLength":Formulas["TokenLength"], "StartingPosition":Formulas["StartingPosition"], "Inline":Formulas["Inline"]})
            write_table(database, 'FormulasPosts', df, "append")
            Formulas = {"FormulaId": [], "Site": [], "PostId": [], "LaTeXBody":[], "TokenLength": [], "StartingPosition": [], "Inline": []}
            df._clear_item_cache()

    df = pd.DataFrame({"FormulaId":Formulas["FormulaId"], "Site": Formulas["Site"], "PostId":Formulas["PostId"],"LaTeXBody":Formulas["LaTeXBody"], "TokenLength":Formulas["TokenLength"], "StartingPosition":Formulas["StartingPosition"], "Inline":Formulas["Inline"]})
    write_table(database, 'FormulasPosts', df, "append")

    statistics_file = os.path.join(Path(database).parent, "statistics.log")
    log(statistics_file, str(formula_index) + " formulas parsed from answers")
    log(statistics_file, str(error_count) + " errors in parsing answer formulas")
    log(statistics_file, "error rate parsing formulas from answers: " + format(error_count/(len(answers["AnswerId"]))*100, ".4f") + " %")

def comments_formula_processing(site_name, database, directory, context_length):
    DB = sqlite3.connect(database)
    comments = pd.read_sql('select CommentId, Text from "Comments" where Site="'+site_name+'"', DB)
    DB.close()

    Formulas = {"FormulaId": [], "Site": [], "CommentId": [], "LaTeXBody":[], "TokenLength": [], "StartingPosition": [], "Inline": []}
    #formula_con = {}

    error_count = 0
    starting_formula_index = current_formula_id(database)
    formula_index = 0
    for comment, body in zip(comments["CommentId"], comments["Text"]):
        if site_name not in DumpDownloader.special_delim:
            formulas, positions, inline, error = formula_extr(body, site_name)
        else:
            formulas, positions, inline, error = formula_extr_special(body, DumpDownloader.special_delim[site_name])
        if not error:
            for formula, position, inl in zip(formulas, positions, inline):
                Formulas["FormulaId"].append(starting_formula_index+formula_index)
                Formulas["Site"].append(site_name)
                Formulas["CommentId"].append(comment)
                Formulas["LaTeXBody"].append(formula)
                #Formulas["SLTBody"].append(get_mathml(formula))
                Formulas["TokenLength"].append(formula_token_length(formula))
                Formulas["StartingPosition"].append(position)
                Formulas["Inline"].append(inl)
                #formula_con[starting_formula_index+formula_index] = [int(comment), formula, position, inl]
                formula_index += 1
        else:
            error_count += 1

        if(len(Formulas["FormulaId"])>1000000):
            df = pd.DataFrame({"FormulaId":Formulas["FormulaId"], "Site": Formulas["Site"],  "CommentId":Formulas["CommentId"],"LaTeXBody":Formulas["LaTeXBody"], "TokenLength":Formulas["TokenLength"], "StartingPosition":Formulas["StartingPosition"], "Inline":Formulas["Inline"]})
            write_table(database, 'FormulasComments', df, "append")
            Formulas = {"FormulaId": [], "Site": [], "CommentId": [], "LaTeXBody":[], "TokenLength": [], "StartingPosition": [], "Inline": []}
            df._clear_item_cache()

    df = pd.DataFrame({"FormulaId":Formulas["FormulaId"], "Site": Formulas["Site"], "CommentId":Formulas["CommentId"],"LaTeXBody":Formulas["LaTeXBody"], "TokenLength":Formulas["TokenLength"], "StartingPosition":Formulas["StartingPosition"], "Inline":Formulas["Inline"]})
    write_table(database, 'FormulasComments', df)

    statistics_file = os.path.join(Path(database).parent, "statistics.log")
    log(statistics_file, str(formula_index) + " formulas parsed from comments")
    log(statistics_file, str(error_count) + " errors in parsing comment formulas")
    log(statistics_file, "error rate parsing formulas from comments: " + format(error_count/(len(comments["CommentId"]))*100, ".4f") + " %")

def formula_processing(site_name, database, directory, context_length):
    #statistics_file = os.path.join(Path(database).parent, "statistics.log")
    questions_formula_processing(site_name, database, directory, context_length)
    #log(statistics_file, "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")
    answers_formula_processing(site_name, database, directory, context_length)
    #log(statistics_file, "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")
    comments_formula_processing(site_name, database, directory, context_length)
    #log(statistics_file, "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")
