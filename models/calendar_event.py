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
from odoo import api, fields, models


BANNER_STYLE = [
    ("none",          "Standard event"),
    ("queen_hearts",  "♥ Queen of Hearts (red, centered)"),
    ("loudmouth",     "👄 Loudmouth Bingo (bold, centered)"),
    ("penny_bingo",   "🎱 Bingo at the Lodge (bold, centered)"),
    ("lodge_meeting", "Lodge Meeting (red banner)"),
    ("live_music",    "🎵 Live Music (accent banner)"),
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
