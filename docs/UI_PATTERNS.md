# Palantir Foundry Fleet Operations PWA - UI Patterns

## Discovered Patterns (January 2026)

This document captures UI/UX patterns discovered during PM Work Item workflow implementation.

---

## Application Architecture

### Single Page Application (SPA)
- **NOT modal dialogs** - all overlays are permanent UI components
- Navigation uses URL routing, not show/hide overlays
- Elements like `bp6-overlay`, `bp6-dialog` are **permanent** SPA structure
- Page transitions observable via URL changes

### Auto-Submit Behavior
- **MVA Input**: Application auto-submits after entering 8 digits
- **No Enter key needed** - pressing Enter causes duplicate submission
- Framework should enter MVA and wait, not send `Keys.RETURN`

---

## HTML Element Patterns

### Button Structure
**Pattern**: Text content is nested in `<p>` tags, not directly in `<span>`

```html
<!-- ACTUAL structure (found in production) -->
<button type="button" class="bp6-button fleet-operations-pwa__nextButton__5dy90n">
    <span class="bp6-button-text">
        <p class="fleet-operations-pwa__submitText__5dy90n">Next</p>
    </span>
</button>

<!-- INCORRECT assumption -->
<button><span>Next</span></button>
```

**XPath Pattern**: `//button[.//p[contains(text(), 'Button Text')]]`

**Examples**:
- Next button: `//button[.//p[contains(text(), 'Next')]]`
- Create Work Item: `//button[.//p[contains(text(), 'Create Work Item')]]`
- Submit Complaint: Uses `<span>` directly (exception to pattern)

---

### Page Titles/Headings

#### Mileage Page
**Pattern**: Uses `<div class="bp6-entity-title-title">` instead of `<h1>`

```html
<div class="bp6-entity-title-title">RECORDED MILEAGE *</div>
```

**XPath**: `//div[contains(@class, 'bp6-entity-title-title') and contains(text(), 'MILEAGE')]`

#### OpCodes Page
**Pattern**: No H1 heading at all - verify by presence of opCode items

```html
<div class="fleet-operations-pwa__opCodeItem__5dy90n">
    <img src="..." alt="Glass" class="fleet-operations-pwa__opCodeImage__5dy90n">
    <div class="fleet-operations-pwa__opCodeText__5dy90n">Glass Repair/Replace</div>
</div>
```

**Verification XPath**: `//div[contains(@class, 'opCodeItem')]`  
**Click XPath**: `//div[contains(@class, 'opCodeItem') and .//div[contains(text(), 'Glass Repair/Replace')]]`

**Note**: OpCode items are clickable `<div>` elements, not `<button>` elements

---

## Workflow Patterns

### Existing Complaint Flow (Reuse)
1. Add Work Item button
2. Select existing complaint tile
3. Click Next
4. **Skips directly to Mileage page** (no Additional Info, no Submit Complaint)
5. Mileage → OpCodes → Create Work Item → Done

**Key**: Steps 4-9 (Drivable → Additional Info → Submit) are **skipped entirely**

### New Complaint Flow (Create)
1. Add Work Item button
2. Click "Add New Complaint"
3. Drivable question (Yes/No)
4. Damage type selection
5. Sub-damage selection
6. Additional Info page (summary with checkboxes)
7. Submit Complaint button
8. Mileage → OpCodes → Create Work Item → Done

**Key**: Steps 4-7 only execute for new complaints

---

## Locator Strategy

### Prefer Specific Classes
- Use `fleet-operations-pwa__*` classes when available
- More stable than generic selectors

### Text-Based Fallbacks
- When class structure is complex, use text content
- Example: `//button[.//p[contains(text(), 'Next')]]`

### Verification Strategy
1. **First choice**: Specific class + text content
2. **Fallback**: Generic class patterns (e.g., `bp6-entity-title-title`)
3. **Last resort**: Text-only selectors

---

## Common Pitfalls

### ❌ Incorrect Assumptions
- Assuming `<h1>` headings exist on all pages
- Looking for text in `<span>` when it's in `<p>`
- Treating OpCodes as buttons instead of divs
- Sending Enter key after MVA input (causes double-submit)
- Waiting for dialogs to disappear (they're permanent overlays)

### ✅ Correct Patterns
- Verify pages by specific UI elements (divs, classes)
- Check button structure with `.//p` for text
- Click divs for OpCode items
- Let application auto-submit MVA after 8 digits
- Use URL changes to detect navigation

---

## Page-Specific Notes

### Mileage Page
- Title: `RECORDED MILEAGE *`
- Input: Numeric input with value (e.g., "7738")
- Button: `<p>Next</p>`
- Next action: Navigate to OpCodes page

### OpCodes Page
- No H1 heading
- Multiple `opCodeItem` divs (clickable)
- Glass options: "Glass Calibrate", "Glass Repair/Replace"
- Each item has image + text div structure

### WorkItem Created Page
- Expected: H1 with "Work Item" or "WorkItem" text
- **Status**: Not yet verified (need HTML from successful run)

### Home Page Verification
- URL contains "health"
- "Add Work Item" button present
- **Status**: Not yet verified (need HTML from successful run)

---

## Testing Recommendations

1. **Always inspect HTML during failures** - assumptions often incorrect
2. **Use debug pause** to manually verify page state
3. **Test both flows**: existing complaint (reuse) and new complaint (create)
4. **Verify locators** on actual pages, not documentation
5. **Check button structure** before writing XPath

---

## Updates Log

- **2026-01-23**: Initial documentation
  - Discovered button `<p>` tag pattern
  - Identified Mileage page div structure
  - Found OpCodes page lacks H1 heading
  - Confirmed SPA architecture (not dialogs)
  - Documented auto-submit MVA behavior
  - Mapped existing vs new complaint flows
