from formula_parsing.TangentCFT.TangentS.math_tan.symbol_tree import SymbolTree
from formula_parsing.TangentCFT.TangentS.math_tan.math_extractor import MathExtractor


def slt(pmml):
    if (pmml == None) or (pmml == ''):
        return ''
    pmml = MathExtractor.isolate_pmml(pmml)
    #print(SymbolTree(MathExtractor.convert_to_layoutsymbol(pmml)).tostring())
    try:
        current_tree = MathExtractor.convert_to_layoutsymbol(pmml)
    except:
        return ''
    return SymbolTree(current_tree).tostring()

def opt(cmml):
    if (cmml == None) or (cmml == ''):
        return ''
    cmml = MathExtractor.isolate_cmml(cmml)
    try:
        current_tree = MathExtractor.convert_to_semanticsymbol(cmml)
    except:
        return ''
    #print(SymbolTree(current_tree).tostring())
    return SymbolTree(current_tree).tostring()
