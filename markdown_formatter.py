"""
Convert Markdown to nicely formatted plain text for WhatsApp/Twilio.
WhatsApp doesn't support Markdown rendering, so we format it as readable plain text.
"""
import re
from latex_converter import convert_math_expressions


def convert_bold_markdown(text):
    """
    Convert markdown bold (**text**) to WhatsApp bold (*text*).
    Must be done before LaTeX conversion to avoid conflicts.
    """
    if not text:
        return text
    
    # Convert **text** to *text* (WhatsApp bold format)
    # Use non-greedy matching and handle multiple bold sections
    text = re.sub(r'\*\*([^*]+?)\*\*', r'*\1*', text)
    
    # Convert __text__ to *text* (alternative markdown bold)
    text = re.sub(r'__(.+?)__', r'*\1*', text)
    
    return text


def format_markdown_to_whatsapp(text):
    """
    Convert Markdown to nicely formatted plain text suitable for WhatsApp.
    Preserves structure and readability without markdown syntax.
    """
    if not text:
        return text
    
    # First, convert all markdown bold to WhatsApp bold format
    # This must be done before LaTeX conversion
    text = convert_bold_markdown(text)
    
    # Split into lines for better processing
    lines = text.split('\n')
    formatted_lines = []
    prev_was_header = False
    prev_was_list = False
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines (we'll add them back strategically)
        if not stripped:
            if formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')
            prev_was_header = False
            prev_was_list = False
            continue
        
        # Headers - format with proper spacing
        if stripped.startswith('#### '):
            # Sub-subsection (Step 1, Step 2, etc.)
            header_text = stripped[5:].strip()
            # Bold is already converted, just convert LaTeX
            header_text = convert_math_expressions(header_text)
            if formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')
            # Check if header already contains bold formatting (has * characters)
            # If it does, don't wrap the whole thing, just add the emoji
            if '*' in header_text:
                formatted_lines.append(f'🔹 {header_text}')
            else:
                formatted_lines.append(f'🔹 *{header_text}*')
            prev_was_header = True
            prev_was_list = False
        elif stripped.startswith('### '):
            # Subsection
            header_text = stripped[4:].strip()
            header_text = convert_math_expressions(header_text)
            if formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')
            formatted_lines.append('━━━━━━━━━━━━━━━━━━━━')
            # Check if header already contains bold formatting
            if '*' in header_text:
                formatted_lines.append(header_text)
            else:
                formatted_lines.append(f'*{header_text}*')
            formatted_lines.append('━━━━━━━━━━━━━━━━━━━━')
            prev_was_header = True
            prev_was_list = False
        elif stripped.startswith('## '):
            # Section
            header_text = stripped[3:].strip()
            header_text = convert_math_expressions(header_text)
            if formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')
            formatted_lines.append('━━━━━━━━━━━━━━━━━━━━')
            # Check if header already contains bold formatting
            if '*' in header_text:
                formatted_lines.append(header_text)
            else:
                formatted_lines.append(f'*{header_text}*')
            formatted_lines.append('━━━━━━━━━━━━━━━━━━━━')
            prev_was_header = True
            prev_was_list = False
        elif stripped.startswith('# '):
            # Main title
            header_text = stripped[2:].strip()
            header_text = convert_math_expressions(header_text)
            if formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')
            formatted_lines.append('━━━━━━━━━━━━━━━━━━━━')
            # Check if header already contains bold formatting
            if '*' in header_text:
                formatted_lines.append(header_text)
            else:
                formatted_lines.append(f'*{header_text}*')
            formatted_lines.append('━━━━━━━━━━━━━━━━━━━━')
            prev_was_header = True
            prev_was_list = False
        
        # Numbered lists
        elif re.match(r'^\d+\.\s+', stripped):
            match = re.match(r'^(\d+)\.\s+(.+)$', stripped)
            if match:
                list_num = match.group(1)
                list_item = match.group(2)
                list_item = convert_math_expressions(list_item)  # Convert LaTeX in list item
                if not prev_was_list and formatted_lines and formatted_lines[-1] != '':
                    formatted_lines.append('')
                formatted_lines.append(f'  {list_num}. {list_item}')
            prev_was_header = False
            prev_was_list = True
        
        # Bullet points
        elif re.match(r'^[-*+]\s+', stripped):
            list_item = re.sub(r'^[-*+]\s+', '', stripped)
            list_item = convert_math_expressions(list_item)  # Convert LaTeX in list item
            if not prev_was_list and formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')
            formatted_lines.append(f'  • {list_item}')
            prev_was_header = False
            prev_was_list = True
        
        # Regular text
        else:
            # Add spacing before new paragraphs if previous was header or list ended
            if prev_was_header or (prev_was_list and not re.match(r'^[-*+\d]', stripped)):
                if formatted_lines and formatted_lines[-1] != '':
                    formatted_lines.append('')
            
            # Convert LaTeX in this line
            formatted_line = convert_math_expressions(stripped)
            
            # Format inline code
            formatted_line = re.sub(r'`([^`]+)`', r'[\1]', formatted_line)
            
            formatted_lines.append(formatted_line)
            prev_was_header = False
            prev_was_list = False
    
    # Join lines and clean up
    text = '\n'.join(formatted_lines)
    
    # Remove any remaining ** markers (safety cleanup)
    text = re.sub(r'\*\*', '', text)
    
    # Clean up excessive blank lines (max 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Clean up leading/trailing whitespace
    text = text.strip()
    
    return text


def format_answer_for_whatsapp(text):
    """
    Main function to format AI-generated answers for WhatsApp.
    Combines LaTeX conversion and Markdown formatting.
    """
    if not text:
        return text
    
    # Convert markdown to WhatsApp-friendly format
    formatted = format_markdown_to_whatsapp(text)
    
    # Ensure proper spacing between sections
    formatted = re.sub(r'\n([📌•])', r'\n\n\1', formatted)
    formatted = re.sub(r'([📌•])\n', r'\1\n', formatted)
    
    # Clean up multiple spaces
    formatted = re.sub(r' {2,}', ' ', formatted)
    
    # Ensure consistent line breaks
    formatted = re.sub(r'\n{3,}', '\n\n', formatted)
    
    return formatted.strip()

