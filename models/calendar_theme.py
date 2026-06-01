# -*- coding: utf-8 -*-
"""
Stock theming for the calendar publisher.

A Theme is just a small bundle of CSS variables + decorative SVG asset +
font choices. The module ships one per month plus an 'Elks fraternal'
theme. Admins can add custom themes without touching code.
"""
from odoo import fields, models


class ElksCalendarTheme(models.Model):
    _name = "elks.calendar.theme"
    _description = "Stock / Custom Calendar Theme"
    _order = "applies_to_month, name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(required=True, help="Kebab-case identifier, e.g. 'spring_blossoms'.")
    primary_color = fields.Char(default="#c0392b", help="Hex. Drives --accent in CSS.")
    secondary_color = fields.Char(default="#1f6f4a", help="Hex. Drives --accent-2 in CSS.")
    header_font = fields.Char(default="Helvetica Neue")
    decor_svg = fields.Binary(help="Optional decorative strip displayed in the header.")
    decor_filename = fields.Char()
    applies_to_month = fields.Integer(
        help="1 = January, ..., 12 = December. Leave 0 for 'any month'.",
        default=0,
    )
    is_stock = fields.Boolean(
        default=False,
        readonly=True,
        help="True for themes shipped with the module. Cannot be deleted.",
    )

    # v19 declarative constraint syntax (replaces _sql_constraints list).
    _code_unique = models.Constraint(
        "unique(code)",
        "Theme code must be unique.",
    )

    # -- TODO ------------------------------------------------------------
    # def render_css_variables(self):
    #     """Return a string of :root { --accent: ...; } for injection."""
    #     ...
