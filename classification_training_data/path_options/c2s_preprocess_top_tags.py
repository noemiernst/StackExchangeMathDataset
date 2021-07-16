import argparse
import sqlite3
import pandas as pd
#from math_tan.math_extractor import MathExtractor
from sklearn.model_selection import train_test_split
import os
import random
from helper import select_random_formulas
from paths_opt import to_opt_tuples
from paths_slt import to_slt_tuples

NUM_MODES = 2
# index 0: nodes and edges
# index 1: nodes only (only OPTs)


# remove all formulas that do not contain one of the top tags
# and also remove all other tags from the formulas
def remove_non_top_tag_formulas_and_tags(df, top_tags, tree_type):
    return_tree = []
    return_tags = []
    return_num_tags = []
    return_latex = []
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
            return_latex.append(row["LaTeXBody"])
    return pd.DataFrame({tree_type: return_tree, 'Tags': return_tags, "NumTags": return_num_tags, "LaTeXBody": return_latex}, columns=[tree_type, 'Tags', "NumTags", "LaTeXBody"])

def split_save(df, output, max_context, path_length, tree_type):
    train, test = train_test_split(df, test_size=0.2)
    val, test = train_test_split(test, test_size=0.5)

    s_only_nodes = "nodes_only"
    s_nodes_and_edges = "nodes_and_edges"

    outputs = [output] * NUM_MODES
    outputs[0] = os.path.join(output, s_nodes_and_edges)
    outputs[1] = os.path.join(output, s_only_nodes)

    for output in outputs:
        if not os.path.isdir(output):
            os.mkdir(output)

    outputs_train = [os.path.join(output, "train") for output in outputs]
    for output in outputs_train:
        open(output, 'w').close()
    print("Writing train file")
    for index, row in train.iterrows():
        example_processing(row[tree_type], row["Tags"], max_context, outputs_train, path_length, tree_type)

    outputs_test = [os.path.join(output, "test") for output in outputs]
    for output in outputs_test:
        open(output, 'w').close()
    print("Writing test file")
    for index, row in test.iterrows():
        example_processing(row[tree_type], row["Tags"], max_context, outputs_test, path_length, tree_type)

    outputs_val = [os.path.join(output, "val") for output in outputs]
    for output in outputs_val:
        open(output, 'w').close()
    print("Writing val file")
    for index, row in val.iterrows():
        example_processing(row[tree_type], row["Tags"], max_context, outputs_val, path_length, tree_type)

def path(path, length):
    if len(path) < length:
        length = len(path)
    string = ""
    for i in range(length):
        string += str(path[i])
        if i != length-1:
            string += "|"

    return string


def remove_edge_labels(path):
    p = []
    for segment in path:
        if (segment != 0) and (segment != 1):
            p.append(segment)
    return p


def tuple_to_context_nodes_and_edges(tuple, path_length):
    return tuple[0] + "," + path(tuple[1], path_length) + "," + tuple[2]

def tuple_to_context_nodes(tuple, path_length):
    return tuple[0] + "," + path(remove_edge_labels(tuple[1]), path_length) + "," + tuple[2]


def all_contexts(tuples, path_length, tree_type):
    examples = [""] * NUM_MODES

    if tree_type == 'OPT':
        for t in tuples:
            if len(t[1]) == 1:
                examples[0] += " " + tuple_to_context_nodes_and_edges(t, path_length)
                if (t[1][0] != 0) and (t[1][0] != 1):
                    examples[1] += " " + tuple_to_context_nodes(t, path_length)
            elif len(t[1]) == 0:
                pass
            else:
                examples[0] += " " + tuple_to_context_nodes_and_edges(t, path_length)
                examples[1] += " " + tuple_to_context_nodes(t, path_length)
    else:
        for t in tuples:
            if len(t[1]) == 0:
                pass
            else:
                examples[0] += " " + tuple_to_context_nodes_and_edges(t, path_length)

    return examples

# processes example and writes to file. shuffle before !
def example_processing(tree, tags, max_context, files, path_length, tree_type):
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

        examples = [example] * NUM_MODES
        contexts = all_contexts(tuples, path_length, tree_type)


        for i in range(NUM_MODES):
            if not ((tree_type == 'SLT') and (i == 1)):
                examples[i] += contexts[i]
                examples[i] += " " * (max_context-count) + "\n"

                with open(files[i], 'a') as f:
                    f.write(examples[i])


    except Exception as e:
        print(e)

def main(dumps, database, output, minlength, max_context, path_length, top_tags, tree_type, seed, num_formulas):
    path_length = int(path_length)
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

        formulas_tags_questions = pd.read_sql('select '+ tree_type +', Tags, LaTeXBody  '
                                              'from "FormulasPosts" join FormulasPostsMathML '
                                              'on FormulasPosts.FormulaId = FormulasPostsMathML.FormulaId '
                                              'join "QuestionTags" '
                                              'on FormulasPosts.PostId = QuestionTags.QuestionId and FormulasPosts.Site = QuestionTags.Site '
                                              'where FormulasPosts.Site="'+ site +'" and TokenLength>='+str(minlength) + " and OPT != '' and SLT != ''", DB)
        formulas_tags_answers = pd.read_sql('select '+ tree_type +', Tags, LaTeXBody  '
                                            'from "FormulasPosts" join FormulasPostsMathML '
                                            'on FormulasPosts.FormulaId = FormulasPostsMathML.FormulaId '
                                            'join "AnswerMeta" '
                                            'on FormulasPosts.PostId = AnswerMeta.AnswerId and FormulasPosts.Site = AnswerMeta.Site '
                                            'join "QuestionTags" '
                                            'on AnswerMeta.QuestionId = QuestionTags.QuestionId and AnswerMeta.Site = QuestionTags.Site '
                                            'where FormulasPosts.Site="'+ site +'" and TokenLength>='+str(minlength) + " and OPT != '' and SLT != ''", DB)
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

        output = os.path.join(output, tree_type.lower() + "_" + str(seed) + "_top" + str(top_tags))
        if not os.path.isdir(output):
            os.mkdir(output)
        split_save(df, output, max_context, path_length, tree_type)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dumps",default="test_dumps", help="File containing stackexchange dump sites names to be processed")
    parser.add_argument("--database", default='../../output/database.db', help="database")
    parser.add_argument("-o", "--output", default='../../output/classification_data/', help="output directory")
    #parser.add_argument("-s", "--separate", default="yes", help="yes or no. Put training data in separate files for each site.")
    parser.add_argument("-f", "--minlength", default="3", help="integer. minimum token length of formulas")
    parser.add_argument("-c", "--context", default="200", help="max number of context fields")
    parser.add_argument("-p", "--path", default="5", help="max path length")
    parser.add_argument("--top_tags", default=50, help="number of top tags")
    parser.add_argument("--seed", default=5678, help="seed for selecting random formulas")
    parser.add_argument("--num_formulas", default=50000, help="number of formulas to select")
    parser.add_argument("--opt", dest='opt', action='store_false')
    parser.add_argument("--slt", dest='opt', action='store_true')
    parser.set_defaults(opt=True)

    args = parser.parse_args()
    tree_type = 'OPT'
    if not args.opt:
        tree_type = 'SLT'

    main(args.dumps, args.database, args.output, args.minlength, args.context, args.path, args.top_tags,
         tree_type, args.seed, args.num_formulas)
