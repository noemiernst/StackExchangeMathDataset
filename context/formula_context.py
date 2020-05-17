import re
from nltk.corpus import stopwords
import html_helper

def get_formulas(text):
    formula = re.compile(r'(\$\$.*?\$\$|\$.*?\$)')
    return formula.findall(text)

def remove_formulas(text):
    return re.sub(r'(\$\$.*?\$\$|\$.*?\$)', '', text)

def tokenize(text):
    words = re.compile(r'\w+')
    tokens = words.findall(text)
    return tokens

def remove_stopwords(tokens):
    en_stops = set(stopwords.words('english'))
    no_stopwords = []
    for word in tokens:
        if word not in en_stops:
            no_stopwords.append(word)
    return no_stopwords

def get_context(text):
    text = html_helper.remove_images(text)
    text = html_helper.remove_links(text)
    paragraphs = html_helper.get_paragraphs(text)
    paragraphs = [remove_formulas(p) for p in paragraphs]
    token_lists = [remove_stopwords(tokenize(p)) for p in paragraphs]
    for list in token_lists:
        paragraphs.append(' '.join(str(x) for x in list))
    print(paragraphs)


with open('text', 'r') as file:
    data = file.read().replace('\n', '')
with open('text2', 'r') as file:
    data2 = file.read().replace('\n', '')
get_context(data)
get_context(data2)
