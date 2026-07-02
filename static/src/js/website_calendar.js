/** @odoo-module **/
/*
 * Elks Calendar — public website widget.
 *
 * Renders a themed monthly grid into any element with class
 * `.elks-cal-mount`. Pulls event data + theme metadata from the
 * /elks/calendar/json/<year>/<month> feed and renders a calendar that
 * matches the printed PDF layout:
 *   * Themed header strip — JUNE [emojis] 2026
 *   * Day-of-week row
 *   * 6 × 7 cell grid with shared borders
 *   * Holiday labels at top of cells (Flag Day, Juneteenth, etc.)
 *   * Banner events — time first, inline icon, headline
 *   * Standard events — time first, then name
 */
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ElksCalendarWidget = publicWidget.Widget.extend({
    selector: ".elks-cal-mount",

    async start() {
        const today = new Date();
        const year = parseInt(this.el.dataset.year) || today.getFullYear();
        const month = parseInt(this.el.dataset.month) || today.getMonth() + 1;
        const showGraphics = this.el.dataset.showGraphics !== "0";

        const resp = await fetch(`/elks/calendar/json/${year}/${month}`);
        if (!resp.ok) {
            this.el.innerHTML = `<p class="text-danger">Calendar unavailable.</p>`;
            return;
        }
        const data = await resp.json();
        this._render(data, showGraphics);
    },

    _escape(str) {
        // Defensive HTML escape for event names that come from the DB.
        return String(str || "").replace(/[&<>"']/g, c => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;",
        }[c]));
    },

    _render(data, showGraphics) {
        // Group events by day-of-month for cell rendering. The JSON feed
        // already sorts events by start ascending, but re-sort here too
        // so a hand-edited or out-of-order payload still renders
        // chronologically (earliest time first within each day).
        //
        // IMPORTANT: bucket by ev.day (server-computed day-of-month in
        // the lodge's timezone), NOT by new Date(ev.start).getDate().
        // The start string is sent as a naive ISO datetime so JavaScript
        // would interpret it as local-browser time and place 6pm Pacific
        // events on the wrong day for any visitor outside Pacific.
        const byDay = {};
        (data.events || []).forEach(ev => {
            const d = (ev.day != null)
                ? ev.day
                : (ev.start ? new Date(ev.start).getDate() : null);
            if (!d) return;
            (byDay[d] = byDay[d] || []).push(ev);
        });
        Object.values(byDay).forEach(list => {
            list.sort((a, b) => {
                // Primary: earliest start time first.
                const ta = a.start ? new Date(a.start).getTime() : 0;
                const tb = b.start ? new Date(b.start).getTime() : 0;
                if (ta !== tb) return ta - tb;
                // Secondary: alphabetical by name (case-insensitive)
                // so events sharing a start time render in a stable
                // predictable order.
                return (a.name || "").toLowerCase()
                    .localeCompare((b.name || "").toLowerCase());
            });
        });

        const firstWeekday = new Date(data.year, data.month - 1, 1).getDay();
        const daysIn = new Date(data.year, data.month, 0).getDate();

        const theme = data.theme || {};
        const accent = theme.primary || "#c0392b";
        const accent2 = theme.secondary || "#1f6f4a";

        // ── Header strip (JUNE [emojis] 2026) ────────────────────────
        const emojiStrip = (data.emojis || [])
            .map(e => `<span>${this._escape(e)}</span>`)
            .join(" ");

        let html = `
          <div class="elks-cal-widget" style="--accent: ${accent}; --accent-2: ${accent2};">
            <div class="elks-cal-header">
              <div class="month">${this._escape(data.month_name || "")}</div>
              <div class="deco">${emojiStrip}</div>
              <div class="year">${data.year}</div>
            </div>
            <div class="elks-cal-day-row">
              ${["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
                  .map(d => `<div>${d}</div>`).join("")}
            </div>
            <div class="elks-cal-grid">
        `;

        // ── Leading blank cells before day 1 ─────────────────────────
        for (let i = 0; i < firstWeekday; i++) {
            html += `<div class="cell blank"></div>`;
        }

        // ── Day cells ────────────────────────────────────────────────
        // Every event renders in its own chronological slot. Banner-styled
        // events (Karaoke, Queen of Hearts, etc.) keep their colour /
        // inline icon / box treatment but stay in time order.
        for (let day = 1; day <= daysIn; day++) {
            const events = byDay[day] || [];
            const holiday = (data.holidays || {})[String(day)] || "";

            html += `<div class="cell">
                       <div class="num">${day}</div>`;

            if (holiday) {
                html += `<div class="holiday">${this._escape(holiday)}</div>`;
            }

            events.forEach(e => {
                const isBanner = e.banner_style && e.banner_style !== "none";
                const color = e.banner_color || "";
                const boxStyle = e.banner_box
                    ? "background:#fff7e6;border:1px dashed #d49100;padding:3px;border-radius:4px;margin-top:2px;"
                    : "";
                const bannerColorStyle = isBanner
                    ? `color:${color || "#1a1a1a"};font-weight:800;`
                    : "";
                const italicStyle = e.banner_italic ? "font-style:italic;" : "";
                const lineStyle = `${boxStyle}${bannerColorStyle}${italicStyle}`;

                html += `<div class="event-line${isBanner ? " banner-line" : ""}" style="${lineStyle}">`;
                if (e.time) {
                    const timeColor = isBanner && color ? `style="color:${color};"` : "";
                    html += `<span class="event-time" ${timeColor}>${this._escape(e.time)}</span> `;
                }
                // Icon priority: emoji from the banner style name first
                // (matches the backend dropdown exactly), then FA icon,
                // then image URL from the graphic library.
                if (isBanner && e.banner_symbol) {
                    html += `<span class="banner-symbol" style="margin-right:3px;">${this._escape(e.banner_symbol)}</span>`;
                } else if (isBanner && showGraphics && e.has_graphic) {
                    if (e.fa_class) {
                        html += `<i class="${this._escape(e.fa_class)}" style="color:${e.fa_color || color || "#c0392b"};font-size:12px;margin-right:3px;vertical-align:middle;"></i>`;
                    } else {
                        html += `<img class="banner-graphic" src="${e.graphic_url}" alt=""/>`;
                    }
                }
                html += this._escape(isBanner ? (e.banner_label || e.name) : e.name);
                if (isBanner && e.banner_sub) {
                    html += `<div class="banner-sub" style="color:${color};">${this._escape(e.banner_sub)}</div>`;
                }
                html += `</div>`;
            });

            html += `</div>`;
        }

        // ── Trailing blanks to fill the grid (always 6 rows) ─────────
        const used = firstWeekday + daysIn;
        const trailing = (7 - (used % 7)) % 7;
        for (let i = 0; i < trailing; i++) {
            html += `<div class="cell blank"></div>`;
        }

        html += `</div>`; // .elks-cal-grid

        if (data.footer_text) {
            html += `<div class="elks-cal-footer">${this._escape(data.footer_text)}</div>`;
        }
        html += `</div>`; // .elks-cal-widget

        this.el.innerHTML = html;
    },
});

export default publicWidget.registry.ElksCalendarWidget;
