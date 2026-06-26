# -*- coding: utf-8 -*-
{
    "name": "Elks Calendar Publisher",
    "summary": "Themed monthly calendar pages from Odoo Calendar events",
    "description": """
Elks Calendar Publisher
=======================

Turns the lodge's Odoo Calendar (calendar.event) into the single
source of truth for what's happening at the Lodge, and from that data
generates a printable monthly newsletter PDF and a live, embeddable
calendar widget for the public website.

Calendar editors can flag any event as a Banner (Queen of Hearts,
Loudmouth Bingo, etc.) and optionally attach a graphic from the
bundled graphic library, or upload a custom one.

Includes:
  * Banner + graphic fields inherited onto calendar.event
  * 13 stock month themes plus an Elks fraternal theme
  * Editable inline-SVG graphic library
  * QWeb PDF report (landscape letter)
  * Public website page + drag-and-drop Website Builder snippet
""",
    "author": "Danny Santiago",
    "website": "https://dannysantiago.info",
    "category": "Productivity/Calendar",
    "version": "19.0.0.5",
    "depends": [
        "base",
        "calendar",
        "web",
        "website",
    ],
    "data": [
        # security first
        "security/ir.model.access.csv",
        # views: theme_views defines action_elks_themes, which publication_views
        # references; publication_views defines the root menu menu_elks_calendar_root,
        # which graphic_views references — so theme → publication → graphic.
        "views/theme_views.xml",
        "views/publication_views.xml",
        "views/graphic_views.xml",
        "views/calendar_event_views.xml",
        "views/res_config_settings_views.xml",
        # reports must register the action before any view that binds to it
        "reports/publication_report.xml",
        "reports/calendar_template.xml",
        # stock data depends on theme/graphic models being installed
        "data/stock_themes.xml",
        "data/stock_graphics.xml",
        # website pieces last
        "views/website_templates.xml",
        "views/website_snippets.xml",
        "views/website_menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "elks_calendar_publisher/static/src/scss/calendar.scss",
        ],
        "web.assets_frontend": [
            "elks_calendar_publisher/static/src/scss/website_calendar.scss",
            "elks_calendar_publisher/static/src/js/website_calendar.js",
        ],
    },
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}
