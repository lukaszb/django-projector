import re

EMAIL_RE = re.compile(r'[A-Z0-9+_\-\.]+@[0-9A-Z][.-0-9A-Z]*\.[A-Z]{2,6}',
    re.IGNORECASE)

def extract_emails(text):
    """
    Returns list of emails founded in a given ``text``.
    """
    emails = re.findall(EMAIL_RE, text)
    return emails

