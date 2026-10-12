# -*- coding: utf-8 -*-
import frappe
from frappe import _

def validate_quarantine_stock(doc, method=None):
    quarantine_keywords = ["quarantine", "near-expiry", "reject"]
    for item in doc.get("items", []):
        warehouse = (item.get("warehouse") or "").lower()
        if any(k in warehouse for k in quarantine_keywords):
            frappe.throw(
                _("Cannot sell or dispatch item {0} from restricted warehouse: <b>{1}</b>. Stock must be formally released by Quality Unit.").format(
                    item.item_code, item.warehouse
                ),
                title=_("Quarantine Restriction")
            )
