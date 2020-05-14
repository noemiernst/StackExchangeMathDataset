
#TODO: nlkt install prereqs und download (python nltk.download) https://www.nltk.org/data.html -> download punktmodel
from nltk.tokenize import sent_tokenize, word_tokenize
import re
import sqlite3
import pandas as pd
from helper import write_table
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer




def remove_html_tags(text):
    """Remove html tags from a string"""
    #TODO: check if any other parts with that pattern! (<.*?>)
    clean = re.compile('<.*?>')
    return re.sub(clean, ' ', text)

def isolate_sentences(text):
    text = remove_html_tags(text)
    return sent_tokenize(text)

def remove_stopwords(words):
    en_stops = set(stopwords.words('english'))
    no_stopwords = []
    for word in words:
        if word not in en_stops:
            no_stopwords.append(word)
    return no_stopwords

def remove_formulas(words):
    try:
        previous = words.index('$')
        formula = True
        while 1:
            #search for the item
            index = words.index('$', previous+1)
            if formula is True:
                for i in range(index-previous+1):
                    words.pop(previous)
                    formula = False
            else:
                formula = True
                previous = index

    except ValueError:
        #no more formulas
        pass


    try:
        previous = words.index('$$')
        formula = True
        while 1:
            #search for the item
            index = words.index('$$', previous+1)
            if formula is True:
                for i in range(index-previous+1):
                    words.pop(previous)
                    formula = False
            else:
                formula = True
                previous = index

    except ValueError:
        #no more formulas
        pass

    return words

def context(sentence):
    words = word_tokenize(sentence)
    words = remove_stopwords(words)
    words = remove_formulas(words)
    return  str(' '.join(str(x) for x in words))




def context_sentence(body, formula):
    sentences = isolate_sentences(body)
    context = []
    formula = "$"+ formula + "$"
    for sentence in sentences:
        if formula in sentence:
            context.append(sentence)
    return context

def formula_context_processing(database):
    DB = sqlite3.connect(database)
    questions = pd.read_sql('select * from "QuestionsText"', DB)
    formulas = pd.read_sql('select * from "FormulasPosts"', DB)
    DB.close()
    questionids = questions["QuestionId"].tolist()
    questiontexts = questions["Body"].tolist()
    questions = {}

    SentenceContext = {"FormulaId": [], "Sentences": []}

    for id, post, formula in zip(formulas["FormulaId"], formulas["PostId"], formulas["Body"]):
        index = questionids.index(post)
        sentences = context_sentence(questiontexts[index], formula)
        SentenceContext["FormulaId"].append(id)
        SentenceContext["Sentences"].append(sentences)

        if len(SentenceContext["FormulaId"]) > 10000:
            df = pd.DataFrame({"FormulaId":SentenceContext["FormulaId"],"Sentences":SentenceContext["Sentences"]})
            write_table(database, 'FormulaSentenceContext', df)
            SentenceContext = {"FormulaId": [], "Sentences": []}

    df = pd.DataFrame({"FormulaId":SentenceContext["FormulaId"],"Sentences":SentenceContext["Sentences"]})
    write_table(database, 'FormulaSentenceContext', df)
