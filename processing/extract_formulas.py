try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import sqlite3
import pandas as pd
from processing.helper import write_table
from processing.helper import log

def formula_extr(text):
    formulas = []

    error = False
    if text.find('$') > -1:
        _,found,after = text.partition('$')
        while found:
            if text.find('$') > -1:
                formula,found,after = after.partition('$')

                if(formula.endswith('\\')):
                    formula_temp,found_temp,after = after.partition('$')
                    formula = formula + found + formula_temp
                if formula != '':
                    if found:
                        formulas.append(formula)
                    else:
                        error = True

                    _,found,after = after.partition('$')
                else:
                    formula,found,after = after.partition('$$')
                    if found:
                        formulas.append(formula)
                    else:
                        after = formula
                        error = True

                    _,found,after = after.partition('$')
            if error:
                break
    return formulas, error

# operatoren: z.B. &amp, &lt, &gt

def posts_formula_processing(database, starting_formula_index):
    DB = sqlite3.connect(database)
    questions = pd.read_sql('select * from "QuestionsText"', DB)
    answers = pd.read_sql('select * from "AnswersText"', DB)
    DB.close()

    Formulas = {"FormulaId": [], "PostId": [], "Body":[]}
    error_count = 0

    # question processing (title and body)
    for question, title, body in zip(questions["QuestionId"], questions["Title"], questions["Body"]):
        formulas_title, error_title = formula_extr(str(title))
        formulas_body, error_body = formula_extr(str(body))
        # parsing errors occur (total of ~6500) do not take formulas from "invalid" texts
        if not error_title and not error_body:
            for formula in formulas_title:
                Formulas["FormulaId"].append(starting_formula_index)
                Formulas["PostId"].append(int(question))
                Formulas["Body"].append(formula)
                starting_formula_index += 1
            for formula in formulas_body:
                Formulas["FormulaId"].append(starting_formula_index)
                Formulas["PostId"].append(int(question))
                Formulas["Body"].append(formula)
                starting_formula_index += 1
        else:
            error_count += 1

    # answer processing (body)
    for answer, body in zip(answers["AnswerId"], answers["Body"]):
        formulas, error = formula_extr(str(body))
        if not error:
            for formula in formulas:
                Formulas["FormulaId"].append(int(starting_formula_index))
                Formulas["PostId"].append(int(answer))
                Formulas["Body"].append(formula)
                starting_formula_index += 1
        else:
            error_count += 1

    df = pd.DataFrame({"FormulaId":Formulas["FormulaId"],"PostId":Formulas["PostId"],"Body":Formulas["Body"]})
    write_table(database, 'Formulas_Posts', df)
    return starting_formula_index, error_count

def comments_formula_processing(database, starting_formula_index):
    DB = sqlite3.connect(database)
    comments = pd.read_sql('select * from "Comments"', DB)
    DB.close()

    Formulas = {"FormulaId": [], "CommentId": [], "Body":[]}
    error_count = 0

    for comment, body in zip(comments["CommentId"], comments["Text"]):
        formulas, error = formula_extr(body)
        if not error:
            for formula in formulas:
                Formulas["FormulaId"].append(starting_formula_index)
                Formulas["CommentId"].append(comment)
                Formulas["Body"].append(formula)
                starting_formula_index += 1
        else:
            error_count += 1

    df = pd.DataFrame({"FormulaId":Formulas["FormulaId"],"CommentId":Formulas["CommentId"],"Body":Formulas["Body"]})
    write_table(database, 'Formulas_Comments', df)
    return starting_formula_index, error_count

def formula_processing(database):
    index, error_count_posts = posts_formula_processing(database, starting_formula_index=1)
    log("../output/statistics.log", "# " + str(error_count_posts) + " errors in parsing posts")
    index, error_count_comments = comments_formula_processing(database, starting_formula_index=index)
    log("../output/statistics.log", "# " + str(error_count_comments) + " errors in parsing comments")
