from TangentCFT.Tangent.math_tan.math_extractor import MathExtractor

def get_slt(formula):
    return MathExtractor.parse_from_tex_opt(formula).tostring()
