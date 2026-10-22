import frappe

def sync_customer_primary_contact(doc, method=None):
	"""
	When a Contact is saved or linked to a Customer:
	If it is marked as Primary (or no billing contact is set),
	ensure is_billing_contact = 1 so Statement of Accounts never fails.
	Also sync the email directly to Customer.email_id.
	"""
	is_primary = doc.get("is_primary_contact")
	is_billing = doc.get("is_billing_contact")

	if is_primary and not is_billing:
		doc.is_billing_contact = 1

	email = doc.get("email_id")
	if not email and doc.get("email_ids"):
		for row in doc.get("email_ids"):
			if row.get("is_primary") or not email:
				email = row.get("email_id")

	for link in doc.get("links", []):
		if link.get("link_doctype") == "Customer" and link.get("link_name"):
			cust_name = link.get("link_name")
			if is_primary or doc.get("is_billing_contact"):
				if email and frappe.db.exists("Customer", cust_name):
					frappe.db.set_value(
						"Customer",
						cust_name,
						{
							"customer_primary_contact": doc.name,
							"email_id": email
						},
						update_modified=False
					)
