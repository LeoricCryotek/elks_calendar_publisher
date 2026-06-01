# -*- coding: utf-8 -*-
"""
Public-facing routes:
  * /elks/calendar/<id>             -- one published month, full page
  * /elks/calendar                  -- latest published month
  * /elks/calendar/json/<year>/<m>  -- JSON feed used by the website widget
  * /elks/calendar/graphic/<event>  -- per-event graphic (SVG or binary)
"""
import json
from datetime import date

from odoo import http
from odoo.http import request


class ElksCalendarController(http.Controller):

    @http.route("/elks/calendar", type="http", auth="public", website=True)
    def latest_calendar(self, **kw):
        Pub = request.env["elks.calendar.publication"].sudo()
        latest = Pub.search([("state", "=", "published")],
                            order="year desc, month desc", limit=1)
        if not latest:
            return request.render("elks_calendar_publisher.public_empty")
        return request.redirect(f"/elks/calendar/{latest.id}")

    @http.route("/elks/calendar/<int:pub_id>",
                type="http", auth="public", website=True)
    def show_calendar(self, pub_id, **kw):
        pub = request.env["elks.calendar.publication"].sudo().browse(pub_id)
        if not pub.exists() or pub.state != "published":
            return request.not_found()
        return request.render(
            "elks_calendar_publisher.public_calendar_page",
            {"pub": pub},
        )

    @http.route("/elks/calendar/json/<int:year>/<int:month>",
                type="http", auth="public", csrf=False)
    def calendar_json(self, year, month, **kw):
        """Feed the embeddable widget. Returns events grouped by day."""
        first = date(year, month, 1)
        if month == 12:
            last = date(year + 1, 1, 1)
        else:
            last = date(year, month + 1, 1)
        Event = request.env["calendar.event"].sudo()
        events = Event.search([("start", ">=", first), ("start", "<", last)])
        payload = []
        for ev in events:
            graphic = ev.effective_graphic() if hasattr(ev, "effective_graphic") else None
            payload.append({
                "id": ev.id,
                "name": ev.name,
                "start": ev.start.isoformat() if ev.start else None,
                "stop": ev.stop.isoformat() if ev.stop else None,
                "banner_style": ev.elks_banner_style or "none",
                "banner_label": ev.display_banner_label() if ev.is_banner() else "",
                "banner_sub": ev.elks_banner_sub or "",
                "has_graphic": bool(graphic),
                "graphic_url": (f"/elks/calendar/graphic/{ev.id}"
                                if graphic else ""),
            })
        return request.make_response(
            json.dumps({"year": year, "month": month, "events": payload}),
            headers=[("Content-Type", "application/json")],
        )

    @http.route("/elks/calendar/graphic/<int:event_id>",
                type="http", auth="public")
    def event_graphic(self, event_id, **kw):
        ev = request.env["calendar.event"].sudo().browse(event_id)
        graphic = ev.effective_graphic() if ev.exists() else None
        if not graphic:
            return request.not_found()
        if "svg" in graphic:
            return request.make_response(
                graphic["svg"],
                headers=[("Content-Type", "image/svg+xml")],
            )
        return request.make_response(
            graphic["binary"],
            headers=[("Content-Type", "application/octet-stream"),
                     ("Content-Disposition",
                      f'inline; filename="{graphic.get("filename", "graphic")}"')],
        )
