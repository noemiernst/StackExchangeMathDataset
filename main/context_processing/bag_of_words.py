from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import os.path
try:
    import cPickle as pickle
except ImportError:
    import pickle

def bow(directory, num_words=5):
    questions = pd.read_pickle(os.path.join(directory, "questiontext.pkl"))
    docs = dict(("".join(("q",str(q))),t+ " " + b) for q,[t, b] in questions.items())
    questions = {}
    answers = pd.read_pickle(os.path.join(directory, "answertext.pkl"))
    docs.update(dict(("".join(("a",str(a))),t) for a,t in answers.items()))
    answers = {}
    comments = pd.read_pickle(os.path.join(directory, "commenttext.pkl"))
    docs.update(dict(("".join(("c",str(c))),t) for c,t in comments.items()))
    comments = {}

    doc_ids = docs.keys()
    doc_values = docs.values()

    vectorizer = TfidfVectorizer(sublinear_tf = True, max_df = 0.75, min_df = 2, max_features=10000)
    features = vectorizer.fit_transform(doc_values)
    feature_names = vectorizer.get_feature_names()

    ques_dict = {}
    answer_dict = {}
    comment_dict = {}

    for k,v in zip(doc_ids,features):
        key = int(k[1:])
        if k[0] == "q":
            df = pd.DataFrame(v.T.todense(), index=feature_names, columns=["tfidf"])
            df = df.sort_values(by=["tfidf"],ascending=False)
            ques_dict[key] = df.head(num_words)
        elif k[0] == "a":
            df = pd.DataFrame(v.T.todense(), index=feature_names, columns=["tfidf"])
            df = df.sort_values(by=["tfidf"],ascending=False)
            answer_dict[key] = df.head(num_words).to_dict()
        elif k[0] == "c":
            df = pd.DataFrame(v.T.todense(), index=feature_names, columns=["tfidf"])
            df = df.sort_values(by=["tfidf"],ascending=False)
            comment_dict[key] = df.head(num_words).to_dict()
    pass

import argparse
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i","--input",default= "../../output/", help = "input category name")
    args = parser.parse_args()
    bow(args.input)
