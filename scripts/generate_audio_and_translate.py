import os
import csv
import time
from gtts import gTTS

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COURSE_DIR = os.path.join(BASE_DIR, "kurslar", "A1_Foundation")
CSV_PATH = os.path.join(COURSE_DIR, "words.csv")
AUDIO_EN_DIR = os.path.join(COURSE_DIR, "ing_audio")
AUDIO_TR_DIR = os.path.join(COURSE_DIR, "tr_audio")

# A1 Dictionary (English -> Turkish)
# This covers the words from deps 1.text
TRANSLATIONS = {
    "hello": "merhaba", "hi": "selam", "I": "ben", "am": "olmak (am)", "you": "sen", "want": "istemek", "water": "su", "food": "yiyecek",
    "yes": "evet", "no": "hayır", "please": "lütfen", "not": "değil", "me": "bana", "this": "bu", "what": "ne",
    "give": "vermek", "take": "almak", "thanks": "teşekkürler", "don't": "yapma", "go": "gitmek", "to": "ye/ya (yönelme)", "home": "ev",
    "come": "gelmek", "here": "burada", "where": "nerede", "there": "orada", "stay": "kalmak", "house": "ev", "bed": "yatak",
    "sleep": "uyumak", "tired": "yorgun", "open": "açık", "the": "bilinen (tanımlık)", "door": "kapı", "close": "kapatmak", "window": "pencere",
    "my": "benim", "bag": "çanta", "dog": "köpek", "cat": "kedi", "rabbit": "tavşan", "man": "adam", "woman": "kadın",
    "boy": "erkek çocuk", "girl": "kız çocuk", "who": "kim", "he": "o (erkek)", "she": "o (kadın)", "it": "o (cansız/hayvan)", "is": "dır/dir",
    "mine": "benimki", "we": "biz", "they": "onlar", "are": "olmak (are)", "good": "iyi", "bad": "kötü", "very": "çok",
    "big": "büyük", "small": "küçük", "red": "kırmızı", "blue": "mavi", "green": "yeşil", "a": "bir", "book": "kitap",
    "pen": "kalem", "paper": "kağıt", "notebook": "defter", "read": "okumak", "write": "yazmak", "look": "bakmak", "see": "görmek",
    "friend": "arkadaş", "play": "oynamak", "with": "ile", "monkey": "maymun", "love": "sevmek", "happy": "mutlu", "but": "ama",
    "sad": "üzgün", "one": "bir", "two": "iki", "three": "üç", "four": "dört", "five": "beş", "six": "altı",
    "seven": "yedi", "eight": "sekiz", "nine": "dokuz", "ten": "on", "eat": "yemek", "drink": "içmek", "bread": "ekmek",
    "and": "ve", "apple": "elma", "banana": "muz", "cow": "inek", "horse": "at", "sheep": "koyun", "duck": "ördek",
    "donkey": "eşek", "hungry": "aç", "thirsty": "susamış", "milk": "süt", "juice": "meyve suyu", "cup": "fincan", "bottle": "şişe",
    "ok": "tamam", "wait": "bekle", "now": "şimdi", "time": "zaman", "put": "koymak", "on": "üstünde", "table": "masa",
    "chair": "sandalye", "sit": "oturmak", "stand": "ayakta durmak", "in": "içinde", "your": "senin", "box": "kutu", "yours": "seninki",
    "mother": "anne", "father": "baba", "son": "oğul", "daughter": "kız evlat", "sister": "kız kardeş", "brother": "erkek kardeş", "family": "aile",
    "his": "onun (erkek)", "her": "onun (kadın)", "hers": "onunki (kadın)", "ours": "bizimki", "theirs": "onlarınki", "make": "yapmak", "kitchen": "mutfak",
    "breakfast": "kahvaltı", "lunch": "öğle yemeği", "dinner": "akşam yemeği", "plate": "tabak", "spoon": "kaşık", "fork": "çatal", "knife": "bıçak",
    "tea": "çay", "or": "veya", "coffee": "kahve", "glass": "bardak", "sugar": "şeker", "salt": "tuz", "hot": "sıcak",
    "cold": "soğuk", "thank you": "teşekkür ederim", "school": "okul", "class": "sınıf", "teacher": "öğretmen", "student": "öğrenci", "learn": "öğrenmek",
    "study": "ders çalışmak", "desk": "sıra", "board": "tahta", "computer": "bilgisayar", "phone": "telefon", "call": "aramak", "picture": "resim",
    "work": "iş", "busy": "meşgul", "can": "yapabilmek", "can't": "yapamamak", "do": "yapmak", "money": "para", "without": "sız/siz",
    "market": "market", "shop": "dükkan", "buy": "satın almak", "get": "almak", "some": "biraz", "cheese": "peynir", "sandwich": "sandviç",
    "meat": "et", "chicken": "tavuk", "fish": "balık", "more": "daha fazla", "rice": "pirinç", "pasta": "makarna", "soup": "çorba",
    "salad": "salata", "vegetable": "sebze", "potato": "patates", "tomato": "domates", "enough": "yeterli", "fruit": "meyve", "egg": "yumurta",
    "sick": "hasta", "doctor": "doktor", "medicine": "ilaç", "hospital": "hastane", "hurt": "acımak", "pain": "ağrı", "well": "iyi",
    "clean": "temiz", "dirty": "kirli", "wash": "yıkamak", "face": "yüz", "hand": "el", "soap": "sabun", "towel": "havlu",
    "bathroom": "banyo", "toilet": "tuvalet", "toilet paper": "tuvalet kağıdı", "new": "yeni", "old": "eski", "car": "araba", "bus": "otobüs",
    "road": "yol", "street": "cadde", "from": "den/dan", "city": "şehir", "walk": "yürümek", "run": "koşmak", "fast": "hızlı",
    "slow": "yavaş", "park": "park", "yellow": "sarı", "six": "altı", "white": "beyaz", "seven": "yedi", "black": "siyah",
    "eight": "sekiz", "orange": "turuncu", "find": "bulmak", "lose": "kaybetmek", "bring": "getirmek", "hold": "tutmak", "change": "değiştirmek",
    "use": "kullanmak", "same": "aynı", "different": "farklı", "easy": "kolay", "hard": "zor", "free": "özgür/bedava", "today": "bugün",
    "Monday": "Pazartesi", "tomorrow": "yarın", "Tuesday": "Salı", "yesterday": "dün", "Wednesday": "Çarşamba", "morning": "sabah", "Thursday": "Perşembe",
    "afternoon": "öğleden sonra", "Friday": "Cuma", "evening": "akşam", "Saturday": "Cumartesi", "night": "gece", "Sunday": "Pazar", "day": "gün",
    "week": "hafta", "month": "ay", "year": "yıl", "weekend": "hafta sonu", "late": "geç", "early": "erken", "all": "hepsi",
    "try": "denemek", "again": "tekrar", "start": "başlamak", "finish": "bitirmek", "ready": "hazır", "turn on": "açmak (elektronik)", "turn off": "kapatmak (elektronik)",
    "wake up": "uyanmak", "leave": "ayrılmak", "hear": "duymak", "listen": "dinlemek", "speak": "konuşmak", "say": "söylemek", "tell": "anlatmak",
    "ask": "sormak", "answer": "cevaplamak", "question": "soru", "word": "kelime", "know": "bilmek", "think": "düşünmek", "idea": "fikir",
    "body": "vücut", "head": "baş", "eye": "göz", "ear": "kulak", "mouth": "ağız", "nose": "burun", "hair": "saç",
    "arm": "kol", "leg": "bacak", "foot": "ayak (tek)", "feet": "ayaklar", "tooth": "diş (tek)", "teeth": "dişler", "problem": "problem",
    "sure": "emin", "maybe": "belki", "left": "sol", "right": "sağ", "up": "yukarı", "down": "aşağı", "under": "altında",
    "inside": "içinde", "outside": "dışında", "near": "yakın", "far": "uzak", "next to": "bitişiğinde", "behind": "arkasında", "between": "arasında",
    "in front of": "önünde", "why": "neden", "because": "çünkü", "so": "bu yüzden", "twenty": "yirmi", "thirty": "otuz",
    "fifty": "elli", "hundred": "yüz", "sorry": "özür dilerim", "excuse me": "affedersiniz", "goodbye": "hoşçakal", "bye": "bay bay", "later": "sonra"
}

def generate_audio(text, lang, path):
    """Generate audio file using gTTS"""
    # Overwrite if exists, or skip? User said "sen yapacaksın", imply redo.
    tts = gTTS(text=text, lang=lang)
    tts.save(path)
    print(f"Generated ({lang}): {path}")

def main():
    if not os.path.exists(CSV_PATH):
        print("CSV not found!")
        return

    rows = []
    
    # Read CSV
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)

    print(f"Processing {len(rows)} words...")

    # Update Translations and Generate Audio
    updated_rows = []
    
    for row in rows:
        english = row['english'].strip()
        current_turkish = row['turkish'].strip()
        
        # 1. Update Turkish if PENDING
        if current_turkish == "PENDING":
            if english in TRANSLATIONS:
                row['turkish'] = TRANSLATIONS[english]
            elif english.lower() in TRANSLATIONS:
                 row['turkish'] = TRANSLATIONS[english.lower()]
            else:
                 print(f"Warning: No translation found for '{english}'")
        
        turkish_text = row['turkish']
        
        # 2. Generate Audio
        audio_en_file = row['audio_en_file']
        audio_tr_file = row['audio_tr_file']
        
        en_path = os.path.join(AUDIO_EN_DIR, audio_en_file)
        tr_path = os.path.join(AUDIO_TR_DIR, audio_tr_file)
        
        # English Audio
        try:
            generate_audio(english, 'en', en_path)
        except Exception as e:
            print(f"Error generating EN audio for {english}: {e}")

        # Turkish Audio (only if not PENDING)
        if turkish_text != "PENDING":
            try:
                generate_audio(turkish_text, 'tr', tr_path)
            except Exception as e:
                print(f"Error generating TR audio for {turkish_text}: {e}")
        else:
             print(f"Skipping TR audio for {english} (PENDING)")

        updated_rows.append(row)
        # Sleep to avoid rate limiting if any
        # gTTS hits Google Translate API
        time.sleep(0.5) 

    # Write updated CSV
    with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

    print("\nProcessing Complete! CSV updated and audio generated.")

if __name__ == "__main__":
    main()
