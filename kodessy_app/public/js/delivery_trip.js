frappe.ui.form.on("Delivery Trip", {
    setup(frm) {
        frm.set_query("delivery_note", "pickup_warehouses", () => ({filters: {docstatus: ["<", 2]}}));
    },
    refresh(frm) {
        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__("Fetch Pickups"), () => fetch_pickups(frm));
            // Trip created from a Delivery Note: stops arrive pre-filled, pickups empty
            if (frm.is_new() && !frm.__pickups_auto) {
                frm.__pickups_auto = true;
                fetch_pickups(frm, true);
            }
        }
        prefill(frm);
    },
    departure_time(frm) { prefill(frm); },
    validate(frm) { prefill(frm); }
});

frappe.ui.form.on("Delivery Stop", {
    delivery_note(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (row.delivery_note && frm.doc.docstatus === 0) {
            add_pickups_from_note(frm, row.delivery_note);
        }
    }
});

frappe.ui.form.on("Delivery Trip Pickup", {
    async warehouse(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.warehouse) return;
        const info = await get_wh_info(row.warehouse);
        frappe.model.set_value(cdt, cdn, {warehouse_address: info.address, pickup_contact: info.contact});
    }
});

// Pickup 1 defaults to the trip's departure time while it is still blank
function prefill(frm) {
    const rows = frm.doc.pickup_warehouses || [];
    if (frm.doc.docstatus === 0 && rows.length && !rows[0].estimated_pickup && frm.doc.departure_time) {
        rows[0].estimated_pickup = frm.doc.departure_time;
        frm.refresh_field("pickup_warehouses");
    }
}

async function get_wh_info(wh_name) {
    const wh = await frappe.db.get_doc("Warehouse", wh_name);
    let address = [wh.address_line_1, wh.address_line_2, wh.city, wh.state, wh.pin].filter(Boolean).join(", ");
    if (!address) {
        try {
            const r = await frappe.call({
                method: "frappe.contacts.doctype.address.address.get_default_address",
                args: {doctype: "Warehouse", name: wh_name}
            });
            if (r.message) {
                const d = await frappe.db.get_doc("Address", r.message);
                address = [d.address_line1, d.address_line2, d.city, d.state, d.pincode, d.country].filter(Boolean).join(", ");
            }
        } catch (e) {}
    }
    return {address: address, contact: wh.mobile_no || wh.phone_no || ""};
}

async function add_pickups_from_note(frm, dn_name) {
    const dn = await frappe.db.get_doc("Delivery Note", dn_name);
    if (dn.docstatus === 2) return;
    const whs = [];
    (dn.items || []).forEach(i => { if (i.warehouse && !whs.includes(i.warehouse)) whs.push(i.warehouse); });
    for (const w of whs) {
        const rows = frm.doc.pickup_warehouses || [];
        // already have this warehouse + note pair
        if (rows.find(r => r.warehouse === w && r.delivery_note === dn_name)) continue;
        const info = await get_wh_info(w);
        // same warehouse, note missing: fill in the note
        const nonote = rows.find(r => r.warehouse === w && !r.delivery_note);
        if (nonote) {
            const vals = {delivery_note: dn_name};
            if (!nonote.warehouse_address) vals.warehouse_address = info.address;
            if (!nonote.pickup_contact) vals.pickup_contact = info.contact;
            await frappe.model.set_value(nonote.doctype, nonote.name, vals);
            continue;
        }
        const vals = {warehouse: w, delivery_note: dn_name, warehouse_address: info.address, pickup_contact: info.contact};
        // reuse a fully blank row, else add a new one
        const blank = rows.find(r => !r.warehouse && !r.warehouse_address && !r.delivery_note);
        if (blank) {
            await frappe.model.set_value(blank.doctype, blank.name, vals);
        } else {
            frm.add_child("pickup_warehouses", vals);
        }
    }
    prefill(frm);
    frm.refresh_field("pickup_warehouses");
}

async function fetch_pickups(frm, quiet) {
    for (const s of (frm.doc.delivery_stops || [])) {
        if (s.delivery_note) await add_pickups_from_note(frm, s.delivery_note);
    }
    prefill(frm);
    if (!quiet) frappe.show_alert({message: __("Pickups updated"), indicator: "green"});
}
