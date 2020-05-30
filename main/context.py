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
    text = re.sub(r'\$\$.*?\$\$|\$.*?\$', ' ', text)
    text = re.sub(r'<a.*?>.*?</a>', ' ', text)
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
    DB.commit()

    ids = []
    cons = []
    for id, context in contexts.items():
        ids.append(int(id))
        cons.append(context)

    df = pd.DataFrame({"Site": [site] * len(ids), "FormulaId": ids, "Context": cons})

    df.to_sql(name=table_name, con=DB, if_exists=if_exists, index=index)
    DB.close()
    print("wrote ", len(df), " entries in table ", table_name, " of database ", database)

def get_words(text, formulas):
    pos_prev = 0
    words = []
    formula_indices = {}
    # formulas = {formulaid: [body, pos, inl]}
    ids_sorted = list(formulas.keys())
    list.sort(ids_sorted)
    for formulaid in ids_sorted:
        if formulas[formulaid][1] == -1:
            formula_indices[formulaid] = -1
        else:
            if formulas[formulaid][2]:
                formula_length = len(formulas[formulaid][0])+2
            else:
                formula_length = len(formulas[formulaid][0])+4
            words.extend(tokenize_words(text[pos_prev:formulas[formulaid][1]]))
            formula_indices[formulaid] = len(words)
            pos_prev = formulas[formulaid][1] + formula_length
    words.extend(tokenize_words(text[pos_prev:]))
    return words, formula_indices


def posts_context(directory, x):
    # read text from pickles
    # read formulas for site from pickle
    questions = read_pickle(os.path.join(directory, "questiontext.pkl"))
    posts = read_pickle(os.path.join(directory, "answertext.pkl"))
    formulas_posts = read_pickle(os.path.join(directory, "formulasposts.pkl"))

    question_titles = {}

    # for each post/comment
    #   text to corpus -> use function from BOW class? already reads text from pickles
    for id, [t, b] in questions.items():
        question_titles[id] = t
        posts[id] = b

    # for each formula (posts and comments)
    #   get context (x) around each formula
    # TODO: efficiency
    context = {}
    posts_formulas = {}
    for formulaid, [postid, body, pos, inl] in formulas_posts.items():
        if postid in posts_formulas:
            posts_formulas[postid].update({formulaid: [body, pos, inl]})
        else:
            posts_formulas[postid] = {formulaid: [body, pos, inl]}

    for postid, formulas in posts_formulas.items():
        # process post with formula positions

        words, formula_indices = get_words(posts[postid], formulas)

        for formulaid, index in formula_indices.items():
            if index == -1:
                context[formulaid] = tokenize_words(question_titles[postid])
            else:
                beg = index - x
                end = index + x
                if index < x:
                    beg = 0
                if (index + x) > len(words):
                    end = len(words)
                context[formulaid] = " ".join(words[beg:end])

    #for formulaid, [postid, body, pos, inl] in formulas_posts.items():
    #    if pos == -1:
    #        context[formulaid] = formula_context(body, pos, inl, question_titles[postid], x)
    #    else:
    #        context[formulaid] = formula_context(body, pos, inl, posts[postid], x)
    return context

def comments_context(directory, x):
    # read text from pickles
    # read formulas for site from pickle
    comments = read_pickle(os.path.join(directory, "commenttext.pkl"))
    formulas_comments = read_pickle(os.path.join(directory, "formulascomments.pkl"))

    # for each formula (posts and comments)
    #   get context (x) around each formula
    # TODO: efficiency
    context = {}
    comments_formulas = {}
    for formulaid, [commentid, body, pos, inl] in formulas_comments.items():
        if commentid in comments_formulas:
            comments_formulas[commentid].update({formulaid: [body, pos, inl]})
        else:
            comments_formulas[commentid] = {formulaid: [body, pos, inl]}

    for commentid, formulas in comments_formulas.items():
        # process post with formula positions
        words, formula_indices = get_words(comments[commentid], formulas)
        for formulaid, index in formula_indices.items():
            beg = index - x
            end = index + x
            if index < x:
                beg = 0
            if (index + x) > len(words):
                end = len(words)
            context[formulaid] = " ".join(words[beg:end])
    #context = {}
    #for formulaid, [commentid, body, pos, inl] in formulas_posts.items():
    #    context[formulaid] = formula_context(body, pos, inl, comments[commentid], x)

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
        t1 = time.time()
        top_n_contexts = bow.get_top_n_tfidf(contexts, n)
        log("../output/statistics.log", "time for contexts posts: "+ str(int((time.time()-t1)/60)) +"min " + str(int((time.time()-t1)%60)) + "sec")

        write_context_table(site, top_n_contexts, database, "FormulaContext", if_exists)

        if_exists = "append"

        contexts = comments_context(directory, x)
        t1 = time.time()
        top_n_contexts = bow.get_top_n_tfidf(contexts, n)
        log("../output/statistics.log", "time for contexts comments: "+ str(int((time.time()-t1)/60)) +"min " + str(int((time.time()-t1)%60)) + "sec")
        write_context_table(site, top_n_contexts, database, "FormulaContext", if_exists)

    log("../output/statistics.log", "total execution time: "+ str(int((time.time()-start)/60)) +"min " + str(int((time.time()-start)%60)) + "sec")
    log("../output/statistics.log", "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")




# TODO:
#  check if all pkl files are there -> error: suggest to run main again
#  tabellen name selber definieren
#  n als alle terme
#  nutzer kann max_df = 0.75, min_df = 2, max_features=5000 ändern in BOW

sites = ["ai"]
dump_directory = "../input/"
database = '../output/database.db'

context_main(sites, dump_directory, database, 10, 3)
