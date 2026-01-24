# Manual Verification Debugging Guide

## Purpose

Interactive prompts have been added after each step (starting from Step 3) to manually verify that the UI actually transitioned as expected. This helps identify **exactly** where the framework and UI get out of sync.

## How to Use

1. **Run the script normally**: `python CreateMissingWorkItems.py`

2. **At each checkpoint**, the script will **pause** and display a prompt in the console:
   ```
   [STEP3 VERIFY] Did 'Is vehicle drivable?' question appear? Press Enter to continue...
   ```

3. **Look at the browser window** - check if the UI matches what the prompt asks

4. **If YES** - the UI matches: Press **Enter** to continue to next step

5. **If NO** - the UI doesn't match: **DO NOT press Enter**. Note this in the logs:
   - What step failed
   - What the UI actually shows vs what was expected
   - Take a screenshot if possible
   - Then press Ctrl+C to stop execution

## Verification Checkpoints

### Step 3: Add New Complaint
**Prompt**: "Did 'Is vehicle drivable?' question appear?"

**What to check**:
- Dialog should show "Is the vehicle drivable?"
- Two buttons: "Yes" and "No"

**If it failed**:
- UI might still show existing complaint tiles
- Dialog might not have opened at all
- Wrong page loaded

---

### Step 4: Drivable Selection → Damage Type Screen
**Prompt**: "Is damage type screen showing (PM, Glass Damage, Tires, etc.)?"

**What to check**:
- Multiple damage type buttons visible:
  - PM
  - Glass Damage
  - Tires
  - Keys
  - Body Damage
  - Etc.

**If it failed**:
- Still on drivable question
- Dialog disappeared
- Different screen loaded

---

### Step 6: Damage Type → Sub-Damage Screen
**Prompt**: "Is sub-damage screen showing options for {damage_type}?"

**What to check**:
- For Glass Damage: Windshield, Side Window, Rear Window, Mirror, etc.
- For PM: specific PM-related options
- For Tires: Flat Tire, Tire Damage, etc.

**If it failed**:
- Still on damage type selection screen
- Wrong sub-options showing (selected wrong damage type)
- Dialog closed

---

### Step 7: Sub-Damage → Additional Info Page
**Prompt**: "Is Additional Info page showing with summary (Drivable, damage type, etc.)?"

**What to check**:
- Top of form shows summary metadata:
  - "Drivable"
  - Selected damage type (e.g., "Glass Damage")
  - Selected sub-type (e.g., "Windshield Crack")
- "Submit Complaint" button visible at bottom
- Optional: Additional information text field

**If it failed**:
- Still on sub-damage selection
- Summary not showing
- Wrong page entirely

---

### Step 9: Submit Complaint Click
**Prompt**: "Was Submit Complaint button clicked? Did form start processing/closing?"

**What to check**:
- Button should have been clicked
- Look for:
  - Form starting to fade/close
  - Loading spinner
  - Dialog beginning to disappear
  - Any visual feedback that submit was triggered

**If it failed**:
- Button wasn't actually clickable
- Nothing happened after click
- Validation error message appeared

---

## Expected Results

**Success Case**: You press Enter at every checkpoint and script completes

**Failure Case**: One checkpoint fails - you'll know **exactly which transition** didn't work

## Example Debug Session

```
[STEP3 VERIFY] Did 'Is vehicle drivable?' question appear? 
✓ Yes, I see it → Press Enter

[STEP4 VERIFY] Is damage type screen showing (PM, Glass Damage, Tires, etc.)?
✓ Yes, I see 8 damage type buttons → Press Enter

[STEP6 VERIFY] Is sub-damage screen showing options for Glass Damage?
✗ NO! Still showing damage type screen! 
  → Ctrl+C to stop
  → Check logs: "Clicked Glass Damage" but screen didn't change
```

This tells us: **Step 6 click happened but UI didn't transition**

## After Finding the Issue

Once you identify which step fails:

1. **Check the timestamp** - was there actually a delay for verification?
2. **Check the locator** - was the right element clicked?
3. **Check the error logs** - what diagnostics were captured?
4. **Consider**: Is there animation/transition time needed? Is the element clickable but disabled?

## Removing Checkpoints

Once debugging is complete, remove all `input()` calls from [pm_actions_selenium.py](../src/compass_core/pm_actions_selenium.py) to restore normal automated operation.

Search for: `# MANUAL VERIFICATION CHECKPOINT`
