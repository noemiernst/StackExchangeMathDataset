from TangentCFT.TangentS.math_tan.math_extractor import MathExtractor
from TangentCFT.TangentS.math_tan.exceptions import UnknownTagException

def get_slt(formula):
    try:
        slt = MathExtractor.parse_from_tex_opt(formula).tostring()
    except NameError:
        slt = "ERROR1"
    except UnknownTagException as e:
        print(e.tag)
        slt = "?"
    print(formula + " " + slt)
    return slt
