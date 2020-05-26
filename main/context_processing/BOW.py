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

class BOW:

    def corpus_from_pickles(self, directory, extend_existing = True):
        if extend_existing:
            corpus = self.unpickle_corpus(directory)
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
        self.pickle_corpus(directory, corpus)
        print("Corpus size = ", len(corpus))

    def pickle_corpus(self, directory, corpus):
        with open(os.path.join(directory, "corpus.pkl"),"wb") as f:
            pickle.dump(corpus,f)

    def unpickle_corpus(self, directory):
        with open(os.path.join(directory, "corpus.pkl"),"rb") as f:
            corpus = pickle.load(f)
        return corpus

    def vectorize_corpus(self, directory):
        corpus = self.unpickle_corpus(directory)

        self.vectorizer = CountVectorizer(max_df = 0.75, min_df = 2, max_features=10000)
        word_count_vector=self.vectorizer.fit_transform(corpus)
        self.tfidf_transformer=TfidfTransformer(smooth_idf=True,use_idf=True)
        self.tfidf_transformer.fit(word_count_vector)
        self.feature_names = self.vectorizer.get_feature_names()

    def get_top_n_tfidf(self, collection, n):
        count_vector=self.vectorizer.transform(collection)
        tf_idf_vector=self.tfidf_transformer.transform(count_vector)
        top_n = []
        for vector in tf_idf_vector:
            df = pd.DataFrame(vector.T.todense(), index=self.feature_names, columns=["tfidf"])
            df = df.sort_values(by=["tfidf"],ascending=False)
            top_n.append(df.head(n))
        return top_n

    def strip_texts(self, texts):
        texts = [context_processing.html_helper.clean_html(t) for t in texts]
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
