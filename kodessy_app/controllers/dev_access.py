# -*- coding: utf-8 -*-
import frappe


def is_dev_authorized():
	"""Check if current user is Administrator or holds System Manager / Script Manager roles."""
	if not hasattr(frappe, "session") or not frappe.session or not frappe.session.user:
		return False
	if frappe.session.user == "Administrator":
		return True
	roles = frappe.get_roles() if frappe.session.user else []
	return bool({"System Manager", "Script Manager"} & set(roles))


def enable_developer_mode(doc=None, method=None):
	"""Dynamically activate developer mode and server scripts for authorized users."""
	if is_dev_authorized():
		frappe.conf.developer_mode = 1
		frappe.conf.server_script_enabled = True
		if hasattr(frappe, "local"):
			frappe.local.dev_server = 1
			if hasattr(frappe.local, "flags"):
				frappe.local.flags.developer_mode = 1


def extend_bootinfo(bootinfo):
	"""Expose developer_mode and server_script_enabled to Frappe Desk UI."""
	if is_dev_authorized():
		bootinfo.developer_mode = 1
		bootinfo.server_script_enabled = 1
