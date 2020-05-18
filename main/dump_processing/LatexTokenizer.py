class LatexTokenizer:
    """Tokenizer for splitting LaTeX expressions into tokens"""

    def tokenize(self, eq):
        result = []
        last_token = ''
        for char in list(eq):
            if char == '\\':
                if last_token:
                    result.append(last_token)
                last_token = '\\'
            elif last_token and last_token[0] in ['\\']:
                if char.isalpha():
                    last_token += char
                else:
                    if last_token:
                        result.append(last_token)
                    last_token = char
            elif char.isdigit() or char == '.':  # TODO support , as decimal seperator?
                if last_token.replace('.', '').isdigit():
                    last_token += char
                else:
                    if last_token:
                        result.append(last_token)
                    last_token = char
            else:
                if last_token:
                    result.append(last_token)
                last_token = char
        result.append(last_token)
        assert ''.join(result) == eq
        return result
