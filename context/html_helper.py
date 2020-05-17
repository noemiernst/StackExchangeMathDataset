import re

def strip_html(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, ' ', text)

def split_html(text):
    text = split_html(text)
    words = text.split()
    return words

def find_links(text):
    link = re.compile('<a.*?>.*?</a>')
    return link.findall(text)

def remove_links(text):
    return re.sub('<a.*?>.*?</a>', '', text)

def find_strong(text):
    bold = re.compile('<strong>.*?</strong>')
    return bold.findall(text)

def find_emphasized(text):
    em = re.compile('<em>.*?</em>')
    return em.findall(text)

def find_blockquotes(text):
    quote = re.compile('<blockquote>.*?</blockquote>')
    return quote.findall(text)

def find_math_containers(text):
    math = re.compile('<span class="math-container">.*?</span>')
    return math.findall(text)

def find_images(text):
    image = re.compile('<img.*?>')
    return image.findall(text)

def remove_images(text):
    return re.sub('<img.*?>', '', text)

def list(text):
    list = re.compile('<ol>.*?</ol>')
    return list.findall(text)

def remove_paragraph_tags(text):
    return re.sub(r'<(|/)p>', '', text)

# br tags? single one to force line breaks <br>
def get_paragraphs(text):
    paragraph = re.compile('<p>.*?</p>')
    all = paragraph.findall(text)
    all = [remove_paragraph_tags(p) for p in all]
    while("" in all) :
        all.remove("")
    if len(all) is 0:
        return text
    return all


