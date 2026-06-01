# Elks Calendar Publisher

> Odoo 17 addon for Lewiston Elks Lodge #896.
> Turns the lodge's `calendar.event` data into themed monthly calendar pages
> (PDF + public website widget), with per-event graphic support
> (Queen of Hearts, Loudmouth Bingo, Bingo at the Lodge, Live Music, etc.).

**Status:** Wireframe / scaffold. Models, manifests, views, controllers,
website templates, snippet, JS widget and stock data are all in place.
The QWeb day-loop and PDF render method still have `TODO` markers — see
`CODE_REVIEW.md` for the punch list.

## Features

- Inherits the built-in **`calendar.event`** model (no separate event store).
- Adds a **Banner** flag + headline + sub-line + priority to any event.
  Banners visually own their day cell on the published calendar.
- Adds an **Include Graphic on Calendar** toggle and **Graphic** picker
  on the event form. When a banner style is chosen, the matching stock
  graphic auto-fills.
- Ships a **graphic library** (`elks.calendar.graphic`) with editable
  defaults for Queen of Hearts, Loudmouth Bingo, Bingo at the Lodge,
  Live Music, Lodge Meeting, Church, Special Event, and Lodge Closed.
  Custom one-off image upload per event is also supported.
- 13 **stock month themes** (snowflakes / hearts / shamrocks /
  florals / sun / flag / leaves / pumpkin / acorn / evergreen + Elks
  fraternal).
- **QWeb PDF report** (`ir.actions.report`) producing landscape letter.
- **Public website page** at `/elks/calendar` plus a JSON feed at
  `/elks/calendar/json/<year>/<month>` for the embeddable widget.
- **Website Builder snippet** ("Elks Monthly Calendar") so editors can
  drag the live calendar onto any page.

## Install

```bash
# In your Odoo addons folder
cd /opt/odoo/custom-addons
git clone https://github.com/lewistonelks/elks_calendar_publisher.git

# Restart Odoo and update apps list, then install "Elks Calendar Publisher"
```

Requires Odoo 17 with the `calendar` and `website` modules enabled.

## How an editor uses it

1. Open the standard Odoo Calendar app, create or edit an event
   (`calendar.event`).
2. Scroll to the new **Lodge Calendar Banner** section, pick a style
   (Queen of Hearts, Loudmouth Bingo, etc.).
3. The **Graphic** section flips on automatically and pre-loads the
   matching stock graphic. The editor can:
   - leave it as-is,
   - swap to a different library graphic,
   - upload a one-off custom image, or
   - untick **Include Graphic on Calendar** to suppress it entirely.
4. Go to **Elks Calendar → Publications**, create a new publication for
   the month, pick a theme, click **Generate PDF**. The PDF goes to the
   record's attachment and the website route serves it publicly.

## Website widget

After install, the **Elks Monthly Calendar** snippet appears in the
Website Builder side panel under the standard content blocks. Drag it
onto any page. Optional data attributes on the snippet root element:

| Attribute            | Default              | Meaning                          |
|----------------------|----------------------|----------------------------------|
| `data-year`          | current year         | Which year to render             |
| `data-month`         | current month        | 1–12                             |
| `data-show-graphics` | `1`                  | Set `0` to hide all event icons  |

The widget hits `/elks/calendar/json/<year>/<month>`, renders a 7-column
grid, and honors each event's `elks_banner_style` + graphic selection.

See `CODE_REVIEW.md` for review findings and what still needs to be
implemented before this is production-ready.
