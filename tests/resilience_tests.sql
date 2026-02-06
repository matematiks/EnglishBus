-- EnglishBus Resilience Tests
-- Tests for long-term system stability
-- Run with: sqlite3 englishbus.db < tests/resilience_tests.sql

.mode column
.headers on

.print "=========================================="
.print "RESILIENCE TEST 8.4: Orphan Data Detection"
.print "=========================================="
.print ""

-- Test 1: Orphan UserProgress (word deleted but progress remains)
.print "Test 1: Orphan UserProgress Entries"
.print "------------------------------------"
SELECT COUNT(*) as orphan_progress_count
FROM UserProgress up
LEFT JOIN Words w ON up.word_id = w.id
WHERE w.id IS NULL;

.print ""
.print "Expected: 0 (no orphan progress)"
.print ""

-- Test 2: Orphan UserCourseProgress (course deleted but progress remains)
.print "Test 2: Orphan UserCourseProgress Entries"
.print "------------------------------------------"
SELECT COUNT(*) as orphan_course_progress_count
FROM UserCourseProgress ucp
LEFT JOIN Courses c ON ucp.course_id = c.id
WHERE c.id IS NULL;

.print ""
.print "Expected: 0 (no orphan course progress)"
.print ""

-- Test 3: Orphan Words (unit deleted but words remain)
.print "Test 3: Orphan Words (No Parent Unit)"
.print "--------------------------------------"
SELECT COUNT(*) as orphan_words_count
FROM Words wo
LEFT JOIN Units u ON wo.unit_id = u.id
WHERE u.id IS NULL;

.print ""
.print "Expected: 0 (all words have valid units)"
.print ""

-- Test 4: Orphan Units (course deleted but units remain)
.print "Test 4: Orphan Units (No Parent Course)"
.print "----------------------------------------"
SELECT COUNT(*) as orphan_units_count
FROM Units un
LEFT JOIN Courses c ON un.course_id = c.id
WHERE c.id IS NULL;

.print ""
.print "Expected: 0 (all units have valid courses)"
.print ""

.print "=========================================="
.print "RESILIENCE TEST 8.5: Turkish Collation Check"
.print "=========================================="
.print ""

.print "Sample Turkish Words (Default Sort):"
.print "-------------------------------------"
SELECT turkish 
FROM Words 
WHERE turkish LIKE '%ğ%' OR turkish LIKE '%ş%' OR turkish LIKE '%ç%'
ORDER BY turkish
LIMIT 10;

.print ""
.print "NOTE: For MVP, client-side sorting is acceptable."
.print "For production, configure COLLATE TURKISH in SQLite."
.print ""

.print "=========================================="
.print "SUMMARY"
.print "=========================================="
.print "✅ If all orphan counts = 0, data integrity is perfect"
.print "❌ If any orphan count > 0, investigate and clean up"
.print ""
