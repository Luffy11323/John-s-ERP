# Next Steps and End-to-End Test Plan

Status as of 2026-10-13. Test target: https://pharma-demo-kodessy.frappe.cloud

## 1. Where we are

| Area | State |
|---|---|
| Code in GitHub | Latest commit includes themes, notifications, naming, controllers, setup fixes |
| Live deploy | Deployment of commits up to `9290da2` was in progress when this was written; `713a80d` (notifications) and `d4ecf1c` (cards) need one more Deploy |
| Automated scenario run | 53 of 57 checks passed against the live site (run before notifications and cards were deployed) |
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
| 11 | Goods return | API | **Fail** | Return without reason was saved (D1) |
| 12 | Credit note | API | Pass | Approve then submit worked; "blocked before approval" result not conclusive (D3) |
| 13 | Statement of account | API | Pass (runs) | Layout and totals not reviewed |
| 14 | Traceability / audit | API | Pass | Receipt -> delivery linked; version log and workflow comments present |

---

## 2. Open defects (fix before client demo)

| ID | Severity | Finding | Likely cause / action |
|---|---|---|---|
| D1 | **High** | A sales return with no `custom_return_reason` / `custom_assessment_status` was saved (SINV-2026-0002, since deleted). Spec requires mandatory reason. | Hook `returns_control.validate_sales_return` is registered on Sales Invoice `validate`; confirm it runs on the live bench (hook load, field population by `make_sales_return`, or DocField mandatory-ness). Reproduce in the UI, then add a server-side test. |
| D2 | Medium | Submitting a Quotation directly (`frappe.client.submit`) as Administrator skipped the approval workflow and ended Approved. | Check whether this is Administrator-only. Test with a Sales User account. If normal users can bypass, block submit unless `workflow_state == Approved`. |
| D3 | Medium | The check "credit note cannot be submitted without approval" returned an ERPNext message about credit notes, not our message. | Re-test through the UI with a fresh return and confirm the text from `require_credit_note_approval`. |
| D4 | Low | Stock Balance report call returned 0 rows although Bin shows stock. | Probably wrong report filters in the test. Re-run with the report's real filter set. |
| D5 | Info | Packing Slip cannot be made from a submitted Delivery Note. | Standard ERPNext. Document it in the guide (done) or switch to the Pick List-based pack slip print. |

## 3. Risks and clean-up items

| ID | Item | Action |
|---|---|---|
| S1 | **Secrets and data in git.** The README previously contained an API key/secret and the admin password, and the repo root holds database and file backup archives. | Rotate the API key/secret and change the Administrator password. Remove the backup archives from the repo and from history (`git filter-repo`/BFG), add them to `.gitignore`. |
| S2 | Workflows that exist only on the live site (Sales Order V3, Stock Reconciliation, Customer, Supplier, Item) are not in `fixtures/workflow.json`. A fresh install would lack them. | Export them into fixtures and list them in `hooks.py` fixtures filters. |
| S3 | Credit override field (`custom_credit_override_approved_by`) is a free Link to User. Anyone editing the order can name any approver. | Restrict to users with a Sales Manager / Finance role, or require the field to equal the session user holding that role. |
| S4 | Test documents left on the live site: PUR-2026-0001, GRN-2026-0001, batches TST-B-EARLY and TST-B-LATE, QTR-2026-0001, SO-2026-0001, DO-2026-0001, SINV-2026-0001, credit note SINV-2026-0003, STE-2026-0001. | Keep as demo trace or cancel in reverse order. Remember stock quantities were created by the receipt. |
| S5 | Demo-data hot-fixes were applied by API (item UOM/pack size/shelf life, supplier groups, `custom_credit_limit`). | Confirm they persist after the next migrate and that **Error Log** has no `Kodessy setup step failed` entries. |
| S6 | Default tax template is Malaysia GST 6%. Items have no Item Price in Standard Selling (ERPNext adds one on first order). | Confirm SST/tax treatment and load real price lists with the client. |
| S7 | `after_migrate` runs in-process; a failing step only logs. | Add a post-deploy checklist query for Error Log. |

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

## 6. Suggested order of work

1. Rotate secrets and remove backups from git (S1).
2. Deploy; re-run automated checks.
3. Fix D1, D2; re-test D3, D4.
4. Export all workflows to fixtures (S2); restrict credit override (S3).
5. Create role test users; run UAT 4.2-4.4.
6. Resolve client open items (4.6); load real master data.
7. Clean up demo documents (S4); freeze a release tag and write the release note.
