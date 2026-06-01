# Code Review — Elks Calendar Publisher v17.0.0.2.0

Reviewed against Odoo 17 conventions and the question "is this a clean
addon to the `calendar` module?". Findings split into ✅ good,
⚠️ watch, and 🛠️ must-fix-before-production.

## ✅ Good — properly built as an addon to `calendar`

| Item | Notes |
|---|---|
| `__manifest__.py` declares `calendar` and `website` in `depends` | Standard Odoo addon dependency wiring. |
| `calendar.event` is **extended via `_inherit`**, not replaced | Lodge keeps using the native calendar UI; we just add fields. |
| New fields are namespaced `elks_*` | No collisions with future Odoo upgrades. |
| Original `calendar.view_calendar_event_form` is inherited via XPath | The Banner / Graphic sections sit inside the same form; no duplicate form. |
| `ir.model.access.csv` grants public read on `elks.calendar.publication` and `elks.calendar.graphic` only | Website visitors can see calendars and graphics; can't see private records. |
| Stock data records carry `noupdate="1"` and `is_stock=True` | Customer changes won't be overwritten on module upgrade. |
| Inline SVG graphics chosen over PNG | Sharp at print + zoom, smaller footprint, no missing-file 404s. |
| Backend assets and frontend assets are split | Avoids loading the website widget JS in the backend. |

## ⚠️ Watch

1. **`elks.calendar.publication.calendar_id`** currently points at `res.users`
   as a stand-in for "which calendar to read." Odoo Calendar doesn't have a
   first-class `calendar.calendar` concept — events are per-user with shared
   attendees. Decide whether to drive it by user, by event tag, or by a new
   "Lodge Calendar" tag model. Document this in the Publication form help text.

2. **Recurring events**: `calendar.event` recurrences (every Tuesday) inherit
   the banner fields automatically (they're stored on the parent). Verify
   on a real instance with `recurrency=True`, especially around how
   `_fetch_events_for_month` handles `calendar.event.recurrence`.

3. **Custom graphic storage**: `elks_graphic_custom` is a `Binary` on the
   event itself. For a lot of one-off uploads this bloats event records.
   Consider `attachment=True` on the field, or store the graphic in the
   library on save. Listed as a future enhancement, not blocking.

4. **`website.snippets` xpath**: I used `inside snippets[@id='snippet_groups']`
   which is the v17 structure. The selector path is fragile across major
   versions. Add a regression test before upgrading to 18.

5. **Public JSON feed** (`/elks/calendar/json/...`) has no rate limiting.
   For a low-traffic lodge site that's fine; if exposed broadly, wrap it
   with `request.env['ir.http']._authenticate('public')` plus a cooldown.

## 🛠️ Must-fix before production

1. **`action_render_pdf` is a stub.** It needs to actually invoke
   `report._render_qweb_pdf(self.ids)`, persist the bytes as an
   `ir.attachment`, set `pdf_attachment_id`, and flip state to `published`.
   Roughly 15 lines.

2. **QWeb day loop is a comment.** `reports/calendar_template.xml`
   describes the algorithm but never iterates. Implement:
   - leading-blank cells before day 1
   - 6×7 grid
   - per-day fetch from `pub._fetch_events_for_month()`
   - banner selection by priority
   - inline-SVG injection for the banner graphic

3. **`_compute_preview_html` returns a placeholder.** Either render the
   full template at quarter scale or remove the field. Right now the form
   shows "Preview will appear here once events load." forever.

4. **Inherited form view test.** Add a Python test that loads the
   inherited form and confirms the Banner + Graphic sections appear.
   Catches the day someone changes the upstream view structure.

5. **Static assets** referenced in the manifest exist as files but the
   `static/description/banner.png` and `static/src/img/snippet_thumb.png`
   placeholders are not bundled — Odoo's app store will warn. Either
   create them or remove the references.

## Quick-review checklist (run before each release)

- [ ] `python -m odoo -d test --test-enable -i elks_calendar_publisher`
- [ ] `ruff check elks_calendar_publisher/`
- [ ] Module installs on a fresh DB
- [ ] Banner + Graphic sections render on the standard event form
- [ ] Create one event with each banner style → graphic auto-loads
- [ ] Generate a publication PDF → opens cleanly
- [ ] `/elks/calendar` returns the latest published calendar
- [ ] Drag the snippet onto a website page → renders current month
