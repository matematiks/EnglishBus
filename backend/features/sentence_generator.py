import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional

# =========================================================
# V13 ENGINE LOGIC
# =========================================================

@dataclass(frozen=True)
class Word:
    text: str
    pos: str                 # noun, verb, adj, pron, q_word
    tags: frozenset
    req_sub: frozenset = frozenset()
    req_obj: frozenset = frozenset()
    base: Optional[str] = None
    third: Optional[str] = None
    past: Optional[str] = None
    ing: Optional[str] = None
    plural: Optional[str] = None


def adapt_vocab(rich_db: dict) -> list[Word]:
    words = []
    for wid, w in rich_db.items():
        # Map DB types to V13 POS
        pos_map = {
            "sub": "pron" if w["text"] in ["I","you","he","she","it","we","they"] else "noun",
            "obj": "noun",
            "verb": "verb",
            "adj": "adj",
            "q_word": "q_word"
        }
        
        db_pos = w.get("type", "unknown")
        if db_pos not in pos_map:
            continue
            
        words.append(
            Word(
                text=w["text"],
                pos=pos_map[db_pos],
                tags=frozenset(w.get("tags", [])),
                req_sub=frozenset(w.get("req_sub", [])),
                req_obj=frozenset(w.get("req_obj", [])),
                base=w.get("base"),
                third=w.get("morph", {}).get("3s"),
                past=w.get("past"),
                ing=w.get("ing"),
                plural=w.get("plural"),
            )
        )
    return words


class SmartIndex:
    def __init__(self, words: list[Word]):
        self.by_pos = defaultdict(list)
        self.by_pos_tag = defaultdict(list)

        for w in words:
            self.by_pos[w.pos].append(w)
            for t in w.tags:
                self.by_pos_tag[(w.pos, t)].append(w)

    def pick(self, pos: str, tag: Optional[str] = None) -> Word:
        pool = self.by_pos_tag[(pos, tag)] if tag else self.by_pos[pos]
        if not pool:
            # Fallback for strict tags in limited vocab
             if tag: pool = self.by_pos[pos] # Broaden search
             if not pool: raise ValueError(f"No word for pos={pos}")
        return random.choice(pool)

    def pick_filtered(self, pos: str, required_tags: frozenset) -> Word:
        # Legacy method - kept if needed but we should use specific requirement checks
        pool = [
            w for w in self.by_pos[pos]
            if not required_tags or (w.tags & required_tags)
        ]
        if not pool: pool = self.by_pos[pos]
        if not pool: raise ValueError("No words available")
        return random.choice(pool)

    def pick_verb_for_subject(self, subj_tags: frozenset) -> Word:
        """ Select a verb where verb.req_sub has intersection with subj_tags """
        # If verb has NO req_sub, it's generic. If it has req_sub, it must match.
        pool = [
            w for w in self.by_pos["verb"]
            if not w.req_sub or (w.req_sub & subj_tags)
        ]
        if not pool:
            # Fallback: lenient search usually not good here, but prevents specific crash
            # Try to find 'any' verb if strict failed, or raise?
            # Let's try to return broad verbs
            pool = [w for w in self.by_pos["verb"] if "human" in w.req_sub] 
        
        if not pool: pool = self.by_pos["verb"] # Total fallback
        if not pool: raise ValueError("No verbs available")
        return random.choice(pool)

    def pick_object_for_verb(self, req_obj: frozenset) -> Word:
        """ Select a noun where noun.tags intersects with req_obj """
        if not req_obj:
            # Verb takes any object? Or intransitive? 
            # If intransitive, this shouldn't be called ideally, but safely pick generic object
            return self.pick("noun")
            
        pool = [
            w for w in self.by_pos["noun"]
            if (w.tags & req_obj)
        ]
        if not pool:
            # Fallback: Pick any noun (creates nonsense but avoids crash)
            # improved: pick 'object' tag as safe fallback
            pool = [w for w in self.by_pos["noun"] if "object" in w.tags]

        if not pool: pool = self.by_pos["noun"]
        if not pool: raise ValueError("No objects available")
        return random.choice(pool)


class Morph:
    @staticmethod
    def verb(verb: Word, subj: Word) -> str:
        if subj.text.lower() in {"he", "she", "it"}:
            return verb.third or verb.base or verb.text
        return verb.text

    @staticmethod
    def plural(noun: Word) -> str:
        if noun.plural:
            return noun.plural
        if "countable" not in noun.tags:
            return noun.text
        if noun.text.endswith("y"):
            return noun.text[:-1] + "ies"
        if noun.text.endswith(("s", "x", "ch", "sh")):
            return noun.text + "es"
        return noun.text + "s"

    @staticmethod
    def article(noun: Word) -> str:
        if "countable" not in noun.tags:
            return "some"
        # Check start of word
        return "an" if noun.text[0].lower() in "aeiou" else "a"

    @staticmethod
    def copula(subj: Word) -> str:
        s = subj.text.lower()
        if s == "i":
            return "am"
        if s in {"he", "she", "it"}:
            return "is"
        return "are"


class SentenceEngineV13:
    def __init__(self, rich_db: dict):
        adapted = adapt_vocab(rich_db)
        self.index = SmartIndex(adapted)

    # -------------------------
    # STATEMENT (SVO)
    # -------------------------

    def make_statement(self) -> tuple[str, str]:
        # Try to pick a pronoun subject first (simpler)
        subj = None
        for p_type, p_tag in [("pron", "human"), ("noun", "human"), ("noun", "animal")]:
            try:
                subj = self.index.pick(p_type, p_tag)
                break
            except: continue
        
        if not subj:
            # Fallback to any noun (e.g. Car, if Vehicle supported)
            try: subj = self.index.pick("noun")
            except: raise ValueError("No subject available")
            
        # verb → req_sub compatible
        verb = self.index.pick_verb_for_subject(subj.tags)
        
        # object → req_obj compatible
        obj = self.index.pick_object_for_verb(verb.req_obj)

        parts = [subj.text, Morph.verb(verb, subj)]

        # Article + Adjective + Noun logic
        article = Morph.article(obj)
        adj_text = ""
        
        if random.random() < 0.4:
            try:
                adj = self.index.pick("adj")
                adj_text = adj.text
            except: pass

        if adj_text:
             parts.extend([article, adj_text])
        else:
             parts.append(article)
        
        # Pluralize randomly? No, strict to singular for simple SVO + Article agreement.
        # "He eats an apple" vs "He eats apples".
        # If we used 'some', we could pluralize. For 'a/an', singular is mandatory.
        # Let's keep singular for now as Morph.article returns a/an/some correctly.
        noun_text = obj.text 
        if article == "some":
            noun_text = Morph.plural(obj)
            
        parts.append(noun_text)

        sentence = " ".join(parts).capitalize() + "."
        return sentence, obj.text

    # -------------------------
    # COPULA (Subject + Be + Adj/Noun)
    # -------------------------

    def make_copula(self) -> tuple[str, str]:
        try:
            subj = self.index.pick("pron", "human")
        except:
            return self.make_statement() # Fallback

        cop = Morph.copula(subj)
        
        # Predicate: Adjective or Noun
        if random.random() < 0.7:
             try:
                pred = self.index.pick("adj")
                pred_text = pred.text
             except:
                return self.make_statement()
        else:
             # "I am a student"
             try:
                pred = self.index.pick("noun", "job") # Job or role
             except:
                return self.make_statement()
             pred_text = f"a {pred.text}"

        sentence = f"{subj.text} {cop} {pred_text}.".capitalize()
        # Keyword is predicate (e.g. happy, student)
        return sentence, pred.text.replace("a ", "")

    # -------------------------
    # QUESTION (Wh + Do/Does + S + V + O)
    # -------------------------

    def make_question(self) -> tuple[str, str]:
        try:
            q = self.index.pick("q_word")
            
            # Prioritize Human Subjects for questions
            subj = None
            for p_type, p_tag in [("pron", "human"), ("noun", "human"), ("noun", "animal")]:
                try:
                    subj = self.index.pick(p_type, p_tag)
                    break
                except: continue
            
            if not subj: subj = self.index.pick("sub") # Fallback

            verb = self.index.pick_verb_for_subject(subj.tags)
        except:
            return self.make_statement()
        
        # Handle 'who' -> subject question? simplified to 'Who likes apple?'
        if q.text.lower() == "who":
             # Who likes x?
             # Treat 'Who' as 3rd person singular human
             verb = self.index.pick_verb_for_subject(frozenset(["human"]))
             obj = self.index.pick_object_for_verb(verb.req_obj)
             # "Who likes the apple?"
             article = Morph.article(obj)
             return f"Who {Morph.verb(verb, Word('he','sub',frozenset()))} {article} {obj.text}?", obj.text

        aux = "does" if subj.text.lower() in {"he", "she", "it"} else "do"
        
        # Check if question asks for object (What)
        if "ask_object" in q.tags:
            # "What do you want?" (Transitive verb needed)
            # Pick verb that NEEDS object
            # For now standard logic is fine
            sentence = f"{q.text} {aux} {subj.text} {verb.text}?"
            return sentence, verb.text

        # Otherwise add object
        obj = self.index.pick_object_for_verb(verb.req_obj)
        article = Morph.article(obj)
        # Simplified question object usually "the" or bare or 'a'
        
        sentence = f"{q.text} {aux} {subj.text} {verb.text} {article} {obj.text}?"
        return sentence, obj.text

    # -------------------------
    # DISPATCHER
    # -------------------------

    def generate_one(self, complexity=0.5):
        r = random.random()
        # Balance distribution
        if r < 0.50:
            return self.make_statement()
        if r < 0.75:
            return self.make_copula()
        return self.make_question()


# ==========================================
# RICH VOCABULARY KNOWLEDGE BASE
# ==========================================
RICH_VOCAB_DB = {
    # --- SUBJECTS (Human) ---
    "I": {"type": "sub", "text": "I", "person": 1, "tags": ["human"], "usage": 0},
    "you": {"type": "sub", "text": "you", "person": 2, "tags": ["human"], "usage": 0},
    "he": {"type": "sub", "text": "he", "person": 3, "tags": ["human"], "usage": 0},
    "she": {"type": "sub", "text": "she", "person": 3, "tags": ["human"], "usage": 0},
    "we": {"type": "sub", "text": "we", "person": 1, "tags": ["human"], "usage": 0},
    "they": {"type": "sub", "text": "they", "person": 3, "tags": ["human"], "usage": 0},
    
    # --- VERBS ---
    "eat": {
        "type": "verb", "text": "eat", 
        "req_sub": ["human", "animal"], "req_obj": ["food"], 
        "morph": {"3s": "eats"}, "usage": 0
    },
    "drink": {
        "type": "verb", "text": "drink", 
        "req_sub": ["human", "animal"], "req_obj": ["drink"], 
        "morph": {"3s": "drinks"}, "usage": 0
    },
    "want": {
        "type": "verb", "text": "want",
        "req_sub": ["human", "animal"], "req_obj": ["object", "food", "drink", "toy", "clothes"],
        "morph": {"3s": "wants"}, "usage": 0
    },
    "have": {
        "type": "verb", "text": "have",
        "req_sub": ["human", "animal"], "req_obj": ["object", "food", "drink", "toy", "family", "body"],
        "morph": {"3s": "has"}, "usage": 0
    },
    "like": {
        "type": "verb", "text": "like",
        "req_sub": ["human", "animal"], "req_obj": ["object", "food", "drink", "toy", "human", "animal"],
        "morph": {"3s": "likes"}, "usage": 0
    },
    "see": {
        "type": "verb", "text": "see",
        "req_sub": ["human", "animal"], "req_obj": ["visible"],
        "morph": {"3s": "sees"}, "usage": 0
    },
    "read": {
        "type": "verb", "text": "read",
        "req_sub": ["human"], "req_obj": ["readable"], # V11 Strict
        "morph": {"3s": "reads"}, "usage": 0
    },
    "write": {
        "type": "verb", "text": "write",
        "req_sub": ["human"], "req_obj": ["readable", "paper", "book"],
        "morph": {"3s": "writes"}, "usage": 0
    },
    "open": {
        "type": "verb", "text": "open",
        "req_sub": ["human"], "req_obj": ["openable"], # V11 Strict
        "morph": {"3s": "opens"}, "usage": 0
    },
    "close": {
        "type": "verb", "text": "close",
        "req_sub": ["human"], "req_obj": ["openable"], # Assumed same as open
        "morph": {"3s": "closes"}, "usage": 0
    },
    "wash": {
        "type": "verb", "text": "wash",
        "req_sub": ["human"], "req_obj": ["washable"], # V11 Strict
        "morph": {"3s": "washes"}, "usage": 0
    },
    "clean": {
        "type": "verb", "text": "clean",
        "req_sub": ["human"], "req_obj": ["object", "place", "room"],
        "morph": {"3s": "cleans"}, "usage": 0
    },
    "know": {
        "type": "verb", "text": "know",
        "req_sub": ["human"], "req_obj": ["human", "place"],
        "morph": {"3s": "knows"}, "usage": 0
    },
    "think": {
        "type": "verb", "text": "think",
        "req_sub": ["human"], "req_obj": ["object"], # Simplified
        "morph": {"3s": "thinks"}, "usage": 0
    },
    "make": {
        "type": "verb", "text": "make",
        "req_sub": ["human"], "req_obj": ["object", "food", "drink", "toy"],
        "morph": {"3s": "makes"}, "usage": 0
    },
    "help": {
        "type": "verb", "text": "help",
        "req_sub": ["human"], "req_obj": ["human", "animal"],
        "morph": {"3s": "helps"}, "usage": 0
    },
    "look": {
        "type": "verb", "text": "look at", 
        "req_sub": ["human", "animal"], "req_obj": ["visible"],
        "morph": {"3s": "looks at"}, "usage": 0
    },
    "listen": {
        "type": "verb", "text": "listen to",
        "req_sub": ["human"], "req_obj": ["music", "human"],
        "morph": {"3s": "listens to"}, "usage": 0
    },
    
    # --- INTRANSITIVE VERBS (SVO HACK) ---
    "go": {
        "type": "verb", "text": "go to", 
        "req_sub": ["human", "animal"], "req_obj": ["place"],
        "morph": {"3s": "goes to"}, "usage": 0
    },
    "come": {
        "type": "verb", "text": "come to",
        "req_sub": ["human", "animal"], "req_obj": ["place"],
        "morph": {"3s": "comes to"}, "usage": 0
    },
    "walk": {
        "type": "verb", "text": "walk to",
        "req_sub": ["human", "animal"], "req_obj": ["place"],
        "morph": {"3s": "walks to"}, "usage": 0
    },
    "run": {
        "type": "verb", "text": "run to",
        "req_sub": ["human", "animal"], "req_obj": ["place"],
        "morph": {"3s": "runs to"}, "usage": 0
    },
    "stay": {
        "type": "verb", "text": "stay at",
        "req_sub": ["human"], "req_obj": ["place", "home"],
        "morph": {"3s": "stays at"}, "usage": 0
    },
    "live": {
        "type": "verb", "text": "live in",
        "req_sub": ["human"], "req_obj": ["place", "city"],
        "morph": {"3s": "lives in"}, "usage": 0
    },
    "sit": {
        "type": "verb", "text": "sit on",
        "req_sub": ["human", "animal"], "req_obj": ["object", "furniture"],
        "morph": {"3s": "sits on"}, "usage": 0
    },
    "sleep": {
        "type": "verb", "text": "sleep in",
        "req_sub": ["human", "animal"], "req_obj": ["room", "object"], # bed is object
        "morph": {"3s": "sleeps in"}, "usage": 0
    },
    
    # --- OBJECTS ---
    "apple": {"type": "obj", "text": "apple", "tags": ["food", "object", "visible", "countable"], "det_whitelist": ["indefinite", "definite", "possessive"], "usage": 0},
    "banana": {"type": "obj", "text": "banana", "tags": ["food", "object", "visible", "countable"], "det_whitelist": ["indefinite", "definite", "possessive"], "usage": 0},
    "water": {"type": "obj", "text": "water", "tags": ["drink", "object", "visible"], "det_whitelist": ["quantity", "definite"], "usage": 0},
    "milk": {"type": "obj", "text": "milk", "tags": ["drink", "object", "visible"], "det_whitelist": ["quantity", "definite"], "usage": 0},
    "book": {"type": "obj", "text": "book", "tags": ["object", "readable", "visible", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "door": {"type": "obj", "text": "door", "tags": ["object", "visible", "countable", "openable"], "det_whitelist": ["definite", "indefinite"], "usage": 0},
    "window": {"type": "obj", "text": "window", "tags": ["object", "visible", "countable", "openable"], "det_whitelist": ["definite", "indefinite"], "usage": 0},
    "car": {"type": "obj", "text": "car", "tags": ["object", "vehicle", "visible", "countable", "washable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    # V11: hand, face -> washable
    "hand": {"type": "obj", "text": "hand", "tags": ["object", "body", "washable", "countable"], "det_whitelist": ["possessive", "definite"], "usage": 0},
    "face": {"type": "obj", "text": "face", "tags": ["object", "body", "washable"], "det_whitelist": ["possessive", "definite"], "usage": 0},
    
    # --- ADJECTIVES ---
    "big": {"type": "adj", "text": "big", "usage": 0},
    "small": {"type": "adj", "text": "small", "usage": 0},
    "red": {"type": "adj", "text": "red", "usage": 0},
    "blue": {"type": "adj", "text": "blue", "usage": 0},
    "happy": {"type": "adj", "text": "happy", "usage": 0},
    "sad": {"type": "adj", "text": "sad", "usage": 0},
    "hot": {"type": "adj", "text": "hot", "usage": 0},
    "cold": {"type": "adj", "text": "cold", "usage": 0},
    
    # --- QUESTIONS ---
    "what": {"type": "q_word", "text": "What", "tags": ["ask_object"], "usage": 0},
    "where": {"type": "q_word", "text": "Where", "tags": [], "usage": 0},
    
    
    # --- NUMBERS (Adjectives/Quantifiers) ---
    "one": {"type": "adj", "text": "one", "usage": 0},
    "two": {"type": "adj", "text": "two", "usage": 0},
    "three": {"type": "adj", "text": "three", "usage": 0},
    "four": {"type": "adj", "text": "four", "usage": 0},
    "five": {"type": "adj", "text": "five", "usage": 0},
    "six": {"type": "adj", "text": "six", "usage": 0},
    "seven": {"type": "adj", "text": "seven", "usage": 0},
    "eight": {"type": "adj", "text": "eight", "usage": 0},
    "nine": {"type": "adj", "text": "nine", "usage": 0},
    "ten": {"type": "adj", "text": "ten", "usage": 0},
    "twenty": {"type": "adj", "text": "twenty", "usage": 0},
    "thirty": {"type": "adj", "text": "thirty", "usage": 0},
    "fifty": {"type": "adj", "text": "fifty", "usage": 0},
    "hundred": {"type": "adj", "text": "hundred", "usage": 0},

    # --- TIME & ADVERBS ---
    "time": {"type": "obj", "text": "time", "tags": ["time", "abstract"], "det_whitelist": ["definite", "indefinite"], "usage": 0},
    "morning": {"type": "obj", "text": "morning", "tags": ["time"], "det_whitelist": ["definite", "indefinite"], "usage": 0},
    "afternoon": {"type": "obj", "text": "afternoon", "tags": ["time"], "det_whitelist": ["definite", "indefinite"], "usage": 0},
    "evening": {"type": "obj", "text": "evening", "tags": ["time"], "det_whitelist": ["definite", "indefinite"], "usage": 0},
    "night": {"type": "obj", "text": "night", "tags": ["time"], "det_whitelist": ["definite"], "usage": 0},
    "day": {"type": "obj", "text": "day", "tags": ["time"], "det_whitelist": ["definite", "indefinite"], "usage": 0},
    "today": {"type": "adv", "text": "today", "adv_type": "time", "usage": 0},
    "tomorrow": {"type": "adv", "text": "tomorrow", "adv_type": "time", "usage": 0},
    "yesterday": {"type": "adv", "text": "yesterday", "adv_type": "time", "usage": 0},
    "later": {"type": "adv", "text": "later", "adv_type": "time", "usage": 0},
    "now": {"type": "adv", "text": "now", "adv_type": "time", "usage": 0},
    "again": {"type": "adv", "text": "again", "adv_type": "freq", "usage": 0},
    "early": {"type": "adj", "text": "early", "usage": 0}, # Also adv
    "late": {"type": "adj", "text": "late", "usage": 0},   # Also adv

    # --- KITCHEN & HOUSEHOLD ---
    "cup": {"type": "obj", "text": "cup", "tags": ["object", "kitchen", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "glass": {"type": "obj", "text": "glass", "tags": ["object", "kitchen", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "bottle": {"type": "obj", "text": "bottle", "tags": ["object", "kitchen", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "plate": {"type": "obj", "text": "plate", "tags": ["object", "kitchen", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "spoon": {"type": "obj", "text": "spoon", "tags": ["object", "kitchen", "tool", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "fork": {"type": "obj", "text": "fork", "tags": ["object", "kitchen", "tool", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "knife": {"type": "obj", "text": "knife", "tags": ["object", "kitchen", "tool", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "breakfast": {"type": "obj", "text": "breakfast", "tags": ["food", "meal"], "det_whitelist": ["definite"], "usage": 0},
    "lunch": {"type": "obj", "text": "lunch", "tags": ["food", "meal"], "det_whitelist": ["definite"], "usage": 0},
    "dinner": {"type": "obj", "text": "dinner", "tags": ["food", "meal"], "det_whitelist": ["definite"], "usage": 0},
    "towel": {"type": "obj", "text": "towel", "tags": ["object", "bathroom", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "soap": {"type": "obj", "text": "soap", "tags": ["object", "bathroom"], "det_whitelist": ["quantity"], "usage": 0},
    "toilet": {"type": "obj", "text": "toilet", "tags": ["object", "bathroom"], "det_whitelist": ["definite"], "usage": 0},
    "toilet paper": {"type": "obj", "text": "toilet paper", "tags": ["object", "bathroom"], "det_whitelist": ["quantity"], "usage": 0},

    # --- ANIMALS (V11) ---
    "dog": {"type": "obj", "text": "dog", "tags": ["animal", "visible", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "cat": {"type": "obj", "text": "cat", "tags": ["animal", "visible", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "rabbit": {"type": "obj", "text": "rabbit", "tags": ["animal", "visible", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "sheep": {"type": "obj", "text": "sheep", "tags": ["animal", "visible"], "plural": "sheep", "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "horse": {"type": "obj", "text": "horse", "tags": ["animal", "visible", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "donkey": {"type": "obj", "text": "donkey", "tags": ["animal", "visible", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "monkey": {"type": "obj", "text": "monkey", "tags": ["animal", "visible", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "cow": {"type": "obj", "text": "cow", "tags": ["animal", "visible", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "duck": {"type": "obj", "text": "duck", "tags": ["animal", "visible", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "bird": {"type": "obj", "text": "bird", "tags": ["animal", "visible", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "mouse": {"type": "obj", "text": "mouse", "tags": ["animal", "visible", "countable"], "plural": "mice", "det_whitelist": ["indefinite", "definite"], "usage": 0},

    # --- FAMILY & PEOPLE (V11) ---
    "mother": {"type": "sub", "text": "mother", "tags": ["human", "family"], "det_whitelist": ["possessive", "definite"], "usage": 0},
    "father": {"type": "sub", "text": "father", "tags": ["human", "family"], "det_whitelist": ["possessive", "definite"], "usage": 0},
    "son": {"type": "sub", "text": "son", "tags": ["human", "family"], "det_whitelist": ["possessive", "definite"], "usage": 0},
    "daughter": {"type": "sub", "text": "daughter", "tags": ["human", "family"], "det_whitelist": ["possessive", "definite"], "usage": 0},
    "sister": {"type": "sub", "text": "sister", "tags": ["human", "family"], "det_whitelist": ["possessive", "definite"], "usage": 0},
    "brother": {"type": "sub", "text": "brother", "tags": ["human", "family"], "det_whitelist": ["possessive", "definite"], "usage": 0},
    "baby": {"type": "sub", "text": "baby", "tags": ["human", "family"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "friend": {"type": "sub", "text": "friend", "tags": ["human"], "det_whitelist": ["possessive", "definite"], "usage": 0},
    "boy": {"type": "sub", "text": "boy", "tags": ["human"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "girl": {"type": "sub", "text": "girl", "tags": ["human"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "man": {"type": "sub", "text": "man", "tags": ["human"], "plural": "men", "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "woman": {"type": "sub", "text": "woman", "tags": ["human"], "plural": "women", "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "teacher": {"type": "sub", "text": "teacher", "tags": ["human", "job"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "student": {"type": "sub", "text": "student", "tags": ["human", "job"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "doctor": {"type": "sub", "text": "doctor", "tags": ["human", "job"], "det_whitelist": ["indefinite", "definite"], "usage": 0},

    # --- FOOD & DRINKS (Extensive V11) ---
    "tea": {"type": "obj", "text": "tea", "tags": ["drink", "food"], "det_whitelist": ["quantity"], "usage": 0},
    "coffee": {"type": "obj", "text": "coffee", "tags": ["drink", "food"], "det_whitelist": ["quantity"], "usage": 0},
    "juice": {"type": "obj", "text": "juice", "tags": ["drink", "food"], "det_whitelist": ["quantity"], "usage": 0},
    "egg": {"type": "obj", "text": "egg", "tags": ["food", "countable"], "det_whitelist": ["indefinite", "definite", "quantity"], "usage": 0},
    "sandwich": {"type": "obj", "text": "sandwich", "tags": ["food", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "sugar": {"type": "obj", "text": "sugar", "tags": ["food", "ingredient"], "det_whitelist": ["quantity"], "usage": 0},
    "salt": {"type": "obj", "text": "salt", "tags": ["food", "ingredient"], "det_whitelist": ["quantity"], "usage": 0},
    "cheese": {"type": "obj", "text": "cheese", "tags": ["food"], "det_whitelist": ["quantity"], "usage": 0},
    "meat": {"type": "obj", "text": "meat", "tags": ["food"], "det_whitelist": ["quantity"], "usage": 0},
    "chicken": {"type": "obj", "text": "chicken", "tags": ["food", "animal"], "det_whitelist": ["quantity", "indefinite"], "usage": 0},
    "fish": {"type": "obj", "text": "fish", "tags": ["food", "animal"], "det_whitelist": ["quantity", "indefinite"], "usage": 0},
    "rice": {"type": "obj", "text": "rice", "tags": ["food"], "det_whitelist": ["quantity"], "usage": 0},
    "pasta": {"type": "obj", "text": "pasta", "tags": ["food"], "det_whitelist": ["quantity"], "usage": 0},
    "soup": {"type": "obj", "text": "soup", "tags": ["food"], "det_whitelist": ["quantity"], "usage": 0},
    "salad": {"type": "obj", "text": "salad", "tags": ["food"], "det_whitelist": ["quantity", "indefinite"], "usage": 0},
    "vegetable": {"type": "obj", "text": "vegetable", "tags": ["food", "countable"], "det_whitelist": ["indefinite"], "usage": 0},
    "potato": {"type": "obj", "text": "potato", "tags": ["food", "countable"], "det_whitelist": ["indefinite"], "usage": 0},
    "tomato": {"type": "obj", "text": "tomato", "tags": ["food", "countable"], "det_whitelist": ["indefinite"], "usage": 0},
    "fruit": {"type": "obj", "text": "fruit", "tags": ["food"], "det_whitelist": ["quantity"], "usage": 0},
    "orange": {"type": "obj", "text": "orange", "tags": ["food", "countable"], "det_whitelist": ["indefinite"], "usage": 0},

    # --- PLACES (V11) ---
    "school": {"type": "obj", "text": "school", "tags": ["place", "location"], "det_whitelist": ["definite"], "usage": 0},
    "class": {"type": "obj", "text": "class", "tags": ["place", "location"], "det_whitelist": ["definite"], "usage": 0},
    "home": {"type": "obj", "text": "home", "tags": ["place", "location"], "det_whitelist": [], "usage": 0}, # Go home (no to)
    "house": {"type": "obj", "text": "house", "tags": ["place", "location", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "room": {"type": "obj", "text": "room", "tags": ["place", "location", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "kitchen": {"type": "obj", "text": "kitchen", "tags": ["place", "location"], "det_whitelist": ["definite"], "usage": 0},
    "bathroom": {"type": "obj", "text": "bathroom", "tags": ["place", "location"], "det_whitelist": ["definite"], "usage": 0},
    "park": {"type": "obj", "text": "park", "tags": ["place", "location"], "det_whitelist": ["definite"], "usage": 0},
    "hospital": {"type": "obj", "text": "hospital", "tags": ["place", "location"], "det_whitelist": ["definite"], "usage": 0},
    "market": {"type": "obj", "text": "market", "tags": ["place", "location"], "det_whitelist": ["definite"], "usage": 0},
    "shop": {"type": "obj", "text": "shop", "tags": ["place", "location"], "det_whitelist": ["definite"], "usage": 0},
    "road": {"type": "obj", "text": "road", "tags": ["place", "location"], "det_whitelist": ["definite", "indefinite"], "usage": 0},
    "street": {"type": "obj", "text": "street", "tags": ["place", "location"], "det_whitelist": ["definite", "indefinite"], "usage": 0},
    "city": {"type": "obj", "text": "city", "tags": ["place", "location"], "det_whitelist": ["definite", "indefinite"], "usage": 0},

    # --- SCHOOL & GENERAL OBJECTS ---
    "pen": {"type": "obj", "text": "pen", "tags": ["object", "school", "countable", "writable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "pencil": {"type": "obj", "text": "pencil", "tags": ["object", "school", "countable", "writable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "bag": {"type": "obj", "text": "bag", "tags": ["object", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "desk": {"type": "obj", "text": "desk", "tags": ["object", "furniture", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "board": {"type": "obj", "text": "board", "tags": ["object", "school", "countable"], "det_whitelist": ["definite"], "usage": 0},
    "computer": {"type": "obj", "text": "computer", "tags": ["object", "tech", "countable", "openable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "phone": {"type": "obj", "text": "phone", "tags": ["object", "tech", "countable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "picture": {"type": "obj", "text": "picture", "tags": ["object", "countable", "visible"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "notebook": {"type": "obj", "text": "notebook", "tags": ["object", "school", "countable", "readable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "medicine": {"type": "obj", "text": "medicine", "tags": ["object", "substance"], "det_whitelist": ["quantity"], "usage": 0},
    "money": {"type": "obj", "text": "money", "tags": ["object", "abstract"], "det_whitelist": ["quantity"], "usage": 0},
    "bus": {"type": "obj", "text": "bus", "tags": ["object", "vehicle", "visible"], "det_whitelist": ["definite", "indefinite"], "usage": 0},
    "game": {"type": "obj", "text": "game", "tags": ["object", "abstract"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "idea": {"type": "obj", "text": "idea", "tags": ["abstract"], "det_whitelist": ["indefinite"], "usage": 0},
    "problem": {"type": "obj", "text": "problem", "tags": ["abstract"], "det_whitelist": ["indefinite"], "usage": 0},
    "word": {"type": "obj", "text": "word", "tags": ["abstract", "readable"], "det_whitelist": ["indefinite"], "usage": 0},


    # --- MISSING VERBS (Updated V11) ---
    "put": {"type": "verb", "text": "put", "req_sub": ["human"], "req_obj": ["object", "food"], "morph": {"3s": "puts"}, "usage": 0},
    "wait": {"type": "verb", "text": "wait for", "req_sub": ["human"], "req_obj": ["human", "bus", "time"], "morph": {"3s": "waits for"}, "usage": 0},
    "call": {"type": "verb", "text": "call", "req_sub": ["human"], "req_obj": ["human", "doctor", "police"], "morph": {"3s": "calls"}, "usage": 0},
    "learn": {"type": "verb", "text": "learn", "req_sub": ["human"], "req_obj": ["lesson", "fact", "word"], "morph": {"3s": "learns"}, "usage": 0},
    "study": {"type": "verb", "text": "study", "req_sub": ["human"], "req_obj": ["lesson", "book"], "morph": {"3s": "studies"}, "usage": 0},
    "speak": {"type": "verb", "text": "speak to", "req_sub": ["human"], "req_obj": ["human"], "morph": {"3s": "speaks to"}, "usage": 0},
    "say": {"type": "verb", "text": "say", "req_sub": ["human"], "req_obj": ["word", "fact", "hello"], "morph": {"3s": "says"}, "usage": 0},
    "tell": {"type": "verb", "text": "tell", "req_sub": ["human"], "req_obj": ["human"], "morph": {"3s": "tells"}, "usage": 0},
    "ask": {"type": "verb", "text": "ask", "req_sub": ["human"], "req_obj": ["question", "human"], "morph": {"3s": "asks"}, "usage": 0},
    "answer": {"type": "verb", "text": "answer", "req_sub": ["human"], "req_obj": ["question", "human"], "morph": {"3s": "answers"}, "usage": 0},
    "start": {"type": "verb", "text": "start", "req_sub": ["human"], "req_obj": ["game", "lesson", "work"], "morph": {"3s": "starts"}, "usage": 0},
    "finish": {"type": "verb", "text": "finish", "req_sub": ["human"], "req_obj": ["game", "lesson", "work", "food"], "morph": {"3s": "finishes"}, "usage": 0},
    "try": {"type": "verb", "text": "try", "req_sub": ["human"], "req_obj": ["food", "game"], "morph": {"3s": "tries"}, "usage": 0},
    "change": {"type": "verb", "text": "change", "req_sub": ["human"], "req_obj": ["clothes", "money", "idea"], "morph": {"3s": "changes"}, "usage": 0},
    "hold": {"type": "verb", "text": "hold", "req_sub": ["human"], "req_obj": ["object", "baby", "hand"], "morph": {"3s": "holds"}, "usage": 0},
    "hurt": {"type": "verb", "text": "hurt", "req_sub": ["object", "body"], "req_obj": ["human", "animal"], "morph": {"3s": "hurts"}, "usage": 0},
    "turn on": {"type": "verb", "text": "turn on", "req_sub": ["human"], "req_obj": ["computer", "light"], "morph": {"3s": "turns on"}, "usage": 0},
    "turn off": {"type": "verb", "text": "turn off", "req_sub": ["human"], "req_obj": ["computer", "light"], "morph": {"3s": "turns off"}, "usage": 0},
    "wake up": {"type": "verb", "text": "wake up", "req_sub": ["human"], "req_obj": ["human"], "morph": {"3s": "wakes up"}, "usage": 0},
    "leave": {"type": "verb", "text": "leave", "req_sub": ["human"], "req_obj": ["place", "home", "city", "school"], "morph": {"3s": "leaves"}, "usage": 0},
    "buy": {"type": "verb", "text": "buy", "req_sub": ["human"], "req_obj": ["object", "food", "drink", "clothes"], "morph": {"3s": "buys"}, "usage": 0},
    "get": {"type": "verb", "text": "get", "req_sub": ["human"], "req_obj": ["object", "food", "idea"], "morph": {"3s": "gets"}, "usage": 0},
    "find": {"type": "verb", "text": "find", "req_sub": ["human"], "req_obj": ["object", "person", "place"], "morph": {"3s": "finds"}, "usage": 0},
    "lose": {"type": "verb", "text": "lose", "req_sub": ["human"], "req_obj": ["object", "money"], "morph": {"3s": "loses"}, "usage": 0},
    "bring": {"type": "verb", "text": "bring", "req_sub": ["human"], "req_obj": ["object", "food"], "morph": {"3s": "brings"}, "usage": 0},
    "use": {"type": "verb", "text": "use", "req_sub": ["human"], "req_obj": ["object", "computer", "phone", "tool"], "morph": {"3s": "uses"}, "usage": 0},
    "play": {"type": "verb", "text": "play", "req_sub": ["human"], "req_obj": ["game"], "morph": {"3s": "plays"}, "usage": 0},
    "play with": {"type": "verb", "text": "play with", "req_sub": ["human", "animal"], "req_obj": ["toy", "friend", "dog"], "morph": {"3s": "plays with"}, "usage": 0},
    "work": {"type": "verb", "text": "work", "req_sub": ["human"], "req_obj": [], "morph": {"3s": "works"}, "usage": 0},
    "love": {"type": "verb", "text": "love", "req_sub": ["human"], "req_obj": ["human", "animal", "family", "object"], "morph": {"3s": "loves"}, "usage": 0},

    # --- PREPOSITIONS (Tagged as PREP to avoid Noun Fallback) ---
    "up": {"type": "prep", "text": "up", "usage": 0},
    "down": {"type": "prep", "text": "down", "usage": 0},
    "under": {"type": "prep", "text": "under", "usage": 0},
    "inside": {"type": "prep", "text": "inside", "usage": 0},
    "outside": {"type": "prep", "text": "outside", "usage": 0},
    "near": {"type": "prep", "text": "near", "usage": 0},
    "far": {"type": "prep", "text": "far", "usage": 0},
    "next to": {"type": "prep", "text": "next to", "usage": 0},
    "behind": {"type": "prep", "text": "behind", "usage": 0},
    "between": {"type": "prep", "text": "between", "usage": 0},
    "in front of": {"type": "prep", "text": "in front of", "usage": 0},
    "left": {"type": "obj", "text": "left", "tags": ["direction"], "usage": 0},
    "right": {"type": "obj", "text": "right", "tags": ["direction"], "usage": 0},
    "with": {"type": "prep", "text": "with", "usage": 0},
    "from": {"type": "prep", "text": "from", "usage": 0},

    # --- PRONOUNS & DETERMINERS ---
    "mine": {"type": "pron", "text": "mine", "tags": ["possessive"], "usage": 0},
    "yours": {"type": "pron", "text": "yours", "tags": ["possessive"], "usage": 0},
    "hers": {"type": "pron", "text": "hers", "tags": ["possessive"], "usage": 0},
    "ours": {"type": "pron", "text": "ours", "tags": ["possessive"], "usage": 0},
    "theirs": {"type": "pron", "text": "theirs", "tags": ["possessive"], "usage": 0},
    "some": {"type": "det", "text": "some", "category": "quantity"},
    "more": {"type": "det", "text": "more", "category": "quantity"},
    "enough": {"type": "det", "text": "enough", "category": "quantity"},
    "all": {"type": "det", "text": "all", "category": "quantity"},
    "this": {"type": "det", "text": "this", "category": "definite"},
    
    # --- ADJECTIVES (Missing V11) ---
    "yellow": {"type": "adj", "text": "yellow", "usage": 0},
    "white": {"type": "adj", "text": "white", "usage": 0},
    "black": {"type": "adj", "text": "black", "usage": 0},
    "green": {"type": "adj", "text": "green", "usage": 0},
    "brown": {"type": "adj", "text": "brown", "usage": 0},
    "orange": {"type": "adj", "text": "orange", "usage": 0}, # Also color
    "fast": {"type": "adj", "text": "fast", "usage": 0},
    "slow": {"type": "adj", "text": "slow", "usage": 0},
    "ready": {"type": "adj", "text": "ready", "usage": 0},
    "sure": {"type": "adj", "text": "sure", "usage": 0},
    "busy": {"type": "adj", "text": "busy", "usage": 0},
    "same": {"type": "adj", "text": "same", "usage": 0},
    "different": {"type": "adj", "text": "different", "usage": 0},
    "easy": {"type": "adj", "text": "easy", "usage": 0},
    "hard": {"type": "adj", "text": "hard", "usage": 0},
    "free": {"type": "adj", "text": "free", "usage": 0},
    "sick": {"type": "adj", "text": "sick", "usage": 0},
    "well": {"type": "adj", "text": "well", "usage": 0},
    "full": {"type": "adj", "text": "full", "usage": 0},
    "hungry": {"type": "adj", "text": "hungry", "usage": 0},
    "thirsty": {"type": "adj", "text": "thirsty", "usage": 0},
    "dirty": {"type": "adj", "text": "dirty", "usage": 0},
    
    # --- AUXILIARIES & NEGATIVES (Excluded from SVO/OBJ pool) ---
    "am": {"type": "verb_aux", "text": "am", "usage": 0},
    "is": {"type": "verb_aux", "text": "is", "usage": 0},
    "are": {"type": "verb_aux", "text": "are", "usage": 0},
    "do": {"type": "verb_aux", "text": "do", "usage": 0},
    "don't": {"type": "verb_aux", "text": "don't", "usage": 0}, # Normalized
    "don’t": {"type": "verb_aux", "text": "don't", "usage": 0}, # Smart quote variant
    "not": {"type": "verb_aux", "text": "not", "usage": 0},
    "can": {"type": "verb_aux", "text": "can", "usage": 0},
    "can't": {"type": "verb_aux", "text": "can't", "usage": 0},
    "can’t": {"type": "verb_aux", "text": "can't", "usage": 0},

    # --- COMMON MISSING WORDS (To prevent Noun Fallback) ---
    "yes": {"type": "intj", "text": "yes", "usage": 0},
    "no": {"type": "intj", "text": "no", "usage": 0},
    "please": {"type": "intj", "text": "please", "usage": 0},
    "hello": {"type": "intj", "text": "hello", "usage": 0},
    "hi": {"type": "intj", "text": "hi", "usage": 0},
    "thanks": {"type": "intj", "text": "thanks", "usage": 0},
    "to": {"type": "prep", "text": "to", "usage": 0},
    "take": {
        "type": "verb", "text": "take", 
        "req_sub": ["human"], "req_obj": ["object", "food", "medicine"], 
        "morph": {"3s": "takes"}, "usage": 0
    },
}


class SentenceEngineWrapper:
    """ Wrapper to expose the V13 Engine with the expected API interface """
    def __init__(self):
        pass

    def generate(self, known_words_list: list[str], count=5) -> list[dict]:
        """
        Returns list of dicts: {'text': str, 'key_word': str}
        """
        # Normalize known words
        known_set = set(w.lower() if w != "I" else "I" for w in known_words_list)
        
        # Build Filtered DB for V13 Adapter
        filtered_db = {}
        for key, meta in RICH_VOCAB_DB.items():
            if key in known_set or meta["text"] in known_set:
                filtered_db[key] = meta
        
        # Fallback: Add known words as generic nouns if strict matching failed
        for word in known_set:
            if word not in filtered_db:
                 filtered_db[word] = {"type": "obj", "text": word, "tags": ["object", "countable"]}

        if not filtered_db:
            return []

        # Initialize V13 Engine with filtered data
        engine = SentenceEngineV13(filtered_db)

        sentences = []
        attempts = 0
        while len(sentences) < count and attempts < 20: # Limit attempts
            attempts += 1
            try:
                result = engine.generate_one()
                text, key = result
                
                if not any(s['text'] == text for s in sentences):
                    sentences.append({'text': text, 'key_word': key})
            except Exception as e:
                # Engine might fail if not enough compatible words found
                continue
        
        return sentences

# Singleton Instance
sentence_engine = SentenceEngineWrapper()
