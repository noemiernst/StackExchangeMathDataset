from context_processing.BOW import BOW
import os.path
try:
    import cPickle as pickle
except ImportError:
    import pickle
import sqlite3
import re
from dump_processing.DumpDownloader import DumpDownloader
import pandas as pd
import time
from dump_processing.helper import log
import resource

#TODO: for performance enhancement
#  tokenize words in between formulas and then just pick and choose for each formula until contex length is satisfied

def read_pickle(file):
    with open(file,"rb") as f:
        return pickle.load(f)

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
        return " ".join(before[-num_context_token:]) + " ".join(after[:num_context_token])

def calculate_idf(directories):
    bow = BOW()
    first = True

    for dir in directories:
        bow.corpus_from_pickles(dir, not first)
        first = False

    bow.vectorize_corpus()
    return bow

def write_context_table(site, contexts, database, table_name, if_exists='append', index=False):
    DB = sqlite3.connect(database)
    cursor = DB.cursor()

    cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='"+ table_name +"' ")

    #if the count is 1, then table exists
    if cursor.fetchone()[0]!=1 :
        cursor.execute("CREATE TABLE '" + table_name + "' ('Site' TEXT, 'FormulaId' INTEGER PRIMARY KEY, 'Context' TEXT)")

    ids = []
    cons = []
    for id, context in contexts.items():
        ids.append(int(id))
        cons.append(context)

    df = pd.DataFrame({"Site": [site] * len(ids), "FormulaId": ids, "Context": cons})

    df.to_sql(name=table_name, con=DB, if_exists=if_exists, index=index)
    DB.close()
    print("wrote ", len(df), " entries in table ", table_name, " of database ", database)

def posts_context(directory, x):
    # read text from pickles
    # read formulas for site from pickle
    questions = read_pickle(os.path.join(directory, "questiontext.pkl"))
    answers = read_pickle(os.path.join(directory, "answertext.pkl"))
    formulas_posts = read_pickle(os.path.join(directory, "formulasposts.pkl"))

    question_titles = {}
    posts = answers

    # for each post/comment
    #   text to corpus -> use function from BOW class? already reads text from pickles
    for id, [t, b] in questions.items():
        question_titles[id] = t
        posts[id] = b

    # for each formula (posts and comments)
    #   get context (x) around each formula
    # TODO: efficiency
    context = {}
    for formulaid, [postid, body, pos, inl] in formulas_posts.items():
        if pos == -1:
            context[formulaid] = formula_context(body, pos, inl, question_titles[postid], x)
            pass
        else:
            context[formulaid] = formula_context(body, pos, inl, posts[postid], x)
    return context

def comments_context(directory, x):
    # read text from pickles
    # read formulas for site from pickle
    comments = read_pickle(os.path.join(directory, "commenttext.pkl"))
    formulas_posts = read_pickle(os.path.join(directory, "formulascomments.pkl"))

    # for each formula (posts and comments)
    #   get context (x) around each formula
    # TODO: efficiency
    context = {}
    for formulaid, [commentid, body, pos, inl] in formulas_posts.items():
        context[formulaid] = formula_context(body, pos, inl, comments[commentid], x)

    return context

def context_main(sites, dump_directory, database, x, n):
    #bag_of_words = calculate_idf(directories)
    #ids, contexts = calculate_topn(directories, bag_of_words, n)

    #write_context_table(sites, ids, contexts, database)


    downloader = DumpDownloader()
    directories = [os.path.join(dump_directory, downloader.get_file_name(site)).replace(".7z", "/") for site in sites]

    print("Calculating idf values of all sites texts")
    start = time.time()
    bow = calculate_idf(directories)
    log("../output/statistics.log", "time calculating idf scores: "+ str(int((time.time()-start)/60)) +"min " + str(int((time.time()-start)%60)) + "sec")


    if_exists = "replace"
    for site, directory in zip(sites, directories):
        try:
            if not os.path.exists(directory):
                raise OSError
        except OSError:
            print(directory + " not found")

        # check if pickles are there -> error: suggest to run main again

        #   for each formula
        #    get context
        #    calculate top n context
        #   save in table in database (option for other table name)
        contexts = posts_context(directory, x)
        top_n_contexts = bow.get_top_n_tfidf(contexts, n)
        write_context_table(site, top_n_contexts, database, "FormulaContext", if_exists)

        if_exists = "append"

        contexts = comments_context(directory, x)
        top_n_contexts = bow.get_top_n_tfidf(contexts, n)
        write_context_table(site, top_n_contexts, database, "FormulaContext", if_exists)

    log("../output/statistics.log", "total execution time: "+ str(int((time.time()-start)/60)) +"min " + str(int((time.time()-start)%60)) + "sec")
    log("../output/statistics.log", "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")




# TODO:
#  check if all pkl files are there -> error: suggest to run main again
#  tabellen name selber definieren
#  n als alle terme

sites = ["ai"]
dump_directory = "../input/"

context_main(sites, dump_directory, "", 10, 3)
