try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import sqlite3
import pandas as pd
from helper import write_table
from helper import log
import resource
from database import max_column_value
from formula_context_processing import isolate_sentences
from formula_context_processing import context

def current_formula_id(database):
    return max(max_column_value(database, "FormulasPosts", "FormulaId"), max_column_value(database, "FormulasComments", "FormulaId")) + 1

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
                    if formula != '':
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

def questions_formula_processing(database):
    DB = sqlite3.connect(database)
    questions = pd.read_sql('select * from "QuestionsText"', DB)
    DB.close()

    Formulas = {"FormulaId": [], "PostId": [], "Body":[]}

    error_count = 0
    starting_formula_index = current_formula_id(database)
    formula_index = 0

    # question processing (title and body)
    for question, title, body in zip(questions["QuestionId"], questions["Title"], questions["Body"]):
        formulas_title, error_title = formula_extr(str(title))
        formulas_body, error_body = formula_extr(str(body))

        # parsing errors occur (total of ~6500) do not take formulas from "invalid" texts
        if not error_title and not error_body:
            for formula in formulas_title:
                Formulas["FormulaId"].append(starting_formula_index+formula_index)
                Formulas["PostId"].append(int(question))
                Formulas["Body"].append(formula)
                formula_index += 1
            for formula in formulas_body:
                Formulas["FormulaId"].append(starting_formula_index+formula_index)
                Formulas["PostId"].append(int(question))
                Formulas["Body"].append(formula)
                formula_index += 1
        else:
            error_count += 1

        if(len(Formulas["FormulaId"])>1000000):
            df = pd.DataFrame({"FormulaId":Formulas["FormulaId"],"PostId":Formulas["PostId"],"Body":Formulas["Body"]})
            write_table(database, 'FormulasPosts', df)
            Formulas = {"FormulaId": [], "PostId": [], "Body":[]}
            df._clear_item_cache()

    df = pd.DataFrame({"FormulaId":Formulas["FormulaId"],"PostId":Formulas["PostId"],"Body":Formulas["Body"]})
    write_table(database, 'FormulasPosts', df)

    log("../output/statistics.log", str(formula_index) + " formulas parsed from questions")
    log("../output/statistics.log", str(error_count) + " errors in parsing question formulas")
    log("../output/statistics.log", "error rate parsing formulas from questions: " + format(error_count/(len(questions["QuestionId"])*2)*100, ".4f") + " %")


def answers_formula_processing(database):
    DB = sqlite3.connect(database)
    answers = pd.read_sql('select * from "AnswersText"', DB)
    DB.close()

    Formulas = {"FormulaId": [], "PostId": [], "Body":[]}
    error_count = 0
    starting_formula_index = current_formula_id(database)
    formula_index = 0

    # answer processing (body)
    for answer, body in zip(answers["AnswerId"], answers["Body"]):
        formulas, error = formula_extr(str(body))
        if not error:
            for formula in formulas:
                Formulas["FormulaId"].append(int(starting_formula_index+formula_index))
                Formulas["PostId"].append(int(answer))
                Formulas["Body"].append(formula)
                formula_index += 1
        else:
            error_count += 1

        if(len(Formulas["FormulaId"])>1000000):
            df = pd.DataFrame({"FormulaId":Formulas["FormulaId"],"PostId":Formulas["PostId"],"Body":Formulas["Body"]})
            write_table(database, 'FormulasPosts', df, "append")
            Formulas = {"FormulaId": [], "PostId": [], "Body":[]}
            df._clear_item_cache()

    df = pd.DataFrame({"FormulaId":Formulas["FormulaId"],"PostId":Formulas["PostId"],"Body":Formulas["Body"]})
    write_table(database, 'FormulasPosts', df, "append")

    log("../output/statistics.log", str(formula_index) + " formulas parsed from answers")
    log("../output/statistics.log", str(error_count) + " errors in parsing answer formulas")
    log("../output/statistics.log", "error rate parsing formulas from answers: " + format(error_count/(len(answers["AnswerId"]))*100, ".4f") + " %")

def comments_formula_processing(database):
    DB = sqlite3.connect(database)
    comments = pd.read_sql('select CommentId, Text from "Comments"', DB)
    DB.close()

    Formulas = {"FormulaId": [], "CommentId": [], "Body":[]}

    error_count = 0
    starting_formula_index = current_formula_id(database)
    formula_index = 0

    for comment, body in zip(comments["CommentId"], comments["Text"]):
        formulas, error = formula_extr(body)
        if not error:
            for formula in formulas:
                Formulas["FormulaId"].append(starting_formula_index+formula_index)
                Formulas["CommentId"].append(comment)
                Formulas["Body"].append(formula)
                formula_index += 1
        else:
            error_count += 1

        if(len(Formulas["FormulaId"])>1000000):
            df = pd.DataFrame({"FormulaId":Formulas["FormulaId"],"CommentId":Formulas["CommentId"],"Body":Formulas["Body"]})
            write_table(database, 'FormulasComments', df, "append")
            Formulas = {"FormulaId": [], "CommentId": [], "Body":[]}
            df._clear_item_cache()

    df = pd.DataFrame({"FormulaId":Formulas["FormulaId"],"CommentId":Formulas["CommentId"],"Body":Formulas["Body"]})
    write_table(database, 'FormulasComments', df)

    log("../output/statistics.log", str(formula_index) + " formulas parsed from comments")
    log("../output/statistics.log", str(error_count) + " errors in parsing comment formulas")
    log("../output/statistics.log", "error rate parsing formulas from comments: " + format(error_count/(len(comments["CommentId"]))*100, ".4f") + " %")

def formula_processing(database):
    questions_formula_processing(database)
    log("../output/statistics.log", "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")
    answers_formula_processing(database)
    log("../output/statistics.log", "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")
    comments_formula_processing(database)
    log("../output/statistics.log", "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")
