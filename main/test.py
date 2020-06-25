from TangentCFT.TangentS.math_tan.exceptions import UnknownTagException
from TangentCFT.TangentS.math_tan.math_extractor import MathExtractor
from TangentCFT.TangentS.math_tan.latex_mml import LatexToMathML
from TangentCFT.TangentS.math_tan.symbol_tree import SymbolTree
import time
import latex2mathml.converter

import subprocess
import sys
import os
import platform

def get_slt(formula):
    try:
        t = time.time()
        slt = MathExtractor.parse_from_tex_opt(formula).tostring()
        print(time.time()-t)
    except NameError:
        slt = "ERROR1"
    except UnknownTagException as e:
        print(e.tag)
        slt = "?"
    print(formula + " " + slt)
    return slt

def get_mathml(formula):
    t = time.time()
    mathml = latex2mathml.converter.convert(formula)
    cmml = MathExtractor.isolate_cmml(mathml)
    print(formula + "   " + cmml)
    print(time.time()-t)
    return cmml

def get_mathml2(formula):
    t = time.time()
    mathml = LatexToMathML.convert_to_mathml2(formula)
    print(time.time()-t)
    print(mathml)
    cmml = MathExtractor.isolate_cmml(mathml)
    ##        print('LaTeX converted to MathML: \n' )
    current_tree = MathExtractor.convert_to_semanticsymbol(cmml)
    print(SymbolTree(current_tree).tostring())

def get_mathml3(formula):
    qvar_template_file = "/Users/noemiernst/Bachelorarbeit/StackExchangeMathDataset/main/TangentCFT/TangentS/math_tan/mws.sty.ltxml"
    if not os.path.exists(qvar_template_file):
        print('Tried %s' % qvar_template_file, end=": ")
        sys.exit("Stylesheet for wildcard is missing")

    t = time.time()
    use_shell = ('Windows' in platform.system())
    p2 = subprocess.Popen(
            ['latexmlmath', '--cmml=-', '--preload=amsmath', '--preload=amsfonts', '--preload=' + qvar_template_file,
             '-'], shell=use_shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, err) = p2.communicate(input=formula.encode())
    print(time.time()-t)
    return output

#get_mathml2(r"f\left(x\right) = 5 = 3")
#get_mathml3(r"f\left(x\right) = 5 = 3")

#print(get_mathml(r"f\left(x\right) = 5 = 3"))
#print(get_mathml(r'(3^2)^2 = 3x3(3x3) = "9x9"'))
print(get_mathml2(r'$f\left(x\right) = 5$\n\n'
                  r'$g\left(y\right) = 3$'))

#print(get_slt(r"f\left(x\right) = 5"))
