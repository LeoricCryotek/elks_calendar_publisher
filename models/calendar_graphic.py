# -*- coding: utf-8 -*-
"""
Reusable graphic library.

Each stock banner style ships with a default graphic (Queen of Hearts =
red heart with crown, Loudmouth Bingo = open-mouth icon, etc.). The
library is also user-editable so the Lodge can add their own graphics
(charity logos, event posters) and use them on any event.
"""
from odoo import fields, models


class ElksCalendarGraphic(models.Model):
    _name = "elks.calendar.graphic"
    _description = "Reusable graphic shown on calendar events"
    _order = "is_stock desc, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, help="Kebab-case identifier.")
    image = fields.Binary(string="Image", attachment=True)
    image_filename = fields.Char()
    svg_inline = fields.Html(
        sanitize=False,
        help="Optional inline SVG. If set, takes priority over image and "
             "scales sharply at any size on the printed calendar. "
             "sanitize=False is required so the <svg> markup isn't stripped.",
    )
    suggested_banner_style = fields.Selection(
        # mirrors BANNER_STYLE in calendar_event.py
        selection=[
            ("none", "Standard"),
            ("queen_hearts", "Queen of Hearts"),
            ("loudmouth", "Loudmouth Bingo"),
            ("penny_bingo", "Bingo at the Lodge"),
            ("lodge_meeting", "Lodge Meeting"),
            ("live_music", "Live Music"),
            ("church", "Grace Bible Church"),
            ("special", "Special Event"),
            ("closed", "Lodge Closed"),
        ],
        default="none",
        help="When an event is tagged with this banner style, the form "
             "will auto-suggest this graphic.",
    )
    is_stock = fields.Boolean(default=False, readonly=True)

    # v19 declarative constraint syntax (replaces _sql_constraints list).
    _code_unique = models.Constraint(
        "unique(code)",
        "Graphic code must be unique.",
    )
