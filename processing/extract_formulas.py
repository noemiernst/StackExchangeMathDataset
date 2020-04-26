def formula_extr(text):
    formulas = []

    error = False
    if text.find('$') > -1:
        _,found,after = text.partition('$')
        while found:
            if text.find('$') > -1:
                formula,found,after = after.partition('$')

                if(formula.endswith('\\')):
                    formula_temp,found_temp,after = after.partition('$')
                    formula = formula + found + formula_temp
                if formula != '':
                    if found:
                        formulas.append(formula)
                    else:
                        error = True

                    _,found,after = after.partition('$')
                else:
                    formula,found,after = after.partition('$$')
                    if found:
                        formulas.append(formula)
                    else:
                        after = formula
                        error = True

                    _,found,after = after.partition('$')
            if error:
                break
    return formulas, error

# operatoren: z.B. &amp, &lt, &gt
