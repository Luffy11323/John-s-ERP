# Kodessy ERP — Pharma, Medical Device & Veterinary Distribution

> **End-to-End ERPNext v15 Implementation & Demo System**  
> Tailored for **Kodessy Sdn Bhd** — Pharmaceutical, Medical Device & Veterinary Importer & Distributor  
> **Currency:** MYR (Malaysian Ringgit) | **Location:** Airport Logistics Zone, Malaysia  

---

## 📌 1. Project Overview & Scope

This repository contains the complete custom app (`kodessy_app`) and production-ready site backup for an end-to-end ERP implementation covering:
1. **Sales & Distribution** (Quotations, Approval Workflows, Credit Limit Enforcement, Delivery Orders, Invoicing)
2. **Fulfilment & Warehousing** (Multi-temperature Warehouses, Quarantine, FEFO Batch Allocation, Pick & Pack Slips)
3. **Procurement** (Overseas & Local Suppliers, Two-Tier Purchase Order Approvals, Lead Time Tracking)
4. **Quality & Compliance** (Incoming QA Inspection, Quarantine Restrictions, Batch Traceability, Sales Returns)
5. **Finance & Accounting** (Chart of Accounts, Accounts Receivable, Credit Notes, Customer Statements of Account)

---

## 📂 2. Repository Structure

```
John-s-ERP/
├── kodessy_app/                                    # Custom Frappe v15 App
│   ├── pyproject.toml                              # Flit / Frappe packaging
│   ├── setup.py                                    # Backward compatibility for pip / Frappe Cloud
│   ├── requirements.txt                            # Python dependencies
│   ├── README.md                                   # App documentation
│   └── kodessy_app/
│       ├── __init__.py                             # App version 0.0.1
│       ├── hooks.py                                # Event hooks, fixture exports, DocType overrides
│       ├── modules.txt                             # Module registry
│       ├── patches.txt                             # Migration patches
│       ├── controllers/                            # Custom Business Logic Controllers
│       │   ├── credit_control.py                   # Customer Credit Limit monitoring & blocking
│       │   ├── quarantine_control.py               # Quarantine / unreleased stock restrictions
│       │   ├── fefo_control.py                     # First Expiry First Out (FEFO) batch allocation
│       │   └── returns_control.py                  # Mandatory return reason & QA assessment validation
│       └── fixtures/                               # Automatic Frappe Fixtures (bench migrate)
│           ├── custom_field.json                   # Custom fields for Pharma, Devices, Pack Size, Temp
│           ├── workflow.json                       # Quotation & 2-Tier PO Approval workflows
│           ├── workflow_state.json                 # Workflow states (Draft, Approvals, QA, etc.)
│           ├── workflow_action_master.json         # Workflow transition actions
│           └── print_format.json                   # Custom Warehouse Pick Slip & Pharma DO print formats
├── 20261007_180518-client_local-database.sql.gz    # Complete MariaDB database dump
├── 20261007_180518-client_local-files.tar          # Public uploaded files archive
├── 20261007_180518-client_local-private-files.tar  # Private uploaded files archive
├── 20261007_180518-client_local-site_config_backup.json # Site config & DB connection details
└── README.md                                       # This complete reference guide
```

---

## 🎯 3. The 14 Demo Scenarios (1:1 Alignment with Client Spec)

Below is the exact mapping of Jonathan's **Section 15: Demo Requirements** to how they are built in this system:

| # | Demo Requirement | Implementation in System |
|---|---|---|
| **1** | **Quotation Management** | **Quotation Approval Workflow**: `Draft` → `Pending Sales Manager Approval` → `Approved`. Once approved, converts to confirmed Sales Order. |
| **2** | **Customer Credit Limit Control** | [`credit_control.py`](file:///E:/Projects/John-s-ERP/kodessy_app/kodessy_app/controllers/credit_control.py): Monitors customer total exposure (unpaid invoices + current order). Triggers alert on Quotation; blocks submission on Sales Order unless authorized override is approved. |
| **3** | **Purchase Order Management** | **Two-Tier Approval Workflow**: `Draft` → `Pending Purchasing Manager Approval` (Tier 1) → `Pending Finance Approval` (Tier 2) → `Approved`. Tracks supplier lead times & outstanding delivery. |
| **4** | **Inventory & FEFO Allocation** | [`fefo_control.py`](file:///E:/Projects/John-s-ERP/kodessy_app/kodessy_app/controllers/fefo_control.py): Auto-allocates earliest expiry batch first (FEFO) on Pick Lists and Delivery Notes, supporting authorized manual override. |
| **5** | **Quality Control & Stock Release** | Mandatory `Quality Inspection` on purchase receipt. Stock is held in Quarantine until authorized Quality Unit approval releases it for sale. |
| **6** | **Quarantine Management** | [`quarantine_control.py`](file:///E:/Projects/John-s-ERP/kodessy_app/kodessy_app/controllers/quarantine_control.py): Blocks any sales order, delivery note, or invoice from fulfilling stock located in `Quarantine Warehouse` or `Near-Expiry Bin`. |
| **7** | **Stock Count & Reconciliation** | Native ERPNext **Stock Reconciliation** configured for monthly physical counts with discrepancy reporting vs. system stock. |
| **8** | **Pick & Pack Slip** | Custom Jinja/CSS **Pharma Pick & Pack Slip** print format showing storage zone, item code, pack size, FEFO batch, and sign-offs for warehouse staff. |
| **9** | **Delivery Order (DO) & Invoicing** | Custom Jinja/CSS **Pharma Delivery Order (DO)** showing registration no., batch numbers, expiry dates, dispatch temperature (Ambient / Cold Chain), and customer receiving stamp. Partial deliveries fully supported. |
| **10** | **Backorder Reporting** | Standard ERPNext Unfulfilled Orders report filtering outstanding quantities and expected arrival dates. |
| **11** | **Goods Return Management** | [`returns_control.py`](file:///E:/Projects/John-s-ERP/kodessy_app/kodessy_app/controllers/returns_control.py): Requires mandatory Return Reason (*Damaged in Transit*, *Quality Issue*, *Wrong Delivery*, *Expired*) and QA assessment status before return can be processed. |
| **12** | **Credit Note Issuance** | Generates Credit Notes against original sales invoices and approved returns with internal manager sign-off. |
| **13** | **Statement of Account** | Accounts Receivable statement showing selected period invoices, credit notes, payments, and running balance in MYR. |
| **14** | **Batch Traceability & Recall** | Complete end-to-end audit trail: Supplier PO receipt → Incoming QA check → Warehouse Storage → Customer Delivery Order. If a batch is recalled, all affected customers are instantly identifiable. |

---

## 🏢 4. Master Data Seeded in the Database

### A. Warehouses Configured
1. **`Main Warehouse (Ambient 25–30°C) - K`**: General warehouse storage for standard pharmaceutical SKUs.
2. **`Cold Chain Warehouse (2–8°C) - K`**: Temperature-controlled unit for biologics, insulins, and vaccines.
3. **`Quarantine Warehouse - K`**: Incoming inspection holding zone and defective stock quarantine.
4. **`Near-Expiry Bin - K`**: Designated location for stock approaching expiry threshold.

### B. Sample Products (SKUs)
* `AMOX-500` — **Amoxicillin 500mg Capsules** (Pharmaceutical, Ambient, Batch & Expiry, Pack: 10x10 Blister)
* `INS-100` — **Insulin Glargine 100 IU/ml** (Pharmaceutical, Cold Chain 2–8°C, Batch & Expiry, Pack: 5x3ml Pens)
* `PARAC-IV` — **Paracetamol 10mg/ml IV Infusion 100ml** (Pharmaceutical, Ambient, Batch & Expiry, Pack: 100ml Vial)
* `VET-AMOX` — **Veterinary Antibiotic Injectable Suspension** (Veterinary, Ambient, Batch & Expiry, Pack: Bottle)
* `PULSE-OX` — **Fingertip Pulse Oximeter Pro** (Medical Device, Ambient, Serial Number tracked, Pack: Unit)

### C. Sample Customers (with Credit Limits in MYR)
* `Gleneagles Hospital KL` — Credit Limit: **100,000 MYR**
* `Sunway Medical Centre` — Credit Limit: **50,000 MYR**
* `Klinik Mediviron Subang` — Credit Limit: **15,000 MYR**

### D. Sample Suppliers
* `Pfizer Global Supply (Overseas)` — Country: United States (Air Cargo)
* `AstraZeneca Biologics (Overseas)` — Country: United Kingdom (Cold Chain Air Cargo)
* `Apex Healthcare Distribution (Local)` — Country: Malaysia

### E. Sample Batches Seeded (for FEFO testing)
* `BATCH-AMOX-2026B` (Amoxicillin) — Expiry: **2026-11-30** (Will be picked FIRST by FEFO)
* `BATCH-AMOX-2026A` (Amoxicillin) — Expiry: **2027-01-31** (Will be picked SECOND by FEFO)
* `BATCH-INS-2026A` (Insulin) — Expiry: **2026-12-15**

---

## 🚀 5. Deployment Instructions

### Method A: Deploy on Frappe Cloud (Recommended)

1. **Log in to Frappe Cloud** → Click **New Site**.
2. Select **Restore from Backup**:
   * Upload `20261007_180518-client_local-database.sql.gz`
   * Upload `20261007_180518-client_local-files.tar`
   * Upload `20261007_180518-client_local-private-files.tar`
3. Under **Apps**, choose **Frappe v15** and **ERPNext v15**.
4. In Frappe Cloud dashboard, navigate to **Apps** → **Add Custom App**:
   * Repository URL: `https://github.com/Luffy11323/John-s-ERP`
   * Branch: `main`
5. Click **Deploy / Install App on Site**.
6. That's it! Your entire demo with all workflows, custom fields, print formats, and seed data is live!

---

### Method B: Deploy on Local Frappe Bench (Linux / WSL2)

```bash
# 1. Initialize Bench v15
bench init --frappe-branch version-15 frappe-bench
cd frappe-bench

# 2. Get ERPNext and Kodessy App
bench get-app erpnext --branch version-15
bench get-app https://github.com/Luffy11323/John-s-ERP

# 3. Create Site and Install Apps
bench new-site client.local
bench --site client.local install-app erpnext
bench --site client.local install-app kodessy_app

# 4. Restore the Database Backup
bench --site client.local restore /path/to/John-s-ERP/20261007_180518-client_local-database.sql.gz \
  --with-public-files /path/to/John-s-ERP/20261007_180518-client_local-files.tar \
  --with-private-files /path/to/John-s-ERP/20261007_180518-client_local-private-files.tar

# 5. Run Database Migration (Imports all fixtures & custom fields)
bench --site client.local migrate

# 6. Start the Bench
bench start
```

---

## 🎬 6. Recommended Client Demo Walkthrough Flow

When presenting this demo to Jonathan and stakeholders, follow this natural flow:

1. **Procurement & 2-Tier Approval**:
   * Create a Purchase Order for `AMOX-500` to `Pfizer Global Supply`.
   * Show Workflow: Purchasing User submits → Purchasing Manager approves Tier 1 → Finance Manager approves Tier 2.
2. **Incoming Inspection & Quarantine**:
   * Receive goods via Purchase Receipt. Show they automatically land in `Quarantine Warehouse`.
   * Attempt to sell from Quarantine: system **blocks** the order.
   * Perform Quality Inspection → Transfer released stock to `Main Warehouse (Ambient 25-30°C)`.
3. **Sales Quotation & Manager Approval**:
   * Create Quotation for `Sunway Medical Centre`. Show Sales Manager approval workflow.
4. **Credit Limit Check**:
   * Demonstrate placing an order that exceeds the customer's limit (e.g. 60,000 MYR when limit is 50,000 MYR). Show the warning & block.
5. **FEFO Warehouse Picking**:
   * Create Delivery Note / Pick List for Amoxicillin.
   * Highlight how the system automatically selects `BATCH-AMOX-2026B` (expiring Nov 2026) instead of `BATCH-AMOX-2026A` (expiring Jan 2027).
   * Print the **Pharma Pick & Pack Slip** for the warehouse.
6. **Delivery Order (DO) & Invoicing**:
   * Print the **Pharma Delivery Order (DO)** showing batch numbers, expiry dates, dispatch temperature, and receiving stamps.
7. **Customer Return & QA Assessment**:
   * Create a Sales Return. Show mandatory Return Reason and QA Assessment status before Credit Note can be created.
8. **Statement of Account & Batch Recall**:
   * Generate the customer Statement of Account.
   * Open the Batch Traceability tool: select any batch to see the entire history from Pfizer shipment to Sunway Medical Centre delivery.

---

*Repository maintained for Kodessy ERP Project.*
