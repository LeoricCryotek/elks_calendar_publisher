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
        // Group events by day-of-month for cell rendering.
        const byDay = {};
        (data.events || []).forEach(ev => {
            if (!ev.start) return;
            const d = new Date(ev.start).getDate();
            (byDay[d] = byDay[d] || []).push(ev);
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
        for (let day = 1; day <= daysIn; day++) {
            const events = byDay[day] || [];
            const banner = events.find(e => e.banner_style && e.banner_style !== "none");
            const holiday = (data.holidays || {})[String(day)] || "";
            const cellClass = banner
                ? `cell has-banner banner-${banner.banner_style}`
                : "cell";

            html += `<div class="${cellClass}">
                       <div class="num">${day}</div>`;

            if (holiday) {
                html += `<div class="holiday">${this._escape(holiday)}</div>`;
            }

            // Banner — time first, inline icon, headline.
            if (banner) {
                html += `<div class="banner"><div class="banner-headline">`;
                if (banner.time) {
                    html += `<span class="event-time">${this._escape(banner.time)}</span> `;
                }
                if (showGraphics && banner.has_graphic) {
                    html += `<img class="banner-graphic" src="${banner.graphic_url}" alt=""/>`;
                }
                html += this._escape(banner.banner_label || banner.name);
                html += `</div>`;
                if (banner.banner_sub) {
                    html += `<div class="banner-sub">${this._escape(banner.banner_sub)}</div>`;
                }
                html += `</div>`;
            }

            // Remaining events as small lines — time first, then name.
            events.filter(e => e !== banner).forEach(e => {
                html += `<div class="event-line">`;
                if (e.time) {
                    html += `<span class="event-time">${this._escape(e.time)}</span> `;
                }
                html += this._escape(e.name);
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
