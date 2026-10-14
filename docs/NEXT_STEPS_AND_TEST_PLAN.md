# Next Steps and End-to-End Test Plan

Status as of 2026-10-14. Last commit: `57aebbb` (UI refactor) / D11 fix: `see below`. Test target: https://pharma-demo-kodessy.frappe.cloud

## 1. Where we are

| Area | State |
|---|---|
| Code in GitHub | Latest commit `00925a2` — full fixture export (12 fixture files, ~700 records); all workflows, custom fields, property setters, print formats, workspaces, number cards, notifications and email templates are now in the repo |
| Live deploy | Commits `713a80d` (notifications), `d4ecf1c` (cards) and `00925a2` (fixture export) are in GitHub but **not yet deployed** to Frappe Cloud — deploy and re-run checks |
| Automated scenario run | 53 of 57 checks passed against the live site (run at commit `9290da2`; notifications and cards not yet live at that point) |
| Manual / role-based UAT | **Not started** |

### 1.1 Results by deliverable (demo scenarios 1-14)

| # | Scenario | Tested how | Result | Notes |
|---|---|---|---|---|
| 1 | Quotation + approval + convert to SO | API as Administrator | Pass | Direct-submit bypass observed (D2) |
| 2 | Credit limit | API | Pass | 1,000,000 order for Sunway (limit 100,000) blocked; quotation alerted; small order accepted |
| 3 | Two-tier PO | API | Pass | Submit -> Tier 1 -> Tier 2 -> Approved; status, per_received and schedule date present |
| 4 | Inventory, batches, FEFO | API | Pass | Receipt with 2 batches; DN auto-picked the earlier-expiry batch; real-time Bin quantity |
| 5 | QC and release | API | Pass | Inspections recorded; Quarantine -> Main by Administrator. **Non-Quality user block not exercised** |
| 6 | Quarantine, expired, recalled | API | Pass | All three blocked |
| 7 | Stock count | API | Partial | Draft reconciliation shows system vs counted; Stock Balance call returned 0 rows (D4) |
| 8 | Pick and pack | API | Partial | Pick list pass; Packing Slip needs a draft DN (ERPNext rule) |
| 9 | DO and invoicing | API | Pass | Partial delivery 6/10 -> 60% delivered |
| 10 | Backorder | API | Pass | Showed 4 outstanding |
| 11 | Goods return | API | **Code-fixed (D1)** | `validate_sales_return` now also runs in `before_submit`; reset_approval now detects reason/assessment changes too. **Must re-test via UI after next deploy.** |
| 12 | Credit note | API | **Code-fixed (D3)** | `require_credit_note_approval` now calls `validate_sales_return` at submit, closing bypass. **Must re-test via UI.** |
| 13 | Statement of account | API | Pass (runs) | Layout and totals not reviewed |
| 14 | Traceability / audit | API | Pass | Receipt -> delivery linked; version log and workflow comments present |

---

## 2. Open defects (fix before client demo)

| ID | Severity | Finding | Likely cause / action |
|---|---|---|---|
| D1 | **High → Code-fixed** | A sales return with no `custom_return_reason` / `custom_assessment_status` could be submitted if `custom_credit_note_approved_by` was already set. Root cause: `require_credit_note_approval` (`before_submit`) never called `validate_sales_return`, so the field check was skipped at submit time; also `reset_approval_if_changed` only reset the approval on `grand_total` change, not on reason/assessment edits. **Fix:** `require_credit_note_approval` now calls `validate_sales_return(doc)` before the approval-stamp check; `reset_approval_if_changed` now also resets when any item's reason or assessment status changes. **Must be re-tested via UI after next deploy.** |
| D2 | Medium | Submitting a Quotation directly (`frappe.client.submit`) as Administrator skipped the approval workflow and ended Approved. | Administrator bypasses workflow by design in Frappe. Test with a Sales User account to confirm normal users cannot bypass. |
| D3 | Medium → Code-fixed | The "credit note cannot be submitted without approval" gate returned an ERPNext system message rather than our custom message. Root cause: same as D1 — the gate ran but reason/assessment were not re-checked at submit. Now fixed in the same `require_credit_note_approval` change. **Re-test via UI to confirm our message text is shown.** |
| D4 | Low | Stock Balance report returned 0 rows although Bin shows stock. | Likely wrong report filter in the API test. Re-run via the UI with correct date and warehouse filters. |
| D5 | Info | Packing Slip cannot be made from a submitted Delivery Note. | Standard ERPNext behaviour. Documented in User Guide. |

## 3. Risks and clean-up items

| ID | Item | Status | Action |
|---|---|---|---|
| S1 | **Secrets and data in git.** The README previously contained an API key/secret and the admin password. Backup archives at repo root may contain customer data. | **Open** | Rotate the API key/secret and change the Administrator password via the Frappe Cloud dashboard. Remove backup archives from the repo and from history (`git filter-repo` / BFG); add `*.sql.gz`, `*.tar` to `.gitignore`. |
| S2 | Workflows that existed only on the live site (Sales Order V3, Stock Reconciliation, Customer, Supplier, Item V3, Journal Entry, Payment Entry) were not in fixtures. A fresh install would have lacked them. | **Resolved `00925a2`** | All 9 active workflows exported and registered in `hooks.py`. |
| S3 | Credit override field (`custom_credit_override_approved_by`) is a free Link to User. Anyone editing the order can name any approver. | **Open** | Restrict to users with a Sales Manager / Finance role, or require the field to equal the session user holding that role. |
| S4 | Test documents left on the live site: PUR-2026-0001, GRN-2026-0001, batches TST-B-EARLY and TST-B-LATE, QTR-2026-0001, SO-2026-0001, DO-2026-0001, SINV-2026-0001, credit note SINV-2026-0003, STE-2026-0001. | **Open** | Keep as demo trace or cancel in reverse order. Remember stock quantities were created by the receipt. |
| S5 | Demo-data hot-fixes were applied by API (item UOM/pack size/shelf life, supplier groups, `custom_credit_limit`). | **Open** | Confirm they persist after the next migrate and that **Error Log** has no `Kodessy setup step failed` entries. |
| S6 | Default tax template is Malaysia GST 6%. Items have no Item Price in Standard Selling. | **Open** | Confirm SST/tax treatment and load real price lists with the client. |
| S7 | `after_migrate` runs in-process; a failing step only logs. | **Open** | Add a post-deploy checklist query for Error Log. |
| S8 | Notifications and glowing-card UI changes pushed in `713a80d` / `d4ecf1c` have not been live-tested. | **Open** | Deploy and verify bell notifications fire on each workflow stage, submit and cancel; verify cards render with glow in light and dark mode. |

---

## 4. Remaining for complete end-to-end testing

### 4.1 Deploy and smoke test (first)
1. Deploy `main` on Frappe Cloud (Update available -> Deploy). Watch for the BOM, supplier group and item errors above.
2. Re-run [automated checks](#5-automated-checks-available) - expect all green.
3. Confirm the deployed CSS: link groups render as cards with glow; sidebar, dialog Yes/No, list and tab hover work in light and dark mode.

### 4.2 Role-based UAT (not yet done - all tests so far used Administrator)
Create one test user per role and run each scenario as that user:

| Role | Must be able to | Must NOT be able to |
|---|---|---|
| Sales User | Create quotation, submit for approval | Approve own quotation, submit directly, override credit |
| Sales Manager | Approve quotation / SO | - |
| Purchase User | Create PO, submit for approval | Approve tiers |
| Purchase Manager | Approve Tier 1 | Approve Tier 2 |
| Accounts Manager | Approve Tier 2, approve credit notes, invoices, payments | Approve a credit note they created |
| Stock User / Manager | Receive, pick, deliver, count | Release from Quarantine (Stock User) |
| Quality Unit | Inspect, release from Quarantine | - |

### 4.3 Scenario-by-scenario UI scripts

| # | Test | Expected |
|---|---|---|
| 1 | Sales User creates quotation, Submit for Approval; Sales Manager approves; Make Sales Order; SO goes through its review stages | Notifications at each stage; SO confirmed only after final approval |
| 2 | Order above `custom_credit_limit`; then set override and re-save; then partially pay an invoice and re-test with real outstanding | Block, override accepted with warning, exposure uses open invoices |
| 3 | PO through both tiers as separate users; receive part; view PO status and Backorder report | Correct state per tier; per_received and outstanding shown |
| 4 | Receive with two batches and expiries; look at Stock Balance by batch/warehouse; deliver without choosing a batch | FEFO selects earliest expiry |
| 5 | Inspection rejected vs accepted; try releasing as Stock User, then Quality Unit | Stock User blocked, Quality Unit allowed |
| 6 | Mark batch recalled; try SO, Pick List, DN, invoice; expire a batch; try Near-Expiry warehouse | All blocked with clear messages |
| 7 | Stock Reconciliation with a shortfall and an overage; submit; check ledger | Differences posted; discrepancy visible |
| 8 | Pick List from SO, print Pick and Pack Slip; make Packing Slip from **draft** DN | Quantities and batches printed |
| 9 | Two partial DNs and invoices for one SO; over-deliver attempt | Quantities track; over-delivery blocked |
| 10 | Backorder report with partial delivery plus an open PO | Outstanding, on-hand, expected arrival |
| 11 | Customer return with and without reason / assessment (fix D1 first); batch captured | Mandatory fields enforced |
| 12 | Credit note: submit unapproved; approve by another user; self-approve attempt; edit amount after approval | Gate holds; approval resets on edit |
| 13 | Statement for a date range including invoice, credit note, payment | Opening, movements, closing correct; print format reviewed |
| 14 | Open Batch -> View Traceability; review Version history and workflow comments | Full chain visible; audit trail complete |

### 4.4 Notifications (new, untested live)
- For every tracked DocType, trigger: stage change, submit, cancel.
- Verify (a) bell notification for each approver user and the owner, (b) timeline entry `Notification sent to <Role>` and `Notification sent to Owner`, (c) no notification to the acting user's bell, (d) no duplicates beyond the intentional stage + submit pair, (e) transactions never fail when no user holds the role.
- Check email delivery settings if email copies are wanted (Notification Settings).

### 4.5 Non-functional
- Near-expiry scheduler: set a batch expiry inside 90 days, run `flag_near_expiry` from Scheduled Job, confirm flag, ToDo and (if wanted) alert.
- Performance: workspace KPI load time; list views with 1,000+ rows.
- Print formats: DO and Pick and Pack Slip on A4, including Malay/English requirements from the client.
- Backup / restore rehearsal on a staging site.
- Browser matrix: Chrome, Edge, Safari; tablet widths.

### 4.6 Client sign-off items still open (from the requirements document)
- Confirm near-expiry threshold (working default 90 days).
- Confirm additional locations beyond head office and the three airport warehouse units.
- Confirm tax (SST) and chart of accounts.
- Unchecked in the client's feature list (out of current scope): multiple-warehouse reporting extras, supplier management extras, near-expiry alerts, barcode scanning, mobile / handheld devices. Near-expiry flagging exists; confirm whether it counts as "alerts".

---

## 5. Automated checks available

Scratch scripts used in this project (kept outside the repo):
- `scratch/live_test.ps1` - connectivity, deployed CSS, naming series, roles, reports, master data (36 checks).
- `scratch/scenarios.py` - creates a PO, receipt, QC, batches, quotation, SO, DN, invoice, return and credit note, then deletes what it can (57 checks).

Recommended: move these into the repository under `tests/live/`, read credentials from environment variables, and run them after every deploy.

## 6. Phase 1 Demo Deliverables — Requirements, Implementation & Test Scripts

This section maps each of the 14 client-required demo scenarios to the system implementation, its current test status and a concrete step-by-step test script that any tester can follow. Column **Defect / TODO** cross-references open items from sections 2–4.

> **Test pattern:** for every scenario below — (a) run as the correct **role** (not Administrator), (b) trigger a **notification** at every approval step and confirm the bell fires, (c) check the document **timeline** for `Notification sent to <Role>` entries, (d) confirm the **naming series** (e.g. `QTR-2026-####`) is applied.

---

### D1 · Quotation Management

**Requirement:** Create quotations with internal approval workflows and convert approved quotations into confirmed sales orders.

**Implementation:** Workflow _Quotation Approval Workflow_ (Draft → Pending Sales Manager Approval → Approved / Rejected). Only an Approved quotation exposes the **Create → Sales Order** button. Credit check alerts at this stage. Naming series `QTR-YYYY-####`.

**Status:** ✅ Pass (API). ⚠️ D2 — Administrator can bypass workflow via direct submit; re-test with Sales User.

**Test script:**
```
1. Log in as Sales User.
2. Selling → Quotation → New.
   - Customer: Gleneagles Hospital KL
   - Item: AMOX-500, qty 100, rate 12
   - Save → workflow state shows "Draft".
3. Click "Submit for Approval" → state: "Pending Sales Manager Approval".
   - Verify: Sales Manager gets a bell notification; timeline shows "Notification sent to Sales Manager".
4. Log in as Sales Manager → open the quotation → click "Approve".
   - State: "Approved". Owner gets bell notification.
5. Back as Sales User → quotation → Create → Sales Order.
   - Confirm SO is created and linked (so_detail populated).
6. NEGATIVE: as Sales User, create a second quotation and attempt direct submit (Ctrl+S or Submit button).
   - Expected: blocked or workflow enforced; state must NOT jump to Approved.
```

---

### D2 · Customer Credit Limit Control

**Requirement:** Set customer credit limits, monitor outstanding balances, and alert or block new orders when limits are exceeded.

**Implementation:** `custom_credit_limit` on Customer. `credit_control.py` calculates exposure = open invoice balances + current order value. Quotation: orange alert only. Sales Order: hard block unless `custom_credit_override_approved_by` is filled by an authorised user.

**Status:** ✅ Pass (API). ⚠️ S3 — override field is unguarded (anyone can type any name).

**Test script:**
```
1. Accounting → Customer → Sunway Medical Centre → custom_credit_limit = 50,000.
2. As Sales User, create Sales Order for Sunway, total = 60,000.
   - Expected on Save: "Credit limit exceeded" → order is BLOCKED.
3. Create Sales Order for Sunway, total = 10,000.
   - Expected: saved without block.
4. Create a partial Payment Entry for an existing invoice to reduce outstanding.
   - Re-save the blocked order → confirm exposure recalculates and new headroom is used.
5. On the Quotation for Sunway at 60,000 → Save.
   - Expected: orange alert shown; quotation still saves (no hard block at quotation stage).
6. OVERRIDE path: as Sales Manager, open the blocked SO → fill Credit Override Approved By → Save.
   - Expected: warning shown; order saves.
```

---

### D3 · Purchase Order Management

**Requirement:** Create supplier POs with two-tier approval; track PO status, supplier lead times and outstanding deliveries.

**Implementation:** Workflow _Purchase Order Two-Tier Approval_ (Draft → Pending PM Approval → Pending Finance Approval → Approved). `per_received` field tracks delivery %. `Required By` date = lead time. Backorder report shows outstanding quantities. Naming series `PUR-YYYY-####`.

**Status:** ✅ Pass (API).

**Test script:**
```
1. Log in as Purchase User → Buying → Purchase Order → New.
   - Supplier: MedSource International
   - Item: AMOX-500, qty 200, rate 8, Required By: +30 days
   - Save → "Submit for Approval" → state: Pending PM Approval.
2. Log in as Purchase Manager → Approve Tier 1 → state: Pending Finance Approval.
   - Verify: Purchase User + Accounts Manager notified.
3. Log in as Accounts Manager → Approve Tier 2 → state: Approved.
4. Back as Purchase User → Create → Purchase Receipt for qty 100 (partial).
   - Check PO: per_received ≈ 50%, status "To Receive and Bill".
5. Open Reports → Backorder and Inbound Supply → confirm the PO row shows 100 outstanding.
6. NEGATIVE: as Purchase User, attempt to approve Tier 1 yourself → expected: blocked by workflow.
```

---

### D4 · Inventory Management

**Requirement:** Record incoming shipments, stock quantities, batch numbers and expiry dates; real-time stock visibility; FEFO stock allocation.

**Implementation:** Purchase Receipt with batch and expiry per line. `fefo_control.py` auto-fills empty batch on Delivery Note with earliest-expiry batch. Stock Balance and Bin show real-time quantities. Near-expiry scheduler flags batches expiring within 90 days.

**Status:** ✅ Pass (API). ⚠️ D4 — Stock Balance returned 0 rows via API; re-test via UI.

**Test script:**
```
1. Create Purchase Receipt for AMOX-500 from an Approved PO:
   - Row 1: Batch BATCH-A, Expiry 2027-01-01, Qty 50, Warehouse: Quarantine
   - Row 2: Batch BATCH-B, Expiry 2026-06-01, Qty 30, Warehouse: Quarantine
   - Submit.
2. Stock → Stock Balance report → filter by Item AMOX-500 → verify qty 80 in Quarantine.
3. Release both batches to Main Warehouse via Stock Entry (Quality Unit role — see D5).
4. Create Delivery Note for qty 20 without selecting a batch.
   - Expected: BATCH-B (earlier expiry 2026-06-01) is auto-selected by FEFO.
5. Run near-expiry: Scheduled Jobs → flag_near_expiry → check BATCH-B.custom_near_expiry = 1
   and a ToDo exists for Stock Manager.
```

---

### D5 · Quality Control & Stock Release

**Requirement:** Record incoming quality checks; require authorised Quality Unit approval before stock is released for sale.

**Implementation:** Items with `custom_requires_qc_release = 1` are auto-routed to Quarantine warehouse on receipt. `quarantine_control.py` blocks any sale/dispatch from Quarantine. Only Quality Unit / Quality Manager / System Manager can move stock out via Stock Entry.

**Status:** ✅ Pass (API). ⚠️ Non-Quality-user block has not been exercised — must test.

**Test script:**
```
1. Confirm Item AMOX-500 has Requires QC Release ticked.
2. Create Purchase Receipt → verify warehouse auto-switches to Quarantine.
3. Log in as Quality Unit → Quality → Quality Inspection → New.
   - Reference: the Purchase Receipt; Template: Pharma Incoming QC.
   - Set all readings → Status: Accepted → Submit.
4. Stock Entry (Material Transfer) from Quarantine → Main Warehouse, batch and qty.
   - Submit as Quality Unit → succeeds.
5. NEGATIVE: log in as Stock User → attempt same Stock Entry from Quarantine.
   - Expected: blocked with "Only Quality Unit may release from Quarantine" message.
6. NEGATIVE: attempt to create Sales Order for an item still in Quarantine.
   - Expected: blocked by quarantine_control.
```

---

### D6 · Quarantine Management

**Requirement:** Restrict quarantined, unreleased, expired or recalled stock from being allocated or sold.

**Implementation:** `quarantine_control.py` blocks Sales Order, Pick List, Delivery Note and Sales Invoice for stock in Quarantine / Near-Expiry / Reject warehouses, expired batches (`batch.expiry_date < today`) and recalled batches (`custom_recalled = 1`).

**Status:** ✅ Pass (API).

**Test script:**
```
1. QUARANTINE block: create SO with item in Quarantine warehouse → expected: blocked.
2. EXPIRED batch: set Batch.expiry_date = yesterday → add to SO line → expected: blocked.
3. RECALLED batch: Batch → custom_recalled = 1 → add to SO / Pick List / DN → expected: blocked at each.
4. NEAR-EXPIRY warehouse: create SO pulling stock from Near-Expiry Bin warehouse → expected: blocked.
5. Confirm error messages are user-readable (not a Python traceback).
6. After releasing batch from Quarantine (D5) and clearing recalled flag → SO saves normally.
```

---

### D7 · Stock Count & Reconciliation

**Requirement:** Generate stock count reports, record physical counts, identify discrepancies between system and actual stock.

**Implementation:** Stock Reconciliation DocType with system qty vs counted qty diff and value. Approval workflow _Stock Reconciliation Approval_ (Draft → Pending Warehouse Manager Approval → Approved). Stock Balance report. Naming series `SRC-YYYY-####`.

**Status:** ⚠️ Partial. Draft reconciliation displays diff; Stock Balance returned 0 rows via API (D4). Workflow approval on live site now in fixtures.

**Test script:**
```
1. Stock → Stock Reconciliation → New.
   - Warehouse: Main Warehouse; use "Get Items" to populate.
   - Change Qty for one item to system_qty - 5 (shortfall) and one to system_qty + 3 (overage).
   - Save → review Difference column and Value Difference.
2. Submit for Approval → Stock Manager approves → Approved.
3. Stock → Stock Ledger → filter by the reconciliation reference → confirm adjustment entry posted.
4. Stock Balance report (UI) → filter Warehouse: Main, date: today → rows should appear with updated qty.
   - If still 0 rows: check date range and "Include Zero Stock Items" toggle.
5. Run a second count with zero difference → confirm no adjustment entry is created.
```

---

### D8 · Pick & Pack Slip

**Requirement:** Generate picking and packing slips from confirmed sales orders, including product quantities and batch details.

**Implementation:** Pick List (`PCK-YYYY-####`) created from SO. Print format _Pharma Pick and Pack Slip_ (item, storage zone, batch, expiry, sign-offs: picked / QA verified / driver hand-off). Packing Slip is created from a **draft** Delivery Note (ERPNext constraint).

**Status:** ⚠️ Partial. Pick List passes; Packing Slip requires draft DN (D5).

**Test script:**
```
1. From an Approved SO → Create → Pick List.
   - Verify batches are pre-filled (FEFO) and warehouse is Main (not Quarantine).
   - Print → Pharma Pick and Pack Slip → review on screen: item, batch, expiry, zone, three sign-off rows.
2. From the same SO → Create → Delivery Note → leave as DRAFT.
3. From the Draft DN → Create → Packing Slip → fill quantities → Save → Print.
4. NEGATIVE: Submit the DN → then try Create → Packing Slip.
   - Expected: button absent or ERPNext blocks it (document in this state).
5. Verify the Pick and Pack Slip prints registration numbers and storage conditions from the Item master.
```

---

### D9 · Delivery Order & Invoicing

**Requirement:** Generate DOs and invoices from sales orders, supporting partial deliveries and accurate quantity tracking.

**Implementation:** Delivery Note (`DO-YYYY-####`) created from SO; partial qty creates a backorder. Sales Invoice (`SINV-YYYY-####`) created from DN. Print format _Pharma Delivery Order_ (registration no., batch, expiry, customer receiving block).

**Status:** ✅ Pass (API). Partial delivery 6/10 = 60% delivered confirmed.

**Test script:**
```
1. From Approved SO (qty 10) → Create → Delivery Note → change qty to 6 → Submit.
   - SO status: "To Deliver and Bill"; per_delivered_qty ≈ 60%.
2. DN → Print → Pharma Delivery Order → review layout, batch and expiry columns.
3. From DN → Create → Sales Invoice → Submit.
4. From the same SO → Create → second Delivery Note for remaining qty 4 → Submit.
   - SO per_delivered_qty ≈ 100%; status: "To Bill".
5. NEGATIVE: attempt to create a third DN for qty 1 on the fully delivered SO.
   - Expected: over-delivery blocked or qty capped.
```

---

### D10 · Backorder Reporting

**Requirement:** Track unfulfilled customer orders, outstanding quantities and expected stock arrival dates.

**Implementation:** Script report _Backorder and Inbound Supply_ — columns: SO, item, ordered qty, delivered qty, backorder qty, on-hand, shortfall, open PO qty, expected arrival date, PO number.

**Status:** ✅ Pass (API). Showed 4 outstanding.

**Test script:**
```
1. Ensure at least one SO is partially delivered (from D9).
2. Reports → Backorder and Inbound Supply → run with no filters.
   - Verify columns: item, backorder qty, on-hand, shortfall, expected arrival (from PO Required By), PO no.
3. Add a new Delivery Note for the remaining qty → re-run report → row should disappear or backorder = 0.
4. Create a SO for an item with zero stock and no open PO → confirm shortfall shows negative and no expected arrival.
```

---

### D11 · Goods Return Management

**Requirement:** Record customer returns with mandatory reasons, product and batch details, and return assessment status.

**Implementation:** Sales Invoice return (is_return = 1). Each line requires `custom_return_reason` and `custom_assessment_status` (enforced by `returns_control.validate_sales_return`). Batch is captured from the original delivery.

**Status:** ✅ **Code-fixed (D1).** `require_credit_note_approval` (`before_submit`) now calls `validate_sales_return` so reason + QA assessment are mandatory at submit time, even if the approval stamp is present. `reset_approval_if_changed` now also resets when reason/assessment are cleared after approval. **Must be re-tested via UI after next deploy.**

**Test script:**
```
1. Open a submitted Sales Invoice → Create → Return / Credit Note.
2. NEGATIVE: leave custom_return_reason blank → Save.
   - Expected: validation error "Return reason is required".
3. NEGATIVE: leave custom_assessment_status blank → Save.
   - Expected: validation error.
4. Fill both fields on each line (e.g. reason: "Damaged in transit", assessment: "Accepted - Quarantine and Scrap").
   - Save → Submit (after credit note approval — see D12).
5. Confirm batch from original invoice is captured on the return line.
6. Check Stock Ledger: returned qty re-enters the Quarantine or Stores warehouse per assessment.
```

---

### D12 · Credit Note Issuance

**Requirement:** Generate credit notes against original invoices and approved returns, with internal approval.

**Implementation:** Sales Invoice (is_return = 1) acts as credit note. `credit_note_control.py` blocks submit until `custom_credit_note_approved_by` is filled by an Accounts Manager who is not the creator. Changing the amount resets the approval.

**Status:** ✅ **Code-fixed (D3).** `require_credit_note_approval` now re-runs `validate_sales_return` before checking the approval stamp, closing the bypass. An extra negative test step added below: clear reason after approval and attempt submit.

**Test script:**
```
1. From the return invoice (D11) → as creator → click Submit.
   - Expected: blocked with "Return Reason is required" (our message from validate_sales_return) or
     "Credit note must be approved" — whichever fires first. NOT a generic ERPNext message.
2. Fill reason + assessment on every line → Save. Do NOT approve yet → click Submit again.
   - Expected: blocked with "Credit Note must be approved by a Finance Manager".
3. As Accounts Manager (different user) → open the credit note → click "Approve Credit Note".
   - custom_credit_note_approved_by = Accounts Manager user; approved_on = today.
4. Now click Submit → should succeed.
5. NEGATIVE (D1 bypass test): approve a credit note → then clear custom_return_reason on one line → Save.
   - Expected: orange alert "Approval has been reset because the credit note details were changed";
     approved_by is cleared. Submit → blocked again.
6. NEGATIVE: edit the grand_total (change item qty) after approval → Save.
   - Expected: same reset behaviour.
7. NEGATIVE: creator attempts to approve own credit note.
   - Expected: blocked with "You cannot approve your own credit note".
```

---

### D13 · Statement of Account

**Requirement:** Generate customer statements showing invoices, credit notes, payments and outstanding balances for a selected period.

**Implementation:** Standard ERPNext Accounts Receivable / General Ledger reports, filtered by Party Type = Customer. All transactions (SINV, credit notes, Payment Entry) post to the GL automatically.

**Status:** ✅ Pass (API — report runs). Layout and totals not reviewed.

**Test script:**
```
1. Accounting → Accounts Receivable → set:
   - Company: Kodessy Sdn Bhd
   - Date range: start of month to today
   - Party Type: Customer; Party: Gleneagles Hospital KL
   - Run report.
2. Verify rows for: Sales Invoice, Credit Note (negative), Payment Entry.
3. Confirm closing balance = invoiced total - credit notes - payments.
4. Print the report (PDF) → review layout for client presentation.
5. Repeat via General Ledger → Party Type Customer → same party and dates → compare totals.
```

---

### D14 · Reporting & Traceability

**Requirement:** Audit trails, approval records and end-to-end batch traceability from supplier receipt to customer delivery.

**Implementation:** Script report _Batch Recall Traceability_ (Purchase Receipt → QC Inspection → Stock Entry → Delivery Note → Sales Invoice → Customer). "View Traceability" button on Batch form. Frappe Version history and workflow timeline on every document.

**Status:** ✅ Pass (API). Receipt → delivery chain linked; version log and workflow comments present.

**Test script:**
```
1. Stock → Batch → open BATCH-B → click "View Traceability".
   - Report opens filtered to that batch.
   - Verify columns: GRN number, QC result, Stock Entry (quarantine release), DN number, invoice, customer.
2. Open the Batch Recall Traceability report directly → enter batch name → Run.
3. Tick custom_recalled = 1 on the batch → confirm the batch is now blocked on SO / Pick List / DN (D6).
4. Open any workflow-tracked document (e.g. PO) → Activity tab → confirm:
   - Each approval stage shows who acted and when.
   - "Notification sent to <Role>" entries appear for every stage.
   - Version tab shows every field change with old and new values.
5. Open Error Log (Settings → Error Log) → confirm no "Kodessy setup step failed" entries post-deploy.
```

---

### Feature Checklist (Phase 1 scope)

| Feature | In scope | Implemented | Notes |
|---|---|---|---|
| Batch Management | ✅ | ✅ | Batch per receipt line; expiry, recall, near-expiry flags |
| Expiry Date Tracking | ✅ | ✅ | Expiry on batch; daily scheduler; FEFO uses it |
| FEFO / FIFO | ✅ | ✅ | `fefo_control.py` on Delivery Note |
| Multiple Warehouses | ✅ | ✅ | Main, Cold Chain, Quarantine, Near-Expiry Bin, GIT, Stores |
| Bin / Location Tracking | ✅ | ✅ | Bin and Stock Ledger per warehouse |
| Customer Credit Limits | ✅ | ✅ | `custom_credit_limit`; alert on QTR, block on SO |
| Supplier Management | ✅ | ✅ | Supplier, Supplier Group; PO workflow |
| Purchase Approvals | ✅ | ✅ | Two-tier PO workflow |
| Sales Approvals | ✅ | ✅ | Quotation + Sales Order V3 workflows |
| Batch / Lot Recall Tracking | ✅ | ✅ | `custom_recalled`; traceability report; block everywhere |
| Near-Expiry Alerts | ✅ | ✅ | Daily scheduler + ToDo for Stock Manager (threshold: 90 days — pending client confirmation) |
| Stock Reconciliation | ✅ | ✅ | SRC workflow; discrepancy posted to ledger |
| Pick-and-Pack / Delivery Management | ✅ | ✅ | Pick List + Pharma Pick and Pack Slip + DO print format |
| Finance Integration | ✅ | ✅ | Invoices, credit notes, payments, GL, SOA |
| Regulatory Compliance Reporting | ✅ | ✅ | Batch traceability, audit trail, version history |
| Barcode Scanning | ❌ Out of scope | — | Not in Phase 1 |
| Mobile / Handheld Devices | ❌ Out of scope | — | Not in Phase 1 |

---

## 7. Suggested order of work

1. **Commit & deploy** the D11 fix (`credit_note_control.py`) and the UI refactor (`kodessy_glass.css` / `.js`) to Frappe Cloud.
2. **Post-deploy smoke check:** Error Log clean; all 9 workflows present; sidebar hover and card lift work (no glow); bell notifications fire on a stage change.
3. **Re-test D1/D3** via UI — fill return lines, approve, then clear reason and attempt submit → approval must reset and submit must block (see D12 script step 5). Confirm our message text is shown, not ERPNext's generic one.
4. **D2 / D4:** test Quotation bypass with a Sales User account; re-run Stock Balance via UI with correct warehouse/date filters.
5. **Role-based UAT** (section 4.2–4.4 + D1–D14 scripts above) — not yet started; needed before client demo.
6. **S1:** rotate API key/secret and Administrator password; remove backup archives from git history.
7. **S3:** restrict credit override field to authorised roles.
8. **S4:** clean up or archive test documents on the live site.
9. Resolve client open items (4.6); load real master data, price lists and tax configuration.
10. Freeze a release tag and write the release note.
