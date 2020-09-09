import argparse
import sqlite3
import pandas as pd
import random
from sklearn.model_selection import train_test_split
from pathlib import Path
import os
import copy

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

        row["Tags"] =  top_tag
    return df

def bottom_tag(df, tags_dict):
    for index, row in df.iterrows():
        tags = [tag[1:] for tag in row["Tags"].split(">") if len(tag) > 0]
        # get top tag
        top_tag = tags[0]
        top_val = max(tags_dict.values())
        for tag in tags:
            if tags_dict[tag] < top_val:
                top_tag = tag
                top_val = tags_dict[tag]

        row["Tags"] =  top_tag
    return df

def split_save(df, output, mode):
    # shuffle data
    # split data
    #print(len(df))
    train, test = train_test_split(df, test_size=0.2)
    #print(len(train))
    train2, test = train_test_split(test, test_size=0.5)
    #print(len(train2))
    #print(len(test))

    # save data
    Path(output).mkdir(parents=True, exist_ok=True)
    train.to_csv(os.path.join(output, "train.formula"), sep=' ', index=False, header=False, columns=["LaTeXBody"],  mode=mode)
    train.to_csv(os.path.join(output, "train.label"), sep=' ', index=False, header=False, columns=["Tags"],  mode=mode)
    train2.to_csv(os.path.join(output, "test.formula"), sep=' ', index=False, header=False, columns=["LaTeXBody"],  mode=mode)
    train2.to_csv(os.path.join(output, "test.label"), sep=' ', index=False, header=False, columns=["Tags"],  mode=mode)
    test.to_csv(os.path.join(output, "val.formula"), sep=' ', index=False, header=False, columns=["LaTeXBody"],  mode=mode)
    test.to_csv(os.path.join(output, "val.label"), sep=' ', index=False, header=False, columns=["Tags"],  mode=mode)


def main(dumps, database, output, separate):
    mode = 'w'
    if separate == "yes":
        separate = True
    elif separate == "no":
        separate = False
    else:
        raise ValueError("argument -separate invalid")
    directory = output

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
                                              'where FormulasPosts.Site="'+ site +'"' , DB)
        formulas_tags_answers = pd.read_sql('select LaTeXBody, Tags '
                                            'from "FormulasPosts" join "AnswerMeta" '
                                            'on FormulasPosts.PostId = AnswerMeta.AnswerId and FormulasPosts.Site = AnswerMeta.Site '
                                            'join "QuestionTags" '
                                            'on AnswerMeta.QuestionId = QuestionTags.QuestionId and AnswerMeta.Site = QuestionTags.Site '
                                            'where FormulasPosts.Site="'+ site +'"', DB)
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

        split_save(df, os.path.join(directory, "multiclass"), mode)
        top_df = top_tag(copy.deepcopy(df), tags_dict)
        split_save(top_df, os.path.join(directory, "most_frequent_tag"), mode)
        bottom_df = bottom_tag(copy.deepcopy(df), tags_dict)
        split_save(bottom_df, os.path.join(directory, "least_frequent_tag"), mode)

        if separate:
            mode = 'a'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dumps",default="test_dumps", help="File containing stackexchange dump sites names to be processed")
    parser.add_argument("--database", default='../output/database.db', help="database")
    parser.add_argument("-o", "--output", default='../output/classification_data/', help="output directory")
    parser.add_argument("-s", "--separate", default="no", help="yes or no. Put training data in separate files for each site.")
    args = parser.parse_args()
    main(args.dumps, args.database, args.output, args.separate)
