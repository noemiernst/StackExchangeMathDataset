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

class BOW:

    def corpus_from_pickles(self, directory, extend_existing = True):
        self.corpus_dir = pathlib.Path(directory).parent.absolute()
        if extend_existing:
            corpus = self.unpickle_corpus()
        else:
            corpus = []
        questions = pd.read_pickle(os.path.join(directory, "questiontext.pkl"))
        texts = list((t+ " " + b) for q,[t, b] in questions.items())
        corpus.extend(self.strip_texts(texts))
        answers = pd.read_pickle(os.path.join(directory, "answertext.pkl"))
        texts = list(t for a,t in answers.items())
        corpus.extend(self.strip_texts(texts))
        comments = pd.read_pickle(os.path.join(directory, "commenttext.pkl"))
        texts = list(t for c,t in comments.items())
        corpus.extend(self.strip_texts(texts))
        self.pickle_corpus(corpus)
        print("Corpus size = ", len(corpus))

    def pickle_corpus(self, corpus):
        with open(os.path.join(self.corpus_dir, "corpus.pkl"),"wb") as f:
            pickle.dump(corpus,f)

    def unpickle_corpus(self):
        with open(os.path.join(self.corpus_dir, "corpus.pkl"),"rb") as f:
            corpus = pickle.load(f)
        return corpus

    def vectorize_corpus(self):
        corpus = self.unpickle_corpus()

        self.vectorizer = CountVectorizer(max_df = 0.75, min_df = 2, max_features=10000)
        word_count_vector=self.vectorizer.fit_transform(corpus)
        self.tfidf_transformer=TfidfTransformer(smooth_idf=True,use_idf=True)
        self.tfidf_transformer.fit(word_count_vector)
        self.feature_names = self.vectorizer.get_feature_names()

    def get_top_n_tfidf(self, dictionary, n):
        count_vector=self.vectorizer.transform(dictionary.values())
        tf_idf_vector=self.tfidf_transformer.transform(count_vector)
        top_n = {}

        track1 = 0
        track2 = 0
        track4 = 0
        t1 = time.time()
        for vector, key in zip(tf_idf_vector, dictionary.keys()):
            t1 = time.time()
            # takes 1/3
            index = [self.feature_names[index] for index in vector.indices]
            term_tfidf = list(zip(index, vector.data))
            term_tfidf.sort(key=lambda pair: pair[1], reverse=True)
            track1 += time.time()-t1
            t2 = time.time()
            # around 1/3 of the time

            track2 +=  time.time()-t2
            t3 = time.time()
            # around 1/3 of the time
            top_n_string = ""
            for term, value in term_tfidf[:n]:
                top_n_string += "<"+term+ ", "+ str(value) + ">"
            top_n[key] = top_n_string
            track4 += time.time()-t3

        print("track1 = ", track1)
        print("track2 = ", track2)
        print("track4 = ", track4)
        print("get top n: "+ str(int((time.time()-t1)/60)) +"min " + str(int((time.time()-t1)%60)) + "sec")
        return top_n

    def strip_texts(self, texts):
        #TODO: strong and emphasized text
        temp = []
        for t in texts:
            text, strong, em = context_processing.html_helper.clean_html(t)
            temp.append(text)
        texts = [context_processing.formula_helper.remove_formulas(t) for t in texts]
        return texts


'''
with open('text', 'r') as file:
    data = file.read().replace('\n', '')
with open('text2', 'r') as file:
    data2 = file.read().replace('\n', '')
bow = BOW

corpus = bow.strip_texts(bow,[data, data2])

bow.corpus_from_pickles(bow, "../../output/", False)
bow.vectorize_corpus(bow, "../../output/")

print(bow.get_top_n_tfidf(bow, corpus, 5))
'''
