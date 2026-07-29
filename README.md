# Elks Calendar Publisher

> Odoo 19 addon for Lewiston Elks Lodge #896.
> Turns the lodge's Odoo Calendar into a printable monthly newsletter
> calendar plus a live web calendar visitors can page through — one
> source of truth, three ways to see it.

**Current version:** 19.0.0.12

---

## Table of contents

- [Who this guide is for](#who-this-guide-is-for)
- [The big picture](#the-big-picture)
- [Day-to-day: adding an event to the lodge calendar](#day-to-day-adding-an-event-to-the-lodge-calendar)
- [Publishing the monthly newsletter calendar](#publishing-the-monthly-newsletter-calendar)
- [The public website widget](#the-public-website-widget)
- [Banner styles — colors and icons for headline events](#banner-styles--colors-and-icons-for-headline-events)
- [Graphics library — advanced icons for events](#graphics-library--advanced-icons-for-events)
- [Themes — seasonal color palettes for each month](#themes--seasonal-color-palettes-for-each-month)
- [Configuration one-time-only steps](#configuration-one-time-only-steps)
- [Troubleshooting](#troubleshooting)
- [Deploying updates (for IT)](#deploying-updates-for-it)

---

## Who this guide is for

Two audiences:

- **Reception staff / calendar editors** — sections 1 through 7. You'll create events, publish the month, and update the website widget.
- **Lodge IT / whoever installs upgrades** — sections 8 through 10.

If you're just here to add events, skim [The big picture](#the-big-picture) then jump to [Day-to-day: adding an event to the lodge calendar](#day-to-day-adding-an-event-to-the-lodge-calendar).

---

## The big picture

Every event is entered **once** in Odoo's built-in Calendar app. From there, this module produces:

1. A **printable monthly PDF calendar** — the one that goes in the newsletter.
2. A **live web widget** — dragged onto any lodge web page, updates instantly when events change, has Previous / Today / Next buttons so visitors can page through months.
3. A **dedicated static page** at `/elks/calendar` — auto-redirects to the most recently published month.

You never re-type an event three times. Change a time once in the Odoo Calendar and all three surfaces reflect it.

---

## Day-to-day: adding an event to the lodge calendar

1. Click the **Calendar** app in Odoo's main menu.
2. Click **New** (top-left) or click on the date/time slot you want.
3. Fill in:
   - **Meeting Subject** — the event name (e.g. "Karaoke with Jake", "Loudmouth Bingo").
   - **Start** and **End** date/time — make sure the time is in Pacific.
   - **Location** — auto-fills to the lodge address if you tick "Lodge Calendar Event" below.
4. Scroll down. You'll see three sections added by this module:

### Elks Charity Activity (optional — only if it's a charity event)
Handled by a separate module. Skip unless the event is a charitable activity.

### Lodge Calendar Banner (this is what you'll use most)
- **Lodge Calendar Event** ← turn this ON. It auto-adds the Lodge as an attendee so the event shows up on the newsletter and the widget.
- **Calendar Banner** — pick a banner style if this is a "headline" event (Queen of Hearts, Karaoke, Live Music, Lodge Meeting, etc.). Leave as *Standard event* for regular things like "Fit & Fall Proof" or "Lounge Menu Available."
- **Banner Label** — usually blank. Use if you want to override the event name on the calendar (e.g. keep the event named "Cards + Bingo" internally but show "Loudmouth Bingo" on the calendar).
- **Banner Sub-line** — optional smaller line under the headline (e.g. "Cards 5:30 · Bingo 6:15").
- **Banner Priority** — usually leave at 10. Higher numbers win visual priority if two banner events land on the same day.

### Graphic (optional — automatic if you picked a banner style)
When you pick a banner style, the matching icon auto-fills. You can:
- Leave it alone (recommended).
- Untick **Include Graphic on Calendar** if you don't want the icon on that specific event.
- Swap to a different library graphic.
- Upload a one-off custom image just for this event.

5. Click **Save**. Done — the event is now on the lodge calendar.

### Recurring events (weekly Fit & Fall Proof, monthly Lodge Meeting, etc.)

- Click **More Options** on the event creation dialog, then in the **Options** tab tick **Recurrent**.
- Configure "every week on Tuesday" or whatever the pattern is.
- Set the banner style and Lodge Calendar Event **once** on the parent event — every future occurrence inherits it.

---

## Publishing the monthly newsletter calendar

You do this once per month. Aim to publish 5–7 days before the newsletter goes out.

1. Go to **Elks Calendar → Publications**.
2. Click **New**.
3. Fill in:
   - **Month** — pick from the dropdown.
   - **Year** — pick from the dropdown (defaults to this year; you can go 10 years forward for advance planning).
   - **Theme** — pick a seasonal theme (Summer Sun for June, Patriotic Flag for July, etc.). See [Themes](#themes--seasonal-color-palettes-for-each-month).
   - **Source User Calendar** — usually **leave blank**. Filling this restricts the calendar to only events organized by one specific user; blank shows all events from all users.
   - **Header Title / Subtitle** — pre-filled with "Lewiston Elks Lodge #896" and "From our Home on the River." Change if needed.
   - **Footer Text** — pre-filled with the standard "Calendar items, dates and times are subject to change…" disclaimer.
4. Click Save. The **Live Preview** tab shows exactly what the printed calendar will look like.
5. When the preview looks right:
   - Click **Publish** to make it live on the website's `/elks/calendar` page. This does not generate a PDF.
   - Click **Generate PDF** to download the printable version. This does not publish.
   - Both buttons can be clicked in either order.
6. Click **Open PDF** anytime to re-download the last-generated PDF.

If the preview looks wrong:
- **Wrong events** — check the events in the Odoo Calendar have the right date/time, are Lodge Calendar Events, and are in the right month.
- **Missing events** — see the [Troubleshooting](#troubleshooting) section.
- **Wrong colors** — pick a different theme.

---

## The public website widget

The **Elks Monthly Calendar** is a drag-and-drop block you can put on any website page (Events page, Home page, dedicated Calendar page — anywhere).

### Adding it to a page

1. Go to the page in a browser.
2. Click **Edit** in the top-right toolbar to enter Website Builder.
3. In the side panel look for the **Elks Lodge** category.
4. Drag the **Elks Monthly Calendar** tile onto the page.
5. Click **Save** in the top-right.
6. View the page — visitors will see the live calendar.

### What visitors can do

- See the current month by default.
- Click **← Previous** or **Next →** to page through other months.
- Click **Today** to jump back to the current month.
- Every change updates instantly — no page reload.
- Times shown are in Pacific (the Lodge's time zone) for every visitor regardless of where they're browsing from.

### Configuration (optional)

By default the widget shows the current month with all event icons. To hardcode a specific month or hide icons, an editor with technical access can set data attributes on the snippet. Reception staff usually don't need to touch this.

---

## Banner styles — colors and icons for headline events

**Elks Calendar → Banner Styles** shows every available banner style. Built-in styles include:

| Style | Emoji | Color | Use for |
|---|---|---|---|
| Standard event | none | black | Regular events (Lounge Menu Available, Fit & Fall Proof) |
| Queen of Hearts | ♥ | red | Weekly Queen of Hearts drawing |
| Loudmouth Bingo | 👄 | black | Wednesday bingo |
| Bingo at the Lodge | 🎱 | black | Regular Sunday bingo |
| Lodge Meeting | (none) | red | Monthly lodge business meetings |
| Live Music | 🎵 | purple | Friday night bands |
| Karaoke | 🎤 | purple | Thursday karaoke |
| Antler Meeting | 🦌 | purple | Antler committee |
| Music Bingo | 🎵 | amber (dashed box) | Music bingo special |
| Grace Bible Church | ⛪ | green | Recurring church rental |
| Special Event | ★ | amber (dashed box) | Weddings, celebrations of life, one-offs |
| Lodge Closed | (none) | gray italic | Days the lodge is closed |

### Adding your own banner style

The lodge picks up a new recurring event and wants a distinct look? No code needed.

1. **Elks Calendar → Banner Styles → New**.
2. **Name** — the label with a leading emoji if you want an icon (e.g. `🎳 Bowling Night`). The emoji shows in both the dropdown AND the calendar.
3. **Code** — a short internal identifier, lowercase and underscores only (e.g. `bowling_night`).
4. **Description** — optional one-liner like "green, centered."
5. **Color** — click the swatch and pick.
6. **Highlighted Box** — tick if you want the dashed amber-box treatment (like Special Event).
7. **Italic Text** — tick if you want the headline italicized (like Lodge Closed).
8. Save. Immediately available in the dropdown on new events.

Built-in styles are marked **Built-in** and shouldn't be edited or deleted (they're re-loaded on module upgrade).

---

## Graphics library — advanced icons for events

For most cases, the leading emoji in a banner style's name is enough. The **Graphic Library** is for cases where you want a custom icon (a charity logo, a special event poster, a hand-drawn SVG).

**Elks Calendar → Graphic Library**. Each graphic supports three flavors:

- **Font Awesome Icon** — pick any Font Awesome 4 icon by name (music, star, microphone, gift, gavel, glass, etc.) and set a color.
- **Inline SVG** — paste a custom SVG. Good for lodge-specific artwork.
- **Uploaded Image** — a PNG/JPG fallback.

The calendar rendering priority is: banner style's emoji → graphic's SVG → graphic's FA icon → graphic's uploaded image. So if you want a custom SVG for a specific event, upload it in the Graphic Library, then on the event: pick the banner style AND set the graphic manually.

---

## Themes — seasonal color palettes for each month

**Elks Calendar → Themes** lists the 13 built-in themes plus any custom ones. Each theme is just:

- A primary color (used for the month name, day-row background, and accents)
- A secondary color (used for the year, sub-accents)

Built-in themes:

| Month | Theme | Primary | Secondary |
|---|---|---|---|
| January | Winter Snowflake | navy | ice blue |
| February | Valentine's Hearts | red | pink |
| March | Shamrock Spring | green | light green |
| April | Easter Florals | pink | yellow |
| May | Spring Blossoms | magenta | green |
| June | Summer Sun | orange | pale yellow |
| July | Patriotic Flag | red | navy |
| August | Late Summer Picnic | amber | green |
| September | Harvest Leaves | brown | orange |
| October | Autumn Pumpkin | orange | purple |
| November | Thanksgiving Acorn | brown | tan |
| December | Holiday Evergreen | dark green | red |
| Any | Elks Fraternal | purple | gold |

Add your own themes anytime via **Themes → New**.

---

## Configuration one-time-only steps

Set once per install, then forget:

### Lodge Timezone
- **Settings → General Settings** → scroll to **Elks Calendar** section.
- **Lodge Timezone** should read `America/Los_Angeles` for Lewiston.
- Change this if the module is ever installed at a lodge in a different time zone.

### Each user's Timezone preference
- Each internal user's profile → Preferences → Timezone → `America/Los_Angeles`.
- Ensures when they type "6:00 PM" in an event, Odoo stores it as 6 PM Pacific (not 6 PM UTC).

### Server clock
- Linux server should be on `America/Los_Angeles` for correct cron and log timestamps. IT-level task.

---

## Troubleshooting

**An event isn't showing on the calendar preview.**
- Is the event marked as a Lodge Calendar Event? Open it, tick **Lodge Calendar Event** at the top of the Lodge Calendar Banner section, save.
- Is the event date/time correct? Odoo stores UTC internally — if your user timezone is wrong, times land on the wrong day.
- Is the publication's *Source User Calendar* filled in? Clear it if you want all lodge events regardless of organizer.

**The calendar preview says "Preview unavailable."**
- Almost always means you haven't picked a theme yet. Pick one and save.

**PDF looks broken (text stacked vertically, boxes for emojis).**
- The server needs an emoji font installed. Ask IT to run `sudo apt install fonts-noto-color-emoji` and restart Odoo.

**Website widget shows the wrong month or old data.**
- The widget respects a no-cache header, but the browser might have cached the JS bundle from an earlier module version. Hard refresh: Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows.

**Times on the widget are off by 7 hours.**
- The user who created those events had their Odoo TZ set to UTC. Have them set it to `America/Los_Angeles` in their profile Preferences, then edit each affected event to re-save the correct time.

**Something broke after upgrade.**
- Check that Odoo was restarted after `git pull`. Model code only reloads on restart.
- Then upgrade the module: Apps → Elks Calendar Publisher → Upgrade. Views and data only reload on Upgrade.

---

## Deploying updates (for IT)

On the production server:

```bash
cd /var/odoo/lewistonelks896.com/extra-addons/elks_calendar_publisher
git pull origin main
cat __manifest__.py | grep version
sudo systemctl restart odona-lewistonelks896.com
```

Then in the browser: **Apps → Elks Calendar Publisher → Upgrade**.

The version in the manifest bumps every release. If `git pull` didn't change the version number in the file, no upgrade is needed — just the restart.

---

## Where to open a ticket

- Wrong behavior in the module → open an issue in the repo.
- Question about how to use it → email lodge@lewistonelks896.com or ask at the office.
- Feature request → same channels; the module is actively maintained.

---

*Elks Calendar Publisher — built for Lewiston Elks Lodge #896.*
*Odoo 19 · LGPL-3 · Maintained by Danny Santiago.*
