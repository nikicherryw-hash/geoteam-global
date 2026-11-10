"""Conservative text identity checks; matching is not supplier verification."""
import re
import unicodedata


def normalized_identity(value):
    text = unicodedata.normalize('NFKC', str(value or '')).casefold()
    text = text.translate(str.maketrans({'–':'-', '—':'-', '‑':'-'}))
    text = re.sub(r'\b(?:ротакс|ротокс)\b', 'rotax', text)
    # Rotax and seller catalogues write 916 iS / 916iS interchangeably.
    # Keep the optional certified ``iSc`` suffix distinct from ``iS``.
    return re.sub(r'(?<=\d)\s+(?=is(?:c)?\b)', '', text)


def model_matches(query, candidate):
    """Keep every requested identifier, manufacturer token and variant.

    Unknown free-text queries are deliberately conservative. A match is a
    prerequisite for evidence, never proof that the source is authoritative.
    """
    target, found = normalized_identity(query), normalized_identity(candidate)
    tokens = re.findall(r'[^\W_]+(?:[-/][^\W_]+)*', target)
    if not tokens or not found.strip():
        return False
    for token in tokens:
        parts = re.split(r'[-/]', token)
        pattern = r'[-/\s]*'.join(re.escape(part) for part in parts)
        if not re.search(r'(?<!\w)' + pattern + r'(?!\w)', found):
            return False
    return True


def candidate_matches(query, candidate):
    """Accept a cited listing when its exact identifier and full identity agree.

    Sellers often put the manufacturer in the title and only the P/N in the
    model field.  A different numbered model must not pass because the title
    happens to mention the requested item as an alternative.
    """
    model = str(candidate.get('model') or '')
    part_number = str(candidate.get('part_number') or '')
    title = str(candidate.get('product_name') or '')
    numbered = [token for token in re.findall(r'[^\W_]+(?:[-/][^\W_]+)*', normalized_identity(query))
                if any(char.isdigit() for char in token)]
    exact_fields = ' '.join(value for value in (model, part_number) if value)
    if numbered and (not exact_fields or not all(model_matches(token, exact_fields) for token in numbered)):
        return False
    return model_matches(query, ' '.join((model, part_number, title)))
