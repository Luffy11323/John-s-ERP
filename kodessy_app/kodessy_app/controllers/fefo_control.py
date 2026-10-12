# -*- coding: utf-8 -*-
import frappe
from frappe import _

def auto_allocate_fefo_batches(doc, method=None):
    for item in doc.get("items", []):
        if not item.item_code or item.get("batch_no"):
            continue
        
        has_batch = frappe.db.get_value("Item", item.item_code, "has_batch_no")
        if not has_batch:
            continue

        batches = frappe.db.sql('''
            SELECT b.name, b.expiry_date, b.batch_qty
            FROM `tabBatch` b
            JOIN `tabStock Ledger Entry` sle ON sle.batch_no = b.name
            WHERE b.item = %s 
              AND b.disabled = 0
              AND (b.expiry_date >= CURDATE() OR b.expiry_date IS NULL)
              AND sle.warehouse = %s
            GROUP BY b.name
            HAVING SUM(sle.actual_qty) > 0
            ORDER BY b.expiry_date ASC
        ''', (item.item_code, item.warehouse), as_dict=True)

        if batches:
            item.batch_no = batches[0].name
