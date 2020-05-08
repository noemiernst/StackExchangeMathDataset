import matplotlib.pyplot as plt
import sqlite3
import pandas as pd
import numpy as np

max_len = 50

def histogram(formulas):
    values = []
    possible_lengths = range(1,max_len+2)
    for formula in zip(formulas["Body"]):
        length = len(formula[0])
        if length >= max_len:
            values.append(max_len+1)
        else:
            values.append(length)
    fin = [ possible_lengths.index(i) for i in values]
    plt.hist(fin, bins=max_len,align="right",edgecolor='black', linewidth=1.2)
    plt.xticks(np.arange(0, max_len+2, step=5))

    plt.title("Formula Length Distribution")
    plt.xlabel("Length of formulas")
    plt.ylabel("Number of formulas")
    plt.show()

    plt.close()

DB = sqlite3.connect("../output/physics.db")
formulas = pd.read_sql('select Body from "'+ "Formulas_Posts"+'"', DB)
DB.close()
histogram(formulas)
