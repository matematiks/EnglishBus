# Settings Menu Overhaul (Design Compliance)
## Phase 1: Infrastructure
- [x] Tailwind: Refactor config to use CSS Variables (`--color-brand-500`)
- [x] CSS: Define default theme variables in `index.html` (:root)
- [x] JS: Update `SettingsManager` to handle Tab switching (`activeTab`) (Obsolete/Grid View)
- [x] JS: Update `SettingsManager` to apply Color Theme and Font Size

## Phase 2: UI Implementation (Tabbed Interface)
- [x] HTML: Implement animated background blobs and keyframes (from App.tsx) <!-- id: 6 -->
- [x] HTML: Refactor Profile Card to match SettingsPage.tsx (Rotated Avatar, Stats) <!-- id: 7 -->
- [x] HTML: Implement 2-Column Grid for 'Algorithm' vs 'Interface' sections <!-- id: 8 -->
- [x] HTML: Refactor Theme Selector to Rectangular Cards <!-- id: 9 -->
- [x] HTML: Implement Collapsible Danger Zone (Reset Progress, Download Data) <!-- id: 10 -->

## Phase 3: Logic & Integration
- [x] JS: Bind Theme/Color pickers to `SettingsManager`
- [x] JS: Implement "Reset Progress" API call (`POST /user/reset-progress`)
- [x] JS: Implement "Download Data" logic
- [x] UI: Polish Avatar Selection (Implemented Modal)
- [x] UI: Fix/Refine Font Size Logic (Added Slider & JS Support)
## Phase 4: Dashboard Harmonization (Stable Restore Point)
- [x] System Restore: Reverted to `iindex.html` (Modern Glass Design) based on user preference.
- [ ] Next Steps: Re-evaluate harmonization needs after stability confirmation.

## Phase 5: Settings Isolation (Current)
- [x] Implement 'Perfect Settings' UI in `#settings-screen` only.
- [x] Rewrite `js/settings.js` to support new UI without affecting Dashboard.
- [x] Verify Settings functionality (Deep Audit Completed).


## Phase 6: Optimization (Performance & UX)
- [x] Fix Icon text visible during load (`display=block`)
- [x] Implement Global Loading Overlay (Hide FOUC)
- [x] Preload Critical Assets (Hero Image, Fonts)

## Phase 7: Backend Audit (Security & Isolation)
- [x] Investigate `UserWordProgress` schema for `user_id`
- [x] Audit all Queries for `user_id` filtering
- [x] Identify and report Ghost Code
- [x] Refactor Global Logic to User-Specific

## Phase 8: Secure Course Reset (Active)
- [x] Backend: Implement `POST /user/reset-course-secure` (checking password) (Used existing `/reset` endpoint)
- [x] Frontend: Create "Confirm Password" Modal in `index.html` (Settings > Danger Zone)
- [x] Frontend: Update `SettingsManager` to handle secure reset flow
- [x] Verification: Test full reset flow with correct/incorrect passwords

## Phase 9: Sentence Generator Logic Fix (Active)
- [x] Backend: Update `practice_endpoints.py` to remove lazy fallback and return proper error if vocabulary is insufficient
- [x] Frontend: Update `study.js` to handle "Insufficient Vocabulary" error gracefully (Show Modal/Alert)
- [x] Verification: Test with Admin (5 words) and confirm error message is shown instead of broken sentences

## Phase 10: Improving Sentence Variety
- [ ] Investigate `sentence_generator.py` template selection logic
- [ ] Verify "food" vs "water" word metadata in DB
- [ ] Add more templates or adjust weights
- [x] Verify fix with diverse vocabulary

## Phase 11: Systemic Sentence Logic Adaptation
- [x] Analyze `A1_Foundation/words.csv` vs `sentence_generator.py` gap
- [x] Categorize all A1 words (Sub, Verb, Obj, Adj) with tags
- [x] Update `RICH_VOCAB_DB` with full vocabulary coverage
- [x] Verify sentence variety with new full dictionary

## Phase 12: Sentence Cards Visual Enhancement
- [x] Backend: Expose `key_word` tuple from `generate_one`
- [x] Backend: Fetch image for sentence key word in `practice_endpoints.py`
- [x] Frontend: Implement 40/60 split layout for sentence mode in `study.js`
- [x] Frontend: Verify image display and responsive layout
## Phase 13: Sentence Variety Maximization (Complete)
- [x] Backend: Add `SV_BASIC`, `SVO_NEG`, and `BE_ADJ` blueprints
- [x] Backend: Update `SentenceAssembler` for negative handling
- [x] Backend: Implement blueprint shuffling and increased retries
- [x] Verification: Test with `debug_generator.py` for structural diversity
## Phase 14: Semantic Conflict Prevention (Complete)
- [x] Backend: Add object pronouns (me, him, her, etc.) to `RICH_VOCAB_DB`
- [x] Backend: Implement identity check in `generate_one` to block "I want me"
- [x] Verification: Test with `debug_refinement.py` for reflexive blockers

## Phase 15: Admin Panel Refactoring (Complete)
- [x] **Design Transfer**: Port CSS variables, glassmorphism, and animations from `index.html`
- [x] **Logic Integration**: Implement Teacher Approval (5-digit ID) and User Stats
- [x] **Functional Polish**: Search, Filter, Course Manager, and Maintenance Mode
- [x] **Verification**: Validate cross-screen consistency and teacher flow

## Phase 16: Service Unification (Data Layer Repair)
- [x] **Diagnosis**: Identify split between Frontend (Logic Error) and Admin (Missing Endpoints).
- [x] **Frontend Fix**: Update `js/api.js` & `js/auth.js` to send `account_type` & `teacher_id`.
- [x] **Backend Fix**: Add `DELETE /users/{id}` & `POST /reset-password` to Admin API.
- [x] **Verification**: Code path analysis confirms "Teacher Register -> Pending List" flow.


## Phase 18: Facade UI Elimination & E2E Verification
- [x] **Diagnosis**: Identify dead buttons and disconnected logic in Messaging and Role flows.
- [x] **Admin Messaging**: Fix double prefix issue (`/admin/messages/admin/messages/send`) in `admin.html`.
- [ ] **Teacher Guard**: Ensure `POST /auth/login` blocks 'pending_approval' users.
- [x] **Student Inbox**: Implement polling/fetching of messages in `index.html`.
- [x] **Auth Fix**: Ensure `teacherId` is saved to `localStorage` in `js/auth.js`.

## Phase 19: Autonomous QA & Hardening
- [x] **Deep Scan**: Inventory all interaction points in `index.html` and `admin.html`.
- [x] **Auth Hardening**: Implement strict frontend validation (Empty fields, duplicate prevention feedback).
- [x] **Settings Fixes**: Ensure `downloadData()` and `resetProgress()` are fully functional.
- [x] **Edge Cases**: Verify Admin self-deletion protection and network error handling.

## Phase 20: Admin UI Polish & Teacher Logic Fixes
- [x] **Teacher Actions Menu**: Implement dropdown for the 'more_vert' button (View Profile, Revoke, etc.).
- [x] **Fix Null IDs**: Investigate and fix why approved teachers have `null` IDs.
- [x] **Revoke Logic**: Add functionality to demote a teacher back to student/individual.

## Phase 21: Frontend Core Rewiring & Dashboard Fix (Completed)
- [x] **Diagnosis**: Stuck "Loading..." state due to ID mismatches and missing API calls.
- [x] **Auth Rewiring**: Rewrote `js/auth.js` to match `index.html` IDs and logic.
- [x] **Dashboard Logic**: Implemented proper data fetching in `js/dashboard.js`.
- [x] **Backend Restoration**: Fixed `Words` table access issue and verified server stability.
- [x] **Verification**: Confirmed full login and dashboard loading flow via Browser Agent.
