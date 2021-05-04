import argparse
import sqlite3
import pandas as pd
from sklearn.model_selection import train_test_split
from pathlib import Path
import os
import copy
from LatexTokenizer import LatexTokenizer
import random

'''
1. Read Formulas and respective Tags (for Question Formulas from Questions and for Answer Formulas from the Question) 
   from the Database (min. Formula Length is 2 Tokens)
2. Read the Table of all Tags and their Count from the Database -> sort and keep top Tags via Count
3. Remove all Formulas not containing one of the top Tags as well as all non-top Tags
4. Duplicate to 3 DataFrames
5. For multiclass: change format of tags from <tag1><tag2>...<tagn> to __label__tag1 __label__tag2 ... __label__tagn
   For least common tag: determine least common label from Count Tag Table and save as __label__least-common-tag
   For most common label: determine most common label from Count Tag Table and save as __label__most-common-tag
6. Transform the LaTeX Formulas in Tokenized strings (LaTeX Tokens) separated by a space (' ') character
7. Write the three Dataframes to three files with one line per formula. Each line starts with the labels and is followed
   by the tokenized LaTeX formula
'''

def select_random_numbers(seed, n, r):
    random.seed(seed)
    numbers = random.sample(range(1, r), n)
    return numbers

def select_random_formulas(df, seed, n):
    range = len(df)
    if range < n:
        return df
    rows = select_random_numbers(seed, n, range)
    return df.iloc[rows]


# remove all formulas that do not contain one of the top tags
# and also remove all other tags from the formulas
def remove_non_top_tag_formulas_and_tags(df, top_tags):
    return_formulas = []
    return_tags = []
    return_num_tags = []
    for index, row in df.iterrows():
        tags = [tag[1:] for tag in row["Tags"].split(">") if len(tag) > 0]
        if any(item in tags for item in top_tags):
            tags = [tag for tag in tags if tag in top_tags]
            tag_string = ''
            for tag in tags:
                tag_string += '<' + tag + ">"
            return_formulas.append(row["LaTeXBody"])
            return_tags.append(tag_string)
            return_num_tags.append(len(tags))
    return pd.DataFrame({"LaTeXBody": return_formulas, 'Tags': return_tags, "NumTags": return_num_tags}, columns=["LaTeXBody", 'Tags', "NumTags"])

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

        df.at[index, "Tags"] = "__label__" + top_tag + " "
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

        df.at[index, "Tags"] =  "__label__" + bottom_tag + " "
    return df

def all_tags(df, tags_dict):
    for index, row in df.iterrows():
        tags = [tag[1:] for tag in row["Tags"].split(">") if len(tag) > 0]
        t = ""
        for tag in tags:
            t += "__label__" + tag + " "

        df.at[index, "Tags"] = t
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


def main(dumps, database, output, separate, minlength, top_tags, seed, num_formulas):
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
        sites = [line.rstrip() for line in f if line != ""]

    print(sites)

    for site in sites:
        DB = sqlite3.connect(database)
        formulas_tags_questions = pd.read_sql('select LaTeXBody, Tags '
                                              'from "FormulasPosts" join FormulasPostsMathML '
                                              'on FormulasPosts.FormulaId = FormulasPostsMathML.FormulaId '
                                              'join "QuestionTags" '
                                              'on FormulasPosts.PostId = QuestionTags.QuestionId and FormulasPosts.Site = QuestionTags.Site '
                                              'where FormulasPosts.Site="'+ site +'" and TokenLength>='+str(minlength) + " and OPT != '' and SLT != ''", DB)
        formulas_tags_answers = pd.read_sql('select LaTeXBody, Tags '
                                            'from "FormulasPosts" join FormulasPostsMathML '
                                            'on FormulasPosts.FormulaId = FormulasPostsMathML.FormulaId '
                                            'join "AnswerMeta" '
                                            'on FormulasPosts.PostId = AnswerMeta.AnswerId and FormulasPosts.Site = AnswerMeta.Site '
                                            'join "QuestionTags" '
                                            'on AnswerMeta.QuestionId = QuestionTags.QuestionId and AnswerMeta.Site = QuestionTags.Site '
                                            'where FormulasPosts.Site="'+ site +'" and TokenLength>='+str(minlength) + " and OPT != '' and SLT != ''", DB)
        tags = pd.read_sql('select Tag, Count from "Tags" '
                                            'where Site="'+ site +'"', DB)
        DB.close()

        sorted_tags = tags.sort_values(by=['Count'], ascending=False)
        top_tags_dict = dict(zip(sorted_tags["Tag"][:int(top_tags)], sorted_tags["Count"][:int(top_tags)]))

        df = pd.concat([formulas_tags_questions, formulas_tags_answers])
        print("number of formulas in " + site + ": " + str(len(df)))
        if len(df["LaTeXBody"]) == 0:
            raise ValueError("No Formula Entries in Database for Site "+ site)

        df = remove_non_top_tag_formulas_and_tags(df, list(top_tags_dict.keys()))
        print("number of formulas in " + site + " tagged with top " + str(top_tags) + " tag: " + str(len(df)))
        print("average tags per formula: "+ str(df["NumTags"].mean()))

        df = select_random_formulas(df, int(seed), int(num_formulas))
        print("number of formulas selected with seed "+str(seed)+": " + str(len(df)))
        print("average tags per formula: "+ str(df["NumTags"].mean()))

        # copy once -> all tags
        # only most common tag
        # only rarest tag

        # remove newlines from LaTeX Formulas
        for index, row in df.iterrows():
            df.at[index, "LaTeXBody"] = df.at[index, "LaTeXBody"].replace("\n", "")

        if separate:
            directory = os.path.join(output, site)
            multi_df = all_tags(copy.deepcopy(df), top_tags_dict)
            split_save(multi_df, os.path.join(directory, "multiclass", site), mode, site)
            top_df = top_tag(copy.deepcopy(df), top_tags_dict)
            split_save(top_df, os.path.join(directory, "most_frequent_tag", site), mode, site)
            bottom_df = bottom_tag(copy.deepcopy(df), top_tags_dict)
            split_save(bottom_df, os.path.join(directory, "least_frequent_tag", site), mode, site)
        else:
            multi_df = all_tags(copy.deepcopy(df), top_tags_dict)
            split_save(multi_df, os.path.join(directory, "multiclass"), mode, site)
            top_df = top_tag(copy.deepcopy(df), top_tags_dict)
            split_save(top_df, os.path.join(directory, "most_frequent_tag"), mode, site)
            bottom_df = bottom_tag(copy.deepcopy(df), top_tags_dict)
            split_save(bottom_df, os.path.join(directory, "least_frequent_tag"), mode, site)

        if separate:
            mode = 'a'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dumps",default="test_dumps", help="File containing stackexchange dump sites names to be processed")
    parser.add_argument("--database", default='../output/database.db', help="database")
    parser.add_argument("-o", "--output", default='../output/classification_data/', help="output directory")
    parser.add_argument("-s", "--separate", default="yes", help="yes or no. Put training data in separate files for each site.")
    parser.add_argument("-f", "--minlength", default="3", help="integer. minimum token length of formulas")
    parser.add_argument("--top_tags", default=50, help="number of top tags")
    parser.add_argument("--seed", default=1234, help="seed for selecting random formulas")
    parser.add_argument("--num_formulas", default=10, help="number of formulas to select")
    args = parser.parse_args()
    main(args.dumps, args.database, args.output, args.separate, args.minlength, args.top_tags, args.seed, args.num_formulas)
