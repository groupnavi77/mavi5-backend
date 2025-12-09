import re

def clean_tag_string_and_split(tag_string):
    """
    Recibe la cadena de tags, elimina el '#' y divide por comas.
    """
    if not tag_string:
        return []
        
    # 1. Limpia cualquier '#' de la cadena completa
    cleaned_string = re.sub(r'#', '', tag_string)
    
    # 2. Divide la cadena limpia por comas y elimina espacios extra.
    tags = [t.strip() for t in cleaned_string.split(',') if t.strip()]
    
    return tags