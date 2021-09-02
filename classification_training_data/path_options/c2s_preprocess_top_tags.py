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
import statistics
import tracemalloc

NUM_MODES = 4
# index 0: SLT and OPT segments mixed
# index 1: OPT nodes and edges
# index 2: OPT nodes only
# index 3: SLT nodes and edges

opt_total_paths = []
slt_total_paths = []


# remove all formulas that do not contain one of the top tags
# and also remove all other tags from the formulas
def remove_non_top_tag_formulas_and_tags(df, top_tags):
    return_opt = []
    return_slt = []
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
            return_opt.append(row["OPT"])
            return_slt.append(row["SLT"])
            return_tags.append(tag_string)
            return_num_tags.append(len(tags))
            return_latex.append(row["LaTeXBody"])
    return pd.DataFrame({"OPT": return_opt,"SLT": return_slt, 'Tags': return_tags, "NumTags": return_num_tags, "LaTeXBody": return_latex}, columns=['OPT', 'SLT', 'Tags', "NumTags", "LaTeXBody"])

def split_save(df, output, max_context, path_length, subtoken, seed):
    train, test = train_test_split(df, test_size=0.2, random_state=seed)
    val, test = train_test_split(test, test_size=0.5, random_state=seed)

    print("Split Data\nMemory: " + str(tracemalloc.get_traced_memory()))

    s_mixed = "mixed_slt_opt"
    s_opt_only_nodes = "opt_nodes_only"
    s_opt_nodes_and_edges = "opt_nodes_and_edges"
    s_slt_nodes_and_edges = "slt_nodes_and_edges"

    outputs = [output] * NUM_MODES
    outputs[0] = os.path.join(output, s_mixed)
    outputs[1] = os.path.join(output, s_opt_nodes_and_edges)
    outputs[2] = os.path.join(output, s_opt_only_nodes)
    outputs[3] = os.path.join(output, s_slt_nodes_and_edges)

    print("Create Output Array\nMemory: " + str(tracemalloc.get_traced_memory()))

    for output in outputs:
        if not os.path.isdir(output):
            os.mkdir(output)

    outputs_train = [os.path.join(output, "train") for output in outputs]
    for output in outputs_train:
        open(output, 'w').close()
    print("Writing train file")
    for index, row in train.iterrows():
        example_processing(row["OPT"], row["SLT"], row["Tags"], max_context, outputs_train, path_length, subtoken)
    del outputs_train

    print("Train file written\nMemory: " + str(tracemalloc.get_traced_memory()))

    outputs_test = [os.path.join(output, "test") for output in outputs]
    for output in outputs_test:
        open(output, 'w').close()
    print("Writing test file")
    for index, row in test.iterrows():
        example_processing(row["OPT"], row["SLT"], row["Tags"], max_context, outputs_test, path_length, subtoken)
    del outputs_test

    print("Test file written\nMemory: " + str(tracemalloc.get_traced_memory()))

    outputs_val = [os.path.join(output, "val") for output in outputs]
    for output in outputs_val:
        open(output, 'w').close()
    print("Writing val file")
    for index, row in val.iterrows():
        example_processing(row["OPT"], row["SLT"], row["Tags"], max_context, outputs_val, path_length, subtoken)
    del outputs_val


    print("Files written\nMemory: " + str(tracemalloc.get_traced_memory()))

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


"""
N! - Number
C! - Constant
V! - Variable
F! - Function
T! - Text
M! - Group Element (M!V-)/Matrix(M!M-)/Set(M!S-)/List(M!L-)/Delimited(M!D-)/MatrixRow(M!R!)/ Case (M!C!)
O! - Ordered operator (not commutative)
U! - Unordered operator (commutative)
+! - Compound operator (uses a subtree to define the operation)
E! - Error!
-! - Unknown type
$! - Temporary nodes
"""
def split_token(token):
    front = token[:2]
    back = token[2:]

    return front + "|" + back

def tuple_to_context_nodes_and_edges(tuple, path_length, subtoken):
    if subtoken:
        start = split_token(tuple[0])
        target = split_token(tuple[2])
    else:
        start = tuple[0]
        target = tuple[2]
    return start + "," + path(tuple[1], path_length) + "," + target

def tuple_to_context_nodes(tuple, path_length, subtoken):
    if subtoken:
        start = split_token(tuple[0])
        target = split_token(tuple[2])
    else:
        start = tuple[0]
        target = tuple[2]
    return start + "," + path(remove_edge_labels(tuple[1]), path_length) + "," + target


def all_contexts(opt_tuples, slt_tuples, path_length, subtoken):
    examples = [""] * NUM_MODES
    global opt_total_paths
    global slt_total_paths


    mixed = opt_tuples + slt_tuples
    random.shuffle(mixed)
    for t in mixed:
        if len(t[1]) == 0:
            pass
        else:
            examples[0] += " " + tuple_to_context_nodes_and_edges(t, path_length, subtoken)
    for t in opt_tuples:
        if len(t[1]) == 1:
            examples[1] += " " + tuple_to_context_nodes_and_edges(t, path_length, subtoken)
            if (t[1][0] != 0) and (t[1][0] != 1):
                examples[2] += " " + tuple_to_context_nodes(t, path_length, subtoken)
        elif len(t[1]) == 0:
            opt_total_paths[-1] -= 1
            pass
        else:
            examples[1] += " " + tuple_to_context_nodes_and_edges(t, path_length, subtoken)
            examples[2] += " " + tuple_to_context_nodes(t, path_length, subtoken)
    for t in slt_tuples:
        if len(t[1]) == 0:
            slt_total_paths[-1] -= 1
            pass
        else:
            examples[3] += " " + tuple_to_context_nodes_and_edges(t, path_length, subtoken)


    return examples

# processes example and writes to file. shuffle before !
def example_processing(opt, slt, tags, max_context, files, path_length, subtoken):
    try:
        global opt_total_paths
        global slt_total_paths
        opt_tuples = to_opt_tuples(opt)
        slt_tuples = to_slt_tuples(slt)
        tags = [tag[1:] for tag in tags.split(">") if len(tag) > 0]
        tags.sort()
        example = "|".join(tags)
        count = 0
        random.shuffle(opt_tuples)
        random.shuffle(slt_tuples)
        opt_total_paths.append(len(opt_tuples))
        slt_total_paths.append(len(slt_tuples))

        examples = [example] * NUM_MODES
        contexts = all_contexts(opt_tuples, slt_tuples, path_length, subtoken)

        for i in range(NUM_MODES):
            examples[i] += contexts[i]
            examples[i] += " " * (max_context-count) + "\n"

            with open(files[i], 'a') as f:
                f.write(examples[i])


    except Exception as e:
        print(e)

def main(dumps, database, output, minlength, maxlength, max_context, path_length, top_tags, seed, num_formulas, subtoken):

    tracemalloc.start()

    path_length = int(path_length)
    minlength = int(minlength)
    maxlength = int(maxlength)
    max_context = int(max_context)
    seed = int(seed)


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

        formulas_tags_questions = pd.read_sql('select OPT, SLT, Tags, LaTeXBody  '
                                              'from "FormulasPosts" join FormulasPostsMathML '
                                              'on FormulasPosts.FormulaId = FormulasPostsMathML.FormulaId '
                                              'join "QuestionTags" '
                                              'on FormulasPosts.PostId = QuestionTags.QuestionId and FormulasPosts.Site = QuestionTags.Site '
                                              'where FormulasPosts.Site="'+ site +'" and TokenLength>='+str(minlength) + ' and TokenLength<='+str(maxlength) + " and OPT != '' and SLT != ''", DB)
        formulas_tags_answers = pd.read_sql('select OPT, SLT, Tags, LaTeXBody  '
                                            'from "FormulasPosts" join FormulasPostsMathML '
                                            'on FormulasPosts.FormulaId = FormulasPostsMathML.FormulaId '
                                            'join "AnswerMeta" '
                                            'on FormulasPosts.PostId = AnswerMeta.AnswerId and FormulasPosts.Site = AnswerMeta.Site '
                                            'join "QuestionTags" '
                                            'on AnswerMeta.QuestionId = QuestionTags.QuestionId and AnswerMeta.Site = QuestionTags.Site '
                                            'where FormulasPosts.Site="'+ site +'" and TokenLength>='+str(minlength) + ' and TokenLength<='+str(maxlength) + " and OPT != '' and SLT != ''", DB)
        DB.close()
        sorted_tags = tags.sort_values(by=['Count'], ascending=False)
        del tags
        tags_dict = dict(zip(sorted_tags["Tag"][:int(top_tags)], sorted_tags["Count"][:int(top_tags)]))
        del sorted_tags

        print("Formulas Retrieved from DB\nMemory: " + str(tracemalloc.get_traced_memory()))

        df = pd.concat([formulas_tags_questions, formulas_tags_answers])
        del formulas_tags_questions
        del formulas_tags_answers
        print("number of formulas in " + site + ": " + str(len(df)))
        if len(df["OPT"]) == 0:
            raise ValueError("No Formula Entries in Database for Site "+ site)

        df = remove_non_top_tag_formulas_and_tags(df, list(tags_dict.keys()))
        print("number of formulas in " + site + " tagged with top " + str(top_tags) + " tag: " + str(len(df)))
        print("average tags per formula: "+ str(df["NumTags"].mean()))

        print("Removed non top tag Formulas and Tags\nMemory: " + str(tracemalloc.get_traced_memory()))

        df = select_random_formulas(df, int(seed), int(num_formulas))
        print("number of formulas selected with seed "+str(seed)+": " + str(len(df)))
        print("average tags per formula: "+ str(df["NumTags"].mean()))

        print("Selected Random Formulas\nMemory: " + str(tracemalloc.get_traced_memory()))

        sub = ""
        if subtoken:
            sub = "_subtoken"
        output = os.path.join(output, site + "_top" + str(top_tags) + "_" + str(seed) + sub)
        if not os.path.isdir(output):
            os.mkdir(output)
        split_save(df, output, max_context, path_length, subtoken, seed)

        global opt_total_paths
        global slt_total_paths
        print("Mean number of paths per opt formula: " + str(statistics.mean(opt_total_paths)))
        print("Mean number of paths per slt formula: " + str(statistics.mean(slt_total_paths)))
        print("Median of number of paths in opt formula: " + str(statistics.median(opt_total_paths)))
        print("Median of number of paths in slt formula: " + str(statistics.median(slt_total_paths)))

        print("Memory: " + str(tracemalloc.get_traced_memory()))
        tracemalloc.stop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dumps",default="test_dumps", help="File containing stackexchange dump sites names to be processed")
    parser.add_argument("--database", default='../../output/database.db', help="database")
    parser.add_argument("-o", "--output", default='../../output/classification_data/', help="output directory")
    #parser.add_argument("-s", "--separate", default="yes", help="yes or no. Put training data in separate files for each site.")
    parser.add_argument("-f", "--minlength", default="3", help="integer. minimum token length of formulas")
    parser.add_argument("--maxlength", default=50, help="integer. maximum token length of formulas")
    parser.add_argument("-c", "--context", default="200", help="max number of context fields")
    parser.add_argument("-p", "--path", default="5", help="max path length")
    parser.add_argument("--top_tags", default=50, help="number of top tags")
    parser.add_argument("--seed", default=5678, help="seed for selecting random formulas")
    parser.add_argument("--num_formulas", default=50000, help="number of formulas to select")
    parser.add_argument("--subtoken_encoding", dest='subtoken', action='store_true')

    args = parser.parse_args()

    main(args.dumps, args.database, args.output, args.minlength, args.maxlength, args.context, args.path, args.top_tags,
         args.seed, args.num_formulas, args.subtoken)
