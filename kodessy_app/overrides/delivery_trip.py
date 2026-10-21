import datetime
import frappe
from frappe import _
from frappe.utils import add_to_date, cint, flt, get_datetime
from erpnext.stock.doctype.delivery_trip.delivery_trip import DeliveryTrip

PICKUP_DWELL_MINUTES = 0  # time spent loading at each pickup


def _addr_text(name):
	a = frappe.db.get_value(
		"Address",
		name,
		["address_line1", "address_line2", "city", "state", "pincode", "country"],
		as_dict=True,
	)
	if not a:
		return ""
	return ", ".join(p for p in (a.address_line1, a.address_line2, a.city, a.state, a.pincode, a.country) if p)


def _client():
	api_key = frappe.db.get_single_value("Google Settings", "api_key")
	if not api_key:
		frappe.throw(_("Enter API key in Google Settings."))

	import googlemaps
	try:
		return googlemaps.Client(key=api_key)
	except Exception as e:
		frappe.throw(e)


class CustomDeliveryTrip(DeliveryTrip):
	@frappe.whitelist()
	def process_route(self, optimize):
		optimize = str(optimize).lower() in ("1", "true")

		all_pickups = list(self.get("pickup_warehouses") or [])
		pickups = [p for p in all_pickups if (p.warehouse_address or "").strip()]
		if not pickups:
			return super().process_route(optimize)  # unchanged core behaviour

		if not self.driver_address:
			frappe.throw(_("Cannot Calculate Arrival Time as Driver Address is Missing"))

		client = _client()
		depot = _addr_text(self.driver_address)
		departure_datetime = get_datetime(self.departure_time)
		t = departure_datetime
		total_m = 0

		# Ensure distance conversion factor is populated
		uom_factor = getattr(self, "uom_conversion_factor", None)
		if uom_factor is None:
			default_uom = self.default_distance_uom if hasattr(self, "default_distance_uom") else "Kilometer"
			uom_factor = frappe.db.get_value("UOM Conversion Factor", {"from_uom": "Meter", "to_uom": default_uom}, "value") or 0.001
			self.uom_conversion_factor = uom_factor
			self.uom = default_uom

		# ---- Phase 1: pickups ----
		addrs = [p.warehouse_address.strip().replace("\n", ", ") for p in pickups]
		try:
			res = client.directions(origin=depot, destination=depot, waypoints=addrs, optimize_waypoints=optimize)
		except Exception as e:
			frappe.throw(_(str(e)))

		if not res:
			frappe.throw(_("Google returned no route for the pickups"))

		order = res[0].get("waypoint_order") or list(range(len(pickups)))
		legs = res[0]["legs"]

		ordered = [pickups[i] for i in order]
		for pos, p in enumerate(ordered):
			t = add_to_date(t, seconds=legs[pos]["duration"]["value"])
			total_m += legs[pos]["distance"]["value"]
			p.estimated_pickup = t
			t = add_to_date(t, minutes=PICKUP_DWELL_MINUTES)
		current = addrs[order[-1]]

		if optimize:
			rest = [p for p in all_pickups if p not in pickups]
			final = ordered + rest
			for i, p in enumerate(final):
				p.idx = i + 1
			self.pickup_warehouses.sort(key=lambda r: r.idx)

		# ---- Phase 2: deliveries, starting from the last pickup ----
		stops = [s for s in self.get("delivery_stops") if s.address]
		if stops:
			if optimize:
				free = [s for s in stops if not s.locked]
				if len(free) > 1:
					try:
						r = client.directions(
							origin=current,
							destination=depot,
							waypoints=[_addr_text(s.address) for s in free],
							optimize_waypoints=True,
						)
						free_sorted = [free[i] for i in r[0]["waypoint_order"]]
						it = iter(free_sorted)
						stops = [s if s.locked else next(it) for s in stops]
					except Exception as e:
						frappe.throw(_(str(e)))

			try:
				r = client.directions(
					origin=current,
					destination=depot,
					waypoints=[_addr_text(s.address) for s in stops],
				)
			except Exception as e:
				frappe.throw(_(str(e)))

			if r and r[0].get("legs"):
				legs = r[0]["legs"]
				stop_delay = cint(frappe.db.get_single_value("Delivery Settings", "stop_delay")) or 0
				for pos, s in enumerate(stops):
					t = add_to_date(t, seconds=legs[pos]["duration"]["value"])
					dist_val = legs[pos]["distance"]["value"]
					total_m += dist_val
					s.estimated_arrival = t
					s.uom = self.default_distance_uom if hasattr(self, "default_distance_uom") else "Kilometer"
					s.distance = flt(dist_val * uom_factor, 2)
					t = add_to_date(t, minutes=stop_delay)
					if optimize:
						s.idx = pos + 1
				if optimize:
					self.delivery_stops.sort(key=lambda r: r.idx)

		self.uom = self.default_distance_uom if hasattr(self, "default_distance_uom") else "Kilometer"
		self.total_distance = flt(total_m * uom_factor, 2)
		self.save()
