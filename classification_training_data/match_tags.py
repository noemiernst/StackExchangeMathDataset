import argparse
import sqlite3
import pandas as pd
from sklearn.model_selection import train_test_split
from pathlib import Path
import os
import copy
from classification_training_data.LatexTokenizer import LatexTokenizer

def top_tag(df, tags_dict):
    for index, row in df.iterrows():
        tags = [tag[1:] for tag in row["Tags"].split(">") if len(tag) > 0]
        # get top tag
        top_tag = tags[0]
        top_val = 0
        for tag in tags:
            if tags_dict[tag] > top_val:
                top_tag = tag
                top_val = tags_dict[tag]

        row["Tags"] =  "__label__" + top_tag + " "
    return df

def bottom_tag(df, tags_dict):
    for index, row in df.iterrows():
        tags = [tag[1:] for tag in row["Tags"].split(">") if len(tag) > 0]
        # get top tag
        bottom_tag = tags[0]
        bottom_val = max(tags_dict.values())
        for tag in tags:
            if tags_dict[tag] < bottom_val:
                bottom_tag = tag
                bottom_val = tags_dict[tag]

        row["Tags"] =  "__label__" + bottom_tag + " "
    return df

def all_tags(df, tags_dict):
    for index, row in df.iterrows():
        tags = [tag[1:] for tag in row["Tags"].split(">") if len(tag) > 0]
        t = ""
        for tag in tags:
            t += "__label__" + tag + " "

        row["Tags"] =  t
    return df

def latex_to_tokenstring(latex):
    tokens = LatexTokenizer.tokenize(latex)
    string = " ".join(tokens)
    # remove duplicated spaces
    return " ".join(string.split())

def df_to_file(df, output, mode):
    with open(output, mode) as f:
        for index, row in df.iterrows():
            f.write(row["Tags"] + latex_to_tokenstring(row["LaTeXBody"]) + "\n")

def split_save(df, output, mode, site):
    # shuffle data
    # split data
    train, test = train_test_split(df, test_size=0.2)
    test, val = train_test_split(test, test_size=0.5)

    # save data
    Path(output).parent.mkdir(parents=True, exist_ok=True)

    df_to_file(train, output + ".train", mode)
    df_to_file(test, output + ".test", mode)
    df_to_file(val, output + ".val", mode)


def main(dumps, database, output, separate, minlength):
    mode = 'w'
    if separate == "yes":
        separate = True
    elif separate == "no":
        separate = False
    else:
        raise ValueError("argument -separate invalid")
    directory = output

    minlength = int(minlength)


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
        tags = pd.read_sql('select Tag, Count from "Tags" '
                                            'where Site="'+ site +'"', DB)
        DB.close()

        tags_dict = dict(zip(tags["Tag"], tags["Count"]))
        df = pd.concat([formulas_tags_questions, formulas_tags_answers])
        print("number of formulas in " + site + ": " + str(len(df)))
        if len(df["LaTeXBody"]) == 0:
            raise ValueError("No Formula Entries in Database for Site "+ site)

        # copy once -> all tags
        # only most common tag
        # only rarest tag

        # remove newlines from LaTeX Formulas
        for index, row in df.iterrows():
            row["LaTeXBody"] = row["LaTeXBody"].replace("\n", "")

        if separate:
            directory = os.path.join(output, site)
            multi_df = all_tags(copy.deepcopy(df), tags_dict)
            split_save(multi_df, os.path.join(directory, "multiclass", site), mode, site)
            top_df = top_tag(copy.deepcopy(df), tags_dict)
            split_save(top_df, os.path.join(directory, "most_frequent_tag", site), mode, site)
            bottom_df = bottom_tag(copy.deepcopy(df), tags_dict)
            split_save(bottom_df, os.path.join(directory, "least_frequent_tag", site), mode, site)
        else:
            multi_df = all_tags(copy.deepcopy(df), tags_dict)
            split_save(multi_df, os.path.join(directory, "multiclass"), mode, site)
            top_df = top_tag(copy.deepcopy(df), tags_dict)
            split_save(top_df, os.path.join(directory, "most_frequent_tag"), mode, site)
            bottom_df = bottom_tag(copy.deepcopy(df), tags_dict)
            split_save(bottom_df, os.path.join(directory, "least_frequent_tag"), mode, site)

        if separate:
            mode = 'a'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dumps",default="test_dumps", help="File containing stackexchange dump sites names to be processed")
    parser.add_argument("--database", default='../output/database.db', help="database")
    parser.add_argument("-o", "--output", default='../output/classification_data/', help="output directory")
    parser.add_argument("-s", "--separate", default="yes", help="yes or no. Put training data in separate files for each site.")
    parser.add_argument("-f", "--minlength", default="2", help="integer. minimum token length of formulas")
    args = parser.parse_args()
    main(args.dumps, args.database, args.output, args.separate, args.minlength)
