# Kodessy ERP - Pharma, Medical Device & Veterinary Distribution

ERPNext v15 / Frappe v15 custom app (`kodessy_app`) for **Kodessy Sdn Bhd**, a pharmaceutical,
medical device and veterinary importer and distributor (no retail pharmacy).

> **Security notice (open action items):**
> - Credentials (API key/secret, Administrator password) appear in earlier git history. They must be rotated before the repo becomes public.
> - Database and file backup archives (`2026*.sql.gz`, `.tar`, site config) are committed at the repo root and may contain customer data. They should be removed from git and its history (`git filter-repo` / BFG), then added to `.gitignore`.

- **Live site:** https://pharma-demo-kodessy.frappe.cloud
- **Currency / location:** MYR, Airport Logistics Zone, Malaysia
- **Scope:** sales (incl. quotations), fulfilment (warehouse and stock), procurement, finance

> Credentials are intentionally **not** stored in this repository. Request API keys and logins
> from the project owner. If you find a key or password in the git history, treat it as exposed and rotate it.

## Documentation map

| Document | Audience | Purpose |
|---|---|---|
| [README.md](README.md) | Developers / project owner | What the app does, how it is built, status, deployment |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | Business users | Every working DocType: why it exists, how it fulfils the requirement, how documents link together |
| [docs/NEXT_STEPS_AND_TEST_PLAN.md](docs/NEXT_STEPS_AND_TEST_PLAN.md) | Project owner / QA | Test results so far, open defects, what remains for full end-to-end testing |

---

## 1. Module coverage

| Module | Coverage |
|---|---|
| Sales and quotations | Quotation -> internal approval -> Sales Order (approval) -> Pick List -> Delivery Note -> Sales Invoice |
| Customer credit control | Exposure check on Quotation (alert) and Sales Order (block, with authorised override) |
| Procurement | Two-tier PO approval (Purchase Manager -> Accounts Manager), status, lead time, outstanding deliveries |
| Warehousing and stock | Multiple temperature-zoned warehouses, batch and expiry tracking, FEFO allocation, partial deliveries |
| Quality and quarantine | Inspection on receipt, auto-routing to Quarantine, release only by Quality Unit |
| Finance | Invoices, returns, credit notes with approval gate, statement of account |
| Traceability and recall | Batch recall flag, batch-to-customer traceability report, audit trail |
| Notifications | Role + owner notifications and timeline activity on every workflow stage, submit and cancel |

---

## 2. What is in the app

### 2.1 Business-rule controllers (`kodessy_app/controllers/`)

| File | Rule enforced | Hooked on |
|---|---|---|
| `credit_control.py` | Exposure = open invoice balance + this order. Over limit: **alert** on Quotation, **block** on Sales Order unless `custom_credit_override_approved_by` is set. Limit read from `Customer.custom_credit_limit`. | Quotation, Sales Order `validate` |
| `quarantine_control.py` | Blocks any sale or dispatch from Quarantine, Near-Expiry or Reject warehouses and any expired or recalled batch. Auto-routes receipts of QC-release items into Quarantine. Only Quality Unit / Quality Manager / System Manager may move stock out of Quarantine. | Sales Order, Pick List, Delivery Note, Sales Invoice, Purchase Receipt, Stock Entry |
| `fefo_control.py` | Fills an empty batch with the earliest-expiry batch that has stock in the line's warehouse. | Delivery Note `validate` |
| `returns_control.py` | Every return line needs `custom_return_reason` and `custom_assessment_status`. | Delivery Note, Sales Invoice `validate` |
| `credit_note_control.py` | Credit note cannot be submitted until approved (`approve_credit_note`); approval resets if the amount changes; creator cannot approve their own note. | Sales Invoice `validate`, `before_submit` |
| `workflow_notify.py` | Sends a bell notification to approver roles + owner and writes a "Notification sent to <Role>" entry to the document timeline on every workflow stage change, submit and cancel. Never blocks a transaction. | 18 tracked DocTypes (see User Guide) |

### 2.2 Setup on every `bench migrate` (`setup_pharma.after_migrate`)

Each step is isolated: a failure is rolled back and written to **Error Log** (title `Kodessy setup step failed: <step>`) without stopping the others.

1. `apply_naming_series` - `PREFIX-YYYY-####` on 16 DocTypes
2. `set_fefo_allocation` - Stock Settings batch pick by expiry
3. `fix_workflow_roles` - maps non-existent "Finance Manager" to "Accounts Manager"
4. `ensure_roles` - creates **Quality Unit**
5. `ensure_uoms`, `ensure_supplier_groups`
6. `fix_demo_items` - UOM table, shelf life and mandatory Pack Size on demo items
7. `set_demo_credit_limits`
8. `ensure_custom_fields`, `make_return_fields_mandatory`
9. `ensure_quality_templates` - QC parameters and template
10. `ensure_stock_reconciliation_workflow`

### 2.3 Naming series

| DocType | Prefix | | DocType | Prefix |
|---|---|---|---|---|
| Quotation | QTR | | Purchase Invoice | PINV |
| Sales Order | SO | | Stock Entry | STE |
| Delivery Note | DO | | Stock Reconciliation | SRC |
| Sales Invoice | SINV | | Quality Inspection | QI |
| Pick List | PCK | | Payment Entry | PAY |
| Material Request | MR | | Journal Entry | JV |
| Purchase Order | PUR | | Supplier Quotation | SQ |
| Purchase Receipt | GRN | | Request for Quotation | RFQ |

### 2.4 Reports

| Report | Type | Purpose |
|---|---|---|
| Batch Recall Traceability | Script | Supplier receipt -> QC -> warehouse -> delivery -> invoice -> customer, per batch |
| Backorder and Inbound Supply | Script | Open SO quantity vs delivered, on-hand, open PO and expected arrival |
| Stock Balance, General Ledger, Accounts Receivable | Standard ERPNext | Stock count basis, customer statement of account |

### 2.5 Custom fields

| DocType | Field | Purpose |
|---|---|---|
| Item | `custom_product_category`, `custom_pack_size` (mandatory), `custom_storage_condition`, `custom_registration_no`, `custom_requires_qc_release` | Regulatory and QC attributes |
| Customer | `custom_credit_limit` | Credit ceiling used by `credit_control.py` |
| Quotation | `custom_sales_manager_approval`, `custom_credit_override` | Approval record, override flag |
| Sales Order | `custom_credit_override_approved_by` | Authorised credit override |
| Delivery Note | `custom_delivery_type`, `custom_temperature_recorded` | DO print format |
| Sales Invoice Item | `custom_return_reason`, `custom_assessment_status` | Return validation |
| Sales Invoice | `custom_credit_note_approved_by`, `custom_credit_note_approved_on` | Credit note approval |
| Batch | `custom_recalled`, `custom_recall_reason`, `custom_near_expiry` | Recall and expiry control |

### 2.6 Workflows

All nine active workflows are now exported to `fixtures/workflow.json` and registered in `hooks.py`. A fresh `bench migrate` loads them automatically.

| DocType | Workflow | Stages | In repo fixtures? |
|---|---|---|---|
| Quotation | Quotation Approval Workflow | Draft → Pending Sales Manager Approval → Approved / Rejected | ✅ Yes |
| Purchase Order | Purchase Order Two-Tier Approval | Draft → Pending PM Approval → Pending Finance Approval → Approved / Rejected | ✅ Yes |
| Sales Order | Sales Order V3 | Preparing → Pending Review → Pending Final Approval → Approved | ✅ Yes |
| Stock Reconciliation | Stock Reconciliation Approval | Draft → Pending Warehouse Manager Approval → Approved / Rejected | ✅ Yes |
| Customer | Customer | Pending Approval → Changes Required → Approved | ✅ Yes |
| Supplier | Supplier | Pending Approval → Changes Required → Approved | ✅ Yes |
| Item | Item V3 | Pending Approval → Changes Required → Approved | ✅ Yes |
| Journal Entry | Journal Entry | Pending Approval → Approved / Rejected | ✅ Yes |
| Payment Entry | Payment Entry | Pending Approval → Approved / Rejected | ✅ Yes |

### 2.7 Scheduler

`tasks.flag_near_expiry` (daily): flags batches expiring within 90 days (`custom_near_expiry = 1`), clears the flag when no longer applicable, and raises a ToDo for Stock Managers. The 90-day threshold is a working default pending client confirmation.

### 2.8 Theme and UI

- `public/css/kodessy_glass.css`: sky-blue / teal / emerald glass theme, vivid navbar gradient, glowing hover on cards, **individual glowing link-group cards** on every workspace, sidebar, dialog (Yes/No), list-row and tab hover, dark-mode variants.
- `public/js/kodessy_glass.js`: workspace KPI cards (data from `api.py`).
- `public/js/sales_invoice.js`: credit-note approval banner. `public/js/batch.js`: "View Traceability" button.
- `fixtures/print_format.json`: Pharma Pick and Pack Slip, Pharma Delivery Order.

---

## 3. Demo scenario status

_Last automated run: 2026-10-13 (commit `9290da2`) — **53 of 57 checks passed.**_
_Commits `713a80d` (notifications), `d4ecf1c` (cards) and `00925a2` (full fixture export) were pushed after that run and have **not yet been verified on live**._

Full details, open defects and remaining work: [docs/NEXT_STEPS_AND_TEST_PLAN.md](docs/NEXT_STEPS_AND_TEST_PLAN.md).

| # | Scenario | Status |
|---|---|---|
| 1 | Quotation management and approval | Pass (see defect D2) |
| 2 | Customer credit limit control | Pass |
| 3 | Purchase order two-tier approval | Pass |
| 4 | Inventory, batches, expiry, FEFO | Pass |
| 5 | Quality control and release | Pass (non-Quality-user block untested) |
| 6 | Quarantine, expired, recalled blocks | Pass |
| 7 | Stock count and reconciliation | Partial (draft count works; report check inconclusive) |
| 8 | Pick and pack | Partial (pick list pass; packing slip must be made from a draft DN) |
| 9 | Delivery order and invoicing, partial deliveries | Pass |
| 10 | Backorder reporting | Pass |
| 11 | Goods return | **Open defect D1** |
| 12 | Credit note with approval | Pass (re-verify D3) |
| 13 | Statement of account | Pass |
| 14 | Reporting and traceability | Pass |

---

## 4. Repository structure

```
John-s-ERP/
  README.md
  docs/
    USER_GUIDE.md
    NEXT_STEPS_AND_TEST_PLAN.md
  pyproject.toml  setup.py  requirements.txt  logo.png
  kodessy_app/
    hooks.py              doc_events, scheduler, assets, fixtures, after_migrate
    api.py                workspace KPI data
    setup_naming.py       naming series
    setup_pharma.py       roles, UOMs, items, custom fields, QC templates, workflows
    tasks.py              near-expiry scheduler
    controllers/          credit, quarantine, fefo, returns, credit note, workflow notifications
    kodessy_app/report/   batch_recall_traceability, backorder_and_inbound_supply
    public/               css, js, images
    fixtures/             custom_field (66), property_setter (134), workflow (9), workflow_state (40),
                         workflow_action_master (36), print_format (36), notification (6),
                         email_template (6), number_card (55), workspace (32), role (2)
```

> **Housekeeping (open):** the repo root contains database / file backup archives (`2026*.sql.gz`, `.tar`, site config). These may hold customer data and secrets. Remove them from version control and history (see next-steps item S1). Credentials in earlier git history also require rotation.

---

## 5. Deployment

```bash
bench get-app kodessy_app https://github.com/Luffy11323/John-s-ERP.git
bench --site <site> install-app kodessy_app
bench --site <site> migrate
```

On **Frappe Cloud** a push does not deploy by itself: open the bench, choose **Update available** for `kodessy_app`, then **Deploy**. The deploy runs a backup, then `bench migrate`.

Troubleshooting seen so far:

| Symptom | Cause | Fix |
|---|---|---|
| Backup fails with MariaDB error 1040 "Too many connections" | Site busy / small plan | Retry after a few minutes, stop other activity, restart bench or raise plan |
| Migrate fails with `Unexpected UTF-8 BOM` on a fixture | File saved with BOM by PowerShell | Re-save as UTF-8 without BOM (fixed in commit `73d2c14`) |
| Orders fail with "UOM Box not found in Item" | `fix_demo_items` failed on mandatory Pack Size | Fixed in setup; check Error Log for `setup step failed` |
| PO creation fails with `cannot unpack non-iterable NoneType` | Supplier references a missing Supplier Group | `ensure_supplier_groups` creates them |
| Workflow missing on fresh install (Sales Order, Stock Recon, etc.) | Workflow existed only in live DB, not in fixtures | Fixed in commit `00925a2` — all 9 workflows now in `fixtures/workflow.json` |

---

*Maintained for the Kodessy ERP pharma project. Built on ERPNext v15 / Frappe v15.*
