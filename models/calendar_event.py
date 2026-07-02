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


class CalendarEventBanner(models.Model):
    _inherit = "calendar.event"

    # -- Banner -----------------------------------------------------------
    #
    # elks_banner_style is a dynamic Selection whose options come from
    # elks.calendar.banner.style records. Adding a Banner Style record
    # via Elks Calendar > Configuration > Banner Styles makes the new
    # option appear here on the next form load — no code changes.

    elks_banner_style = fields.Selection(
        selection="_get_banner_style_selection",
        default="none",
        string="Calendar Banner",
        help="If set, this event visually dominates its day cell on the "
             "published monthly calendar. Add or edit the available options "
             "at Elks Calendar > Configuration > Banner Styles.",
    )

    @api.model
    def _get_banner_style_selection(self):
        return self.env["elks.calendar.banner.style"].get_selection_options()
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

    # -- Lodge Calendar Event flag ---------------------------------------
    #
    # Convenience toggle on the event form. When ticked and saved, Odoo
    # auto-assigns the Source User Calendar (from any elks.calendar.
    # publication) as the event's organizer AND adds them as an attendee.
    # That way the event shows up on the Lodge Calendar publication
    # regardless of who created it.
    elks_is_lodge_event = fields.Boolean(
        string="Lodge Calendar Event",
        default=False,
        help="Tick to publish this event on the Lodge Calendar. Odoo will "
             "set the Source User Calendar user (from Elks Calendar → "
             "Publications) as the organizer of this event and add them "
             "as an attendee, so the event surfaces on the printed "
             "newsletter and the website widget.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("elks_is_lodge_event"):
                self._apply_lodge_calendar_assignment(vals)
        return super().create(vals_list)

    def write(self, vals):
        result = super().write(vals)
        # If the checkbox was JUST turned on, apply the assignment to
        # each affected record.
        if vals.get("elks_is_lodge_event"):
            lodge_user = self._get_lodge_calendar_user()
            if lodge_user:
                for rec in self:
                    update = {}
                    if not rec.user_id or rec.user_id != lodge_user:
                        update["user_id"] = lodge_user.id
                    partner_ids = rec.partner_ids.ids
                    if lodge_user.partner_id.id not in partner_ids:
                        update["partner_ids"] = [(4, lodge_user.partner_id.id)]
                    if update:
                        # Skip our create/write hook to avoid recursion.
                        super(CalendarEventBanner, rec).write(update)
        return result

    @api.model
    def _apply_lodge_calendar_assignment(self, vals):
        """Mutate a create-vals dict so the event is owned + attended by
        the Lodge Calendar user."""
        lodge_user = self._get_lodge_calendar_user()
        if not lodge_user:
            return
        vals.setdefault("user_id", lodge_user.id)
        existing = vals.get("partner_ids", [])
        # partner_ids may already be a list of command tuples; append.
        partner_id = lodge_user.partner_id.id
        already = False
        for cmd in existing:
            if isinstance(cmd, (list, tuple)) and len(cmd) >= 2:
                if cmd[1] == partner_id or (
                    cmd[0] == 6 and partner_id in (cmd[2] or [])
                ):
                    already = True
                    break
            elif cmd == partner_id:
                already = True
                break
        if not already:
            existing = list(existing) + [(4, partner_id)]
            vals["partner_ids"] = existing

    @api.model
    def _get_lodge_calendar_user(self):
        """Return the res.users configured as Source User Calendar on any
        publication. If more than one, the first-created wins."""
        Pub = self.env.get("elks.calendar.publication")
        if Pub is None:
            return None
        pub = Pub.sudo().search([
            ("calendar_id", "!=", False),
        ], order="id asc", limit=1)
        return pub.calendar_id if pub else None

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

    # -- Default Location from FRS Lodge Settings ------------------------
    #
    # When a user creates a new event on the "Source User Calendar" of a
    # publication (i.e. this user is set as calendar_id on any
    # elks.calendar.publication record), pre-fill the Location field with
    # the lodge's mailing address stored in the FRS module's
    # elks.lodge.settings singleton. The user can clear or change it for
    # off-site events; this just saves entry time for the common case.
    #
    # Personal calendar users whose account isn't a source calendar for
    # any publication do NOT get the autofill — their private events stay
    # blank as before.
    #
    # Only fires when both FRS and a lodge-tied publication exist. The
    # env.get() guard makes elks_calendar_publisher install/run cleanly
    # even without elksfrs.

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        if "location" in fields_list and not vals.get("location"):
            if self._is_lodge_source_user_calendar():
                addr = self._get_lodge_address_from_frs()
                if addr:
                    vals["location"] = addr
        return vals

    @api.model
    def _is_lodge_source_user_calendar(self):
        """True when the current user is set as the Source User Calendar
        on any elks.calendar.publication. That's the signal that events
        created by this user belong to the lodge's calendar and should
        default to the lodge's address.
        """
        target_user_id = self.env.context.get("default_user_id") or self.env.uid
        Pub = self.env.get("elks.calendar.publication")
        if Pub is None:
            return False
        return bool(Pub.sudo().search_count([
            ("calendar_id", "=", target_user_id),
        ]))

    @api.model
    def _get_lodge_address_from_frs(self):
        """Assemble the Lodge's mailing address from elksfrs's
        elks.lodge.settings singleton. Returns None if the model isn't
        registered (FRS not installed) or the singleton has no address.
        """
        Settings = self.env.get("elks.lodge.settings")
        if Settings is None:
            return None
        settings = Settings.sudo().search([], limit=1)
        if not settings:
            return None
        street = (settings.lodge_address or "").strip()
        city = (settings.lodge_city or "").strip()
        state = (settings.lodge_state or "").strip()
        zip_code = (settings.lodge_zip or "").strip()
        if not (street or city or state or zip_code):
            return None
        # "3444 10th St, Lewiston, ID 83501"
        tail_parts = []
        if city:
            tail_parts.append(city)
        state_zip = " ".join(p for p in (state, zip_code) if p)
        if state_zip:
            tail_parts.append(state_zip)
        tail = ", ".join(tail_parts)
        if street and tail:
            return f"{street}, {tail}"
        return street or tail

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

    # -- Banner style helpers ----------------------------------------
    def _banner_style_rec(self):
        """Return the elks.calendar.banner.style record for this event's
        code, or empty recordset if code is 'none' / not found. Used by
        QWeb/JSON/JS so colour and box/italic styling can travel with
        the event without duplicating rules in SCSS."""
        self.ensure_one()
        if not self.elks_banner_style or self.elks_banner_style == "none":
            return self.env["elks.calendar.banner.style"]
        return self.env["elks.calendar.banner.style"].sudo().search(
            [("code", "=", self.elks_banner_style)], limit=1,
        )

    def banner_color(self):
        rec = self._banner_style_rec()
        return rec.color if rec else ""

    def banner_is_box(self):
        rec = self._banner_style_rec()
        return bool(rec.is_highlighted_box) if rec else False

    def banner_is_italic(self):
        rec = self._banner_style_rec()
        return bool(rec.is_italic) if rec else False

    def banner_symbol(self):
        """Leading emoji/symbol from the banner style's name — used by
        the calendar template and website widget as the inline icon so
        the dropdown label and the calendar render display identically.
        Empty string when the banner style's name is a plain word."""
        rec = self._banner_style_rec()
        return rec.leading_symbol() if rec else ""

    def effective_graphic(self):
        """Return the bytes / SVG / Font Awesome icon / uploaded image
        that should be rendered for this event, honouring the use_graphic
        toggle and custom override.

        Priority order:
          1. Per-event custom binary upload (elks_graphic_custom)
          2. Library graphic's inline SVG
          3. Library graphic's Font Awesome icon + colour
          4. Library graphic's uploaded image (binary)
        """
        self.ensure_one()
        if not self.elks_use_graphic:
            return None
        if self.elks_graphic_custom:
            return {"binary": self.elks_graphic_custom,
                    "filename": self.elks_graphic_custom_filename}
        g = self.elks_graphic_id
        if g and g.svg_inline:
            return {"svg": g.svg_inline}
        if g and g.fa_icon:
            return {
                "fa_class": g.fa_icon_class(),
                "fa_color": g.fa_color or "#c0392b",
            }
        if g and g.image:
            return {"binary": g.image,
                    "filename": g.image_filename}
        return None
