import pandas as pd
import os.path
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
try:
    import cPickle as pickle
except ImportError:
    import pickle
import context_processing.html_helper
import context_processing.formula_helper
import pathlib
import time
import string
import sqlite3
import re

class BOW:

    def corpus_from_database(self, directory, database, site_name, extend_existing = True):
        self.corpus_dir = pathlib.Path(directory).parent.absolute()
        if extend_existing:
            corpus = self.unpickle_corpus()
        else:
            corpus = []
        DB = sqlite3.connect(database)
        questions = pd.read_sql('select Title, Body from "QuestionText" where Site="'+site_name+'"', DB)
        questions = list((t+ " " + b) for t, b in zip(questions["Title"], questions["Body"]))
        for i in range(len(questions)):
            t = questions.pop()
            # remove html tags
            t, _, _ = context_processing.html_helper.clean_html(t)
            # remove formulas
            re.sub(r'\$\$.*?\$\$|\$.*?\$', ' ', t)
            # remove punctuation
            t = t.translate(str.maketrans('', '', string.punctuation))
            corpus.append(t)
        #corpus.extend(self.strip_texts(questions))
        questions.clear()
        answers = pd.read_sql('select Body from "AnswerText" where Site="'+site_name+'"', DB)
        answers = list(answers["Body"])
        for i in range(len(answers)):
            t = answers.pop()
            # remove html tags
            t, _, _ = context_processing.html_helper.clean_html(t)
            # remove formulas
            re.sub(r'\$\$.*?\$\$|\$.*?\$', ' ', t)
            # remove punctuation
            t = t.translate(str.maketrans('', '', string.punctuation))
            corpus.append(t)
        #corpus.extend(self.strip_texts(answers))
        answers.clear()
        comments = pd.read_sql('select Text from "Comments" where Site="'+site_name+'"', DB)
        DB.close()
        comments = list(comments["Text"])
        for i in range(len(comments)):
            t = comments.pop()
            # remove html tags
            t, _, _ = context_processing.html_helper.clean_html(t)
            # remove formulas
            re.sub(r'\$\$.*?\$\$|\$.*?\$', ' ', t)
            # remove punctuation
            t = t.translate(str.maketrans('', '', string.punctuation))
            corpus.append(t)
        #corpus.extend(self.strip_texts(comments))
        comments.clear()
        self.pickle_corpus(corpus)
        print("Corpus size = ", len(corpus))

    def pickle_corpus(self, corpus):
        with open(os.path.join(self.corpus_dir, "corpus.pkl"),"wb") as f:
            pickle.dump(corpus,f)

    def unpickle_corpus(self):
        with open(os.path.join(self.corpus_dir, "corpus.pkl"),"rb") as f:
            corpus = pickle.load(f)
        return corpus

    def vectorize_corpus(self, stopwords):
        corpus = self.unpickle_corpus()

        self.vectorizer = CountVectorizer(stop_words=stopwords)
        word_count_vector=self.vectorizer.fit_transform(corpus)
        self.tfidf_transformer=TfidfTransformer(smooth_idf=True,use_idf=True)
        self.tfidf_transformer.fit(word_count_vector)
        self.feature_names = self.vectorizer.get_feature_names()


    #tf-idf over entire post/comment or just formula context
    def get_top_n_tfidf(self, dictionary, n, all = False):
        docs = list(dictionary.values())
        count_vector=self.vectorizer.transform(docs)
        tf_idf_vector=self.tfidf_transformer.transform(count_vector)
        top_n = {}
        print( "getting top n terms")
        t1 = time.time()

        formulaids = dictionary.keys()
        dictionary = {}

        for vector, key in zip(tf_idf_vector, formulaids):
            index = [self.feature_names[index] for index in vector.indices]
            term_tfidf = list(zip(index, vector.data))
            term_tfidf.sort(key=lambda pair: pair[1], reverse=True)

            top_n_string = ""
            if all:
                n = len(term_tfidf)
            for term, value in term_tfidf[:n]:
                top_n_string += "<"+term+ ", "+ str(value) + ">"
            top_n[key] = top_n_string

        print("get top n: "+ str(int((time.time()-t1)/60)) +"min " + str(int((time.time()-t1)%60)) + "sec")
        return top_n

    #tf-idf over entire post/comment or just formula context
    def get_top_n_tfidf2(self, dictionary, docs, n, tfidf = True, all = False):
        postids = list(docs.keys())
        docs = list(docs.values())
        count_vector=self.vectorizer.transform(docs)
        tf_idf_vector=self.tfidf_transformer.transform(count_vector)
        top_n = {}
        print( "getting top n terms")
        t1 = time.time()


        for vector, postid in zip(tf_idf_vector, postids):
            index = [self.feature_names[index] for index in vector.indices]
            term_tfidf = list(zip(index, vector.data))
            term_tfidf.sort(key=lambda pair: pair[1], reverse=True)

            for formulaid, formulacontext in (dictionary[postid]).items():
                terms = [(w, idf) for (w, idf) in term_tfidf if w in formulacontext]
                top_n_string = ""
                if all:
                    n = len(terms)
                if tfidf:
                    for term, value in terms[:n]:
                        top_n_string += "<"+term+ ", "+ str(value) + ">"
                else:
                    for term, value in terms[:n]:
                        top_n_string += "<"+term+">"
                top_n[formulaid] = top_n_string

        print("get top n: "+ str(int((time.time()-t1)/60)) +"min " + str(int((time.time()-t1)%60)) + "sec")
        return top_n

    def strip_texts(self, texts):
        temp = []
        for t in texts:
            text, strong, em = context_processing.html_helper.clean_html(t)
            temp.append(text)
        texts = [context_processing.formula_helper.remove_formulas(t) for t in temp]
        temp = []
        #texts = [t.split() for t in texts]
        table = str.maketrans('', '', string.punctuation)
        for words in texts:
            temp.append(words.translate(table).lower())
        return temp
