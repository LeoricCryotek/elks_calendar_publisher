# -*- coding: utf-8 -*-
"""
Data-driven Banner Style catalog.

Before this model existed, banner styles were a hardcoded Python
Selection list. Adding a new one meant editing three files and
redeploying. Now each style is a database record any admin can add or
edit from the Elks Calendar > Configuration > Banner Styles menu.

The Selection fields on calendar.event and elks.calendar.graphic use a
callable that fetches records at runtime, so a new banner style is
available in the dropdown instantly — no server restart.
"""
from odoo import api, fields, models


class ElksCalendarBannerStyle(models.Model):
    _name = "elks.calendar.banner.style"
    _description = "Calendar Banner Style"
    _order = "sequence, name"

    name = fields.Char(
        required=True, translate=True,
        help="Human-readable label shown in the Calendar Banner dropdown "
             "on the event form.",
    )
    code = fields.Char(
        required=True,
        help="Kebab-case identifier used as the internal value and CSS "
             "class suffix. Should match [a-z0-9_]+ pattern. Once set, "
             "avoid changing this on stock records because events already "
             "reference it.",
    )
    description = fields.Char(
        translate=True,
        help="Short appearance summary shown next to the name, e.g. "
             "'red, centered' or 'highlighted box'.",
    )
    color = fields.Char(
        default="#c0392b",
        help="Hex colour applied to the banner headline text on both the "
             "printed calendar and the website widget.",
    )
    is_highlighted_box = fields.Boolean(
        string="Highlighted Box",
        help="Wrap the banner in a dashed amber box (like Special Event).",
    )
    is_italic = fields.Boolean(
        string="Italic Text",
        help="Render the banner headline in italics (like Lodge Closed).",
    )
    is_stock = fields.Boolean(
        string="Built-in",
        default=False, readonly=True,
        help="True for banner styles that ship with the module as "
             "defaults. Built-in styles are protected from being "
             "overwritten on module upgrade. Styles you create yourself "
             "should stay unticked.",
    )
    sequence = fields.Integer(
        default=10,
        help="Order in the dropdown. Lower numbers appear first. Standard "
             "event is 0 so it lands at the top.",
    )

    _code_unique = models.Constraint(
        "unique(code)",
        "Banner style code must be unique.",
    )

    def is_banner(self):
        """Convenience — is this a real banner (not 'Standard event')?"""
        self.ensure_one()
        return bool(self.code) and self.code != "none"

    @api.model
    def get_selection_options(self):
        """Return (code, name) tuples for use as a Selection field's
        selection method. Called from calendar.event.elks_banner_style and
        elks.calendar.graphic.suggested_banner_style so their dropdowns
        reflect the current banner style catalog live.

        Safe fallback: if no records exist yet (fresh install before
        stock data loaded), returns just the Standard option so the
        Selection never renders empty.
        """
        recs = self.sudo().search([], order="sequence, name")
        if not recs:
            return [("none", "Standard event")]
        return [(r.code, r.name) for r in recs]
