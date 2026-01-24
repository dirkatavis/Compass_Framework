# Diagnostic Logging Reference

## Overview

Every verification step now includes comprehensive diagnostic logging that captures **why** a failure occurred, not just that it happened. When a TimeoutException occurs, the framework automatically logs:

1. **What was expected** - The specific locator/element being waited for
2. **What was found** - Elements actually present on the page
3. **Page state** - Current URL, title, visible dialogs
4. **Button states** - Whether elements exist but are disabled/hidden
5. **Alternatives** - What similar elements ARE available

## Diagnostic Information by Step

### Step 1-2: Create Work Item Dialog

**What's verified**: After clicking "Add Work Item", the Create Work Item dialog must load with "Add New Complaint" button

**On failure, logs**:
```
[STEP2] FAILED - Add New Complaint button not found after 30s
[STEP2] Locator: //button[contains(@class, 'fleet-operations-pwa__nextButton__')]
[STEP2] Current URL: https://...
[STEP2] Page title: Fleet Operations
[STEP2] Dialogs on page: 0 found
```

**Interpretation**:
- If dialogs = 0: Dialog didn't open at all, click may have failed
- If dialogs > 0: Dialog opened but wrong content loaded

---

### Step 3: Add New Complaint

**What's verified**: "Add New Complaint" button is clickable

**On failure, logs**:
```
[STEP3] FAILED - Add New Complaint button not clickable after 30s
[STEP3] Locator: //button[contains(@class, 'fleet-operations-pwa__nextButton__')]
[STEP3] Current URL: https://...
[STEP3] Matching buttons found: 1
[STEP3] Button enabled: False
[STEP3] Button displayed: True
```

**Interpretation**:
- Button found but enabled=False: Existing complaint may need to be selected first
- Button not found: Wrong page loaded
- Button found, enabled=True but not clickable: Overlay/blocker in the way

---

### Step 4: Drivable Question

**What's verified**: "Is vehicle drivable?" question appears with Yes/No buttons

**On failure, logs**:
```
[STEP4] FAILED - Drivable 'Yes' button not found/clickable after 30s
[STEP4] Locator: //button[contains(@class, 'fleet-operations-pwa__drivable-option-button__')][.//h1[text()='Yes']]
[STEP4] Current URL: https://...
[STEP4] Drivable buttons found: 2
[STEP4] Button 0: text='Yes', enabled=True
[STEP4] Button 1: text='No', enabled=True
```

**Interpretation**:
- Buttons found but match failed: Text may have changed or class name changed
- No buttons found: Wrong screen loaded, may have skipped to damage type
- Buttons found but enabled=False: Form validation issue

---

### Step 5: Damage Type Screen

**What's verified**: Damage type selection screen loads with expected damage type button (e.g., "Glass Damage")

**On failure, logs**:
```
[STEP5] FAILED - Damage type 'Glass Damage' button not found after 45s
[STEP5] Locator: //button[contains(@class, 'fleet-operations-pwa__damage-option-button__') and .//h1[text()='Glass Damage']]
[STEP5] Current URL: https://...
[STEP5] Damage option buttons found: 8
[STEP5] Option 0: 'PM'
[STEP5] Option 1: 'Tires'
[STEP5] Option 2: 'Keys'
[STEP5] Option 3: 'Glass'
...
```

**Interpretation**:
- Options found but no match: Check exact text - may be "Glass" not "Glass Damage"
- No options found: Wrong screen, may still be on drivable question
- Correct option in list: Locator needs adjustment for text matching

---

### Step 6: Damage Type Selection

**What's verified**: Damage type button is clickable and click succeeds

**On failure, logs**:
```
[STEP6] FAILED - Damage type 'Glass Damage' button not clickable after 30s
[STEP6] Locator: //button[...]
[STEP6] Current URL: https://...
[STEP6] Button found but enabled=False, displayed=True
```

**Interpretation**:
- enabled=False: Previous selection required or validation error
- Button not found: Timeout in Step 5 was insufficient
- displayed=False: Element exists in DOM but hidden by CSS

---

### Step 7: Sub-Damage Type Selection

**What's verified**: Sub-damage type button (e.g., "Windshield Crack") is clickable

**On failure, logs**:
```
[STEP7] FAILED - Sub-damage type 'Windshield Crack' button not found/clickable after 30s
[STEP7] Locator: //button[contains(@class, 'fleet-operations-pwa__damage-option-button__') and .//h1[text()='Windshield Crack']]
[STEP7] Current URL: https://...
[STEP7] Sub-damage option buttons found: 4
[STEP7] Option 0: 'Windshield'
[STEP7] Option 1: 'Side Window'
[STEP7] Option 2: 'Rear Window'
[STEP7] Option 3: 'Mirror'
```

**Interpretation**:
- Options don't match: Text may be just "Windshield" not "Windshield Crack"
- No options: Still on damage type screen, Step 6 may have failed silently
- Wrong options: Selected wrong damage type in Step 6

---

### Step 8: Additional Info Page

**What's verified**: Submit page loads showing summary with "Drivable" heading

**On failure, logs**:
```
[STEP8] FAILED - Additional Info page summary not found after 45s
[STEP8] Locator: //h1[contains(text(), 'Drivable')]
[STEP8] Current URL: https://...
[STEP8] Page title: Create Work Item
[STEP8] H1 elements found: 3
[STEP8] H1 0: 'Glass Damage'
[STEP8] H1 1: 'Windshield'
[STEP8] H1 2: 'Additional Information'
```

**Interpretation**:
- H1s present but no "Drivable": Summary format changed, need alternative locator
- No H1s: Wrong page entirely
- Right H1s but different structure: Page redesign

---

### Step 9: Submit Complaint Button

**What's verified**: Submit Complaint button is clickable

**On failure, logs**:
```
[STEP9] FAILED - Submit Complaint button not found/clickable after 30s
[STEP9] Locator: //button[.//span[contains(text(), 'Submit Complaint')]]
[STEP9] Current URL: https://...
[STEP9] Total buttons on page: 12
[STEP9] Submit-like button 0: text='Next', enabled=True
[STEP9] Submit-like button 1: text='Submit', enabled=False
[STEP9] Submit-like button 2: text='Cancel', enabled=True
```

**Interpretation**:
- "Submit" found but enabled=False: Validation error, required field missing
- Only "Next" found: Not on final page, need to advance workflow
- "Submit Complaint" exists but enabled=False: Check form validation

---

### Step 10: Form Closure Verification (CRITICAL)

**What's verified**: Dialog/overlay disappears after Submit, indicating successful submission

**On failure, logs**:
```
[STEP10] FAILED - Dialog/overlay still visible after 45s timeout
[STEP10] Expected element to disappear: div.bp6-dialog, div.bp6-overlay
[STEP10] Current URL: https://...
[STEP10] bp6-dialog elements still visible: 1
[STEP10] bp6-overlay elements still visible: 1
[STEP10] Dialog classes: bp6-dialog bp6-dialog-container
[STEP10] Submit Complaint button still present: True
[STEP10] Checking if back at WorkItem tab as fallback...
[STEP10] FAILED - Form still open and not at WorkItem tab. URL: https://...
[STEP10] Diagnosis: Dialog stuck open, Submit may have failed or validation error occurred
```

**Interpretation**:
- Dialog + overlay still visible: Form didn't submit
- Submit button still present: Submission failed or validation error
- Dialog stuck but Submit gone: Submission processing, but slow server response
- At WorkItem tab but dialog visible: False positive from stale overlay element

**Common causes**:
1. **Validation error**: Required field not filled, user sees error message in dialog
2. **Network timeout**: Submit sent but server not responding
3. **JavaScript error**: Client-side error prevented submission
4. **Disabled submit**: Button was clicked but wasn't actually enabled

---

## Using Diagnostics to Debug

### Example 1: Wrong Text Match

**Log output**:
```
[STEP7] FAILED - Sub-damage type 'Windshield Crack' button not found
[STEP7] Option 0: 'Windshield'
[STEP7] Option 1: 'Side Window'
```

**Fix**: CSV has wrong value. Change from "Windshield Crack" to "Windshield"

---

### Example 2: Button Disabled

**Log output**:
```
[STEP9] Submit-like button 1: text='Submit Complaint', enabled=False
```

**Fix**: Form validation failed. Check earlier steps - may have skipped required field

---

### Example 3: Dialog Never Opened

**Log output**:
```
[STEP2] FAILED - Add New Complaint button not found
[STEP2] Dialogs on page: 0 found
```

**Fix**: "Add Work Item" click in Step 1 didn't work. Possible locator change or button was disabled

---

### Example 4: Form Stuck After Submit

**Log output**:
```
[STEP10] Dialog stuck open, Submit may have failed or validation error occurred
[STEP10] Submit Complaint button still present: True
```

**Fix**: Check browser console for JavaScript errors or validation messages. May need to fill additional required field.

---

## Log Levels

- **INFO**: Normal operation, state transitions
- **WARNING**: Fallback logic used, uncertain state (being phased out)
- **ERROR**: Verification failed, operation cannot continue

When you see ERROR logs, the operation **will fail** and return `status: "failed"` - no more silent failures.

---

## Related Documentation

- [VERIFICATION_IMPROVEMENTS.md](VERIFICATION_IMPROVEMENTS.md) - Why verification was added
- [pm_actions_selenium.py](../src/compass_core/pm_actions_selenium.py) - Full implementation
