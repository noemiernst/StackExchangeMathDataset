from context_processing.BOW import BOW
import os.path
import sqlite3
import re
from dump_processing.DumpDownloader import DumpDownloader
import pandas as pd
import time
from dump_processing.helper import log
import resource
import string
import sys
import argparse
import context_processing.html_helper

def tokenize_words(text):
    # remove links and formulas
    text = re.sub(r'\$\$.*?\$\$|\$.*?\$', ' ', text)
    # remove html tags
    text, strong, em = context_processing.html_helper.clean_html(text)
    # tokenize
    text = text.split()
    table = str.maketrans('', '', string.punctuation)
    text =  [(w.translate(table)).lower() for w in text]
    #stop_words = set(stopwords.words('english'))
    #text = [w for w in text if not w in stop_words]
    return text, strong, em

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
        before, b_strong, b_em = tokenize_words(text[:position])
        after, a_strong, a_em = tokenize_words(text[position+formula_length:])
        # placeholder of formula in the middle
        return " ".join(before[-num_context_token:]) + " ".join(after[:num_context_token]), b_strong + a_strong, b_em + a_em

def calculate_idf(sites, directories, database):
    bow = BOW()
    first = True

    for site, dir in zip(sites, directories):
        bow.corpus_from_database(dir, database, site, not first)
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
    strong = []
    emphasized = []
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
            w, s, e = tokenize_words(text[pos_prev:formulas[formulaid][1]])
            words.extend(w)
            strong.extend(s)
            emphasized.extend(e)
            formula_indices[formulaid] = len(words)
            pos_prev = formulas[formulaid][1] + formula_length
    w, s, e = tokenize_words(text[pos_prev:])
    words.extend(w)
    strong.extend(s)
    emphasized.extend(e)
    return words, formula_indices, strong, emphasized


def posts_context(directory, database, site_name, x, all):
    DB = sqlite3.connect(database)
    answers = pd.read_sql('select AnswerId, Body from "AnswerText" where Site="'+site_name+'"', DB)
    questions = pd.read_sql('select QuestionId, Title, Body from "QuestionText" where Site="'+site_name+'"', DB)
    formulas_posts = pd.read_sql('select FormulaId, PostId, Body, StartingPosition, Inline from "FormulasPosts" where Site="'+site_name+'"', DB)
    DB.close()

    question_titles = {}
    posts = {}

    for id, b in zip(answers["AnswerId"], answers["Body"]):
        posts[id] = b
    answers.pop("AnswerId")
    answers.pop("Body")

    # for each post/comment
    for id, t, b in zip(questions["QuestionId"], questions["Title"], questions["Body"]):
        question_titles[id] = t
        posts[id] = b
    questions.pop("QuestionId")
    questions.pop("Body")
    questions.pop("Title")

    # for each formula (posts and comments)
    #   get context (x) around each formula
    # TODO: efficiency
    context = {}
    posts_formulas = {}
    for formulaid, postid, body, pos, inl in zip(formulas_posts["FormulaId"],formulas_posts["PostId"],formulas_posts["Body"],formulas_posts["StartingPosition"],formulas_posts["Inline"]):
        if postid in posts_formulas:
            posts_formulas[postid].update({formulaid: [body, pos, inl]})
        else:
            posts_formulas[postid] = {formulaid: [body, pos, inl]}
    formulas_posts.pop("FormulaId")
    formulas_posts.pop("PostId")
    formulas_posts.pop("Body")
    formulas_posts.pop("StartingPosition")
    formulas_posts.pop("Inline")

    docs = {}

    for postid, formulas in posts_formulas.items():
        # process post with formula positions

        words, formula_indices, strong, emphasized = get_words(posts[postid], formulas)
        docs[postid] = " ".join(words)
        print(strong)
        print(emphasized)
        d = {}
        for formulaid, index in formula_indices.items():
            if index == -1:
                w, s, e = tokenize_words(question_titles[postid])
                d[formulaid] = w
            else:
                if all:
                    d[formulaid] = words
                else:
                    beg = index - x
                    end = index + x
                    if index < x:
                        beg = 0
                    if (index + x) > len(words):
                        end = len(words)
                    d[formulaid] = words[beg:end]
        context[postid] = d

    #for formulaid, [postid, body, pos, inl] in formulas_posts.items():
    #    if pos == -1:
    #        context[formulaid] = formula_context(body, pos, inl, question_titles[postid], x)
    #    else:
    #        context[formulaid] = formula_context(body, pos, inl, posts[postid], x)
    return context, docs

def comments_context(directory, database, site_name, x, all):
    DB = sqlite3.connect(database)
    comments = pd.read_sql('select CommentId, Text from "Comments" where Site="'+site_name+'"', DB)
    formulas_comments = pd.read_sql('select FormulaId, CommentId, Body, StartingPosition, Inline from "FormulasComments" where Site="'+site_name+'"', DB)
    DB.close()

    comments_dict = {}

    for id, b in zip(comments["CommentId"], comments["Text"]):
        comments_dict[id] = b
    comments.pop("CommentId")
    comments.pop("Text")

    # for each formula (posts and comments)
    #   get context (x) around each formula
    # TODO: efficiency
    context = {}
    comments_formulas = {}
    for formulaid, commentid, body, pos, inl in zip(formulas_comments["FormulaId"],formulas_comments["CommentId"],formulas_comments["Body"],formulas_comments["StartingPosition"],formulas_comments["Inline"]):
        if commentid in comments_formulas:
            comments_formulas[commentid].update({formulaid: [body, pos, inl]})
        else:
            comments_formulas[commentid] = {formulaid: [body, pos, inl]}
    formulas_comments.pop("FormulaId")
    formulas_comments.pop("CommentId")
    formulas_comments.pop("Body")
    formulas_comments.pop("StartingPosition")
    formulas_comments.pop("Inline")

    docs = {}

    for commentid, formulas in comments_formulas.items():
        # process post with formula positions
        words, formula_indices, strong, emphasized = get_words(comments_dict[commentid], formulas)
        docs[commentid] = " ".join(words)
        d = {}
        for formulaid, index in formula_indices.items():
            if all:
                d[formulaid] = words
            else:
                beg = index - x
                end = index + x
                if index < x:
                    beg = 0
                if (index + x) > len(words):
                    end = len(words)
                d[formulaid] = words[beg:end]
        context[commentid] = d
    #context = {}
    #for formulaid, [commentid, body, pos, inl] in formulas_posts.items():
    #    context[formulaid] = formula_context(body, pos, inl, comments[commentid], x)

    return context, docs

def context_main(filename_dumps, dump_directory, database, x, n, corpus, tablename, tfidf, all):
    start = time.time()
    with open(filename_dumps) as f:
        sites = [line.rstrip() for line in f if line is not ""]
    downloader = DumpDownloader()
    directories = [os.path.join(dump_directory, downloader.get_file_name(site)).replace(".7z", "/") for site in sites]

    if all == 'yes':
        all = True
    else:
        all = False
    if tfidf== 'yes':
        tfidf = True
    else:
        tfidf=False

    if not all:
        try:
            if not ((corpus == "all") | (corpus == "individual")):
                raise ValueError
        except ValueError:
            sys.exit("option for --corpus must be 'all' or 'individual'")
        if corpus == "all":
            print("Calculating idf values of all sites texts")
            t1 = time.time()
            bow = calculate_idf(sites, directories, database)
            log("../output/statistics.log", "time calculating idf scores: "+ str(int((time.time()-t1)/60)) +"min " + str(int((time.time()-t1)%60)) + "sec")


    if_exists = "replace"
    for site, directory in zip(sites, directories):
        try:
            if not os.path.exists(directory):
                raise OSError
        except OSError:
            print(directory + " not found")

        if (corpus == "individual") and not all:
            print("Calculating idf values of texts of site "+ site)
            t1 = time.time()
            bow = calculate_idf([site], directories, database)
            log("../output/statistics.log", "time calculating idf scores: "+ str(int((time.time()-t1)/60)) +"min " + str(int((time.time()-t1)%60)) + "sec")


        #   for each formula
        #    get context
        #    calculate top n context
        #   save in table in database (option for other table name)
        contexts, docs = posts_context(directory, database, site, x, all)
        t1 = time.time()
        if all:
            top_n_contexts = {}
            for postid in contexts:
                for id, context in contexts[postid].items():
                    top_n_contexts[id] = " ".join(context)
        else:
            top_n_contexts = bow.get_top_n_tfidf2(contexts, docs, n, tfidf, all)
        log("../output/statistics.log", "time for contexts posts: "+ str(int((time.time()-t1)/60)) +"min " + str(int((time.time()-t1)%60)) + "sec")

        write_context_table(site, top_n_contexts, database, tablename, if_exists)

        if_exists = "append"

        contexts, docs = comments_context(directory, database, site, x, all)
        t1 = time.time()
        if all:
            top_n_contexts = {}
            for commentid in contexts:
                for id, context in contexts[commentid].items():
                    top_n_contexts[id] = " ".join(context)
        else:
            top_n_contexts = bow.get_top_n_tfidf2(contexts, docs, n, tfidf, all)
        log("../output/statistics.log", "time for contexts comments: "+ str(int((time.time()-t1)/60)) +"min " + str(int((time.time()-t1)%60)) + "sec")
        write_context_table(site, top_n_contexts, database, tablename, if_exists)

    log("../output/statistics.log", "total execution time: "+ str(int((time.time()-start)/60)) +"min " + str(int((time.time()-start)%60)) + "sec")
    log("../output/statistics.log", "max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")




# TODO:
#  n als alle terme
#  nutzer kann max_df = 0.75, min_df = 2, max_features=5000 ändern in BOW
#  strong and emphasized text
#  stem and normalize words? need to stem? or tokenizing enough?


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i","--input",default= "../input/", help = "input directory of stackexchange dump files and directories")
    parser.add_argument("-d", "--dumps",default="test_dumps", help="File containing stackexchange dump sites names to be processed")
    parser.add_argument("-o", "--database", default='../output/database.db', help="database output")
    parser.add_argument("-c", "--context", default='10', help="number of words around formula to be reagarded as possible context")
    parser.add_argument("-n", "--topn", default='3', help="number of top terms in context regarding their tf-idf scores")
    parser.add_argument("--corpus", default="all", help="options: all or individual. corpus for idf over all sites or individually for each")
    parser.add_argument("-t", "--tablename", default="FormulaContext", help="name of table to write topn contexts words of formulas in (will be overwritten if it exists)")
    parser.add_argument("--tfidf", default="yes", help="Whether or not to show tf-idf ratings with top context words. Options: yes, no")
    parser.add_argument("-a", "--all", default="no", help="get all words. Options: yes, no. Option Yes will lead to ignoring options context, topn, corpus, and tfidf.")
    args = parser.parse_args()
    context_main(args.dumps, args.input, args.database, int(args.context), int(args.topn), args.corpus, args.tablename, args.tfidf, args.all)
