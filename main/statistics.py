# TODO:
#  wv text pro gleichung

from dump_processing.helper import log
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
from dump_processing.LatexTokenizer import LatexTokenizer
from collections import Counter
import matplotlib.pyplot as plt
import argparse
import sqlite3
import pandas as pd
import collections
import re
import resource
import string


# formulaid_postid = {formulaid: postid}, all_postids = [], token_lengths = []
def formulas_per_post(formulaid_postid, all_postids, token_lengths, site):
    posts = len(all_postids)
    formulas = len(formulaid_postid)
    print("# posts: "+ str(posts))
    print("# formulas in posts: "+ str(formulas))
    print("# average number of formulas per post: "+ format(formulas/posts, ".2f"))
    # percentage of posts with at least 1 formula
    unique_postids = len(set(formulaid_postid.values()))
    print("# posts containing formulas: "+ str(unique_postids) + " -> "+ format(100* unique_postids/posts, ".2f") + "% of posts")

    # number of formulas in post {postid: #formulas}
    counter = Counter(formulaid_postid.values())

    # number of posts with x formulas {x: #posts}
    counts_counter = Counter(counter.values())
    # manually add number of posts with 0 formulas
    counts_counter[0] = posts - unique_postids

    rev_ordered_counts_counter = collections.OrderedDict(sorted(counts_counter.items(), reverse=True))

    to_remove = 0.02*unique_postids
    removed = 0
    for k,v in rev_ordered_counts_counter.items():
        if removed <= to_remove:
            counts_counter.pop(k)
            removed += v
        else:
            break


    # make this into a histogram of number of formula distribution in questions, answers, posts and comments
    #counts_counter_below_100 = {k:v for (k,v) in counts_counter.items() if k <100}
    plt.subplot(2, 1, 1)
    plt.subplots_adjust(left=0.15, hspace=0.55, wspace=0.3)
    plt.bar(list(counts_counter.keys()), counts_counter.values(), color='g',edgecolor='black', linewidth=1)
    plt.title("Formula Distribution of '"+ site + "' Dump")
    plt.xlabel("Number of Formulas per Post")
    plt.ylabel("Number of Posts")

    top_filtered = sorted(token_lengths, reverse=True)[int(0.05*len(token_lengths)):]
    plt.subplot(2, 1, 2)
    plt.hist(top_filtered, bins=len(set(top_filtered)), color='g',edgecolor='black', linewidth=1, align='left')
    plt.title("Formula Length Distribution in '"+ site + "' Dump")
    plt.xlabel("Number of Tokens per Formula")
    plt.ylabel("Number of Formulas")
    plt.show()

    # text pro gleichung: avg text of post with formula


def common_words(docs, x):
    docs = [re.sub(r'(\$\$.*?\$\$|\$.*?\$)|<.*?>|\\amp', ' ', d) for d in docs]
    table = str.maketrans('', '', string.punctuation)
    temp = []
    for words in docs:
        temp.append(words.translate(table).lower())
    vectorizer = CountVectorizer(max_df=0.75, max_features=x, stop_words='english')
    word_count_vector = vectorizer.fit_transform(temp)
    count_list = word_count_vector.toarray().sum(axis=0)
    word_list = vectorizer.get_feature_names()
    words = dict(zip(word_list, count_list))
    words = collections.OrderedDict(sorted(words.items(), key=lambda item: item[1], reverse=True))
    print(pd.DataFrame(words.items(), columns=['Word', 'idf']).to_string())

def common_tokens(tokens, x):
    token_dict = {}
    for token in tokens:
        if token in token_dict:
            token_dict[token] += 1
        else:
            token_dict[token] = 1
    counter = Counter(tokens)
    topx = counter.most_common(x)
    print(pd.DataFrame(topx, columns=['Token', 'Occurences']).to_string())

def all_tokens(formulas):
    tokens = []
    tokenizer = LatexTokenizer()
    for formula in formulas:
        t = tokenizer.tokenize(formula)
        tokens.extend(t)
    return tokens


def main(filename_dumps, database):
    with open(filename_dumps) as f:
        sites = [line.rstrip() for line in f if line is not ""]

    for site in sites:
        DB = sqlite3.connect(database)
        formulas_posts = pd.read_sql('select FormulaId, PostId, TokenLength from "FormulasPosts" where Site="'+site+'"', DB)
        question_ids = pd.read_sql('select QuestionId from "QuestionTags" where Site="'+site+'"', DB)
        answer_ids = pd.read_sql('select AnswerId from "AnswerMeta" where Site="'+site+'"', DB)
        DB.close()
        post_ids = question_ids["QuestionId"] + answer_ids["AnswerId"]
        question_ids.pop("QuestionId")
        answer_ids.pop("AnswerId")

        formulas_per_post(dict(zip(formulas_posts["FormulaId"], formulas_posts["PostId"])), post_ids, list(formulas_posts["TokenLength"]), site)
        formulas_posts.pop("FormulaId")
        formulas_posts.pop("PostId")
        print("max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")

        DB = sqlite3.connect(database)
        question_texts = pd.read_sql('select Title, Body from "QuestionText" where Site="'+site+'"', DB)
        answer_texts = pd.read_sql('select Body from "AnswerText" where Site="'+site+'"', DB)
        DB.close()

        common_words(list(question_texts["Title"]) + list(question_texts["Body"]) + list(answer_texts["Body"]), 100)
        question_texts.pop("Title")
        question_texts.pop("Body")
        answer_texts.pop("Body")
        print("max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")

        DB = sqlite3.connect(database)
        formulas_posts = pd.read_sql('select Body from "FormulasPosts" where Site="'+site+'"', DB)
        DB.close()

        common_tokens(all_tokens(list(formulas_posts["Body"])), 100)
        formulas_posts.pop("Body")
        print("max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dumps",default="test_dumps", help="File containing stackexchange dump sites names to be processed")
    parser.add_argument("--database", default='../output/database.db', help="database")
    args = parser.parse_args()
    main(args.dumps, args.database)
