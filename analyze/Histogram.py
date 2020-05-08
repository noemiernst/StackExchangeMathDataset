import matplotlib.pyplot as plt
import sqlite3
import pandas as pd
import numpy as np
from LatexTokenizer import LatexTokenizer

class Histogram:

    def create_token_length_distribution(self, items, max_len =50):
        tokenizer = LatexTokenizer
        values = []
        possible_lengths = range(1,max_len+2)
        for item in items:
            tokens = tokenizer.tokenize(tokenizer, item)
            length = len(tokens)
            if length >= max_len:
                values.append(max_len+1)
            else:
                values.append(length)
        fin = [ possible_lengths.index(i) for i in values]
        plt.hist(fin, bins=max_len,align="right",edgecolor='black', linewidth=1.2)
        plt.xticks(np.arange(0, max_len+2, step=5))

        plt.title("Formula Length Distribution")
        plt.xlabel("Number of Tokens in Formulas")
        plt.ylabel("Number of Formulas")
        plt.show()

    def create_length_distribution(self, items, max_len =50):
        values = []
        possible_lengths = range(1,max_len+2)
        for item in items:
            length = len(item)
            if length >= max_len:
                values.append(max_len+1)
            else:
                values.append(length)
        fin = [ possible_lengths.index(i) for i in values]
        plt.hist(fin, bins=max_len,align="right",edgecolor='black', linewidth=1.2)
        plt.xticks(np.arange(0, max_len+2, step=5))

        plt.title("Formula Length Distribution")
        plt.xlabel("Length of formulas")
        plt.ylabel("Number of Formulas")
        plt.show()
