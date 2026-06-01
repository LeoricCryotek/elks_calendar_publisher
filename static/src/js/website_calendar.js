/** @odoo-module **/
/*
 * Elks Calendar — public website widget.
 *
 * Renders a small monthly grid into any element with class
 * `.elks-cal-mount`. Pulls event data from the JSON feed and
 * honors the per-event banner style + graphic flag.
 *
 * Wireframe stage: structure + fetch wired up, styling left to
 * website_calendar.scss. Cell rendering loops over events.
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

    _render(data, showGraphics) {
        const byDay = {};
        data.events.forEach(ev => {
            const d = new Date(ev.start).getDate();
            (byDay[d] = byDay[d] || []).push(ev);
        });

        const firstWeekday = new Date(data.year, data.month - 1, 1).getDay();
        const daysIn = new Date(data.year, data.month, 0).getDate();

        let html = `
            <div class="elks-cal-grid">
              ${["Sun","Mon","Tue","Wed","Thu","Fri","Sat"].map(d => `<div class="head">${d}</div>`).join("")}
        `;

        for (let i = 0; i < firstWeekday; i++) {
            html += `<div class="cell empty"></div>`;
        }
        for (let day = 1; day <= daysIn; day++) {
            const events = byDay[day] || [];
            const banner = events.find(e => e.banner_style !== "none");
            html += `<div class="cell ${banner ? "has-banner banner-" + banner.banner_style : ""}">
                       <div class="num">${day}</div>`;

            if (banner) {
                html += `<div class="banner-block">`;
                if (showGraphics && banner.has_graphic) {
                    html += `<img class="banner-graphic" src="${banner.graphic_url}" alt=""/>`;
                }
                html += `<div class="banner-headline">${banner.banner_label}</div>`;
                if (banner.banner_sub) {
                    html += `<div class="banner-sub">${banner.banner_sub}</div>`;
                }
                html += `</div>`;
            }

            // Remaining events render as small lines
            events.filter(e => e !== banner).forEach(e => {
                html += `<div class="event-line">${e.name}</div>`;
            });

            html += `</div>`;
        }
        html += `</div>`;
        this.el.innerHTML = html;
    },
});

export default publicWidget.registry.ElksCalendarWidget;
