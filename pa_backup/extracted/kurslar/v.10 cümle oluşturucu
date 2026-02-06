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
        # Bu yapı sayesinde cümleler hep aynı sırada (SVO) çıkmaz.
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

    def generate(self, complexity=0.5):
        """
        complexity (0.0 - 1.0): Cümlenin zenginliği.
        """
        # 1. Şablon Seç
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
                # Eat -> req_obj=["food"]. Water -> tags=["drink"]. Eşleşmez!
                obj_id = self.selector.select("obj", req_tags=v_data.get("req_obj"))
                
                if obj_id:
                    token = TokenV10(obj_id, self.ctx[obj_id], "obj")
                    
                    # Determiner Çeşitliliği (My, The, This, Some)
                    whitelist = self.ctx[obj_id].get("det_whitelist", [])
                    if random.random() < complexity and whitelist:
                        # Context'teki 'det' tipindeki kelimeleri bul
                        # (Bu kısım normalde optimize edilebilir ama şimdilik scan)
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
                        prob *= 0.5 # Her eklemede ihtimal azalır

            elif "adv" in slot:
                # adv_time, adv_freq...
                a_type = slot.split("_")[1]
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
# 4. TEST VERİSİ VE ÇALIŞTIRMA
# ==========================================

# Veritabanından gelen JSON verisi
final_context = {
    # ÖZNELER
    "I": {"type": "sub", "text": "I", "person": 1, "tags": ["human"], "usage": 0},
    "she": {"type": "sub", "text": "she", "person": 3, "tags": ["human"], "usage": 5},
    "cat": {"type": "sub", "text": "the cat", "person": 3, "tags": ["animal"], "usage": 2},

    # FİİLLER (Semantik kurallara dikkat)
    "eat": {
        "type": "verb", "text": "eat", 
        "req_sub": ["human", "animal"], 
        "req_obj": ["food"], # SADECE YİYECEK
        "morph": {"3s": "eats"}, "usage": 10
    },
    "drink": {
        "type": "verb", "text": "drink", 
        "req_sub": ["human", "animal"], 
        "req_obj": ["drink"], # SADECE İÇECEK
        "morph": {"3s": "drinks"}, "usage": 8
    },

    # NESNELER
    "apple": {
        "type": "obj", "text": "apple", "tags": ["food"], 
        "det_whitelist": ["indefinite", "definite", "possessive"], # a/an alabilir
        "usage": 2
    },
    "water": {
        "type": "obj", "text": "water", "tags": ["drink"], 
        "det_whitelist": ["definite", "possessive", "quantity"], # a/an YASAK
        "usage": 2
    },
    "bread": {
        "type": "obj", "text": "bread", "tags": ["food"],
        "det_whitelist": ["quantity", "definite"],
        "usage": 1
    },

    # DETAYLAR (Determiners, Adj, Adv)
    "my": {"type": "det", "text": "my", "category": "possessive"},
    "the": {"type": "det", "text": "the", "category": "definite"},
    "some": {"type": "det", "text": "some", "category": "quantity"},

    "big": {"type": "adj", "text": "big", "usage": 0},
    "cold": {"type": "adj", "text": "cold", "usage": 0},
    "fresh": {"type": "adj", "text": "fresh", "usage": 0},

    "now": {"type": "adv", "text": "now", "adv_type": "time"},
    "always": {"type": "adv", "text": "always", "adv_type": "freq"},
    "quickly": {"type": "adv", "text": "quickly", "adv_type": "manner"}
}

# --- MOTORU BAŞLAT ---
engine = EngineV10()
engine.set_context(final_context)

print("--- V10 NİHAİ TEST ÇIKTILARI ---")
print("(Semantic Check: 'Eat water' asla çıkmamalı.)")
print("-" * 40)

for i in range(12):
    # Complexity her seferinde rastgele değişsin
    comp = random.random()
    sent = engine.generate(complexity=comp)
    if sent:
        print(f"{i+1}. {sent}")