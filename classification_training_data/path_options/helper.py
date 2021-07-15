import random

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
