import argparse
import sqlite3
import pandas as pd
from math_tan.math_extractor import MathExtractor
from math_tan.symbol_tree import SymbolTree
from sklearn.model_selection import train_test_split
import os
import random


def to_slt_tuples(slt_string):
    temp = SymbolTree.parse_from_slt(slt_string)
    aaa = temp.get_pairs(window=2, eob=True)
    return aaa


def to_opt_tuples(opt_string):
    temp = SymbolTree.parse_from_opt(opt_string)
    aaa = temp.get_pairs(window=2, eob=True)
    return aaa

def split_save(df, output, max_context, pad_length):
    train, test = train_test_split(df, test_size=0.2)
    val, test = train_test_split(test, test_size=0.5)


    open(os.path.join(output, "train"), 'w').close()
    print("Writing train file")
    for index, row in train.iterrows():
        example_processing(row["OPT"], row["Tags"], max_context, os.path.join(output, "train"), pad_length)

    open(os.path.join(output, "test"), 'w').close()
    print("Writing test file")
    for index, row in test.iterrows():
        example_processing(row["OPT"], row["Tags"], max_context, os.path.join(output, "test"), pad_length)

    open(os.path.join(output, "val"), 'w').close()
    print("Writing val file")
    for index, row in val.iterrows():
        example_processing(row["OPT"], row["Tags"], max_context, os.path.join(output, "val"), pad_length)

def pad_path(path, length):
    path = list(path)
    string = ""
    for i in range(length):
        if len(path) <= i:
            string += "<pad>"
        else:
            string += path[i]
        if i != length-1:
            string += "|"

    return string

def tuple_to_context(tuple, pad_length):
    return tuple[0] + "," + pad_path(tuple[2] + "#" + tuple[3], pad_length) + "," + tuple[1]

# processes example and writes to file. shuffle before !
def example_processing(opt, tags, max_context, file, pad_length):
    try:
        tuples = to_opt_tuples(opt)
        tags = [tag[1:] for tag in tags.split(">") if len(tag) > 0]
        tags.sort()
        example = "|".join(tags)
        count = 0
        random.shuffle(tuples)
        for t in tuples:
            t = t.split("\t")
            count += 1
            if count > max_context:
                break
            example += " " + tuple_to_context(t, pad_length)
        example += " " * (max_context-count) + "\n"
        with open(file, 'a') as f:
            f.write(example)
    except Exception as e:
        print(e)

def main(dumps, database, output, minlength, max_context, pad_length):
    directory = output
    pad_length = int(pad_length)
    minlength = int(minlength)
    max_context = int(max_context)


    # for site in sites
    # get all formulas with post id
    # get all post ids with tags -> questions
    # get all post ids for answers and match with tags of questions
    # get all post ids of comments and math with tags of questions
    with open(dumps) as f:
        sites = [line.rstrip() for line in f if line is not ""]

    print(sites)

    for site in sites:
        DB = sqlite3.connect(database)
        formulas_tags_questions = pd.read_sql('select OPT, Tags '
                                              'from "FormulasPosts" join FormulasPostsMathML '
                                              'on FormulasPosts.FormulaId = FormulasPostsMathML.FormulaId '
                                              'join "QuestionTags" '
                                              'on FormulasPosts.PostId = QuestionTags.QuestionId and FormulasPosts.Site = QuestionTags.Site '
                                              'where FormulasPosts.Site="'+ site +'" and TokenLength>='+str(minlength) + " and OPT != ''", DB)
        formulas_tags_answers = pd.read_sql('select OPT, Tags '
                                            'from "FormulasPosts" join FormulasPostsMathML '
                                            'on FormulasPosts.FormulaId = FormulasPostsMathML.FormulaId '
                                            'join "AnswerMeta" '
                                            'on FormulasPosts.PostId = AnswerMeta.AnswerId and FormulasPosts.Site = AnswerMeta.Site '
                                            'join "QuestionTags" '
                                            'on AnswerMeta.QuestionId = QuestionTags.QuestionId and AnswerMeta.Site = QuestionTags.Site '
                                            'where FormulasPosts.Site="'+ site +'" and TokenLength>='+str(minlength) + " and OPT != ''", DB)
        DB.close()

        df = pd.concat([formulas_tags_questions, formulas_tags_answers])
        print("number of formulas in " + site + ": " + str(len(df)))
        if len(df["OPT"]) == 0:
            raise ValueError("No Formula Entries in Database for Site "+ site)

        if not os.path.isdir(output):
            os.mkdir(output)
        split_save(df, output, max_context, pad_length)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dumps",default="test_dumps", help="File containing stackexchange dump sites names to be processed")
    parser.add_argument("--database", default='../output/database.db', help="database")
    parser.add_argument("-o", "--output", default='../output/classification_data/', help="output directory")
    #parser.add_argument("-s", "--separate", default="yes", help="yes or no. Put training data in separate files for each site.")
    parser.add_argument("-f", "--minlength", default="5", help="integer. minimum token length of formulas")
    parser.add_argument("-c", "--context", default="20", help="max number of context fields")
    parser.add_argument("-p", "--padding", default="6", help="length of padding in path")
    args = parser.parse_args()
    main(args.dumps, args.database, args.output, args.minlength, args.context, args.padding)
