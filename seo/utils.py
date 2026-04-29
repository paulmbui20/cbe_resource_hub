def generate_meta_description(text, max_length=160):
    """
    Generate a meta description from text content
    """
    if not text:
        return ""

    # Strip HTML tags if present
    from django.utils.html import strip_tags
    clean_text = strip_tags(text)

    # Truncate to max_length
    if len(clean_text) <= max_length:
        return clean_text

    # Find last complete sentence within limit
    truncated = clean_text[:max_length]
    last_period = truncated.rfind('.')

    if last_period > max_length * 0.7:  # If we have at least 70% of text
        return clean_text[:last_period + 1]

    # Otherwise just truncate with ellipsis
    return clean_text[:max_length - 3] + '...'


def generate_keywords(name, *additional_terms):
    """
    Generate keywords from name and additional terms
    """
    keywords = [name.lower()]

    for term in additional_terms:
        if term:
            keywords.append(f"{name.lower()} {term.lower()}")
            keywords.append(f"{term.lower()} {name.lower()}")

    return ", ".join(keywords)
