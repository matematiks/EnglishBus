import random

# ==========================================
# 1. AKILLI SEÇİCİ (WEIGHTED & SEMANTIC SELECTOR)
# ==========================================
class SmartSelector:
    def __init__(self, context):
        self.context = context
        self.indices = {"type": {}, "tag": {}, "adv_type": {}}
        self._build_indices()

    def _build_indices(self):
        """Veriyi hızlı erişim için indexler (O(n) -> O(1))"""
        for wid, meta in self.context.items():
            t = meta.get("type")
            self.indices.setdefault("type", {}).setdefault(t, []).append(wid)
            
            if t == "adv":
                at = meta.get("adv_type")
                self.indices.setdefault("adv_type", {}).setdefault(at, []).append(wid)

            # Tag Indexing (Semantic Filtre için kritik)
            for tag in meta.get("tags", []):
                self.indices.setdefault("tag", {}).setdefault(tag, []).append(wid)

    def select(self, w_type, req_tags=None, adv_type=None):
        """
        Kelimeleri filtreler ve kullanım sıklığına (usage) göre seçer.
        req_tags: ["food"] gibi zorunlulukları kontrol eder.
        """
        candidates = self.indices["type"].get(w_type, [])
        
        # 1. Zarf Türü Filtresi (Time vs Frequency)
        if adv_type:
            candidates = [c for c in candidates if c in self.indices["adv_type"].get(adv_type, [])]
        
        # 2. SEMANTİK FİLTRE (Eat Water Engelleyici)
        # Eğer fiil belirli tag'ler istiyorsa (örn: 'food'), sadece o tag'e sahip nesneler kalır.
        if req_tags:
            req_set = set(req_tags)
            # Kesişim kümesi boş olanları ele (intersection)
            candidates = [c for c in candidates if set(self.context[c].get("tags", [])).intersection(req_set)]

        if not candidates: return None

        # 3. Ağırlıklı Rastgelelik (Weighted Random)
        # Az kullanılan (düşük usage) kelimenin şansı artar.
        weights = []
        for c in candidates:
            # Usage 0 ise 1 kabul et
            usage = self.context[c].get("usage", 0) + 1
            weights.append(1.0 / usage) # Ters orantı

        selected_id = random.choices(candidates, weights=weights, k=1)[0]
        
        # Kullanım sayısını artır (Simülasyon)
        self.context[selected_id]["usage"] = self.context[selected_id].get("usage", 0) + 1
        
        return selected_id

# ==========================================
# 2. TOKEN VE CÜMLE MONTAJCISI
# ==========================================
class TokenV10:
    def __init__(self, word_id, meta, role):
        self.id = word_id
        self.meta = meta
        self.role = role # sub, verb, obj, adj, adv
        self.decorators = [] # Sıfatlar, Zarflar
        self.specifier = None # my, the, a/an

    def resolve_text(self):
        return self.meta.get("text", self.id)

class SentenceAssembler:
    def __init__(self, context):
        self.ctx = context

    def resolve_specifier(self, token):
        """Determiner (a/an, the, my) seçimi"""
        if not token.specifier:
            # Otomatik a/an (default)
            whitelist = token.meta.get("det_whitelist", [])
            # Eğer 'indefinite' (a/an) izinli ise:
            if "indefinite" in whitelist:
                # Sıradaki kelimenin ilk harfine bak (Sıfat varsa sıfat, yoksa isim)
                next_text = token.decorators[0].resolve_text() if token.decorators else token.resolve_text()
                return "an" if next_text[0].lower() in "aeiou" else "a"
            return ""
        
        # Özel seçilmişse (my, the, this)
        return self.ctx[token.specifier]["text"]

    def build(self, tokens, sentence_type="statement"):
        parts = []
        
        # Soru Kalıbı (Simple Present)
        if sentence_type == "question_yes_no":
            sub = next((t for t in tokens if t.role == "sub"), None)
            # 3. tekil şahıs için Does, diğerleri Do
            aux = "Does" if sub and sub.meta.get("person") == 3 else "Do"
            parts.append(aux)

        for token in tokens:
            # 1. Specifier (Article/Possessive) - Sadece Objeler için
            if token.role == "obj":
                spec = self.resolve_specifier(token)
                if spec: parts.append(spec)
            
            # 2. Decorators (Adjectives)
            for dec in token.decorators:
                parts.append(dec.resolve_text())
            
            # 3. Ana Kelime
            text = token.resolve_text()
            
            # Fiil Çekimi (Morphology)
            if token.role == "verb":
                 if sentence_type == "question_yes_no":
                     # Soruda fiil yalın kalır: "Does he eat?" (eats değil)
                     pass 
                 elif sentence_type == "statement":
                     # Düz cümlede özneye göre çekimle
                     sub = next((t for t in tokens if t.role == "sub"), None)
                     if sub and sub.meta.get("person") == 3:
                         text = token.meta.get("morph", {}).get("3s", text)
            
            parts.append(text)
        
        full = " ".join(parts)
        if "question" in sentence_type: return full + "?"
        return full.capitalize() + "."

# ==========================================
# 3. BLUEPRINT ENGINE (ŞABLON MOTORU)
# ==========================================
class EngineV10:
    def __init__(self):
        self.ctx = {}
        self.selector = None
        self.assembler = None
        
        # Cümle Şablonları (Blueprints)
        self.blueprints = {
            "SVO_BASIC": ["sub", "verb", "obj"],
            "SVO_TIME_FRONT": ["adv_time", "sub", "verb", "obj"],
            "SVO_FREQ_MID": ["sub", "adv_freq", "verb", "obj"],
            "SVO_MANNER_END": ["sub", "verb", "obj", "adv_manner"]
        }

    def set_context(self, context):
        """Veriyi yükler ve indexleri oluşturur."""
        self.ctx = context
        self.selector = SmartSelector(context)
        self.assembler = SentenceAssembler(context)

    def generate_one(self, complexity=0.5):
        """
        complexity (0.0 - 1.0): Cümlenin zenginliği.
        """
        if not self.ctx: return None

        # 1. Şablon Seç
        # Şablon için gerekli kelime türleri var mı kontrol etmeliyiz aslında
        # Basitlik için rastgele seçiyoruz, bulamazsa None döner.
        bp_name = random.choice(list(self.blueprints.keys()))
        blueprint = self.blueprints[bp_name]
        
        sentence_tokens = []
        
        # 2. Önce Fiili Seç (Cümlenin kalbi)
        verb_id = self.selector.select("verb")
        if not verb_id: return None
        v_data = self.ctx[verb_id]
        
        # 3. Fiile Uygun Özne Seç (req_sub)
        sub_id = self.selector.select("sub", req_tags=v_data.get("req_sub"))
        if not sub_id: return None
        
        # 4. Şablonu Doldur
        for slot in blueprint:
            token = None
            
            if slot == "sub":
                token = TokenV10(sub_id, self.ctx[sub_id], "sub")
                
            elif slot == "verb":
                token = TokenV10(verb_id, v_data, "verb")
                
            elif slot == "obj":
                # KRİTİK: Fiilin istediği tag'e göre nesne seç (req_obj)
                req_obj_tags = v_data.get("req_obj")
                obj_id = self.selector.select("obj", req_tags=req_obj_tags)
                
                if obj_id:
                    token = TokenV10(obj_id, self.ctx[obj_id], "obj")
                    
                    # Determiner Çeşitliliği (My, The, This, Some)
                    whitelist = self.ctx[obj_id].get("det_whitelist", [])
                    if random.random() < complexity and whitelist:
                        valid_dets = [
                            d for d, m in self.ctx.items() 
                            if m.get("type") == "det" and m.get("category") in whitelist
                        ]
                        if valid_dets:
                            token.specifier = random.choice(valid_dets)

                    # Sıfat Zinciri (Recursive Adjectives)
                    prob = complexity
                    while random.random() < prob:
                        adj_id = self.selector.select("adj")
                        if adj_id:
                            token.decorators.append(TokenV10(adj_id, self.ctx[adj_id], "adj"))
                        prob *= 0.5 

            elif "adv" in slot:
                # adv_time, adv_freq...
                parts = slot.split("_")
                if len(parts) > 1:
                    a_type = parts[1]
                    # Complexity yeterliyse zarf ekle
                    if random.random() < complexity + 0.2:
                        adv_id = self.selector.select("adv", adv_type=a_type)
                        if adv_id:
                            token = TokenV10(adv_id, self.ctx[adv_id], "adv")

            if token:
                sentence_tokens.append(token)
        
        # Soru veya Düz Cümle Modu (%20 ihtimalle soru olsun)
        sType = "question_yes_no" if random.random() < 0.2 else "statement"
        
        return self.assembler.build(sentence_tokens, sentence_type=sType)

# ==========================================
# 4. RICH VOCABULARY KNOWLEDGE BASE
# ==========================================
# This dictionary maps the simple English words (keys) to their semantic metadata.
# Used to upgrade the user's simple word list into a smart context.
RICH_VOCAB_DB = {
    # --- SUBJECTS ---
    "I": {"type": "sub", "text": "I", "person": 1, "tags": ["human"], "usage": 0},
    "you": {"type": "sub", "text": "you", "person": 2, "tags": ["human"], "usage": 0},
    "he": {"type": "sub", "text": "he", "person": 3, "tags": ["human"], "usage": 0},
    "she": {"type": "sub", "text": "she", "person": 3, "tags": ["human"], "usage": 0},
    "it": {"type": "sub", "text": "it", "person": 3, "tags": ["animal", "object"], "usage": 0},
    "we": {"type": "sub", "text": "we", "person": 1, "tags": ["human"], "usage": 0},
    "they": {"type": "sub", "text": "they", "person": 3, "tags": ["human"], "usage": 0},
    "mom": {"type": "sub", "text": "mom", "person": 3, "tags": ["human"], "usage": 0},
    "dad": {"type": "sub", "text": "dad", "person": 3, "tags": ["human"], "usage": 0},
    "cat": {"type": "sub", "text": "the cat", "person": 3, "tags": ["animal"], "usage": 0},
    "dog": {"type": "sub", "text": "the dog", "person": 3, "tags": ["animal"], "usage": 0},
    "man": {"type": "sub", "text": "the man", "person": 3, "tags": ["human"], "usage": 0},
    "woman": {"type": "sub", "text": "the woman", "person": 3, "tags": ["human"], "usage": 0},
    "teacher": {"type": "sub", "text": "the teacher", "person": 3, "tags": ["human"], "usage": 0},

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
        "req_sub": ["human", "animal"], "req_obj": ["food", "drink", "toy", "object"],
        "morph": {"3s": "wants"}, "usage": 0
    },
    "have": {
        "type": "verb", "text": "have",
        "req_sub": ["human", "animal"], "req_obj": ["food", "drink", "toy", "object"],
        "morph": {"3s": "has"}, "usage": 0
    },
    "like": {
        "type": "verb", "text": "like",
        "req_sub": ["human", "animal"], "req_obj": ["food", "drink", "toy", "object", "person"],
        "morph": {"3s": "likes"}, "usage": 0
    },
     "see": {
        "type": "verb", "text": "see",
        "req_sub": ["human", "animal"], "req_obj": ["human", "animal", "object"],
        "morph": {"3s": "sees"}, "usage": 0
    },
    "buy": {
        "type": "verb", "text": "buy",
        "req_sub": ["human"], "req_obj": ["food", "drink", "toy", "object", "clothes"],
        "morph": {"3s": "buys"}, "usage": 0
    },
    "wear": {
        "type": "verb", "text": "wear",
        "req_sub": ["human"], "req_obj": ["clothes"],
        "morph": {"3s": "wears"}, "usage": 0
    },
    "read": {
        "type": "verb", "text": "read",
        "req_sub": ["human"], "req_obj": ["readable"],
        "morph": {"3s": "reads"}, "usage": 0
    },

    # --- OBJECTS ---
    "apple": {"type": "obj", "text": "apple", "tags": ["food", "object"], "det_whitelist": ["indefinite", "definite", "possessive"], "usage": 0},
    "bread": {"type": "obj", "text": "bread", "tags": ["food", "object"], "det_whitelist": ["quantity", "definite"], "usage": 0},
    "water": {"type": "obj", "text": "water", "tags": ["drink", "object"], "det_whitelist": ["quantity", "definite", "possessive"], "usage": 0},
    "milk": {"type": "obj", "text": "milk", "tags": ["drink", "object"], "det_whitelist": ["quantity", "definite", "possessive"], "usage": 0},
    "tea": {"type": "obj", "text": "tea", "tags": ["drink", "object"], "det_whitelist": ["quantity", "definite"], "usage": 0},
    "coffee": {"type": "obj", "text": "coffee", "tags": ["drink", "object"], "det_whitelist": ["quantity", "definite"], "usage": 0},
    "book": {"type": "obj", "text": "book", "tags": ["object", "readable"], "det_whitelist": ["indefinite", "definite", "possessive"], "usage": 0},
    "pen": {"type": "obj", "text": "pen", "tags": ["object"], "det_whitelist": ["indefinite", "definite", "possessive"], "usage": 0},
    "ball": {"type": "obj", "text": "ball", "tags": ["object", "toy"], "det_whitelist": ["indefinite", "definite", "possessive"], "usage": 0},
    "car": {"type": "obj", "text": "car", "tags": ["object", "vehicle"], "det_whitelist": ["indefinite", "definite", "possessive"], "usage": 0},
    "bus": {"type": "obj", "text": "bus", "tags": ["object", "vehicle"], "det_whitelist": ["indefinite", "definite"], "usage": 0},
    "clothes": {"type": "obj", "text": "clothes", "tags": ["clothes", "object"], "det_whitelist": ["possessive", "quantity"], "usage": 0},
    "hat": {"type": "obj", "text": "hat", "tags": ["clothes", "object"], "det_whitelist": ["indefinite", "definite", "possessive"], "usage": 0},
    "newspaper": {"type": "obj", "text": "newspaper", "tags": ["object", "readable"], "det_whitelist": ["indefinite", "definite"], "usage": 0},

    # --- DETERMINERS (Always available if in known list) --
    "my": {"type": "det", "text": "my", "category": "possessive"},
    "your": {"type": "det", "text": "your", "category": "possessive"},
    "his": {"type": "det", "text": "his", "category": "possessive"},
    "her": {"type": "det", "text": "her", "category": "possessive"},
    "the": {"type": "det", "text": "the", "category": "definite"},
    "some": {"type": "det", "text": "some", "category": "quantity"},

    # --- ADJECTIVES ---
    "big": {"type": "adj", "text": "big", "usage": 0},
    "small": {"type": "adj", "text": "small", "usage": 0},
    "hot": {"type": "adj", "text": "hot", "usage": 0},
    "cold": {"type": "adj", "text": "cold", "usage": 0},
    "good": {"type": "adj", "text": "good", "usage": 0},
    "bad": {"type": "adj", "text": "bad", "usage": 0},
    "fresh": {"type": "adj", "text": "fresh", "usage": 0},
    "red": {"type": "adj", "text": "red", "usage": 0},
    "blue": {"type": "adj", "text": "blue", "usage": 0},
    "new": {"type": "adj", "text": "new", "usage": 0},
    "old": {"type": "adj", "text": "old", "usage": 0},

    # --- ADVERBS ---
    "now": {"type": "adv", "text": "now", "adv_type": "time"},
    "today": {"type": "adv", "text": "today", "adv_type": "time"},
    "always": {"type": "adv", "text": "always", "adv_type": "freq"},
    "never": {"type": "adv", "text": "never", "adv_type": "freq"},
    "quickly": {"type": "adv", "text": "quickly", "adv_type": "manner"},
    "slowly": {"type": "adv", "text": "slowly", "adv_type": "manner"},
}


class SentenceEngineWrapper:
    """ Wrapper to expose the V10 Engine with the expected API interface """
    def __init__(self):
        pass

    def generate(self, known_words_list: list[str], count=5) -> list[str]:
        """
        1. Filters RICH_VOCAB_DB using known_words_list.
        2. Initializes EngineV10 with this filtered context.
        3. Generates sentences.
        """
        # Normalize inputs
        known_set = set(w.lower() if w != "I" else "I" for w in known_words_list)
        
        # Build Context: Include only words the user knows AND we have metadata for.
        # Auto-include 'the', 'a' if implicit (handled by whitelist logic), but for explicit dets checking known_set
        
        filtered_context = {}
        for key, meta in RICH_VOCAB_DB.items():
            # Key check (simple) OR Text check
            if key in known_set or meta["text"] in known_set:
                filtered_context[key] = meta.copy() # Copy to avoid mutation of usage in global DB across calls (optional)

        # If too few words, return empty or fallback
        if len(filtered_context) < 3:
            return []

        # Initialize V10 Engine
        engine = EngineV10()
        engine.set_context(filtered_context)

        sentences = []
        attempts = 0
        while len(sentences) < count and attempts < 20:
            attempts += 1
            # Random complexity
            comp = random.random()
            sent = engine.generate_one(complexity=comp)
            if sent and sent not in sentences:
                sentences.append(sent)
        
        return sentences

# Singleton Instance
sentence_engine = SentenceEngineWrapper()
