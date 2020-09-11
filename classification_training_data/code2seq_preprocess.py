import argparse
import sqlite3
import pandas as pd
from math_tan.math_extractor import MathExtractor
from sklearn.model_selection import train_test_split
import os


def latex_math_to_slt_tuples(latex_formula):
    temp = MathExtractor.parse_from_tex(latex_formula)
    aaa = temp.get_pairs(window=2, eob=True)
    return aaa


def latex_math_to_opt_tuples(latex_formula):
    temp = MathExtractor.parse_from_tex_opt(latex_formula)
    aaa = temp.get_pairs(window=2, eob=True)
    return aaa

def split_save(df, output, max_context):
    train, test = train_test_split(df, test_size=0.2)
    val, test = train_test_split(test, test_size=0.5)


    open(os.path.join(output, "train"), 'w').close()
    print("Writing train file")
    print(train)
    for index, row in train.iterrows():
        example_processing(row["LaTeXBody"], row["Tags"], max_context, os.path.join(output, "train"))

    open(os.path.join(output, "test"), 'w').close()
    print("Writing test file")
    print(test)
    for index, row in test.iterrows():
        example_processing(row["LaTeXBody"], row["Tags"], max_context, os.path.join(output, "test"))

    open(os.path.join(output, "val"), 'w').close()
    print("Writing val file")
    print(val)
    for index, row in val.iterrows():
        example_processing(row["LaTeXBody"], row["Tags"], max_context, os.path.join(output, "val"))


def tuple_to_context(tuple):
    return tuple[0] + "," + tuple[2] + "#" + tuple[3] + "," + tuple[1]

# processes example and writes to file. shuffle before !
def example_processing(latex, tags, max_context, file):
    try:
        tuples = latex_math_to_slt_tuples(latex)
        tags = [tag[1:] for tag in tags.split(">") if len(tag) > 0]
        example = tags.pop()
        for tag in tags:
            example += "|" + tag
        count = 0
        for t in tuples:
            t = t.split("\t")
            count += 1
            if count > max_context:
                break
            example += " " + tuple_to_context(t)
        example += " " * (max_context-count) + "\n"
        with open(file, 'a') as f:
            f.write(example)
    except:
        pass

def main(dumps, database, output, minlength, max_context):
    directory = output

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
        formulas_tags_questions = pd.read_sql('select LaTeXBody, Tags '
                                              'from "FormulasPosts" join "QuestionTags" '
                                              'on FormulasPosts.PostId = QuestionTags.QuestionId and FormulasPosts.Site = QuestionTags.Site '
                                              'where FormulasPosts.Site="'+ site +'" and TokenLength>='+str(minlength), DB)
        formulas_tags_answers = pd.read_sql('select LaTeXBody, Tags '
                                            'from "FormulasPosts" join "AnswerMeta" '
                                            'on FormulasPosts.PostId = AnswerMeta.AnswerId and FormulasPosts.Site = AnswerMeta.Site '
                                            'join "QuestionTags" '
                                            'on AnswerMeta.QuestionId = QuestionTags.QuestionId and AnswerMeta.Site = QuestionTags.Site '
                                            'where FormulasPosts.Site="'+ site +'" and TokenLength>='+str(minlength), DB)
        DB.close()

        df = pd.concat([formulas_tags_questions, formulas_tags_answers])
        print("number of formulas in " + site + ": " + str(len(df)))
        if len(df["LaTeXBody"]) == 0:
            raise ValueError("No Formula Entries in Database for Site "+ site)

        if not os.path.isdir(output):
            os.mkdir(output)
        split_save(df, output, max_context)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dumps",default="test_dumps", help="File containing stackexchange dump sites names to be processed")
    parser.add_argument("--database", default='../output/database.db', help="database")
    parser.add_argument("-o", "--output", default='../output/classification_data/', help="output directory")
    #parser.add_argument("-s", "--separate", default="yes", help="yes or no. Put training data in separate files for each site.")
    parser.add_argument("-f", "--minlength", default="5", help="integer. minimum token length of formulas")
    parser.add_argument("-c", "--context", default="20", help="max number of context fields")
    args = parser.parse_args()
    main(args.dumps, args.database, args.output, args.minlength, args.context)
