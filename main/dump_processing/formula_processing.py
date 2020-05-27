try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import sqlite3
import pandas as pd
from dump_processing.helper import write_table
from dump_processing.helper import log
import resource
from dump_processing.database import max_column_value
from dump_processing.LatexTokenizer import LatexTokenizer
import re

def tokenize_words(text):
    # remove links
    text = re.sub('<a.*?>.*?</a>', ' ', text)
    # remove html tags
    text = re.sub('<.*?>',' ',text)
    # remove formulas
    text = re.sub(r'(\$\$.*?\$\$|\$.*?\$)', ' ', text)
    # tokenize
    words = re.compile(r'\w+')
    tokens = words.findall(text)
    return tokens

def formula_context(position, formula, inline, text, num_context_token):
    # if formula in question title
    if position == -1:
        return tokenize_words(text)
    # otherwise get context of some tokens before and after
    else:
        if inline:
            formula_length = len(formula)+2
        else:
            formula_length = len(formula)+4
        before = tokenize_words(text[:position])
        after = tokenize_words(text[position+formula_length:])
        # placeholder of formula in the middle
        return " ".join(before[-num_context_token:]) + " $$ " + " ".join(after[:num_context_token])

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

def questions_formula_processing(site_name, database):
    DB = sqlite3.connect(database)
    questions = pd.read_sql('select * from "QuestionsText"', DB)
    DB.close()

    Formulas = {"FormulaId": [], "Site": [], "PostId": [], "Body":[], "TokenLength": [], "StartingPosition": []}
    error_count = 0
    starting_formula_index = current_formula_id(database)
    formula_index = 0

    # question processing (title and body)
    for question, title, body in zip(questions["QuestionId"], questions["Title"], questions["Body"]):
        formulas_title, positions_title, inline, error_title = formula_extr(str(title))
        formulas_body, positions_body, inline, error_body = formula_extr(str(body))

        # parsing errors occur (total of ~6500) do not take formulas from "invalid" texts
        if not error_title and not error_body:
            for formula, position in zip(formulas_title, positions_title):
                Formulas["FormulaId"].append(starting_formula_index+formula_index)
                Formulas["Site"].append(site_name)
                Formulas["PostId"].append(int(question))
                Formulas["Body"].append(formula)
                Formulas["TokenLength"].append(formula_token_length(formula))
                # position -1 for formulas in title
                Formulas["StartingPosition"].append(-1)
                formula_index += 1
            for formula, position in zip(formulas_body, positions_body):
                Formulas["FormulaId"].append(starting_formula_index+formula_index)
                Formulas["Site"].append(site_name)
                Formulas["PostId"].append(int(question))
                Formulas["Body"].append(formula)
                Formulas["TokenLength"].append(formula_token_length(formula))
                Formulas["StartingPosition"].append(position)
                formula_index += 1
        else:
            error_count += 1

        if(len(Formulas["FormulaId"])>1000000):
            df = pd.DataFrame({"FormulaId":Formulas["FormulaId"], "Site": Formulas["Site"], "PostId":Formulas["PostId"],"Body":Formulas["Body"], "TokenLength":Formulas["TokenLength"], "StartingPosition":Formulas["StartingPosition"]})
            write_table(database, 'FormulasPosts', df)
            Formulas = {"FormulaId": [], "Site": [], "PostId": [], "Body":[], "TokenLength": [], "StartingPosition": []}
            df._clear_item_cache()

    df = pd.DataFrame({"FormulaId":Formulas["FormulaId"], "Site": Formulas["Site"], "PostId":Formulas["PostId"],"Body":Formulas["Body"], "TokenLength":Formulas["TokenLength"], "StartingPosition":Formulas["StartingPosition"]})
    write_table(database, 'FormulasPosts', df)

    log("../output/statistics.log", str(formula_index) + " formulas parsed from questions")
    log("../output/statistics.log", str(error_count) + " errors in parsing question formulas")
    log("../output/statistics.log", "error rate parsing formulas from questions: " + format(error_count/(len(questions["QuestionId"])*2)*100, ".4f") + " %")


def answers_formula_processing(site_name, database):
    DB = sqlite3.connect(database)
    answers = pd.read_sql('select * from "AnswersText"', DB)
    DB.close()

    Formulas = {"FormulaId": [], "Site": [], "PostId": [], "Body":[], "TokenLength": [], "StartingPosition": []}
    error_count = 0
    starting_formula_index = current_formula_id(database)
    formula_index = 0

    # answer processing (body)
    for answer, body in zip(answers["AnswerId"], answers["Body"]):
        formulas, positions, inline, error = formula_extr(str(body))
        if not error:
            for formula, position in zip(formulas, positions):
                Formulas["FormulaId"].append(int(starting_formula_index+formula_index))
                Formulas["Site"].append(site_name)
                Formulas["PostId"].append(int(answer))
                Formulas["Body"].append(formula)
                Formulas["TokenLength"].append(formula_token_length(formula))
                Formulas["StartingPosition"].append(position)
                formula_index += 1
        else:
            error_count += 1

        if(len(Formulas["FormulaId"])>1000000):
            df = pd.DataFrame({"FormulaId":Formulas["FormulaId"], "Site": Formulas["Site"], "PostId":Formulas["PostId"],"Body":Formulas["Body"], "TokenLength":Formulas["TokenLength"], "StartingPosition":Formulas["StartingPosition"]})
            write_table(database, 'FormulasPosts', df, "append")
            Formulas = {"FormulaId": [], "Site": [], "PostId": [], "Body":[], "TokenLength": [], "StartingPosition": []}
            df._clear_item_cache()

    df = pd.DataFrame({"FormulaId":Formulas["FormulaId"], "Site": Formulas["Site"], "PostId":Formulas["PostId"],"Body":Formulas["Body"], "TokenLength":Formulas["TokenLength"], "StartingPosition":Formulas["StartingPosition"]})
    write_table(database, 'FormulasPosts', df, "append")

    log("../output/statistics.log", str(formula_index) + " formulas parsed from answers")
    log("../output/statistics.log", str(error_count) + " errors in parsing answer formulas")
    log("../output/statistics.log", "error rate parsing formulas from answers: " + format(error_count/(len(answers["AnswerId"]))*100, ".4f") + " %")

def comments_formula_processing(site_name, database):
    DB = sqlite3.connect(database)
    comments = pd.read_sql('select CommentId, Text from "Comments"', DB)
    DB.close()

    Formulas = {"FormulaId": [], "Site": [], "CommentId": [], "Body":[], "TokenLength": [], "StartingPosition": []}

    error_count = 0
    starting_formula_index = current_formula_id(database)
    formula_index = 0

    for comment, body in zip(comments["CommentId"], comments["Text"]):
        formulas, positions, inline, error = formula_extr(body)
        if not error:
            for formula, position in zip(formulas, positions):
                Formulas["FormulaId"].append(starting_formula_index+formula_index)
                Formulas["Site"].append(site_name)
                Formulas["CommentId"].append(comment)
                Formulas["Body"].append(formula)
                Formulas["TokenLength"].append(formula_token_length(formula))
                Formulas["StartingPosition"].append(position)
                formula_index += 1
        else:
            error_count += 1

        if(len(Formulas["FormulaId"])>1000000):
            df = pd.DataFrame({"FormulaId":Formulas["FormulaId"], "Site": Formulas["Site"],  "CommentId":Formulas["CommentId"],"Body":Formulas["Body"], "TokenLength":Formulas["TokenLength"], "StartingPosition":Formulas["StartingPosition"]})
            write_table(database, 'FormulasComments', df, "append")
            Formulas = {"FormulaId": [], "Site": [], "CommentId": [], "Body":[], "TokenLength": [], "StartingPosition": []}
            df._clear_item_cache()

    df = pd.DataFrame({"FormulaId":Formulas["FormulaId"], "Site": Formulas["Site"], "CommentId":Formulas["CommentId"],"Body":Formulas["Body"], "TokenLength":Formulas["TokenLength"], "StartingPosition":Formulas["StartingPosition"]})
    write_table(database, 'FormulasComments', df)

    log("../output/statistics.log", str(formula_index) + " formulas parsed from comments")
    log("../output/statistics.log", str(error_count) + " errors in parsing comment formulas")
    log("../output/statistics.log", "error rate parsing formulas from comments: " + format(error_count/(len(comments["CommentId"]))*100, ".4f") + " %")

def formula_processing(site_name, database):
    questions_formula_processing(site_name, database)
    log("../output/statistics.log", "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")
    answers_formula_processing(site_name, database)
    log("../output/statistics.log", "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")
    comments_formula_processing(site_name, database)
    log("../output/statistics.log", "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")
