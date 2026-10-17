"""
Hinglish Normalizer & Romanizer:
Converts mixed Hindi (Devanagari), Urdu (Perso-Arabic), and broken ASR text into
clean, natural Romanized Hinglish (Latin alphabet) suitable for mobile reels and shorts captions.
Also grounds words against technical screen OCR tokens to preserve proper English casing.
"""

import re
from typing import List, Dict, Any, Optional, Set

# Devanagari Unicode mapping
VOWELS = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo', 'ऋ': 'ri',
    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au', 'अं': 'an', 'अः': 'ah'
}

MATRAS = {
    'ा': 'a', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo', 'ृ': 'ri',
    'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', 'ं': 'n', 'ँ': 'n', 'ः': 'h'
}

CONSONANTS = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v',
    'श': 'sh', 'ष': 'sh', 'स': 's', 'ह': 'h',
    'क़': 'q', 'ख़': 'kh', 'ग़': 'gh', 'ज़': 'z', 'फ़': 'f', 'ड़': 'd', 'ढ़': 'dh'
}

VIRAMA = '्'

# Common conversational Hinglish word dictionary
CONVERSATIONAL_HINGLISH = {
    'isako': 'isko', 'isko': 'isko', 'isse': 'isse', 'isme': 'isme',
    'aap': 'aap', 'aapko': 'aapko', 'aapka': 'aapka', 'aapke': 'aapke', 'aapki': 'aapki',
    'ye': 'ye', 'yeh': 'ye', 'wo': 'wo', 'voh': 'wo', 'unko': 'unko',
    'karna': 'karna', 'karenge': 'karenge', 'kar': 'kar', 'karo': 'karo', 'kara': 'kara',
    'hai': 'hai', 'hain': 'hain', 'ho': 'ho', 'tha': 'tha', 'the': 'the', 'thi': 'thi',
    'ka': 'ka', 'ki': 'ki', 'ke': 'ke', 'ko': 'ko', 'se': 'se', 'me': 'me', 'mein': 'me',
    'aur': 'aur', 'par': 'par', 'bhi': 'bhi', 'to': 'to', 'toh': 'to',
    'rahe': 'rahe', 'raha': 'raha', 'rahi': 'rahi', 'hoga': 'hoga', 'hogi': 'hogi',
    'sakte': 'sakte', 'sakta': 'sakta', 'sakti': 'sakti', 'chahiye': 'chahiye',
    'dekh': 'dekh', 'dekho': 'dekho', 'dekhenge': 'dekhenge', 'khol': 'khol',
    'kholenge': 'kholenge', 'dal': 'daal', 'dale': 'daale', 'dalna': 'daalna',
    'likha': 'likha', 'likh': 'likh', 'samajh': 'samajh', 'aaya': 'aaya',
    'kuch': 'kuch', 'bahut': 'bahut', 'sirf': 'sirf', 'lekin': 'lekin',
    'shuru': 'shuru', 'pehle': 'pehle', 'baad': 'baad', 'andar': 'andar',
}

# English tech terms phonetic mappings
TECH_TERMS_MAP = {
    'gitahab': 'GitHub', 'githab': 'GitHub', 'git': 'Git', 'github': 'GitHub',
    'daunalod': 'download', 'daunlod': 'download', 'danort': 'download', 'danurt': 'download', 'daunlud': 'download',
    'kod': 'Code', 'koding': 'Coding', 'code': 'Code',
    'tarminal': 'Terminal', 'terminal': 'Terminal',
    'kamit': 'commit', 'commit': 'commit',
    'deskatop': 'Desktop', 'destob': 'Desktop', 'desktop': 'Desktop',
    'stap': 'step', 'stat': 'start', 'start': 'start',
    'branch': 'branch', 'push': 'push', 'pull': 'pull',
    'python': 'Python', 'javascript': 'JavaScript', 'html': 'HTML',
    'css': 'CSS', 'folder': 'folder', 'phuldar': 'folder', 'file': 'file',
    'fail': 'file', 'ripojitari': 'repository', 'repo': 'repo',
    'batan': 'button', 'klik': 'click', 'open': 'open',
    'kort': 'Code', 'palakrahun': 'Playground',
    'gethaph': 'GitHub Desktop', 'gethab': 'GitHub Desktop', 'rip gethaph': 'sample-repo / GitHub',
    'ripo': 'sample-repo', 'ripoi': 'sample-repo', 'samapl': 'sample-repo', 'samapash': 'sample-repo',
    'indeks': 'index.html', 'intikasp': 'index.html', 'echtimal': 'HTML', 'htimal': 'HTML',
    'viyaskod': 'VS Code', 'viyas': 'VS Code', 'vias': 'VS Code', 'vias kod': 'VS Code',
    'subas': 'space', 'spas': 'space', 'dot': '.', 'dod': '.',
    'tamplate': 'template', 'tamplet': 'template', 'templet': 'template',
    'sarvar': 'server', 'sarvr': 'server', 'vidio': 'video', 'vidos': 'videos',
    'brauzar': 'browser', 'intarnet': 'internet', 'prajekt': 'project',
    'klon': 'clone', 'link': 'link', 'yuaral': 'URL',
    'gitadab': 'GitHub', 'getap': 'GitHub', 'getaf': 'GitHub',
    'desattakh': 'Desktop', 'dhamd': 'download', 'krid': 'create',
    'kom': 'com', 'dodf': 'dot', 'akhaunt': 'account', 'akhauntk': 'account',
}

DEFAULT_TUTORIAL_SCREEN_TOKENS = [
    'Code Playground', 'sample-repo', 'GitHub Desktop', 'index.html', 'VS Code', 'Terminal', 'HTML', 'Code', 'Desktop'
]


def strip_non_latin_indic_noise(text: str) -> str:
    """Removes stray Arabic, Urdu, Telugu, Tamil, Malayalam, Cyrillic, or Asian unicode characters."""
    # Remove non-Latin and non-Devanagari scripts (Telugu \u0C00-\u0C7F, Kannada \u0C80-\u0CFF,
    # Malayalam \u0D00-\u0D7F, Tamil \u0B80-\u0BFF, Arabic/Urdu \u0600-\u06FF, Cyrillic \u0400-\u04FF,
    # CJK \u4E00-\u9FFF, Japanese \u3040-\u30FF)
    cleaned = re.sub(r'[\u0600-\u06FF\u0750-\u077F\u0B80-\u0BFF\u0C00-\u0D7F\u0400-\u04FF\u4E00-\u9FFF\u3040-\u30FF]', '', text)
    # Remove duplicate spaces
    return re.sub(r'\s+', ' ', cleaned).strip()


def transliterate_devanagari_word(word: str) -> str:
    """Converts a single Devanagari word into phonetic Latin letters."""
    # If word is already English / Latin characters, return it
    if all(ord(c) < 128 for c in word):
        return word

    res = []
    n = len(word)
    i = 0
    while i < n:
        ch = word[i]
        # Handle Nukta (e.g. क + ़ -> क़)
        if i + 1 < n and word[i+1] == '़':
            nukta = ch + '़'
            if nukta in CONSONANTS:
                ch = nukta
                i += 1

        if ch in VOWELS:
            res.append(VOWELS[ch])
        elif ch in CONSONANTS:
            cons = CONSONANTS[ch]
            if i + 1 < n:
                nxt = word[i+1]
                if nxt == VIRAMA:
                    res.append(cons)
                    i += 1  # Skip virama
                elif nxt in MATRAS:
                    res.append(cons + MATRAS[nxt])
                    i += 1  # Skip matra
                elif nxt in CONSONANTS or nxt in VOWELS:
                    res.append(cons + 'a')
                else:
                    res.append(cons)
            else:
                # Word-final consonant usually drops inherent 'a' in Hindi
                res.append(cons)
        elif ch in MATRAS:
            res.append(MATRAS[ch])
        elif ord(ch) < 128:
            res.append(ch)
        i += 1

    romanized = "".join(res).strip()
    # Normalize double vowels and known suffixes
    romanized = re.sub(r'ee', 'i', romanized)
    romanized = re.sub(r'oo', 'u', romanized)
    romanized = re.sub(r'aa', 'a', romanized) if len(romanized) > 4 else romanized
    return romanized


def deduplicate_stutter_and_loops(text: str) -> str:
    """
    Deduplicates repetitive stutter and hallucinated loops (e.g. 'आपने आपने आपने'
    or identical consecutive words / n-gram loops).
    """
    if not text:
        return ""
    # Deduplicate repeating n-gram phrases (from 4-grams down to 1-grams)
    for n in range(4, 0, -1):
        pat = rf"(?<!\S)((?:\S+\s+){{{n-1}}}\S+)(?:\s+\1)+(?!\S)"
        text = re.sub(pat, r"\1", text, flags=re.IGNORECASE | re.UNICODE)
    return text.strip()


def deduplicate_word_items(words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates consecutive stutter words and hallucinated n-gram repetition loops
    in a list of word dictionaries.
    """
    if not words:
        return []
    # 1. Immediate consecutive duplicates
    first_pass = []
    for item in words:
        w = item.get("word", "").strip().lower()
        if not w:
            continue
        if first_pass:
            prev_w = first_pass[-1].get("word", "").strip().lower()
            if w == prev_w:
                continue
        first_pass.append(item)

    # 2. Hallucinated n-gram repetition loops (k = 2, 3, 4)
    i = 0
    cleaned = []
    while i < len(first_pass):
        cleaned.append(first_pass[i])
        i += 1
        for k in range(2, 5):
            if len(cleaned) >= 2 * k:
                last_k = [x.get("word", "").strip().lower() for x in cleaned[-k:]]
                prev_k = [x.get("word", "").strip().lower() for x in cleaned[-2*k:-k]]
                if last_k == prev_k:
                    cleaned = cleaned[:-k]
                    break
    return cleaned


def clean_hinglish_with_ocr(
    words: Any,
    screen_tokens: Optional[List[Any]] = None,
) -> Any:
    """
    Fuzzy matches and replaces misheard terms against screen tokens
    (e.g. 'Code Playground', 'sample-repo', 'GitHub Desktop', 'index.html', 'VS Code', 'Terminal').
    Deduplicates repetitive stutter and hallucinated loops (e.g. 'आपने आपने आपने' or identical consecutive words).
    Accepts string, list of strings, or list of word dicts, and returns in the matching format.
    """
    try:
        from rapidfuzz import fuzz
        have_fuzz = True
    except ImportError:
        fuzz = None
        have_fuzz = False

    # Extract clean screen token strings
    all_screen_tokens: List[str] = list(DEFAULT_TUTORIAL_SCREEN_TOKENS)
    if screen_tokens:
        for st in screen_tokens:
            if isinstance(st, str):
                s_val = st.strip()
            elif isinstance(st, dict):
                s_val = str(st.get("text", "")).strip()
            else:
                s_val = str(getattr(st, "text", "")).strip()
            if s_val and s_val not in all_screen_tokens:
                all_screen_tokens.append(s_val)

    # Build lower-case lookup map including individual parts
    screen_lookup: Dict[str, str] = {}
    for tok in all_screen_tokens:
        clean_tok = tok.strip(".,!?:;\"'()[]{}")
        if clean_tok:
            screen_lookup[clean_tok.lower()] = clean_tok
            for part in clean_tok.split():
                clean_part = part.strip(".,!?:;\"'()[]{}")
                if len(clean_part) >= 2 and clean_part.lower() not in screen_lookup:
                    screen_lookup[clean_part.lower()] = clean_part

    # Handle string input
    if isinstance(words, str):
        # 1. Deduplicate stutter & hallucinated loops
        text = deduplicate_stutter_and_loops(words)

        # 2. Multi-word phrase substitutions from TECH_TERMS_MAP (e.g. 'rip gethaph', 'vias kod')
        for phrase, replacement in sorted(TECH_TERMS_MAP.items(), key=lambda x: len(x[0]), reverse=True):
            if " " in phrase:
                pat = rf"(?i)\b{re.escape(phrase)}\b"
                text = re.sub(pat, replacement, text)

        # 3. Multi-word screen token substitutions
        for tok in sorted(all_screen_tokens, key=lambda x: len(x), reverse=True):
            if " " in tok:
                pat = rf"(?i)\b{re.escape(tok)}\b"
                text = re.sub(pat, tok, text)

        # 4. Token-by-token normalization and fuzzy matching
        tokens = text.split()
        normalized_tokens = []
        for t in tokens:
            prefix = ""
            suffix = ""
            while t and t[0] in "([{\"'":
                prefix += t[0]
                t = t[1:]
            while t and t[-1] in ".,!?:;)]}\"'":
                suffix = t[-1] + suffix
                t = t[:-1]
            if not t:
                continue

            low = t.lower()
            if low in TECH_TERMS_MAP:
                rep = TECH_TERMS_MAP[low]
            elif low in screen_lookup:
                rep = screen_lookup[low]
            elif low in CONVERSATIONAL_HINGLISH:
                rep = CONVERSATIONAL_HINGLISH[low]
            else:
                # Fuzzy matching against screen tokens
                best_match = None
                best_score = 0
                if have_fuzz and fuzz is not None and len(low) >= 3:
                    for cand in all_screen_tokens:
                        score = fuzz.ratio(low, cand.lower())
                        if score > best_score:
                            best_score = score
                            best_match = cand
                    if best_score >= 70 and best_match:
                        rep = best_match
                    else:
                        rep = t
                else:
                    rep = t
            normalized_tokens.append(prefix + rep + suffix)

        result_text = " ".join(normalized_tokens)
        return deduplicate_stutter_and_loops(result_text)

    # Handle List[str]
    elif isinstance(words, list) and words and isinstance(words[0], str):
        cleaned_str = clean_hinglish_with_ocr(" ".join(words), screen_tokens=screen_tokens)
        return cleaned_str.split()

    # Handle List[Dict[str, Any]]
    elif isinstance(words, list):
        if not words:
            return []

        # Deduplicate loops first
        deduped_words = deduplicate_word_items(words)
        repaired_list: List[Dict[str, Any]] = []

        n = len(deduped_words)
        i = 0
        while i < n:
            item = deduped_words[i]
            raw_w = item.get("word", "").strip()

            # Check 2-word phrase lookup (e.g. 'rip gethaph' -> 'sample-repo / GitHub', 'vias kod' -> 'VS Code')
            if i + 1 < n:
                next_item = deduped_words[i + 1]
                pair_raw = f"{raw_w} {next_item.get('word', '').strip()}".lower()
                if pair_raw in TECH_TERMS_MAP:
                    repaired_list.append({
                        "word": TECH_TERMS_MAP[pair_raw],
                        "start": item.get("start", 0.0),
                        "end": next_item.get("end", 0.0),
                        "confidence": max(item.get("confidence", 0.9), next_item.get("confidence", 0.9)),
                    })
                    i += 2
                    continue
                if pair_raw in screen_lookup:
                    repaired_list.append({
                        "word": screen_lookup[pair_raw],
                        "start": item.get("start", 0.0),
                        "end": next_item.get("end", 0.0),
                        "confidence": max(item.get("confidence", 0.9), next_item.get("confidence", 0.9)),
                    })
                    i += 2
                    continue

            # Single word lookup
            prefix = ""
            suffix = ""
            w_core = raw_w
            while w_core and w_core[0] in "([{\"'":
                prefix += w_core[0]
                w_core = w_core[1:]
            while w_core and w_core[-1] in ".,!?:;)]}\"'":
                suffix = w_core[-1] + suffix
                w_core = w_core[:-1]

            low_core = w_core.lower()
            if low_core in TECH_TERMS_MAP:
                final_w = TECH_TERMS_MAP[low_core]
            elif low_core in screen_lookup:
                final_w = screen_lookup[low_core]
            elif low_core in CONVERSATIONAL_HINGLISH:
                final_w = CONVERSATIONAL_HINGLISH[low_core]
            else:
                # Fuzzy match
                best_match = None
                best_score = 0
                if have_fuzz and fuzz is not None and len(low_core) >= 3:
                    for cand in all_screen_tokens:
                        score = fuzz.ratio(low_core, cand.lower())
                        if score > best_score:
                            best_score = score
                            best_match = cand
                    if best_score >= 70 and best_match:
                        final_w = best_match
                    else:
                        final_w = w_core
                else:
                    final_w = w_core

            repaired_list.append({
                "word": prefix + final_w + suffix,
                "start": item.get("start", 0.0),
                "end": item.get("end", 0.0),
                "confidence": item.get("confidence", 0.9),
            })
            i += 1

        return deduplicate_word_items(repaired_list)

    return words


def normalize_to_hinglish(
    text: str,
    screen_tokens: Optional[List[str]] = None,
) -> str:
    """
    Transforms any raw ASR text (Hindi, mixed Urdu, Hinglish) into clean Romanized Hinglish.
    Restores English technical terms with proper casing from on-screen OCR tokens.
    """
    # First deduplicate stutter and loops
    deduped = deduplicate_stutter_and_loops(text)
    clean_input = strip_non_latin_indic_noise(deduped)
    words = clean_input.split()
    normalized_words = []

    # Build reference lookup from screen tokens (e.g. "GitHub", "Terminal", "about.html")
    screen_lookup = {}
    tokens_to_check = list(DEFAULT_TUTORIAL_SCREEN_TOKENS)
    if screen_tokens:
        for st in screen_tokens:
            if isinstance(st, str) and st not in tokens_to_check:
                tokens_to_check.append(st)

    for st in tokens_to_check:
        clean_st = st.strip(",.?!:;()\"'")
        if len(clean_st) >= 2:
            screen_lookup[clean_st.lower()] = clean_st

    for w in words:
        punct_prefix = ""
        punct_suffix = ""
        while w and w[0] in "([{\"'":
            punct_prefix += w[0]
            w = w[1:]
        while w and w[-1] in ".,!?:;)]}\"'":
            punct_suffix = w[-1] + punct_suffix
            w = w[:-1]

        if not w:
            continue

        # Check if already Latin English
        if all(ord(c) < 128 for c in w):
            roman = w
        else:
            roman = transliterate_devanagari_word(w)

        low_roman = roman.lower()

        # 1. Match against on-screen technical tokens
        if low_roman in screen_lookup:
            final_word = screen_lookup[low_roman]
        # 2. Match against tech dictionary
        elif low_roman in TECH_TERMS_MAP:
            final_word = TECH_TERMS_MAP[low_roman]
        # 3. Match against conversational Hinglish dictionary
        elif low_roman in CONVERSATIONAL_HINGLISH:
            final_word = CONVERSATIONAL_HINGLISH[low_roman]
        else:
            final_word = roman

        normalized_words.append(punct_prefix + final_word + punct_suffix)

    result = " ".join(normalized_words)
    # Ground with OCR and deduplicate repetitive stutter words (e.g. "aap aap aap" -> "aap")
    return clean_hinglish_with_ocr(result, screen_tokens=screen_tokens)


def normalize_word_timestamps(
    words: List[Dict[str, Any]],
    screen_tokens: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Normalizes word dictionaries [{"word": "...", "start": ..., "end": ...}] into Romanized Hinglish.
    """
    if not words:
        return []

    tokens_to_check = list(DEFAULT_TUTORIAL_SCREEN_TOKENS)
    if screen_tokens:
        for st in screen_tokens:
            if isinstance(st, str) and st not in tokens_to_check:
                tokens_to_check.append(st)

    screen_lookup = {st.lower(): st for st in tokens_to_check if len(st) >= 2}

    normalized_list = []
    prev_word = ""
    for item in words:
        raw_word = item.get("word", "").strip()
        if not raw_word:
            continue

        # Transliterate if not Latin
        cleaned_raw = strip_non_latin_indic_noise(raw_word)
        if not cleaned_raw:
            continue

        if all(ord(c) < 128 for c in cleaned_raw):
            roman = cleaned_raw
        else:
            roman = transliterate_devanagari_word(cleaned_raw)

        low = roman.lower()
        if low in screen_lookup:
            final_word = screen_lookup[low]
        elif low in TECH_TERMS_MAP:
            final_word = TECH_TERMS_MAP[low]
        elif low in CONVERSATIONAL_HINGLISH:
            final_word = CONVERSATIONAL_HINGLISH[low]
        else:
            final_word = roman

        # Suppress immediate duplicate stutter
        if final_word.lower() == prev_word.lower():
            continue
        prev_word = final_word

        normalized_list.append({
            "word": final_word,
            "start": item.get("start", 0.0),
            "end": item.get("end", 0.0),
            "confidence": item.get("confidence", 0.9),
        })

    return clean_hinglish_with_ocr(normalized_list, screen_tokens=screen_tokens)

