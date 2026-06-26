# -*- coding: utf-8 -*-
"""
Extension of the built-in calendar.event model.

Adds two things:
  1. Banner metadata so the calendar renderer can blow up certain events
     (Queen of Hearts, Loudmouth Bingo, etc.) so they visually dominate
     their cell.
  2. A per-event graphic picker so editors can include / suppress a
     graphic (or pick a custom one) directly from the event form.

Banner styles map to CSS classes in the calendar template. Adding a new
style is one row in BANNER_STYLE + one CSS rule + (optionally) one
stock graphic record.
"""
import pytz

from odoo import api, fields, models

# Fallback used only if the system parameter hasn't been set yet (fresh
# install before anyone visits Settings). After a Lodge picks their
# timezone from the Settings page it lives in ir.config_parameter.
_DEFAULT_LODGE_TZ = "America/Los_Angeles"


BANNER_STYLE = [
    ("none",          "Standard event"),
    ("queen_hearts",  "♥ Queen of Hearts (red, centered)"),
    ("loudmouth",     "👄 Loudmouth Bingo (bold, centered)"),
    ("penny_bingo",   "🎱 Bingo at the Lodge (bold, centered)"),
    ("lodge_meeting", "Lodge Meeting (red banner)"),
    ("live_music",    "🎵 Live Music (accent banner)"),
    ("karaoke",       "🎤 Karaoke (accent banner)"),
    ("church",        "⛪ Grace Bible Church (green, centered)"),
    ("special",       "★ Special Event (highlighted box)"),
    ("closed",        "Lodge Closed (gray, centered)"),
]


class CalendarEventBanner(models.Model):
    _inherit = "calendar.event"

    # -- Banner -----------------------------------------------------------

    elks_banner_style = fields.Selection(
        BANNER_STYLE,
        default="none",
        string="Calendar Banner",
        help="If set, this event visually dominates its day cell on the "
             "published monthly calendar.",
    )
    elks_banner_label = fields.Char(
        string="Banner Label",
        help="Optional short headline shown on the calendar (e.g. "
             "'Loudmouth Bingo'). Defaults to the event name.",
    )
    elks_banner_sub = fields.Char(
        string="Banner Sub-line",
        help="Optional smaller line under the headline (e.g. "
             "'Cards 5:30 · Bingo 6:15').",
    )
    elks_banner_priority = fields.Integer(
        string="Banner Priority",
        default=10,
        help="Higher-priority banner wins the cell if two collide.",
    )

    # -- Graphic ----------------------------------------------------------

    elks_use_graphic = fields.Boolean(
        string="Include Graphic on Calendar",
        default=False,
        help="Tick to include a graphic (Queen of Hearts heart, Loudmouth "
             "Bingo mouth, etc.) on this event's calendar cell. Defaults "
             "off so editors must opt in.",
    )
    elks_graphic_id = fields.Many2one(
        "elks.calendar.graphic",
        string="Graphic",
        help="Pick from the library, or leave blank to use the default "
             "for the chosen banner style.",
    )
    elks_graphic_custom = fields.Binary(
        string="Custom Graphic",
        help="One-off image for this event only. Overrides Graphic if set.",
    )
    elks_graphic_custom_filename = fields.Char()

    # -- Onchange ---------------------------------------------------------

    @api.onchange("elks_banner_style")
    def _onchange_banner_style_suggest_graphic(self):
        """When the editor picks a banner style, pre-fill the graphic
        with the matching stock graphic. They can still override or untick
        Include Graphic to suppress it."""
        for rec in self:
            if rec.elks_banner_style and rec.elks_banner_style != "none":
                match = self.env["elks.calendar.graphic"].search(
                    [("suggested_banner_style", "=", rec.elks_banner_style)],
                    limit=1,
                )
                if match and not rec.elks_graphic_id:
                    rec.elks_graphic_id = match
                    rec.elks_use_graphic = True

    # -- Helpers used by the QWeb template / website widget ---------------

    def display_banner_label(self):
        self.ensure_one()
        return self.elks_banner_label or self.name or ""

    @api.model
    def _get_lodge_tz(self):
        """Read the Lodge's configured timezone from the system parameter.
        The Lodge sets this in Settings > General Settings > Elks Calendar.
        Falls back to the install-time default when the parameter is
        unset (fresh install) or unrecognized."""
        tz_name = (
            self.env["ir.config_parameter"].sudo().get_param(
                "elks_calendar_publisher.lodge_tz",
                _DEFAULT_LODGE_TZ,
            )
        )
        if tz_name not in pytz.all_timezones_set:
            tz_name = _DEFAULT_LODGE_TZ
        return tz_name

    def _to_lodge_local(self):
        """Convert the event's UTC start to the lodge's local timezone.
        Stored datetimes in Odoo are always UTC; this is the single place
        we hop into local time so display_time/display_day always agree.
        """
        self.ensure_one()
        if not self.start:
            return None
        utc_dt = self.start.replace(tzinfo=pytz.utc)
        return utc_dt.astimezone(pytz.timezone(self._get_lodge_tz()))

    def display_time(self):
        """Return the event's start time formatted as e.g. '6:15pm', '7pm',
        '8:15am'. Returns an empty string for all-day events or events
        without a start time. Always in the LODGE's local timezone — no
        per-user-timezone variation.
        """
        self.ensure_one()
        if not self.start or self.allday:
            return ""
        local = self._to_lodge_local()
        hour = local.hour
        minute = local.minute
        am_pm = "am" if hour < 12 else "pm"
        hour12 = hour % 12 or 12
        if minute == 0:
            return f"{hour12}{am_pm}"
        return f"{hour12}:{minute:02d}{am_pm}"

    def display_day(self):
        """Day-of-month for this event's start, in lodge local time.
        Sent to the widget so the widget doesn't have to do any timezone
        math on a naive ISO string (which JS would otherwise parse as the
        visitor's browser-local time and get wrong).
        """
        self.ensure_one()
        local = self._to_lodge_local()
        return local.day if local else None

    def is_banner(self):
        self.ensure_one()
        return self.elks_banner_style and self.elks_banner_style != "none"

    def effective_graphic(self):
        """Return the bytes / SVG / record that should be rendered for
        this event, honoring the use_graphic toggle and custom override."""
        self.ensure_one()
        if not self.elks_use_graphic:
            return None
        if self.elks_graphic_custom:
            return {"binary": self.elks_graphic_custom,
                    "filename": self.elks_graphic_custom_filename}
        if self.elks_graphic_id and self.elks_graphic_id.svg_inline:
            return {"svg": self.elks_graphic_id.svg_inline}
        if self.elks_graphic_id and self.elks_graphic_id.image:
            return {"binary": self.elks_graphic_id.image,
                    "filename": self.elks_graphic_id.image_filename}
        return None
