# -*- coding: utf-8 -*-
"""
Reusable graphic library.

Each stock banner style ships with a default graphic (Queen of Hearts =
red heart with crown, Loudmouth Bingo = open-mouth icon, etc.). The
library is also user-editable so the Lodge can add their own graphics
(charity logos, event posters) and use them on any event.
"""
from odoo import api, fields, models


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
    fa_icon = fields.Char(
        string="Font Awesome Icon",
        help="Pick a Font Awesome icon by name — e.g. 'music', 'star', "
             "'microphone', 'gift', 'flag', 'heart'. Odoo ships with the "
             "full Font Awesome 4.7 icon set built in. See the full list "
             "at https://fontawesome.com/v4/icons/ (drop the 'fa-' prefix "
             "when typing here; both 'music' and 'fa-music' work).",
    )
    fa_color = fields.Char(
        string="Icon Color",
        default="#c0392b",
        help="Hex color for the Font Awesome icon (e.g. #c0392b for red, "
             "#1f6f4a for green, #6f1d77 for Elks purple).",
    )
    suggested_banner_style = fields.Selection(
        selection="_get_banner_style_selection",
        default="none",
        help="When an event is tagged with this banner style, the form "
             "will auto-suggest this graphic. Options come from Elks "
             "Calendar > Configuration > Banner Styles — add a new "
             "banner style there and it appears in this dropdown "
             "instantly.",
    )

    @api.model
    def _get_banner_style_selection(self):
        return self.env["elks.calendar.banner.style"].get_selection_options()
    is_stock = fields.Boolean(
        string="Built-in",
        default=False, readonly=True,
        help="True for graphics that ship with the module as defaults. "
             "Ticked automatically on install; leave unticked on any "
             "graphic you create yourself. Built-in graphics are protected "
             "from being overwritten on module upgrade.",
    )

    # v19 declarative constraint syntax (replaces _sql_constraints list).
    _code_unique = models.Constraint(
        "unique(code)",
        "Graphic code must be unique.",
    )

    def fa_icon_class(self):
        """Full Font Awesome CSS class for this graphic, e.g. 'fa fa-music'.
        Handles both 'music' and 'fa-music' as user input."""
        self.ensure_one()
        if not self.fa_icon:
            return ""
        name = self.fa_icon.strip()
        if name.startswith("fa-"):
            name = name[3:]
        return f"fa fa-{name}"

    # Live preview shown on the graphic form so editors see their icon
    # + colour update as they type / pick.
    preview_html = fields.Html(
        compute="_compute_preview_html",
        sanitize=False,
        string="Preview",
    )

    @api.depends("fa_icon", "fa_color", "svg_inline", "image")
    def _compute_preview_html(self):
        for rec in self:
            if rec.svg_inline:
                rec.preview_html = (
                    f'<div style="text-align:center;padding:12px;background:#f7f4ee;border-radius:6px;">'
                    f'<div style="width:72px;height:72px;margin:0 auto;">{rec.svg_inline}</div>'
                    f'<div style="font-size:11px;color:#888;margin-top:6px;">Inline SVG</div>'
                    f'</div>'
                )
            elif rec.fa_icon:
                color = rec.fa_color or "#c0392b"
                rec.preview_html = (
                    f'<div style="text-align:center;padding:12px;background:#f7f4ee;border-radius:6px;">'
                    f'<i class="{rec.fa_icon_class()}" style="font-size:48px;color:{color};"></i>'
                    f'<div style="font-size:11px;color:#888;margin-top:6px;">'
                    f'Font Awesome — <code>{rec.fa_icon_class()}</code></div>'
                    f'</div>'
                )
            elif rec.image:
                rec.preview_html = (
                    '<div style="text-align:center;padding:12px;background:#f7f4ee;border-radius:6px;">'
                    '<em style="color:#888;">Uploaded image (see field below)</em>'
                    '</div>'
                )
            else:
                rec.preview_html = (
                    '<div style="text-align:center;padding:12px;background:#f7f4ee;border-radius:6px;color:#888;">'
                    '<em>No graphic set yet</em>'
                    '</div>'
                )
