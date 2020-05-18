import re
from nltk.corpus import stopwords
import html_helper
import sqlite3
import pandas as pd
from helper import write_table
from helper import log
import argparse
import time
import resource

def get_formulas(text):
    formula = re.compile(r'(\$\$.*?\$\$|\$.*?\$)')
    return formula.findall(text)

def remove_formulas(text):
    return re.sub(r'(\$\$.*?\$\$|\$.*?\$)', '', text)

def remove_newlines(text):
    return text.replace("\n", " ")

def tokenize(text):
    words = re.compile(r'\w+')
    tokens = words.findall(text)
    return tokens

def remove_stopwords(tokens):
    en_stops = set(stopwords.words('english'))
    no_stopwords = []
    for word in tokens:
        if word not in en_stops:
            no_stopwords.append(word)
    return no_stopwords

def get_context(text):
    text = remove_newlines(text)
    text = html_helper.remove_images(text)
    text = html_helper.remove_links(text)
    paragraphs = html_helper.get_paragraphs(text)
    paragraphs = [remove_formulas(p) for p in paragraphs]
    paragraphs = [p for p in paragraphs if p]
    token_lists = [remove_stopwords(tokenize(p)) for p in paragraphs]
    context = []
    for list in token_lists:
        context.append(' '.join(str(x) for x in list))
    return context

def context_questions(database):
    DB = sqlite3.connect(database)
    questions = pd.read_sql('select * from "QuestionsText"', DB)
    DB.close()
    questionids = questions["QuestionId"].tolist()
    questiontexts = questions["Body"].tolist()
    SentenceContext = {"SentenceId": [], "PostId":[], "Sentence": []}
    df = pd.DataFrame({"SentenceId":SentenceContext["SentenceId"], "PostId": SentenceContext["PostId"],"Sentence":SentenceContext["Sentence"]})
    write_table(database, 'SentenceContext', df, "replace")

    index = 1
    for questionid, questiontext in zip(questionids, questiontexts):
        sentences = get_context(questiontext)
        for sentence in sentences:
            SentenceContext["SentenceId"].append(index)
            index += 1
            SentenceContext["PostId"].append(questionid)
            SentenceContext["Sentence"].append(sentence)

        if len(SentenceContext["SentenceId"]) > 100000:
            df = pd.DataFrame({"SentenceId":SentenceContext["SentenceId"], "PostId": SentenceContext["PostId"],"Sentence":SentenceContext["Sentence"]})
            write_table(database, 'SentenceContext', df)
            SentenceContext = {"SentenceId": [], "PostId":[], "Sentence": []}
            df._clear_item_cache()

    df = pd.DataFrame({"SentenceId":SentenceContext["SentenceId"], "PostId": SentenceContext["PostId"],"Sentence":SentenceContext["Sentence"]})
    write_table(database, 'SentenceContext', df)

def context_comments(database):
    pass

def context(database):
    start = time.time()
    context_questions(database)
    #context_comments(database)
    log("../output/statistics.log", "total execution time: "+ str(int((time.time()-start)/60)) +"min " + str(int((time.time()-start)%60)) + "sec")
    log("../output/statistics.log", "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d","--database",default= "../output/physics.db", help = "input database with LaTeX formulas")
    #parser.add_argument("-d","--database",default= "../output/mathematics.db", help = "input database with LaTeX formulas")
    args = parser.parse_args()

    context(args.database)



#with open('text', 'r') as file:
#    data = file.read().replace('\n', '')
#with open('text2', 'r') as file:
#    data2 = file.read().replace('\n', '')
#get_context(data)
#data2 = "<p>A few years ago I went to a museum, where there was a board with 2 bar magnets, on a pole each so they could rotate.\n" \
#        "If you rotated them so the lined up with the same poles (N) facing each other, they'd repel spinning until the south poles lined up, then they'd repel and spin so the north poles lined up and so. This was without any extra help, once you lined them up they would just keep spinning by their selves. How exactly is this possible that the 2 magnets kept producing kinetic energy?</p>"
#print(get_context(data2))
