try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
try:
    import cPickle as pickle
except ImportError:
    import pickle
import os.path
import sqlite3
import pandas as pd
from dump_processing.helper import write_table
from dump_processing.helper import log
import resource
from dump_processing.database import max_column_value
from dump_processing.LatexTokenizer import LatexTokenizer
import re
import time

# TODO: for performance enhancement
#  tokenize words in between formulas and then just pick and choose for each formula until contex length is satisfied

def context_pickle(formula_context_dict, directory, extend = True):
    if extend:
        with open(os.path.join(directory, "formulacontext.pkl"),"rb") as f:
            previous_formula_context_dict = pickle.load(f)
            formula_context_dict.update(previous_formula_context_dict)
    with open(os.path.join(directory, "formulacontext.pkl"),"wb") as f:
        pickle.dump(formula_context_dict,f)

def tokenize_words(text):
    # remove links and formulas
    text = re.sub(r'<a.*?>.*?</a>|\$\$.*?\$\$|\$.*?\$', ' ', text)
    # remove html tags
    text = re.sub('<.*?>',' ',text)
    # tokenize
    words = re.compile(r'\w+')
    tokens = words.findall(text)
    return tokens

def formula_context(formula, position, inline, text, num_context_token):
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

def questions_formula_processing(site_name, database, directory, context_length):
    questions = pd.read_pickle(os.path.join(directory, "questiontext.pkl"))

    Formulas = {"FormulaId": [], "Site": [], "PostId": [], "Body":[], "TokenLength": [], "StartingPosition": []}
    formula_con={}
    error_count = 0
    starting_formula_index = current_formula_id(database)
    formula_index = 0

    # question processing (title and body)
    for question, texts in questions.items():
        formulas_title, positions_title, _, error_title = formula_extr(texts[0])
        formulas_body, positions_body, inline, error_body = formula_extr(texts[1])

        # parsing errors occur (total of ~6500) do not take formulas from "invalid" texts
        if not error_title and not error_body:
            '''
            inbetween = []
            previous = 0
            for formula, position, inl in zip(formulas_body, positions_body, inline):
                inbetween.append(" ".join(tokenize_words(body[previous:position])))
                previous = position + len(formula) + 2
                if not inline:
                    previous += 2
            inbetween.append(" ".join(tokenize_words(body[positions_body[-1]:])))
            '''


            for formula, position in zip(formulas_title, positions_title):
                Formulas["FormulaId"].append(starting_formula_index+formula_index)
                Formulas["Site"].append(site_name)
                Formulas["PostId"].append(int(question))
                Formulas["Body"].append(formula)
                Formulas["TokenLength"].append(formula_token_length(formula))
                # position -1 for formulas in title
                Formulas["StartingPosition"].append(-1)
                #formula_con[starting_formula_index+formula_index] = formula_context(formula, -1, True, title, 0)
                formula_index += 1
            for formula, position, inl in zip(formulas_body, positions_body, inline):
                Formulas["FormulaId"].append(starting_formula_index+formula_index)
                Formulas["Site"].append(site_name)
                Formulas["PostId"].append(int(question))
                Formulas["Body"].append(formula)
                Formulas["TokenLength"].append(formula_token_length(formula))
                Formulas["StartingPosition"].append(position)
                #formula_con[starting_formula_index+formula_index] = formula_context(formula, position, inl, body, context_length)
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

    #context_pickle(formula_con,directory, False)

    log("../output/statistics.log", str(formula_index) + " formulas parsed from questions")
    log("../output/statistics.log", str(error_count) + " errors in parsing question formulas")
    log("../output/statistics.log", "error rate parsing formulas from questions: " + format(error_count/(len(questions)*2)*100, ".4f") + " %")


def answers_formula_processing(site_name, database, directory, context_length):
    answers = pd.read_pickle(os.path.join(directory, "answertext.pkl"))

    Formulas = {"FormulaId": [], "Site": [], "PostId": [], "Body":[], "TokenLength": [], "StartingPosition": []}
    formula_con = {}
    error_count = 0
    starting_formula_index = current_formula_id(database)
    formula_index = 0

    # answer processing (body)
    for answer, body in answers.items():
        formulas, positions, inline, error = formula_extr(str(body))
        if not error:
            for formula, position, inl in zip(formulas, positions, inline):
                Formulas["FormulaId"].append(int(starting_formula_index+formula_index))
                Formulas["Site"].append(site_name)
                Formulas["PostId"].append(int(answer))
                Formulas["Body"].append(formula)
                Formulas["TokenLength"].append(formula_token_length(formula))
                Formulas["StartingPosition"].append(position)
                #formula_con[starting_formula_index+formula_index] = formula_context(formula, position, inl, body, context_length)
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

    #context_pickle(formula_con,directory, True)

    log("../output/statistics.log", str(formula_index) + " formulas parsed from answers")
    log("../output/statistics.log", str(error_count) + " errors in parsing answer formulas")
    log("../output/statistics.log", "error rate parsing formulas from answers: " + format(error_count/(len(answers))*100, ".4f") + " %")

def comments_formula_processing(site_name, database, directory, context_length):
    comments = pd.read_pickle(os.path.join(directory, "commenttext.pkl"))

    Formulas = {"FormulaId": [], "Site": [], "CommentId": [], "Body":[], "TokenLength": [], "StartingPosition": []}
    formula_con = {}

    error_count = 0
    starting_formula_index = current_formula_id(database)
    formula_index = 0

    for comment, body in comments.items():
        formulas, positions, inline, error = formula_extr(body)
        if not error:
            for formula, position, inl in zip(formulas, positions, inline):
                Formulas["FormulaId"].append(starting_formula_index+formula_index)
                Formulas["Site"].append(site_name)
                Formulas["CommentId"].append(comment)
                Formulas["Body"].append(formula)
                Formulas["TokenLength"].append(formula_token_length(formula))
                Formulas["StartingPosition"].append(position)
                #formula_con[starting_formula_index+formula_index] = formula_context(formula, position, inl, body, context_length)
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

    #context_pickle(formula_con,directory, True)

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
