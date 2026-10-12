# -*- coding: utf-8 -*-
import frappe
from frappe import _

def validate_sales_return(doc, method=None):
    if not doc.get("is_return"):
        return

    for item in doc.get("items", []):
        if not item.get("custom_return_reason"):
            frappe.throw(
                _("Row #{0}: Mandatory <b>Return Reason</b> must be specified for item {1}.").format(item.idx, item.item_code),
                title=_("Return Validation")
            )
        if not item.get("custom_assessment_status"):
            frappe.throw(
                _("Row #{0}: QA Assessment Status is required before return credit note can be processed.").format(item.idx),
                title=_("Return Assessment Required")
            )
