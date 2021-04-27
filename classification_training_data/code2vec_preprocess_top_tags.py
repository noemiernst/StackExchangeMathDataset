import argparse
import sqlite3
import pandas as pd
#from math_tan.math_extractor import MathExtractor
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
def remove_non_top_tag_formulas_and_tags(df, top_tags, tree_type):
    return_tree = []
    return_tags = []
    return_num_tags = []
    for index, row in df.iterrows():
        tags = [tag[1:] for tag in row["Tags"].split(">") if len(tag) > 0]
        if any(item in tags for item in top_tags):
            tags = [tag for tag in tags if tag in top_tags]
            tag_string = ''
            for tag in tags:
                tag_string += '<' + tag + ">"
            return_tree.append(row[tree_type])
            return_tags.append(tag_string)
            return_num_tags.append(len(tags))
    return pd.DataFrame({tree_type: return_tree, 'Tags': return_tags, "NumTags": return_num_tags}, columns=[tree_type, 'Tags', "NumTags"])

def split_save(df, output, max_context, tree_type):
    train, test = train_test_split(df, test_size=0.2)
    val, test = train_test_split(test, test_size=0.5)


    open(os.path.join(output, "train"), 'w').close()
    print("Writing train file")
    for index, row in train.iterrows():
        example_processing(row[tree_type], row["Tags"], max_context, os.path.join(output, "train"), tree_type)

    open(os.path.join(output, "test"), 'w').close()
    print("Writing test file")
    for index, row in test.iterrows():
        example_processing(row[tree_type], row["Tags"], max_context, os.path.join(output, "test"), tree_type)

    open(os.path.join(output, "val"), 'w').close()
    print("Writing val file")
    for index, row in val.iterrows():
        example_processing(row[tree_type], row["Tags"], max_context, os.path.join(output, "val"), tree_type)

def tuple_to_context(tuple):
    tuple = [t.replace(' ', '').replace(',', '') for t in tuple]
    return tuple[0] + "," + tuple[2] + "#" + tuple[3] + "," + tuple[1]

# processes example and writes to file. shuffle before !
def example_processing(tree, tags, max_context, file, tree_type):
    try:
        if tree_type == 'OPT':
            tuples = to_opt_tuples(tree)
        else:
            tuples = to_slt_tuples(tree)
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
            example += " " + tuple_to_context(t)
        example += " " * (max_context-count) + "\n"
        with open(file, 'a') as f:
            f.write(example)
    except Exception as e:
        print(e)

def main(dumps, database, output, minlength, max_context, top_tags, tree_type, seed, num_formulas):
    minlength = int(minlength)
    max_context = int(max_context)


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
        tags = pd.read_sql('select Tag, Count from "Tags" '
                                    'where Site="'+ site +'"', DB)

        formulas_tags_questions = pd.read_sql('select '+ tree_type +', Tags '
                                              'from "FormulasPosts" join FormulasPostsMathML '
                                              'on FormulasPosts.FormulaId = FormulasPostsMathML.FormulaId '
                                              'join "QuestionTags" '
                                              'on FormulasPosts.PostId = QuestionTags.QuestionId and FormulasPosts.Site = QuestionTags.Site '
                                              'where FormulasPosts.Site="'+ site +'" and TokenLength>='+str(minlength) + " and "+ tree_type +" != ''", DB)
        formulas_tags_answers = pd.read_sql('select '+ tree_type +', Tags '
                                            'from "FormulasPosts" join FormulasPostsMathML '
                                            'on FormulasPosts.FormulaId = FormulasPostsMathML.FormulaId '
                                            'join "AnswerMeta" '
                                            'on FormulasPosts.PostId = AnswerMeta.AnswerId and FormulasPosts.Site = AnswerMeta.Site '
                                            'join "QuestionTags" '
                                            'on AnswerMeta.QuestionId = QuestionTags.QuestionId and AnswerMeta.Site = QuestionTags.Site '
                                            'where FormulasPosts.Site="'+ site +'" and TokenLength>='+str(minlength) + " and "+ tree_type +" != ''", DB)
        DB.close()
        sorted_tags = tags.sort_values(by=['Count'], ascending=False)
        tags_dict = dict(zip(sorted_tags["Tag"][:int(top_tags)], sorted_tags["Count"][:int(top_tags)]))

        df = pd.concat([formulas_tags_questions, formulas_tags_answers])
        print("number of formulas in " + site + ": " + str(len(df)))
        if len(df[tree_type]) == 0:
            raise ValueError("No Formula Entries in Database for Site "+ site)

        df = remove_non_top_tag_formulas_and_tags(df, list(tags_dict.keys()), tree_type)
        print("number of formulas in " + site + " tagged with top " + str(top_tags) + " tag: " + str(len(df)))
        print("average tags per formula: "+ str(df["NumTags"].mean()))

        df = select_random_formulas(df, int(seed), int(num_formulas))
        print("number of formulas selected with seed "+str(seed)+": " + str(len(df)))
        print("average tags per formula: "+ str(df["NumTags"].mean()))

        if not os.path.isdir(output):
            os.mkdir(output)
        split_save(df, output, max_context, tree_type)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dumps",default="test_dumps", help="File containing stackexchange dump sites names to be processed")
    parser.add_argument("--database", default='../output/database.db', help="database")
    parser.add_argument("-o", "--output", default='../output/classification_data/', help="output directory")
    #parser.add_argument("-s", "--separate", default="yes", help="yes or no. Put training data in separate files for each site.")
    parser.add_argument("-f", "--minlength", default="3", help="integer. minimum token length of formulas")
    parser.add_argument("-c", "--context", default="200", help="max number of context fields")
    parser.add_argument("--top_tags", default=10, help="number of top tags")
    parser.add_argument("--seed", default=1234, help="seed for selecting random formulas")
    parser.add_argument("--num_formulas", default=1000, help="number of formulas to select")
    parser.add_argument("--opt", dest='opt', action='store_true')
    parser.add_argument("--slt", dest='opt', action='store_false')
    parser.set_defaults(opt=True)

    args = parser.parse_args()
    tree_type = 'OPT'
    if not args.opt:
        tree_type = 'SLT'

    main(args.dumps, args.database, args.output, args.minlength, args.context, args.top_tags,
         tree_type, args.seed, args.num_formulas)
