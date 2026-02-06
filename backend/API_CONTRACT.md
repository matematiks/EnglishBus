# EnglishBus API Contract

**Version:** 1.0.0  
**Base URL:** `http://localhost:8001`  
**Protocol:** REST/JSON  
**Status:** LOCKED (Do not modify without system-wide review)

---

## 🎯 Design Principles

1. **Stateless**: Each request fully self-contained
2. **Atomic**: Session completion is all-or-nothing
3. **Deterministic**: Same input = same output
4. **Frontend-Agnostic**: No UI logic in backend

---

## 📋 Core Endpoints

### 1. Health Check

**Endpoint:** `GET /health`

**Purpose:** Verify system is running

**Request:** None

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

**Status Codes:**
- `200 OK`: System operational

---

### 2. Start Session

**Endpoint:** `POST /session/start`

**Purpose:** Get learning content for current step

**Request:**
```json
{
  "user_id": 1,
  "course_id": 1
}
```

**Response:**
```json
{
  "current_step": 12,
  "items": [
    {
      "word_id": 45,
      "english": "house",
      "turkish": "ev",
      "type": "NEW",
      "image_url": "kurslar/A1_English/images/045.jpg",
      "audio_en_url": "kurslar/A1_English/ing_audio/ing_045.mp3",
      "audio_tr_url": "kurslar/A1_English/tr_audio/tr_045.mp3",
      "order_number": 45
    },
    {
      "word_id": 12,
      "english": "door",
      "turkish": "kapı",
      "type": "REVIEW",
      "image_url": "kurslar/A1_English/images/012.jpg",
      "audio_en_url": "kurslar/A1_English/ing_audio/ing_012.mp3",
      "audio_tr_url": "kurslar/A1_English/tr_audio/tr_012.mp3",
      "order_number": 12,
      "repetition_count": 3
    }
  ],
  "total_items": 2,
  "has_more": false
}
```

**Field Definitions:**

| Field | Type | Description |
|-------|------|-------------|
| `current_step` | int | User's current step in course |
| `items` | array | Words to study this session |
| `word_id` | int | Unique word identifier |
| `type` | string | "NEW" or "REVIEW" |
| `image_url` | string | Relative path to image |
| `audio_en_url` | string | Relative path to English audio |
| `audio_tr_url` | string | Relative path to Turkish audio |
| `order_number` | int | Word's position in course (1-based) |
| `repetition_count` | int | How many times seen (REVIEW only) |
| `total_items` | int | Number of items in session |
| `has_more` | bool | If true, overflow occurred (avalanche guard) |

**Business Rules:**

1. **NEW words:** `order_number <= current_step` AND `repetition_count = 0`
2. **REVIEW words:** `next_review_step <= current_step`
3. **Avalanche Guard:** Max 40 items per session
   - If more, return first 40 and set `has_more: true`
4. **Empty Step:** If no content, increment step and recurse (max 200 skips)

**Status Codes:**
- `200 OK`: Session created
- `404 Not Found`: User or course doesn't exist
- `500 Internal Error`: Database issue

---

### 3. Complete Session

**Endpoint:** `POST /session/complete`

**Purpose:** Atomically update progress after session

**Request:**
```json
{
  "user_id": 1,
  "course_id": 1,
  "completed_word_ids": [45, 12, 8, 23]
}
```

**Response:**
```json
{
  "status": "success",
  "new_step": 13,
  "words_updated": 4
}
```

**Field Definitions:**

| Field | Type | Description |
|-------|------|-------------|
| `completed_word_ids` | array[int] | IDs of words user completed |
| `new_step` | int | User's updated step number |
| `words_updated` | int | Count of progress records updated |

**Business Rules:**

1. **Atomic Transaction:**
   ```
   BEGIN TRANSACTION
     - Increment current_step
     - Update repetition_count for each word
     - Calculate next_review_step (Fibonacci)
   COMMIT or ROLLBACK
   ```

2. **Fibonacci Calculation:**
   - First time (`rep_count = 0 → 1`): `next_review = current_step + 1`
   - Subsequent: `next_review = current_step + Fibonacci[rep_count]`

3. **Error Handling:**
   - Any failure → Complete rollback
   - No partial updates allowed

**Status Codes:**
- `200 OK`: All updates succeeded
- `400 Bad Request`: Invalid word IDs
- `500 Internal Error`: Transaction failed (rollback occurred)

**Error Response:**
```json
{
  "status": "error",
  "error": "Transaction failed: <details>",
  "rollback": true
}
```

---

### 4. Get Unit States (Optional)

**Endpoint:** `GET /courses/{course_id}/units`

**Purpose:** Get unlock status of all units

**Request:** None (course_id in URL)

**Query Parameters:**
- `user_id` (required): User ID

**Response:**
```json
{
  "units": [
    {
      "unit_id": 1,
      "name": "A1 English 1.1",
      "order_number": 1,
      "word_count": 50,
      "status": "OPEN",
      "progress": {
        "seen_count": 50,
        "mastered_count": 50
      }
    },
    {
      "unit_id": 2,
      "name": "A1 English 1.2",
      "order_number": 2,
      "word_count": 50,
      "status": "OPEN",
      "progress": {
        "seen_count": 35,
        "mastered_count": 12
      }
    },
    {
      "unit_id": 3,
      "name": "A1 English 1.3",
      "order_number": 3,
      "word_count": 22,
      "status": "PREVIEW",
      "progress": {
        "seen_count": 0,
        "mastered_count": 0
      }
    }
  ]
}
```

**Unit Status Values:**

| Status | Meaning | User Can |
|--------|---------|----------|
| `OPEN` | Fully unlocked | Study freely |
| `PREVIEW` | Partially unlocked | View words only |
| `LOCKED` | Not yet available | Nothing |

**Unlock Rules:**

1. **First unit:** Always OPEN
2. **PREVIEW:** Previous unit 50% seen (`seen_count >= word_count * 0.5`)
3. **OPEN:** Previous unit mastered (`mastered_count >= word_count` where `rep_count >= 7`)

**Status Codes:**
- `200 OK`: Units retrieved
- `404 Not Found`: Course doesn't exist

---

## 🛡️ Error Handling

### Standard Error Response

```json
{
  "status": "error",
  "error_code": "TRANSACTION_FAILED",
  "message": "Session update failed: database locked",
  "timestamp": "2025-12-14T22:30:00Z"
}
```

### Common Error Codes

| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `USER_NOT_FOUND` | 404 | User doesn't exist |
| `COURSE_NOT_FOUND` | 404 | Course doesn't exist |
| `INVALID_WORD_ID` | 400 | Word ID not in course |
| `TRANSACTION_FAILED` | 500 | Database rollback occurred |
| `EMPTY_COURSE` | 404 | No words in course |

---

## 🧪 Example Flows

### Flow 1: New User First Session

**Step 1:** Start session
```http
POST /session/start
{ "user_id": 1, "course_id": 1 }
```

**Response:** 10 NEW words (order 1-10)

**Step 2:** Complete session
```http
POST /session/complete
{ "user_id": 1, "course_id": 1, "completed_word_ids": [1,2,3,4,5,6,7,8,9,10] }
```

**Response:** `new_step: 2`

---

### Flow 2: Review Session

**Step 1:** Start session (step 15)
```http
POST /session/start
{ "user_id": 1, "course_id": 1 }
```

**Response:**
- 5 NEW words (order 11-15)
- 8 REVIEW words (from steps 1-14)

**Step 2:** Complete
```http
POST /session/complete
{ "completed_word_ids": [11,12,13,14,15,1,2,3,4,5,6,7,8] }
```

**Response:** `new_step: 16`

---

### Flow 3: Crash Recovery

**Step 1:** Start session
```http
POST /session/start
{ "user_id": 1, "course_id": 1 }
```

**Step 2:** Complete (network fails mid-request)
```http
POST /session/complete
{ "completed_word_ids": [1,2,3] }
```

**Response:** 500 error

**Step 3:** Retry (transaction rolled back, safe to retry)
```http
POST /session/complete
{ "completed_word_ids": [1,2,3] }
```

**Response:** 200 OK (idempotent for same step)

---

## 📝 Implementation Notes

### Database Integration

**Implementation uses:**
- `backend/session_manager.py` → `complete_session()`
- SQLite transactions (BEGIN/COMMIT/ROLLBACK)
- `UserCourseProgress` table for step tracking
- `UserProgress` table for word-level data

### Frontend Contract

**Frontend MUST:**
1. Never modify `current_step` locally
2. Trust backend for progress state
3. Handle `has_more: true` gracefully
4. Show user-friendly error messages
5. Allow retry on 500 errors

**Frontend SHOULD NOT:**
- Calculate Fibonacci intervals
- Determine unit unlock status
- Filter words by step
- Handle avalanche logic

---

## ✅ Contract Validation

### Checklist

- [ ] All endpoints documented
- [ ] Request/Response schemas complete
- [ ] Error codes defined
- [ ] Business rules explicit
- [ ] Example flows provided
- [ ] Edge cases covered

---

**Last Updated:** 2025-12-14  
**Status:** LOCKED - Ready for Implementation  
**Next Step:** FastAPI implementation using this contract
