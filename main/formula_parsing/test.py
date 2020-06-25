from TangentCFT.TangentS.math_tan.exceptions import UnknownTagException
from TangentCFT.TangentS.math_tan.math_extractor import MathExtractor
import time
import latex2mathml.converter


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

def get_mathml2(formula):
    try:
        t = time.time()
        mathml = MathExtractor.parse_from_tex3(formula)
        print(time.time()-t)
    except NameError:
        mathml = "ERROR1"
    except UnknownTagException as e:
        print(e.tag)
        mathml = "ERROR?"
    print(formula + " " + mathml)
    return mathml

def get_mathml(formula):
    try:
        print(formula)
        mathml = latex2mathml.converter.convert(formula)
        cmml = MathExtractor.isolate_cmml(mathml)
        print(cmml)
    except IndexError:
        cmml = "ERROR"
    return cmml

get_slt(r"f\left(x\right) = 5")
get_mathml(r"f\left(x\right) = 5 = 3")
