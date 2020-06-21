# TODO:
#  wv text pro gleichung

from sklearn.feature_extraction.text import CountVectorizer
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
import os.path
from collections import OrderedDict
from matplotlib.ticker import StrMethodFormatter

# TODO:
#  #posts etc stats also in html
#  comments and comment formulas

def reduce_labels(labels):
    if len(labels) < 5:
        return [l for l in labels]
    if len(labels) < 15:
        return [l for l in labels if int(l) % 3 == 0]
    if len(labels) < 50:
        return [l for l in labels if int(l) % 5 == 0]
    return [l for l in labels if int(l) % 10 == 0]


# formulaid_postid = {formulaid: postid}, all_postids = [], token_lengths = []
def formulas_per_post(formulaid_postid, all_postids, token_lengths, site, directory, text_type):
    posts = len(all_postids)
    formulas = len(formulaid_postid)
    stats_titles = []
    stats_values = []

    stats_titles.append("total " + text_type + "s: ")
    stats_values.append(format(posts,',d'))

    stats_titles.append("total formulas in " + text_type + "s: ")
    stats_values.append(format(formulas,',d'))

    stats_titles.append("average number of formulas per " + text_type + ": ")
    stats_values.append(format(formulas/posts, ".2f"))

    # percentage of posts with at least 1 formula
    unique_postids = len(set(formulaid_postid.values()))
    stats_titles.append("total number of " + text_type + "s containing formulas: ")
    stats_values.append(format(unique_postids,',d'))
    stats_titles.append("percentage of " + text_type + "s containing formulas: ")
    stats_values.append(format(100* unique_postids/posts, ".2f"))

    # number of formulas in post {postid: #formulas}
    counter = Counter(formulaid_postid.values())

    # number of posts with x formulas {x: #posts}
    counts_counter = Counter(counter.values())
    # manually add number of posts with 0 formulas
    counts_counter[0] = posts - unique_postids

    rev_ordered_counts_counter = collections.OrderedDict(sorted(counts_counter.items(), reverse=True))

    to_remove = 0.02*posts
    removed = 0
    top = []
    for k,v in rev_ordered_counts_counter.items():
        if k < 20:
            break
        if removed <= to_remove:
            top.append(counts_counter.pop(k))
            removed += v
        else:
            break

    prev = 0
    for k in sorted(counts_counter.keys()):
        while k > prev+1:
            prev += 1
            counts_counter[prev] = 0
        prev = k

    fig, (ax1, ax2) = plt.subplots(2, 1)
    # make this into a histogram of number of formula distribution in questions, answers, posts and comments
    #plt.subplot(2, 1, 1)
    fig.subplots_adjust(left=0.15, hspace=0.55, wspace=0.3)
    o_counts_counter = OrderedDict(sorted(counts_counter.items()))
    labels = [str(k) for k in o_counts_counter.keys()] + ["x"]
    o_counts_counter[len(o_counts_counter)] = removed

    ax1.bar(labels, o_counts_counter.values(), color='g',edgecolor='black', linewidth=1)
    ax1.set_title("Formula Distribution of '"+ site + "' in " + text_type.title() + "s")
    ax1.set_xlabel("Number of Formulas per " + text_type.title())
    ax1.set_ylabel("Number of " + text_type.title() + "s")
    plt.sca(ax1)
    labels.remove("x")
    maximum = labels[len(labels)-1]
    if int(maximum) < 20:
        locations = reduce_labels(labels)
        labels = locations
    else:
        locations = reduce_labels(labels)
        if (locations[-1] == labels[-1]) & (len(locations)>5):
            locations.remove(labels[-1])
            labels.remove(labels[-1])
        locations.append("x")
        labels = reduce_labels(labels)
        labels.append(r'$\geq$'+str(int(maximum)+1))
    plt.xticks(locations, labels)
    plt.gca().yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))


    counter = Counter(sorted(token_lengths))
    counter[0] = 0
    removed = 0

    rev_ordered_counter = collections.OrderedDict(sorted(counter.items(), reverse=True))

    to_remove = 0.05*len(token_lengths)
    top = []
    for k,v in rev_ordered_counter.items():
        if k < 20:
            break
        if removed <= to_remove:
            top.append(counter.pop(k))
            removed += v
        else:
            break

    prev = 0
    for k in sorted(counter.keys()):
        while k > prev+1:
            prev += 1
            counter[prev] = 0
        prev = k

    ordered_counter = collections.OrderedDict(sorted(counter.items()))
    labels = [str(k) for k in ordered_counter.keys()] + ["x"]

    ordered_counter[max(ordered_counter.keys())+1] = removed
    ax2.bar(labels, ordered_counter.values(), color='g',edgecolor='black', linewidth=1)
    ax2.set_title("Formula Length Distribution of " + text_type.title() + "s in '"+ site + "'")
    ax2.set_xlabel("Number of Tokens per Formula")
    ax2.set_ylabel("Number of Formulas")
    plt.sca(ax2)
    labels.remove("x")
    maximum = labels[len(labels)-1]
    locations = reduce_labels(labels)
    if (locations[-1] == labels[-1]) & (len(locations)>5):
        locations.remove(labels[-1])
        labels.remove(labels[-1])
    locations.append("x")
    labels = reduce_labels(labels)
    labels.append(r'$\geq$'+str(int(maximum)+1))
    plt.xticks(locations, labels)
    plt.gca().yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))


    file = os.path.join(directory,"diagrams", site + "_" + text_type + "_stats.png")
    fig.savefig(file, dpi=300)
    print("Figure saved to " + file)
    return os.path.join("diagrams", site + "_" + text_type + "_stats.png"), pd.DataFrame({"Title": stats_titles, "Value": stats_values})

    # text pro gleichung: avg text of post with formula


def common_words(docs, x):
    docs = [re.sub(r'(\$\$.*?\$\$|\$.*?\$)|<.*?>|&amp;|&lt;|&gt;', ' ', d) for d in docs]
    table = str.maketrans('', '', string.punctuation)
    temp = []
    for words in docs:
        temp.append(words.translate(table).lower())
    vectorizer = CountVectorizer(max_df=0.75, max_features=x, stop_words='english')
    word_count_vector = vectorizer.fit_transform(temp)
    count_list = word_count_vector.toarray().sum(axis=0)
    word_list = vectorizer.get_feature_names()
    count_list = [format(c, ',d') for c in count_list]
    words = dict(zip(word_list, count_list))
    words = collections.OrderedDict(sorted(words.items(), key=lambda item: item[1], reverse=True))
    return pd.DataFrame(words.items(), columns=['Word', 'df'])

def common_tokens(tokens, x):
    token_dict = {}
    for token in tokens:
        if token in token_dict:
            token_dict[token] += 1
        else:
            token_dict[token] = 1
    counter = Counter(tokens)
    topx = counter.most_common(x)
    topx = [(k, format(v, ',d')) for (k, v) in topx]

    return pd.DataFrame(topx, columns=['Token', 'Occurences'])

def save_to_html(figure_file_p, figure_file_c, df_tokens, df_words, df_stats_p, df_stats_c, directory, site):
    df_tokens.index += 1
    df_words.index += 1
    tokens = df_tokens.to_html(classes='table table-striped', bold_rows=False, justify='center', border=2)
    words = df_words.to_html(classes='table table-striped', bold_rows=False, justify='center', border=2)
    df_stats = pd.concat([df_stats_p, df_stats_c])
    stats = df_stats.to_html(classes='table table-striped', index=False, justify='center', border=2)

    f = open(os.path.join(directory, site+'_stats.html'),'w')

    text = """<html><head></head><body>
    <div style="margin-top:50px"><h1 style="text-align: center;">"""+ site +"""</h1></div>
    <div style="float:left; margin:15px">"""+ words + """</div>
    <div style="float:left; margin:15px">"""+ tokens + """</div>
    <div style="float:left; margin:15px">
    <div style="float:top">"""+ stats + """</div>
    <div style="float:top; margin-top:30px">"""+ '<img src="' + figure_file_p +'" alt="statistics figure ' + figure_file_p + '" width="600" style=\'border:2px solid #000000\'>' + """</div>
    <div style="float:top; margin-top:30px">"""+ '<img src="' + figure_file_c +'" alt="statistics figure ' + figure_file_c + '" width="600" style=\'border:2px solid #000000\'>' + """</div>
    </div>
    </body></html>"""
    f.write(text)
    f.close()

def all_tokens(formulas):
    tokens = []
    tokenizer = LatexTokenizer()
    for formula in formulas:
        t = tokenizer.tokenize(formula)
        tokens.extend(t)
    return tokens


def main(filename_dumps, database, directory):
    with open(filename_dumps) as f:
        sites = [line.rstrip() for line in f if line is not ""]

    for site in sites:
        DB = sqlite3.connect(database)
        formulas_posts = pd.read_sql('select FormulaId, PostId, TokenLength from "FormulasPosts" where Site="'+site+'"', DB)
        question_ids = pd.read_sql('select QuestionId from "QuestionTags" where Site="'+site+'"', DB)
        answer_ids = pd.read_sql('select AnswerId from "AnswerMeta" where Site="'+site+'"', DB)
        DB.close()
        post_ids = list(question_ids["QuestionId"]) + list(answer_ids["AnswerId"])
        question_ids.pop("QuestionId")
        answer_ids.pop("AnswerId")

        figure_file_p, df_stats_p = formulas_per_post(dict(zip(formulas_posts["FormulaId"], formulas_posts["PostId"])), post_ids, list(formulas_posts["TokenLength"]), site, directory, "post")
        formulas_posts.pop("FormulaId")
        formulas_posts.pop("PostId")
        print("max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")

        DB = sqlite3.connect(database)
        question_texts = pd.read_sql('select Title, Body from "QuestionText" where Site="'+site+'"', DB)
        answer_texts = pd.read_sql('select Body from "AnswerText" where Site="'+site+'"', DB)
        DB.close()

        df_words = common_words(list(question_texts["Title"]) + list(question_texts["Body"]) + list(answer_texts["Body"]), 100)
        question_texts.pop("Title")
        question_texts.pop("Body")
        answer_texts.pop("Body")
        print("max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")


        DB = sqlite3.connect(database)
        formulas_comments = pd.read_sql('select FormulaId, CommentId, TokenLength from "FormulasComments" where Site="'+site+'"', DB)
        comment_ids = pd.read_sql('select CommentId from "Comments" where Site="'+site+'"', DB)
        DB.close()

        figure_file_c, df_stats_c = formulas_per_post(dict(zip(formulas_comments["FormulaId"], formulas_comments["CommentId"])), list(comment_ids["CommentId"]), list(formulas_comments["TokenLength"]), site, directory, "comment")
        comment_ids.pop("CommentId")
        formulas_comments.pop("FormulaId")
        formulas_comments.pop("CommentId")


        DB = sqlite3.connect(database)
        formulas_posts = pd.read_sql('select Body from "FormulasPosts" where Site="'+site+'"', DB)
        formulas_comments = pd.read_sql('select Body from "FormulasComments" where Site="'+site+'"', DB)
        DB.close()

        all_formulas = list(formulas_posts["Body"]) + list(formulas_comments["Body"])
        formulas_posts.pop("Body")
        formulas_comments.pop("Body")
        df_tokens = common_tokens(all_tokens(all_formulas), 100)
        all_formulas = []
        print("max memory usage: " + format((resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)/pow(2,30), ".3f")+ " GigaByte")

        save_to_html(figure_file_p, figure_file_c, df_tokens, df_words, df_stats_p, df_stats_c, directory, site)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dumps",default="test_dumps", help="File containing stackexchange dump sites names to be processed")
    parser.add_argument("--database", default='../output/database.db', help="database")
    parser.add_argument("-o", "--output", default='../output/', help="output directory")
    args = parser.parse_args()
    main(args.dumps, args.database, args.output)