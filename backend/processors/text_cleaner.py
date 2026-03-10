"""
processors/text_cleaner.py
Cleans raw tweet/Reddit text before NLP processing.
"""
import re
import html
import unicodedata


# ── Compiled Regex Patterns ───────────────────────────────────────────────────
_URL_RE       = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_HTML_TAG_RE  = re.compile(r"<[^>]+>")
_MENTION_RE   = re.compile(r"@\w+")
_HASHTAG_RE   = re.compile(r"#(\w+)")         # Keep the word, remove the #
_WHITESPACE   = re.compile(r"\s+")
_EMOJI_RE     = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002700-\U000027BF"  # dingbats
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)
_SPECIAL_CHARS = re.compile(r"[^\w\s\.\,\!\?\-\:\;\'\"]", re.UNICODE)


def clean_text(text: str, keep_mentions: bool = False) -> str:
    """
    Full cleaning pipeline for a raw tweet or Reddit post.

    Steps:
    1. HTML entity decode (&amp; → &)
    2. Remove HTML tags
    3. Remove URLs
    4. Optionally remove @mentions (keep for politician tracking)
    5. Normalize hashtags (#war → war)
    6. Remove emojis
    7. Remove non-ASCII special characters (keep punctuation)
    8. Normalize whitespace
    9. Strip leading/trailing whitespace

    Returns cleaned text string.
    """
    if not text:
        return ""

    # 1. Decode HTML entities
    text = html.unescape(text)

    # 2. Remove HTML tags
    text = _HTML_TAG_RE.sub(" ", text)

    # 3. Remove URLs
    text = _URL_RE.sub(" ", text)

    # 4. Handle mentions
    if not keep_mentions:
        text = _MENTION_RE.sub(" ", text)

    # 5. Normalize hashtags: #ceasefire → ceasefire
    text = _HASHTAG_RE.sub(r"\1", text)

    # 6. Remove emojis
    text = _EMOJI_RE.sub(" ", text)

    # 7. Unicode normalize — handle accented chars etc.
    text = unicodedata.normalize("NFKD", text)

    # 8. Remove excessive special chars (keep word chars + punctuation)
    text = _SPECIAL_CHARS.sub(" ", text)

    # 9. Normalize whitespace
    text = _WHITESPACE.sub(" ", text).strip()

    return text


def is_meaningful(text: str, min_length: int = 20, min_words: int = 4) -> bool:
    """
    Returns True if the text is long enough to be worth processing.
    Filters out very short or empty posts.
    """
    if not text:
        return False
    words = text.split()
    return len(text) >= min_length and len(words) >= min_words

