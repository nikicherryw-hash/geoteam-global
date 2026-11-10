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

