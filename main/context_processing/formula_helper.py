import re

def get_formulas(text):
    formula = re.compile(r'(\$\$.*?\$\$|\$.*?\$)')
    return formula.findall(text)

def remove_formulas(text):
    return re.sub(r'(\$\$.*?\$\$|\$.*?\$)', '', text)
