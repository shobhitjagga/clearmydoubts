"""
Convert LaTeX to plain ASCII text for WhatsApp/Twilio compatibility.
WhatsApp and Twilio don't support LaTeX rendering, so we convert to readable text.
"""
import re


def latex_to_text(text):
    """
    Convert LaTeX mathematical expressions to plain ASCII text.
    Handles common LaTeX commands and converts them to readable format.
    """
    if not text:
        return text
    
    # Remove LaTeX display math delimiters
    text = re.sub(r'\\\[', '', text)
    text = re.sub(r'\\\]', '', text)
    text = re.sub(r'\$\$', '', text)
    text = re.sub(r'\$', '', text)
    
    # Common mathematical symbols (order matters - do specific ones first)
    replacements = {
        # Functions (must come before other replacements that might match)
        r'\\sin\b': 'sin',
        r'\\cos\b': 'cos',
        r'\\tan\b': 'tan',
        r'\\cot\b': 'cot',
        r'\\sec\b': 'sec',
        r'\\csc\b': 'csc',
        r'\\log\b': 'log',
        r'\\ln\b': 'ln',
        r'\\exp\b': 'exp',
        r'\\arcsin\b': 'sin^-1',
        r'\\arccos\b': 'cos^-1',
        r'\\arctan\b': 'tan^-1',
        
        # Integrals and derivatives (must come before \\in)
        r'\\int\b': '∫',
        r'\\sum\b': 'Σ',
        r'\\prod\b': 'Π',
        r'\\partial\b': '∂',
        r'\\nabla\b': '∇',
        
        # Greek letters (common ones)
        r'\\alpha\b': 'alpha',
        r'\\beta\b': 'beta',
        r'\\gamma\b': 'gamma',
        r'\\delta\b': 'delta',
        r'\\epsilon\b': 'epsilon',
        r'\\theta\b': 'theta',
        r'\\lambda\b': 'lambda',
        r'\\mu\b': 'mu',
        r'\\pi\b': 'pi',
        r'\\sigma\b': 'sigma',
        r'\\phi\b': 'phi',
        r'\\omega\b': 'omega',
        
        # Operators
        r'\\times\b': '×',
        r'\\cdot\b': '·',
        r'\\div\b': '÷',
        r'\\pm\b': '±',
        r'\\mp\b': '∓',
        r'\\leq\b': '≤',
        r'\\geq\b': '≥',
        r'\\neq\b': '≠',
        r'\\approx\b': '≈',
        r'\\equiv\b': '≡',
        
        # Sets and logic (\\in must come after \\sin, \\int, etc.)
        r'\\notin\b': '∉',
        r'\\subset\b': '⊂',
        r'\\supset\b': '⊃',
        r'\\cup\b': '∪',
        r'\\cap\b': '∩',
        r'\\emptyset\b': '∅',
        r'\\in\b': '∈',  # Must be last among similar patterns
        
        # Fractions: \frac{a}{b} -> (a)/(b) or a/b
        r'\\frac\{([^}]+)\}\{([^}]+)\}': r'(\1)/(\2)',
        
        # Superscripts: x^{n} -> x^(n) or x^n
        r'\^\{([^}]+)\}': r'^(\1)',
        r'\^([a-zA-Z0-9])': r'^\1',
        
        # Subscripts: x_{n} -> x_(n) or x_n
        r'_\{([^}]+)\}': r'_(\1)',
        r'_([a-zA-Z0-9])': r'_\1',
        
        # Limits: \lim_{x \to a} -> lim(x->a)
        r'\\lim_\{([^}]+)\}': r'lim(\1)',
        r'\\to': '->',
        
        # Common commands
        r'\\left': '',
        r'\\right': '',
        r'\\,': ' ',  # thin space
        r'\\;': ' ',  # medium space
        r'\\!': '',   # negative space
        r'\\quad': ' ',
        r'\\qquad': '  ',
        r'\\text\{([^}]+)\}': r'\1',  # text mode
        r'\\mathrm\{([^}]+)\}': r'\1',
        r'\\mathbf\{([^}]+)\}': r'\1',
        r'\\mathit\{([^}]+)\}': r'\1',
        
        # Brackets and delimiters
        r'\\left\(': '(',
        r'\\right\)': ')',
        r'\\left\[': '[',
        r'\\right\]': ']',
        r'\\left\{': '{',
        r'\\right\}': '}',
        r'\\left\|': '|',
        r'\\right\|': '|',
        
        # Arrows
        r'\\rightarrow': '->',
        r'\\leftarrow': '<-',
        r'\\Rightarrow': '=>',
        r'\\Leftarrow': '<=',
        r'\\leftrightarrow': '<->',
        
        # Infinity and other symbols
        r'\\infty': '∞',
        r'\\partial': '∂',
        r'\\nabla': '∇',
        r'\\sum': 'Σ',
        r'\\prod': 'Π',
    }
    
    # Apply replacements
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)

    # Square root with braces: \sqrt{a} -> √(a)
    text = re.sub(r'\\sqrt\{([^}]+)\}', r'√(\1)', text)
    # Square root without braces: \sqrt a -> √(a)
    text = re.sub(r'\\sqrt\s+([a-zA-Z0-9]+)', r'√(\1)', text)
    # Plain sqrt(...) -> √(...)
    text = re.sub(r'\bsqrt\(([^)]+)\)', r'√(\1)', text)
    # Plain sqrt x -> √(x)
    text = re.sub(r'\bsqrt\s+([a-zA-Z0-9]+)', r'√(\1)', text)

    # Inverse trig forms: \sin^{-1} x -> sin^-1 x
    text = re.sub(r'sin\^\{-?1\}', r'sin^-1', text)
    text = re.sub(r'cos\^\{-?1\}', r'cos^-1', text)
    text = re.sub(r'tan\^\{-?1\}', r'tan^-1', text)
    text = re.sub(r'sin\^\(-?1\)', r'sin^-1', text)
    text = re.sub(r'cos\^\(-?1\)', r'cos^-1', text)
    text = re.sub(r'tan\^\(-?1\)', r'tan^-1', text)

    # Plain English inverse phrases: "sin inverse x" -> "sin^-1 x"
    text = re.sub(r'\b(sin|cos|tan)\s+inverse\b', r'\1^-1', text, flags=re.IGNORECASE)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Clean up extra parentheses around single characters
    text = re.sub(r'\(([a-zA-Z0-9])\)', r'\1', text)
    
    # Remove trailing/leading whitespace from each line
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    text = '\n'.join(lines)
    
    # Remove empty lines (but keep structure)
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    
    return text.strip()


def convert_math_expressions(text):
    """
    Main function to convert LaTeX math expressions in text to plain ASCII.
    Handles both inline and display math.
    """
    if not text:
        return text
    
    # First, handle display math blocks \[ ... \] - preserve line breaks
    def process_math_block(match):
        content = match.group(1)
        # Convert LaTeX to text
        converted = latex_to_text(content)
        # Preserve line breaks for readability
        return converted
    
    text = re.sub(
        r'\\\[(.*?)\\\]',
        process_math_block,
        text,
        flags=re.DOTALL
    )
    
    # Handle $$ ... $$ blocks
    text = re.sub(
        r'\$\$(.*?)\$\$',
        process_math_block,
        text,
        flags=re.DOTALL
    )
    
    # Handle inline math $ ... $ (single line)
    text = re.sub(
        r'\$(.*?)\$',
        lambda m: latex_to_text(m.group(1)),
        text
    )
    
    # Handle any remaining LaTeX commands in the text
    text = latex_to_text(text)
    
    # Clean up excessive line breaks but preserve structure
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text

