import os
import re

BASE_DIR = "/Users/emrah/Documents/Projeler/EnglishBus"
KURSLAR_DIR = os.path.join(BASE_DIR, "kurslar")
PROMPT_FILE = os.path.join(KURSLAR_DIR, "prompt.text")

def get_all_words():
    words = set()
    files = [f for f in os.listdir(KURSLAR_DIR) if f.endswith('.text') and f != "prompt.text"]
    for fname in files:
        path = os.path.join(KURSLAR_DIR, fname)
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                w = line.strip().lower()
                if w:
                    words.add(w)
    return words

def fix_prompt_file():
    valid_words = get_all_words()
    print(f"Found {len(valid_words)} unique words from text files.")
    
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # It causes issues if we just replace blindly.
    # We want to replace " word:" with "\nword:"
    # But only if "word" is in valid_words.
    # And we need to be careful about overlap? 
    # Since we are inserting \n, the string grows.
    
    # Better approach: find all indices of " word:"
    # We can use regex with a callback, or just iterative replacement.
    
    # Construct a huge regex? No, risky.
    # Let's iterate through the set of words and replace, but that might double replace.
    # e.g. "fireman" and "man". 
    # "fireman:" -> "\nfireman:"
    # "man:" -> "\nman:"
    # If we replace "man:" first, "fireman:" might become "fire\nman:".
    
    # Correct approach:
    # 1. Sort words by length descending.
    #    Actually regex `\b(word):` is safe-ish. But we are looking for ` word:` (space before).
    #    The file is one line. So `\s(word):`
    
    # Let's try to tokenize the string by "avoid: ... ".
    # Most prompts end with "avoid: ..." usually.
    # Or just use the regex `\s(key):` where key is in valid_words.
    
    # We will build a regex pattern of all words joined by OR.
    # Escape words just in case.
    escaped_words = [re.escape(w) for w in valid_words]
    # Sort by length desc to match longest first
    escaped_words.sort(key=len, reverse=True)
    
    pattern_str = r'\s(' + '|'.join(escaped_words) + r'):'
    pattern = re.compile(pattern_str)
    
    new_content = pattern.sub(r'\n\1:', content)
    
    # Also handle the very start of the file if it doesn't have a space?
    # It might be correct already.
    
    # Write back
    with open(PROMPT_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("Fixed prompt.text formatting.")

if __name__ == "__main__":
    fix_prompt_file()
