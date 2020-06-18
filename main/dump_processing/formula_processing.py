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
from dump_processing.formula_tree_parse import get_slt


def current_formula_id(database):
    return max(max_column_value(database, "FormulasPosts", "FormulaId"), max_column_value(database, "FormulasComments", "FormulaId")) + 1

def formula_token_length(formula):
    tokenizer = LatexTokenizer
    return len(tokenizer.tokenize(tokenizer, formula))

def formula_extr(text):
    formulas = []
    positions = []
    inline = []

    error = False
    postion = 0

    if text.find('$') > -1:
        before,found,after = text.partition('$')
        position = len(before)
        while found:
            if text.find('$') > -1:
                formula,found,after = after.partition('$')

                if(formula.endswith('\\')):
                    formula_temp,found_temp,after = after.partition('$')
                    formula = formula + found + formula_temp
                if formula != '':
                    if found:
                        formulas.append(formula)
                        positions.append(position)
                        inline.append(True)
                    else:
                        error = True

                    before,found,after = after.partition('$')
                    position += len(formula) + len(before) + 2
                else:
                    formula,found,after = after.partition('$$')
                    if formula != '':
                        if found:
                            formulas.append(formula)
                            positions.append(position)
                            inline.append(False)
                        else:
                            after = formula
                            error = True

                    before,found,after = after.partition('$')
                    position += len(formula) + len(before) + 4

            if error:
                break
    return formulas, positions, inline, error

# operatoren: z.B. &amp, &lt, &gt

def questions_formula_processing(site_name, database, directory, context_length):
    DB = sqlite3.connect(database)
    questions = pd.read_sql('select * from "QuestionText" where Site="'+site_name+'"', DB)
    DB.close()

    Formulas = {"FormulaId": [], "Site": [], "PostId": [], "LaTeXBody":[], "SLTBody": [], "TokenLength": [], "StartingPosition": [], "Inline": []}
    #formula_con={}
    error_count = 0
    starting_formula_index = current_formula_id(database)
    formula_index = 0

    # question processing (title and body)
    for question, title, body in zip(questions["QuestionId"], questions["Title"], questions["Body"]):
        formulas_title, positions_title, _, error_title = formula_extr(title)
        formulas_body, positions_body, inline, error_body = formula_extr(body)

        # parsing errors occur (total of ~6500) do not take formulas from "invalid" texts
        if not error_title and not error_body:
            for formula, position in zip(formulas_title, positions_title):
                Formulas["FormulaId"].append(starting_formula_index+formula_index)
                Formulas["Site"].append(site_name)
                Formulas["PostId"].append(int(question))
                Formulas["LaTeXBody"].append(formula)
                Formulas["SLTBody"].append(get_slt(formula))
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
                Formulas["SLTBody"].append(get_slt(formula))
                Formulas["TokenLength"].append(formula_token_length(formula))
                Formulas["StartingPosition"].append(position)
                Formulas["Inline"].append(inl)
                #formula_con[starting_formula_index+formula_index] = [int(question), formula, position, inl]
                formula_index += 1
        else:
            error_count += 1

        if(len(Formulas["FormulaId"])>1000000):
            df = pd.DataFrame({"FormulaId":Formulas["FormulaId"], "Site": Formulas["Site"], "PostId":Formulas["PostId"],"LaTeXBody":Formulas["LaTeXBody"], "SLTBody":Formulas["SLTBody"], "TokenLength":Formulas["TokenLength"], "StartingPosition":Formulas["StartingPosition"], "Inline":Formulas["Inline"]})
            write_table(database, 'FormulasPosts', df)
            Formulas = {"FormulaId": [], "Site": [], "PostId": [], "LaTeXBody":[], "SLTBody": [], "TokenLength": [], "StartingPosition": [], "Inline": []}
            df._clear_item_cache()

    df = pd.DataFrame({"FormulaId":Formulas["FormulaId"], "Site": Formulas["Site"], "PostId":Formulas["PostId"],"LaTeXBody":Formulas["LaTeXBody"], "SLTBody":Formulas["SLTBody"], "TokenLength":Formulas["TokenLength"], "StartingPosition":Formulas["StartingPosition"], "Inline":Formulas["Inline"]})
    write_table(database, 'FormulasPosts', df)

    log("../output/statistics.log", str(formula_index) + " formulas parsed from questions")
    log("../output/statistics.log", str(error_count) + " errors in parsing question formulas")
    log("../output/statistics.log", "error rate parsing formulas from questions: " + format(error_count/(len(questions)*2)*100, ".4f") + " %")


def answers_formula_processing(site_name, database, directory, context_length):
    DB = sqlite3.connect(database)
    answers = pd.read_sql('select * from "AnswerText" where Site="'+site_name+'"', DB)
    DB.close()

    Formulas = {"FormulaId": [], "Site": [], "PostId": [], "LaTeXBody":[], "SLTBody": [], "TokenLength": [], "StartingPosition": [], "Inline": []}
    #formula_con = {}
    error_count = 0
    starting_formula_index = current_formula_id(database)
    formula_index = 0

    for answer, body in zip(answers["AnswerId"], answers["Body"]):
        formulas, positions, inline, error = formula_extr(str(body))
        if not error:
            for formula, position, inl in zip(formulas, positions, inline):
                Formulas["FormulaId"].append(int(starting_formula_index+formula_index))
                Formulas["Site"].append(site_name)
                Formulas["PostId"].append(int(answer))
                Formulas["LaTeXBody"].append(formula)
                Formulas["SLTBody"].append(get_slt(formula))
                Formulas["TokenLength"].append(formula_token_length(formula))
                Formulas["StartingPosition"].append(position)
                Formulas["Inline"].append(inl)
                #formula_con[starting_formula_index+formula_index] = [int(answer), formula, position, inl]
                formula_index += 1
        else:
            error_count += 1

        if(len(Formulas["FormulaId"])>1000000):
            df = pd.DataFrame({"FormulaId":Formulas["FormulaId"], "Site": Formulas["Site"], "PostId":Formulas["PostId"],"LaTeXBody":Formulas["LaTeXBody"], "SLTBody":Formulas["SLTBody"], "TokenLength":Formulas["TokenLength"], "StartingPosition":Formulas["StartingPosition"], "Inline":Formulas["Inline"]})
            write_table(database, 'FormulasPosts', df, "append")
            Formulas = {"FormulaId": [], "Site": [], "PostId": [], "LaTeXBody":[], "SLTBody": [], "TokenLength": [], "StartingPosition": [], "Inline": []}
            df._clear_item_cache()

    df = pd.DataFrame({"FormulaId":Formulas["FormulaId"], "Site": Formulas["Site"], "PostId":Formulas["PostId"],"LaTeXBody":Formulas["LaTeXBody"], "SLTBody":Formulas["SLTBody"], "TokenLength":Formulas["TokenLength"], "StartingPosition":Formulas["StartingPosition"], "Inline":Formulas["Inline"]})
    write_table(database, 'FormulasPosts', df, "append")

    log("../output/statistics.log", str(formula_index) + " formulas parsed from answers")
    log("../output/statistics.log", str(error_count) + " errors in parsing answer formulas")
    log("../output/statistics.log", "error rate parsing formulas from answers: " + format(error_count/(len(answers))*100, ".4f") + " %")

def comments_formula_processing(site_name, database, directory, context_length):
    DB = sqlite3.connect(database)
    comments = pd.read_sql('select CommentId, Text from "Comments" where Site="'+site_name+'"', DB)
    DB.close()

    Formulas = {"FormulaId": [], "Site": [], "CommentId": [], "LaTeXBody":[], "SLTBody": [], "TokenLength": [], "StartingPosition": [], "Inline": []}
    #formula_con = {}

    error_count = 0
    starting_formula_index = current_formula_id(database)
    formula_index = 0
    for comment, body in zip(comments["CommentId"], comments["Text"]):
        formulas, positions, inline, error = formula_extr(body)
        if not error:
            for formula, position, inl in zip(formulas, positions, inline):
                Formulas["FormulaId"].append(starting_formula_index+formula_index)
                Formulas["Site"].append(site_name)
                Formulas["CommentId"].append(comment)
                Formulas["LaTeXBody"].append(formula)
                Formulas["SLTBody"].append(get_slt(formula))
                Formulas["TokenLength"].append(formula_token_length(formula))
                Formulas["StartingPosition"].append(position)
                Formulas["Inline"].append(inl)
                #formula_con[starting_formula_index+formula_index] = [int(comment), formula, position, inl]
                formula_index += 1
        else:
            error_count += 1

        if(len(Formulas["FormulaId"])>1000000):
            df = pd.DataFrame({"FormulaId":Formulas["FormulaId"], "Site": Formulas["Site"],  "CommentId":Formulas["CommentId"],"Body":Formulas["Body"], "TokenLength":Formulas["TokenLength"], "StartingPosition":Formulas["StartingPosition"], "Inline":Formulas["Inline"]})
            write_table(database, 'FormulasComments', df, "append")
            Formulas = {"FormulaId": [], "Site": [], "CommentId": [], "LaTeXBody":[], "SLTBody": [], "TokenLength": [], "StartingPosition": [], "Inline": []}
            df._clear_item_cache()

    df = pd.DataFrame({"FormulaId":Formulas["FormulaId"], "Site": Formulas["Site"], "CommentId":Formulas["CommentId"],"LaTeXBody":Formulas["LaTeXBody"], "SLTBody":Formulas["SLTBody"], "TokenLength":Formulas["TokenLength"], "StartingPosition":Formulas["StartingPosition"], "Inline":Formulas["Inline"]})
    write_table(database, 'FormulasComments', df)

    log("../output/statistics.log", str(formula_index) + " formulas parsed from comments")
    log("../output/statistics.log", str(error_count) + " errors in parsing comment formulas")
    log("../output/statistics.log", "error rate parsing formulas from comments: " + format(error_count/(len(comments))*100, ".4f") + " %")

def formula_processing(site_name, database, directory, context_length):
    questions_formula_processing(site_name, database, directory, context_length)
    log("../output/statistics.log", "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")
    answers_formula_processing(site_name, database, directory, context_length)
    log("../output/statistics.log", "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")
    comments_formula_processing(site_name, database, directory, context_length)
    log("../output/statistics.log", "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")
