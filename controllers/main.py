# -*- coding: utf-8 -*-
"""
Public-facing routes:
  * /elks/calendar/<id>             -- one published month, full page
  * /elks/calendar                  -- latest published month
  * /elks/calendar/json/<year>/<m>  -- JSON feed used by the website widget
  * /elks/calendar/graphic/<event>  -- per-event graphic (SVG or binary)

The JSON feed returns enough metadata for the JS widget to render a fully
themed calendar that matches the printed PDF: month name, year,
seasonal/holiday emoji strip, theme primary/secondary colours, holiday
labels per day, and a formatted time string on every event.
"""
import calendar as pycal
import json
from datetime import date, datetime, time, timedelta

import pytz

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
        """Feed the embeddable widget. Returns events grouped by day plus
        enough header metadata (month name, year, emoji strip, theme
        colours, holiday labels) for the widget to render an unstyled
        page into a themed calendar."""
        first = date(year, month, 1)
        if month == 12:
            last = date(year + 1, 1, 1)
        else:
            last = date(year, month + 1, 1)
        # Convert the [first, last) local-time window into UTC-naive
        # bounds because Odoo stores calendar.event.start as UTC. Without
        # this, an event at 5:30 PM on the last day of the month in
        # Pacific time (00:30 UTC of the FIRST OF NEXT MONTH) would fall
        # outside a naive "start < last" filter and get dropped.
        lodge_tz = pytz.timezone(
            request.env["calendar.event"]._get_lodge_tz()
        )
        local_start_bound = lodge_tz.localize(datetime.combine(first, time.min))
        local_end_bound = lodge_tz.localize(datetime.combine(last, time.min))

        # Look up the matching publication (if any) so we can pick up its
        # theme. If none exists for this month/year, create a transient
        # (in-memory) record so we can still call the helpers.
        Pub = request.env["elks.calendar.publication"].sudo()
        pub = Pub.search([
            ("year", "=", str(year)),
            ("month", "=", str(month)),
        ], limit=1)
        if not pub:
            pub = Pub.new({
                "year": str(year),
                "month": str(month),
            })

        theme = pub.theme_id if pub.theme_id else None
        emojis = pub.month_emojis()

        # Per-day holiday labels for the month.
        days_in_month = pycal.monthrange(year, month)[1]
        holidays = {}
        for d in range(1, days_in_month + 1):
            label = pub.holiday_for_day(d)
            if label:
                holidays[str(d)] = label

        # Events — UTC bounds converted from the lodge-local window
        # computed above, so late-evening events on the last day of the
        # month don't spill into the next UTC date and get dropped.
        start_dt = local_start_bound.astimezone(pytz.utc).replace(tzinfo=None)
        end_dt = local_end_bound.astimezone(pytz.utc).replace(tzinfo=None)
        # display_time / display_day on calendar.event already convert to
        # the LODGE_TZ constant defined in models/calendar_event.py — no
        # per-user-timezone variation. No `with_context(tz=...)` needed
        # here.
        Event = request.env["calendar.event"].sudo()
        # Sort by (start asc, name asc) so events sharing a start time
        # render alphabetically after chronological. The JS widget
        # re-sorts defensively but a sorted payload also keeps the JSON
        # debuggable.
        events = Event.search([
            ("start", ">=", start_dt),
            ("start", "<", end_dt),
        ], order="start asc, name asc")
        payload = []
        for ev in events:
            graphic = ev.effective_graphic() if hasattr(ev, "effective_graphic") else None
            payload.append({
                "id": ev.id,
                "name": ev.name,
                # day is the day-of-month in the lodge's TZ, server-computed
                # so the widget doesn't need to do timezone math on a naive
                # ISO datetime string.
                "day": ev.display_day() if hasattr(ev, "display_day") else None,
                "start": ev.start.isoformat() if ev.start else None,
                "stop": ev.stop.isoformat() if ev.stop else None,
                "time": ev.display_time() if hasattr(ev, "display_time") else "",
                "allday": bool(getattr(ev, "allday", False)),
                "banner_style": ev.elks_banner_style or "none",
                "banner_label": ev.display_banner_label() if ev.is_banner() else "",
                "banner_sub": ev.elks_banner_sub or "",
                # Colour + box + italic sourced from the elks.calendar.banner.style
                # record — so a lodge that adds a new banner style via the GUI
                # gets it fully styled on the widget with no code change.
                "banner_color": ev.banner_color() if ev.is_banner() else "",
                "banner_box": ev.banner_is_box() if ev.is_banner() else False,
                "banner_italic": ev.banner_is_italic() if ev.is_banner() else False,
                # Leading emoji from the banner style name so the widget
                # renders the same icon the dropdown does.
                "banner_symbol": ev.banner_symbol() if ev.is_banner() else "",
                "has_graphic": bool(graphic),
                # For FA-icon graphics, send the class + colour directly
                # so the JS renders an <i> tag inline — no image endpoint
                # round-trip needed. For SVG/binary, keep the URL.
                "fa_class": graphic.get("fa_class", "") if graphic else "",
                "fa_color": graphic.get("fa_color", "") if graphic else "",
                "graphic_url": (
                    f"/elks/calendar/graphic/{ev.id}"
                    if graphic and "fa_class" not in graphic else ""
                ),
            })

        return request.make_response(
            json.dumps({
                "year": year,
                "month": month,
                "month_name": pycal.month_name[month],
                "emojis": emojis,
                "theme": {
                    "primary": theme.primary_color if theme else "#c0392b",
                    "secondary": theme.secondary_color if theme else "#1f6f4a",
                    "name": theme.name if theme else "",
                },
                "holidays": holidays,
                "events": payload,
                "header_title": pub.header_title or "",
                "header_subtitle": pub.header_subtitle or "",
                "footer_text": pub.footer_text or "",
            }),
            headers=[
                ("Content-Type", "application/json"),
                # No-cache so a freshly-saved event time shows up on the
                # next page refresh instead of being served from the
                # browser's or any CDN's cached response.
                ("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0"),
                ("Pragma", "no-cache"),
                ("Expires", "0"),
            ],
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
