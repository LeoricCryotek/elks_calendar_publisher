# -*- coding: utf-8 -*-
"""
The main publishable record. Pick a month + year + theme + source calendar,
and the system renders a printable monthly calendar PDF.
"""
import base64
import calendar as pycal
from datetime import date, datetime, time, timedelta

import pytz

from odoo import api, fields, models


MONTHS = [(str(i), pycal.month_name[i]) for i in range(1, 13)]


class ElksCalendarPublication(models.Model):
    _name = "elks.calendar.publication"
    _description = "Monthly Calendar Publication"
    _order = "year desc, month desc"

    name = fields.Char(compute="_compute_name", store=True)
    month = fields.Selection(MONTHS, required=True, default=str(date.today().month))
    year = fields.Selection(
        selection="_get_year_options",
        required=True,
        default=lambda self: str(date.today().year),
    )

    @api.model
    def _get_year_options(self):
        """Dropdown options for the Year field — current year plus 10 forward.

        Re-evaluated each time the form opens, so the list stays current
        without anyone touching the code.
        """
        current = date.today().year
        return [(str(y), str(y)) for y in range(current, current + 11)]
    theme_id = fields.Many2one("elks.calendar.theme", required=True, string="Theme")
    calendar_id = fields.Many2one(
        "res.users",  # placeholder; Odoo's calendar is per-user.
        string="Source User Calendar",
        help="User whose calendar.event records will populate the grid. "
             "Leave blank to include events from every user.",
    )
    event_filter_ids = fields.Many2many(
        "calendar.event",
        string="Manually Pinned Events",
        help="Optional: events to force-include regardless of date filter.",
    )

    header_title = fields.Char(default="Lewiston Elks Lodge #896")
    header_subtitle = fields.Char(default="From our Home on the River")
    footer_text = fields.Text(
        default="Calendar items, dates and times are subject to change. "
                "Watch the Lewiston Elks Lodge #896 Facebook page for updates.",
    )

    state = fields.Selection(
        [("draft", "Draft"), ("published", "Published")],
        default="draft",
    )
    pdf_attachment_id = fields.Many2one("ir.attachment", readonly=True)
    preview_html = fields.Html(compute="_compute_preview_html", sanitize=False)

    # -- Computed ---------------------------------------------------------

    @api.depends("month", "year")
    def _compute_name(self):
        for rec in self:
            if rec.month and rec.year:
                rec.name = (
                    f"{pycal.month_name[int(rec.month)]} {rec.year} Calendar"
                )
            else:
                rec.name = "New Calendar"

    @api.depends("month", "year", "theme_id", "calendar_id", "event_filter_ids")
    def _compute_preview_html(self):
        """Render a small HTML preview using the same QWeb body the PDF
        uses, so editors can see what they're about to publish.

        Render the BODY template only — not report_calendar_document —
        because the body is a fragment that fits inside an HTML field.
        report_calendar_document wraps the body in web.html_container,
        which would inject a full <!DOCTYPE html>...</html> string into
        the field and crash Odoo's readonly HTML widget (retargetLinks
        sees a null ownerDocument when full-document HTML is parsed in
        a fragment context).
        """
        for rec in self:
            if not rec.theme_id:
                rec.preview_html = (
                    "<em>Pick a theme to see a preview.</em>"
                )
                continue
            try:
                rec.preview_html = self.env["ir.qweb"]._render(
                    "elks_calendar_publisher.report_calendar_body",
                    {"pub": rec},
                )
            except Exception as exc:
                rec.preview_html = (
                    f"<em>Preview unavailable: {exc}</em>"
                )

    # -- Public API -------------------------------------------------------

    def action_render_pdf(self):
        """Render the QWeb report and save it as an attachment on this record.

        This does NOT change the publication state — it just produces the PDF
        so the editor can preview/download it. Call action_publish to make
        the publication public.

        Odoo 19 API: call _render_qweb_pdf on the ir.actions.report model
        with the report's xml-id. Returns a (pdf_bytes, content_type) tuple.
        """
        self.ensure_one()
        report_ref = "elks_calendar_publisher.action_report_calendar"
        pdf_content, _content_type = (
            self.env["ir.actions.report"]
            ._render_qweb_pdf(report_ref, res_ids=self.ids)
        )
        # Replace any prior attachment for this publication so we don't
        # accumulate stale copies.
        if self.pdf_attachment_id:
            self.pdf_attachment_id.unlink()
        attachment = self.env["ir.attachment"].create({
            "name": f"{self.name}.pdf",
            "type": "binary",
            "datas": base64.b64encode(pdf_content),
            "res_model": self._name,
            "res_id": self.id,
            "mimetype": "application/pdf",
        })
        self.pdf_attachment_id = attachment
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{attachment.id}?download=true",
            "target": "self",
        }

    def action_publish(self):
        """Mark this publication as live on the public website.

        Does NOT render a PDF. The website widget reads events directly
        from calendar.event, so a PDF isn't required to go live. Editors
        can click Generate PDF separately when they want a printable copy.
        """
        self.ensure_one()
        self.state = "published"
        return True

    def action_unpublish(self):
        """Take this publication off the public website (back to draft)."""
        self.ensure_one()
        self.state = "draft"
        return True

    def action_open_pdf(self):
        self.ensure_one()
        if not self.pdf_attachment_id:
            return self.action_render_pdf()
        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/{self.pdf_attachment_id.id}?download=true",
            "target": "self",
        }

    # -- Internals --------------------------------------------------------

    def _fetch_events_for_month(self):
        """Return {day_int: [event_records, ...]} for the publication month.

        Timezone-aware: month bounds are computed in LODGE local time and
        converted to UTC for the DB query. Bucketing uses each event's
        lodge-local day (via display_day). Without this, evening events
        on the last day of the month leak into the next month's UTC date
        and get either excluded or bucketed under the wrong day.
        """
        self.ensure_one()
        first, last = self._month_bounds()

        # Lodge-local window: midnight on the 1st through midnight of the
        # first-of-next-month. Convert to UTC-naive (Odoo Datetime storage
        # is always UTC).
        lodge_tz = pytz.timezone(
            self.env["calendar.event"]._get_lodge_tz()
        )
        local_start = lodge_tz.localize(datetime.combine(first, time.min))
        local_end = lodge_tz.localize(
            datetime.combine(last + timedelta(days=1), time.min)
        )
        utc_start = local_start.astimezone(pytz.utc).replace(tzinfo=None)
        utc_end = local_end.astimezone(pytz.utc).replace(tzinfo=None)

        domain = [
            ("start", ">=", utc_start),
            ("start", "<", utc_end),
        ]
        if self.calendar_id:
            domain.append(("user_id", "=", self.calendar_id.id))
        # Sort by (start asc, name asc) so each day's events render in
        # chronological order first, then alphabetical for events sharing
        # the same start time.
        events = self.env["calendar.event"].search(
            domain, order="start asc, name asc",
        ) | self.event_filter_ids
        days_in_month = pycal.monthrange(int(self.year), int(self.month))[1]
        buckets = {d: [] for d in range(1, days_in_month + 1)}
        # Belt-and-suspenders sort so pinned event_filter_ids merge in
        # cleanly with the query results.
        for ev in events.sorted(key=lambda e: (e.start or False, (e.name or "").lower())):
            if not ev.start:
                continue
            # Lodge-local day — NOT ev.start.day (which is UTC day and
            # would mis-place any 5pm+ Pacific event onto the next date).
            day = ev.display_day()
            if day in buckets:
                buckets[day].append(ev)
        return buckets

    def _month_bounds(self):
        self.ensure_one()
        m = int(self.month)
        y = int(self.year)
        first = date(y, m, 1)
        last_day = pycal.monthrange(y, m)[1]
        last = date(y, m, last_day)
        return first, last

    def _get_grid_data(self):
        """Build a 6-week × 7-day calendar grid for the QWeb template.

        Returns a list of 6 weeks, each a list of 7 cells. Each cell is a
        dict with:
          * day:      integer day number, or None for blank padding cells
          * blank:    True if this cell is outside the current month
          * top:      the highest-priority banner event for the day, or None
          * lines:    remaining standard + secondary banner events, as a
                      list of calendar.event records

        Week starts on Sunday to match the template header.
        """
        self.ensure_one()
        m = int(self.month)
        y = int(self.year)
        first_day = date(y, m, 1)
        days_in_month = pycal.monthrange(y, m)[1]
        # weekday(): Monday=0..Sunday=6 ; we want Sunday=0..Saturday=6
        leading_blanks = (first_day.weekday() + 1) % 7

        buckets = self._fetch_events_for_month()
        cells = []

        # Leading blanks before day 1
        for _ in range(leading_blanks):
            cells.append({"day": None, "blank": True, "events": []})

        # Real days — every event renders in its own chronological slot,
        # regardless of banner style. The banner styling (color, icon,
        # box) is applied inline where each event actually appears in the
        # day's timeline. No more "banner owns the cell" concept.
        for day in range(1, days_in_month + 1):
            events = sorted(
                buckets.get(day, []),
                key=lambda e: (e.start or False, (e.name or "").lower()),
            )
            cells.append({
                "day": day,
                "blank": False,
                "events": events,
            })

        # Pad to 42 cells (6 full weeks)
        while len(cells) < 42:
            cells.append({"day": None, "blank": True, "events": []})

        # Slice into weeks
        return [cells[i:i + 7] for i in range(0, 42, 7)]

    def month_label(self):
        """Convenience for the QWeb template — full month name."""
        self.ensure_one()
        return pycal.month_name[int(self.month)] if self.month else ""

    # -- Header decorations ----------------------------------------------

    # Seasonal emoji strip per month, shown between the month and year in
    # the calendar header. Five-ish emojis each — kept short so they fit
    # on landscape Letter without wrapping.
    _MONTH_EMOJIS = {
        1:  ["❄️", "⛄", "✨"],
        2:  ["❤️", "\U0001f339", "\U0001f49d"],
        3:  ["☘️", "\U0001f340", "\U0001f337"],
        4:  ["\U0001f337", "\U0001f338", "\U0001f423"],
        5:  ["\U0001f338", "\U0001f337", "\U0001f490", "\U0001f33c"],
        6:  ["\U0001f1fa\U0001f1f8", "⭐", "\U0001f454", "\U0001f3a9", "\U0001f1fa\U0001f1f8"],
        7:  ["\U0001f1fa\U0001f1f8", "\U0001f386", "⭐", "\U0001f387"],
        8:  ["☀️", "\U0001f33d", "\U0001f349", "\U0001f33b"],
        9:  ["\U0001f342", "\U0001f34e", "\U0001f33e", "\U0001f341"],
        10: ["\U0001f383", "\U0001f47b", "\U0001f342", "\U0001f987"],
        11: ["\U0001f983", "\U0001f330", "\U0001f342", "\U0001f341"],
        12: ["\U0001f384", "⛄", "❄️", "✨", "\U0001f381"],
    }

    def month_emojis(self):
        """List of decorative emojis for the current month."""
        self.ensure_one()
        return self._MONTH_EMOJIS.get(int(self.month) if self.month else 0, [])

    # -- Holidays --------------------------------------------------------

    def holiday_for_day(self, day):
        """Return the US holiday label for the given day in this publication's
        month/year, or empty string if none. The label is what shows up on
        the calendar (e.g. 'Flag Day', 'Juneteenth', 'Happy Father's Day').
        """
        self.ensure_one()
        if not (self.month and self.year):
            return ""
        m = int(self.month)
        y = int(self.year)

        # Fixed-date holidays
        fixed = {
            (1, 1):   "New Year's Day",
            (2, 2):   "Groundhog Day",
            (2, 14):  "Valentine's Day",
            (3, 17):  "St. Patrick's Day",
            (4, 22):  "Earth Day",
            (6, 14):  "Flag Day",
            (6, 19):  "Juneteenth",
            (7, 4):   "Independence Day",
            (10, 31): "Halloween",
            (11, 11): "Veterans Day",
            (12, 25): "Christmas Day",
            (12, 31): "New Year's Eve",
        }
        if (m, day) in fixed:
            return fixed[(m, day)]

        # Floating holidays (nth weekday of month). weekday: Mon=0..Sun=6
        weekday = date(y, m, day).weekday()
        # Which occurrence is this (1st, 2nd, 3rd, 4th) of that weekday?
        nth = (day - 1) // 7 + 1
        # Last weekday of the month?
        last_day = pycal.monthrange(y, m)[1]
        is_last = day + 7 > last_day

        floating = {
            (1,  3, 0): "Martin Luther King Jr. Day",   # 3rd Monday of January
            (2,  3, 0): "Presidents' Day",              # 3rd Monday of February
            (5,  2, 6): "Mother's Day",                 # 2nd Sunday of May
            (6,  3, 6): "Happy Father's Day",           # 3rd Sunday of June
            (9,  1, 0): "Labor Day",                    # 1st Monday of September
            (10, 2, 0): "Columbus Day",                 # 2nd Monday of October
            (11, 4, 3): "Thanksgiving",                 # 4th Thursday of November
        }
        if (m, nth, weekday) in floating:
            return floating[(m, nth, weekday)]
        # Memorial Day = last Monday of May
        if m == 5 and weekday == 0 and is_last:
            return "Memorial Day"
        return ""
