# -*- coding: utf-8 -*-
"""
Lodge-wide configuration for the calendar publisher.

The Lodge's local timezone is the single most important per-instance
setting — it controls how every event time is displayed on the printed
calendar PDF and the public website widget. Stored as a system parameter
so it survives module upgrades and can be edited from
Settings > General Settings > Elks Calendar.
"""
import pytz

from odoo import api, fields, models


# Used when no parameter has been set yet. Lewiston, ID is in
# America/Los_Angeles (Pacific Time).
DEFAULT_LODGE_TZ = "America/Los_Angeles"


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    elks_calendar_lodge_tz = fields.Selection(
        selection="_tz_get",
        string="Lodge Timezone",
        config_parameter="elks_calendar_publisher.lodge_tz",
        default=DEFAULT_LODGE_TZ,
        help="Timezone the lodge physically operates in. All event "
             "times on the printed monthly calendar and the public "
             "website widget will be shown in this timezone, "
             "regardless of where a visitor is located or what "
             "timezone a logged-in user has set. Defaults to "
             "America/Los_Angeles (Pacific Time).",
    )

    @api.model
    def _tz_get(self):
        """Selection options — every IANA timezone pytz knows about,
        sorted alphabetically so the lodge can find theirs quickly."""
        return [(tz, tz) for tz in sorted(pytz.all_timezones)]
