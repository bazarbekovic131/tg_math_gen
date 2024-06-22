import re



def wrap_latex_code(latex_code):
    patterns = [
        r'\\begin{pmatrix}.*?\\end{pmatrix}',  # Environments like pmatrix
        r'\\[a-zA-Z]+(?:{[^}]+})*',  # General LaTeX commands with possible arguments
        r'\\frac{[^}]+}{[^}]+}',     # Fraction
        r'\\sqrt{[^}]+}',            # Square root
    ] # TODO: #1 add more

    combined_pattern = '|'.join(patterns) # Combine all patterns into a single pattern
    combined_pattern = re.compile(combined_pattern)

    def replacer(match):
        matched_text = match.group(0)
        if not (matched_text.startswith('$') and matched_text.endswith('$')):
            return f'$ {matched_text} $'
        return matched_text

    # Replace all matches in the LaTeX code
    wrapped_code = combined_pattern.sub(replacer, latex_code)
    return wrapped_code

example_code = r"""
Here is an equation: \pi = \frac{a}{b}.
This is a matrix: \begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}.
Here is a square root: \sqrt{4}.
Here is a vector: \vec{v}.
And an arrow: \rightarrow.
"""

wrapped_code = wrap_latex_code(example_code)
print(wrapped_code)
