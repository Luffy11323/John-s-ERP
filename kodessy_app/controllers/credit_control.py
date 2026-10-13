# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.utils import flt

def check_customer_credit_limit(doc, method=None):
    customer = doc.get("customer")
    if not customer and doc.get("quotation_to") == "Customer":
        customer = doc.get("party_name")
    if not customer:
        return

    credit_limit = flt(frappe.db.get_value("Customer", customer, "custom_credit_limit") or 0)
    if credit_limit <= 0:
        return

    outstanding = flt(frappe.db.sql('''
        SELECT SUM(outstanding_amount) 
        FROM `tabSales Invoice`
        WHERE customer = %s AND docstatus = 1 AND company = %s
    ''', (customer, doc.company))[0][0] or 0.0)

    total_exposure = outstanding + flt(doc.grand_total)

    if total_exposure > credit_limit:
        exceeded_by = total_exposure - credit_limit
        msg = _(
            "<b>Customer Credit Limit Exceeded:</b> {0}<br>"
            "Credit Limit: {1:,.2f} {2}<br>"
            "Outstanding Balance: {3:,.2f} {2}<br>"
            "Current Order Total: {4:,.2f} {2}<br>"
            "<b>Total Exposure: {5:,.2f} {2}</b> (Exceeds by {6:,.2f} {2})"
        ).format(customer, credit_limit, doc.currency, outstanding, flt(doc.grand_total), total_exposure, exceeded_by)

        if doc.doctype == "Sales Order":
            if not doc.get("custom_credit_override_approved_by"):
                frappe.throw(msg, title=_("Order Blocked: Credit Limit Exceeded"))
            else:
                frappe.msgprint(msg, title=_("Credit Warning (Authorized Override)"), indicator="orange")
        else:
            frappe.msgprint(msg, title=_("Credit Limit Alert"), indicator="orange")
