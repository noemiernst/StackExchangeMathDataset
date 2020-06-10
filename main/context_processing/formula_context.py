import re
import html_helper

def get_formulas(text):
    formula = re.compile(r'(\$\$.*?\$\$|\$.*?\$)')
    return formula.findall(text)

def remove_formulas(text):
    return re.sub(r'(\$\$.*?\$\$|\$.*?\$)', '', text)

def remove_newlines(text):
    return text.replace("\n", " ")

def tokenize(text):
    words = re.compile(r'\w+')
    tokens = words.findall(text)
    return tokens

#def remove_stopwords(tokens):
#    en_stops = set(stopwords.words('english'))
#    no_stopwords = []
#    for word in tokens:
#        if word not in en_stops:
#            no_stopwords.append(word)
#    return no_stopwords

def get_context(text):
    text = remove_newlines(text)
    paragraphs, begin_end = html_helper.get_paragraphs(text)
    paragraphs = [html_helper.remove_images(p) for p in paragraphs]
    paragraphs = [html_helper.remove_links(p) for p in paragraphs]
    paragraphs = [remove_formulas(p) for p in paragraphs]
    paragraphs = [p for p in paragraphs if p]
    token_lists = [remove_stopwords(tokenize(p)) for p in paragraphs]
    context = {"Sentences": [], "Range": [], "SentenceId": []}
    context["Range"] = begin_end
    for list in token_lists:
        context["Sentences"].append(' '.join(str(x) for x in list))
    return context
