# Kodessy ERP — Pharma, Medical Device & Veterinary Distribution

> **End-to-End ERPNext v15 Live Implementation & Evaluation System**  
> Tailored for **Kodessy Sdn Bhd** — Pharmaceutical, Medical Device & Veterinary Importer & Distributor  
> **Currency:** MYR (Malaysian Ringgit) | **Location:** Airport Logistics Zone, Malaysia  
> **Live Cloud URL:** [https://pharma-demo-kodessy.frappe.cloud](https://pharma-demo-kodessy.frappe.cloud)  
> **Default Admin Access:** `Administrator` / `123`  

---

## 📌 1. Project Overview & Scope

This repository contains the production custom app (`kodessy_app`) and the live restored database for an enterprise pharmaceutical distribution workflow covering:
1. **Sales & Distribution** (Quotations, Approval Workflows, Credit Limit Enforcement, Delivery Orders, Invoicing)
2. **Fulfilment & Warehousing** (Multi-temperature Warehouses, Quarantine, FEFO Batch Allocation, Pick & Pack Slips)
3. **Procurement** (Overseas & Local Suppliers, Two-Tier Purchase Order Approvals, Lead Time Tracking)
4. **Quality & Compliance** (Incoming QA Inspection, Quarantine Restrictions, Batch Traceability, Sales Returns)
5. **Finance & Accounting** (Chart of Accounts, Accounts Receivable, Credit Notes, Customer Statements of Account)

---

## 📂 2. Repository Structure

```
John-s-ERP/
├── pyproject.toml                                  # Flit/uv packaging with [tool.bench.frappe-dependencies]
├── setup.py                                        # Backward compatibility for editable pip install
├── requirements.txt                                # Python requirements (flit)
├── kodessy_app/                                    # Root Frappe Custom App Package
│   ├── __init__.py                                 # App version 0.0.1
│   ├── hooks.py                                    # Event hooks, fixture exports, DocType overrides
│   ├── modules.txt                                 # Registered module list
│   ├── patches.txt                                 # Migration patches
│   ├── controllers/                                # Custom Business Logic Controllers
│   │   ├── credit_control.py                       # Customer Credit Limit monitoring & blocking
│   │   ├── quarantine_control.py                   # Quarantine / unreleased stock restrictions
│   │   ├── fefo_control.py                         # First Expiry First Out (FEFO) batch allocation
│   │   └── returns_control.py                      # Mandatory return reason & QA assessment validation
│   └── fixtures/                                   # Frappe Fixtures with explicit 'name' attributes
│       ├── custom_field.json                       # Custom fields for Pharma, Devices, Pack Size, Temp
│       ├── workflow.json                           # Quotation & 2-Tier PO Approval workflows
│       ├── workflow_state.json                     # Workflow states (Draft, Approvals, QA, etc.)
│       ├── workflow_action_master.json             # Workflow transition actions
│       └── print_format.json                       # Custom Warehouse Pick Slip & Pharma DO print formats
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
| **2** | **Customer Credit Limit Control** | [`credit_control.py`](file:///E:/Projects/John-s-ERP/kodessy_app/controllers/credit_control.py): Monitors customer total exposure (unpaid invoices + current order). Triggers alert on Quotation; blocks submission on Sales Order unless authorized override is approved. |
| **3** | **Purchase Order Management** | **Two-Tier Approval Workflow**: `Draft` → `Pending Purchasing Manager Approval` (Tier 1) → `Pending Finance Approval` (Tier 2) → `Approved`. Tracks supplier lead times & outstanding delivery. |
| **4** | **Inventory & FEFO Allocation** | [`fefo_control.py`](file:///E:/Projects/John-s-ERP/kodessy_app/controllers/fefo_control.py): Auto-allocates earliest expiry batch first (FEFO) on Pick Lists and Delivery Notes, supporting authorized manual override. |
| **5** | **Quality Control & Stock Release** | Mandatory `Quality Inspection` on purchase receipt. Stock is held in Quarantine until authorized Quality Unit approval releases it for sale. |
| **6** | **Quarantine Management** | [`quarantine_control.py`](file:///E:/Projects/John-s-ERP/kodessy_app/controllers/quarantine_control.py): Blocks any sales order, delivery note, or invoice from fulfilling stock located in `Quarantine Warehouse` or `Near-Expiry Bin`. |
| **7** | **Stock Count & Reconciliation** | Native ERPNext **Stock Reconciliation** configured for monthly physical counts with discrepancy reporting vs. system stock. |
| **8** | **Pick & Pack Slip** | Custom Jinja/CSS **Pharma Pick & Pack Slip** print format showing storage zone, item code, pack size, FEFO batch, and sign-offs for warehouse staff. |
| **9** | **Delivery Order (DO) & Invoicing** | Custom Jinja/CSS **Pharma Delivery Order (DO)** showing registration no., batch numbers, expiry dates, dispatch temperature (Ambient / Cold Chain), and customer receiving stamp. Partial deliveries fully supported. |
| **10** | **Backorder Reporting** | Standard ERPNext Unfulfilled Orders report filtering outstanding quantities and expected arrival dates. |
| **11** | **Goods Return Management** | [`returns_control.py`](file:///E:/Projects/John-s-ERP/kodessy_app/controllers/returns_control.py): Requires mandatory Return Reason (*Damaged in Transit*, *Quality Issue*, *Wrong Delivery*, *Expired*) and QA assessment status before return can be processed. |
| **12** | **Credit Note Issuance** | Generates Credit Notes against original sales invoices and approved returns with internal manager sign-off. |
| **13** | **Statement of Account** | Accounts Receivable statement showing selected period invoices, credit notes, payments, and running balance in MYR. |
| **14** | **Batch Traceability & Recall** | Complete end-to-end audit trail: Supplier PO receipt → Incoming QA check → Warehouse Storage → Customer Delivery Order. If a batch is recalled, all affected customers are instantly identifiable. |

---

## 📊 4. Interactive Dashboard Cards & Workspace Schemas

To provide an executive overview for management and operational visibility for departments, configure these **Interactive Number Cards** and **Dashboard Charts** on your workspaces:

### A. Recommended Interactive Number Cards
1. **Total Stock Value in Quarantine (MYR)**:
   * DocType: `Bin` | Function: `Sum` on `stock_value`
   * Filter: `warehouse = Quarantine Warehouse - K`
   * Purpose: Real-time visibility into inventory awaiting Quality Unit release.
2. **Near-Expiry Stock Alert (Next 90 Days)**:
   * DocType: `Batch` | Function: `Count`
   * Filter: `expiry_date between Today and Today + 90 Days` and `disabled = 0`
   * Purpose: Proactive flagging of stock to prevent expired goods write-offs.
3. **Customer Credit Limit Violations**:
   * DocType: `Sales Order` | Function: `Count`
   * Filter: `docstatus = 0` and `custom_credit_override_approved_by is set`
   * Purpose: Executive oversight on sales exceeding customer credit limits.
4. **Pending PO Approvals (Tier 1 & Tier 2)**:
   * DocType: `Purchase Order` | Function: `Count`
   * Filter: `workflow_state in ('Pending Purchasing Manager Approval', 'Pending Finance Approval')`
   * Purpose: Procurement bottleneck monitor.

### B. Dashboard Charts
* **Cold Chain vs. Ambient Inventory Ratio**: Donut chart grouped by `custom_storage_condition`.
* **Monthly Sales by Healthcare Facility**: Bar chart grouped by `Customer` (Hospitals vs. Clinics).
* **Supplier Lead Time Performance**: Line chart comparing `expected_delivery_date` vs. actual receipt date.

---

## 🏢 5. Master Data Seeded in the Database

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
* `BATCH-AMOX-2026B` (Amoxicillin) — Expiry: **2026-11-30** (Allocated FIRST by FEFO)
* `BATCH-AMOX-2026A` (Amoxicillin) — Expiry: **2027-01-31** (Allocated SECOND by FEFO)
* `BATCH-INS-2026A` (Insulin) — Expiry: **2026-12-15**

---

## 🧪 6. End-to-End Testing Guide (Interactive UI & REST API)

You can test all 14 scenarios either through the **Frappe Desk UI** or via **REST API** using API Keys with role-based permissions.

### A. Step-by-Step UI Test Walkthrough

1. **Procurement & 2-Tier Approval Flow**:
   * Login as **Purchase User** → Navigate to **Purchase Order** → Create new PO for `Pfizer Global Supply` with item `AMOX-500` (1,000 Boxes @ 45 MYR = 45,000 MYR).
   * Click **Action → Submit for Approval** (State changes to `Pending Purchasing Manager Approval`).
   * Login as **Purchase Manager** → Click **Action → Approve Tier 1** (State changes to `Pending Finance Approval`).
   * Login as **Finance Manager** → Click **Action → Approve Tier 2** (PO submits with `DocStatus = 1`).

2. **Incoming Inspection & Quarantine Restriction**:
   * Go to **Purchase Receipt** against the approved PO. Set accepted warehouse to `Quarantine Warehouse - K`. Submit receipt.
   * Try creating a **Sales Order** or **Delivery Note** pulling stock directly from `Quarantine Warehouse - K`.
   * **Expected Result:** Blocked by [`quarantine_control.py`](file:///E:/Projects/John-s-ERP/kodessy_app/controllers/quarantine_control.py) with message *"Cannot sell or dispatch item from restricted warehouse: Quarantine Warehouse"*.
   * Navigate to **Stock Entry (Material Transfer)**: Transfer stock from `Quarantine Warehouse - K` to `Main Warehouse (Ambient 25-30°C) - K` once QA inspection passes.

3. **Quotation & Sales Manager Approval**:
   * Navigate to **Quotation** → Create quotation for `Sunway Medical Centre` with item `AMOX-500`.
   * Click **Action → Submit for Approval** (State changes to `Pending Sales Manager Approval`).
   * Login as **Sales Manager** → Click **Action → Approve**.
   * Click **Create → Sales Order**.

4. **Customer Credit Limit Validation**:
   * Create a Sales Order for `Klinik Mediviron Subang` (Credit Limit: 15,000 MYR).
   * Add items exceeding 15,000 MYR (e.g., 20,000 MYR).
   * Click **Save / Submit**.
   * **Expected Result:** Blocked by [`credit_control.py`](file:///E:/Projects/John-s-ERP/kodessy_app/controllers/credit_control.py) with *"Order Blocked: Credit Limit Exceeded"*.
   * Check field `Allow Credit Limit Override` and specify `custom_credit_override_approved_by` to test authorized override flow.

5. **FEFO Warehouse Picking & Pick Slip**:
   * On approved Sales Order, click **Create → Pick List**.
   * The system automatically allocates `BATCH-AMOX-2026B` (expiring 2026-11-30) before `BATCH-AMOX-2026A` (expiring 2027-01-31).
   * Click **Print** → Select **Pharma Pick and Pack Slip** print format. Notice the warehouse location, batch, expiry, and signature blocks.

6. **Delivery Order (DO) & Invoicing**:
   * Click **Create → Delivery Note**.
   * Print using **Pharma Delivery Order (DO)**. Observe dispatch temperature, batch/lot numbers, and customer sign-off box.
   * Click **Create → Sales Invoice** to complete fulfillment and recognize revenue.

7. **Returns Management & Credit Note**:
   * Create a **Sales Invoice** with `is_return = 1`.
   * Try submitting without selecting a Return Reason.
   * **Expected Result:** Blocked by [`returns_control.py`](file:///E:/Projects/John-s-ERP/kodessy_app/controllers/returns_control.py) with *"Mandatory Return Reason must be specified"*.
   * Select Return Reason: *Damaged in Transit* and QA Assessment Status: *Accepted - Quarantine & Scrap*.
   * Submit to generate the approved Credit Note.

---

### B. Automated End-to-End REST API Testing

To execute automated tests via Postman, Python, or cURL:

#### 1. Generate API Credentials
In Frappe Desk (`https://pharma-demo-kodessy.frappe.cloud`):
* Navigate to **User List** → Open your test user (or `Administrator`).
* Under **API Access**, click **Generate Keys**.
* Copy the `api_key` and `api_secret`.

#### 2. Authentication Header
All requests must include:
```http
Authorization: token <api_key>:<api_secret>
Content-Type: application/json
```

#### 3. API Test Sequence (cURL Examples)

* **Test Credit Limit Check:**
```bash
curl -X POST https://pharma-demo-kodessy.frappe.cloud/api/resource/Quotation \
  -H "Authorization: token <api_key>:<api_secret>" \
  -H "Content-Type: application/json" \
  -d '{
    "customer": "Sunway Medical Centre",
    "company": "Kodessy",
    "items": [{
      "item_code": "AMOX-500",
      "qty": 100,
      "rate": 55.00
    }]
  }'
```

* **Test Workflow Transition via API:**
```bash
curl -X POST https://pharma-demo-kodessy.frappe.cloud/api/method/frappe.model.workflow.apply_workflow \
  -H "Authorization: token <api_key>:<api_secret>" \
  -H "Content-Type: application/json" \
  -d '{
    "doc": {"doctype": "Purchase Order", "name": "PO-2026-00001"},
    "action": "Approve Tier 1"
  }'
```

* **Test FEFO Batch Query:**
```bash
curl -X GET "https://pharma-demo-kodessy.frappe.cloud/api/resource/Batch?filters=[["item","=","AMOX-500"],["disabled","=",0]]&order_by=expiry_date%20asc" \
  -H "Authorization: token <api_key>:<api_secret>"
```

---

*Repository maintained for Kodessy ERP Project.*
