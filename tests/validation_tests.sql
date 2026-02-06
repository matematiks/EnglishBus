-- EnglishBus Database Validation Tests
-- Run with: sqlite3 englishbus.db < tests/validation_tests.sql

.mode column
.headers on
.width 5 20 10 10

-- ============================================
-- TEST SUITE 1: DATABASE INTEGRITY
-- ============================================

.print "=========================================="
.print "TEST 1.1: Course Import Validation"
.print "=========================================="
SELECT id, name, total_words, order_number 
FROM Courses 
WHERE name = 'A1 English';

.print ""
.print "Expected: id=1, name='A1 English', total_words=122"
.print ""

-- ============================================
.print "=========================================="
.print "TEST 1.2: Unit Partitioning"
.print "=========================================="
SELECT id, name, order_number, word_count 
FROM Units 
WHERE course_id = 1 
ORDER BY order_number;

.print ""
.print "Expected:"
.print "  Unit 1.1: word_count=50"
.print "  Unit 1.2: word_count=50"
.print "  Unit 1.3: word_count=22"
.print ""

-- ============================================
.print "=========================================="
.print "TEST 1.3: Word Distribution"
.print "=========================================="
SELECT unit_id, COUNT(*) as word_count 
FROM Words 
WHERE course_id = 1 
GROUP BY unit_id 
ORDER BY unit_id;

.print ""
.print "Expected: 50, 50, 22"
.print ""

-- ============================================
.print "=========================================="
.print "TEST 1.4: Boundary Words Check"
.print "=========================================="
.width 5 10 20 10 8
SELECT id, english, turkish, unit_id, order_number 
FROM Words 
WHERE course_id = 1 
AND order_number IN (1, 50, 51, 100, 101, 122)
ORDER BY order_number;

.print ""
.print "Expected:"
.print "  Word 1-50   → unit_id=1"
.print "  Word 51-100 → unit_id=2"
.print "  Word 101-122→ unit_id=3"
.print ""

-- ============================================
.print "=========================================="
.print "TEST 1.5: Media Paths Format"
.print "=========================================="
.width 5 10 40 40
SELECT id, english, image_url, audio_en_url 
FROM Words 
WHERE course_id = 1 
LIMIT 3;

.print ""
.print "Expected format:"
.print "  image_url: kurslar/A1_English/images/XXX.jpg"
.print "  audio_en_url: kurslar/A1_English/ing_audio/ing_XXX.mp3"
.print ""

-- ============================================
-- TEST SUITE 2: DATA QUALITY
-- ============================================

.print "=========================================="
.print "TEST 2.1: No NULL Values"
.print "=========================================="
SELECT 
  COUNT(*) as total_words,
  SUM(CASE WHEN english IS NULL THEN 1 ELSE 0 END) as null_english,
  SUM(CASE WHEN turkish IS NULL THEN 1 ELSE 0 END) as null_turkish,
  SUM(CASE WHEN image_url IS NULL THEN 1 ELSE 0 END) as null_images,
  SUM(CASE WHEN audio_en_url IS NULL THEN 1 ELSE 0 END) as null_audio_en
FROM Words 
WHERE course_id = 1;

.print ""
.print "Expected: All null counts = 0"
.print ""

-- ============================================
.print "=========================================="
.print "TEST 2.2: Sequential Order Numbers"
.print "=========================================="
SELECT 
  MIN(order_number) as min_order,
  MAX(order_number) as max_order,
  COUNT(DISTINCT order_number) as unique_orders,
  COUNT(*) as total_words
FROM Words 
WHERE course_id = 1;

.print ""
.print "Expected: min=1, max=122, unique_orders=122, total_words=122"
.print ""

-- ============================================
.print "=========================================="
.print "TEST 2.3: Turkish Character Encoding"
.print "=========================================="
.width 5 15 20
SELECT id, english, turkish 
FROM Words 
WHERE course_id = 1 
AND (turkish LIKE '%ğ%' 
     OR turkish LIKE '%ü%' 
     OR turkish LIKE '%ş%' 
     OR turkish LIKE '%ı%' 
     OR turkish LIKE '%ö%' 
     OR turkish LIKE '%ç%')
LIMIT 5;

.print ""
.print "Expected: Turkish special characters display correctly"
.print ""

-- ============================================
-- TEST SUITE 3: TABLE STRUCTURE
-- ============================================

.print "=========================================="
.print "TEST 3.1: Required Tables Exist"
.print "=========================================="
.tables

.print ""
.print "Expected: Courses, Units, Words, Users, UserProgress, UserCourseProgress"
.print ""

-- ============================================
.print "=========================================="
.print "TEST 3.2: Words Table Schema"
.print "=========================================="
PRAGMA table_info(Words);

.print ""
.print "Expected columns: id, course_id, unit_id, english, turkish,"
.print "                  image_url, audio_en_url, audio_tr_url, order_number"
.print ""

-- ============================================
-- SUMMARY
-- ============================================

.print ""
.print "=========================================="
.print "TEST SUMMARY"
.print "=========================================="
.print "✅ If all tests show expected results, database is valid"
.print "❌ If any discrepancies, investigate data/import issues"
.print ""
