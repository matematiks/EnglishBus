import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

# =========================================================
# V13 ENGINE LOGIC
# =========================================================

@dataclass(frozen=True)
class Word:
    text: str
    pos: str                 
    tags: frozenset
    req_sub: frozenset = frozenset()
    req_obj: frozenset = frozenset()
    base: str | None = None
    third: str | None = None
    past: str | None = None
    ing: str | None = None
    plural: str | None = None


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

    def pick(self, pos: str, tag: str | None = None) -> Word:
        pool = self.by_pos_tag[(pos, tag)] if tag else self.by_pos[pos]
        if not pool:
            # Fallback for strict tags in limited vocab
             if tag: pool = self.by_pos[pos] # Broaden search
             if not pool: raise ValueError(f"No word for pos={pos}")
        return random.choice(pool)

    def pick_filtered(self, pos: str, required_tags: frozenset) -> Word:
        pool = [
            w for w in self.by_pos[pos]
            if not required_tags or (w.tags & required_tags)
        ]
        if not pool:
            # Fallback: Just pick any word of that POS to avoid crash
            pool = self.by_pos[pos]
        
        if not pool: raise ValueError("No words available")
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
        try:
            subj = self.index.pick("pron", "human")
        except:
            subj = self.index.pick("noun") # Fallback
            
        # verb → req_sub compatible
        verb = self.index.pick_filtered("verb", subj.tags)
        
        # object → req_obj compatible
        obj = self.index.pick_filtered("noun", verb.req_obj)

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
            subj = self.index.pick("pron", "human")
            verb = self.index.pick_filtered("verb", subj.tags)
        except:
            return self.make_statement()

        aux = "does" if subj.text.lower() in {"he", "she", "it"} else "do"
        
        # Check if question asks for object (What)
        if "ask_object" in q.tags:
            sentence = f"{q.text} {aux} {subj.text} {verb.text}?"
            return sentence, verb.text

        # Otherwise add object
        obj = self.index.pick_filtered("noun", verb.req_obj)
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
