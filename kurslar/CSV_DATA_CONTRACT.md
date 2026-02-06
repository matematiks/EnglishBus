# EnglishBus CSV Data Contract

## 🎯 Purpose
This document defines the **canonical CSV schema** for EnglishBus course imports.  
**This is the single source of truth.**  
All course generation tools (Colab, scripts, manual) MUST produce this exact format.

---

## 📋 Canonical CSV Schema

### Header Row (EXACT, DO NOT MODIFY)
```csv
id,english,turkish,image_file,audio_en_file,audio_tr_file
```

### Column Definitions

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | Integer | Sequential order number (1, 2, 3...) | `1` |
| `english` | String | English word or phrase | `hello` |
| `turkish` | String | Turkish translation | `merhaba` |
| `image_file` | String | Image filename (with extension) | `001.jpg` |
| `audio_en_file` | String | English audio filename | `ing_001.mp3` |
| `audio_tr_file` | String | Turkish audio filename | `tr_001.mp3` |

---

## 📁 File Naming Conventions

### Images
- **Location:** `kurslar/{COURSE_NAME}/images/`
- **Format:** `{id}.{ext}`  where `ext` = jpg, jpeg, png, or webp
- **Example:** `001.jpg`, `025.png`, `100.webp`

### Audio Files (English)
- **Location:** `kurslar/{COURSE_NAME}/ing_audio/`
- **Format:** `ing_{id}.mp3`
- **Example:** `ing_001.mp3`, `ing_025.mp3`

### Audio Files (Turkish)
- **Location:** `kurslar/{COURSE_NAME}/tr_audio/`
- **Format:** `tr_{id}.mp3`
- **Example:** `tr_001.mp3`, `tr_025.mp3`

---

## ✅ Complete Example

### CSV File (`words.csv`)
```csv
id,english,turkish,image_file,audio_en_file,audio_tr_file
1,hello,merhaba,001.jpg,ing_001.mp3,tr_001.mp3
2,goodbye,hoşçakal,002.png,ing_002.mp3,tr_002.mp3
3,please,lütfen,003.jpg,ing_003.mp3,tr_003.mp3
```

### Directory Structure
```
kurslar/
  A1_English/
    words.csv
    images/
      001.jpg
      002.png
      003.jpg
    ing_audio/
      ing_001.mp3
      ing_002.mp3
      ing_003.mp3
    tr_audio/
      tr_001.mp3
      tr_002.mp3
      tr_003.mp3
```

---

## ⚠️ Critical Rules

1. **NEVER change header column names** - `import_course.py` depends on exact names
2. **ALWAYS use 3-digit zero-padded IDs** - `001` not `1`
3. **Prefixes are mandatory** - `ing_` and `tr_` for audio files
4. **UTF-8 encoding required** - Especially for Turkish characters
5. **No empty rows** - CSV should end immediately after last word

---

## 🚫 Common Mistakes to Avoid

| ❌ Wrong | ✅ Correct | Reason |
|---------|-----------|--------|
| `order,ing_kelimeler,tr_kelimeler` | `id,english,turkish,...` | Column names mismatch |
| `1.mp3` | `ing_001.mp3` | Missing prefix and zero-padding |
| `audio/001.mp3` | `ing_audio/ing_001.mp3` | Wrong folder structure |
| `image_path` column | `image_file` column | Wrong column name |

---

## 🔄 For Course Creators

If you are using **Colab** or any automated tool to generate courses:

1. **Output CSV MUST match this schema exactly**
2. **Test with `import_course.py` before finalizing**
3. **Never manually edit column names "to be more readable"**

**Why?** Because `import_course.py` expects these exact column names.  
Any mismatch = import failure.

---

## 📝 Version History

- **v1.0** (2025-12-14): Initial canonical schema defined
- Format: `id, english, turkish, image_file, audio_en_file, audio_tr_file`
- Audio naming: `ing_XXX.mp3` / `tr_XXX.mp3`

---

**Last Updated:** 2025-12-14  
**Status:** CANONICAL - DO NOT MODIFY WITHOUT SYSTEM-WIDE UPDATE
