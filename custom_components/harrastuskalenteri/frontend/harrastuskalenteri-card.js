class HarrastuskalenteriCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._config = {};
  }

  static getStubConfig() {
    return {
      title: "Harrastukset tänään",
    };
  }

  static getConfigElement() {
    return document.createElement("harrastuskalenteri-card-editor");
  }

  setConfig(config) {
    this._config = {
      title: "Harrastukset tänään",
      ...config,
    };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 5;
  }

  getGridOptions() {
    return {
      columns: "full",
      rows: "auto",
      min_rows: 3,
    };
  }

  _children() {
    return [
      { name: "Elias", entity: "sensor.elias_harrastukset", icon: "⚽" },
      { name: "Amanda", entity: "sensor.amanda_harrastukset", icon: "⚽" },
      { name: "Lydia", entity: "sensor.lydia_harrastukset", icon: "🤸" },
      { name: "Linda", entity: "sensor.linda_harrastukset", icon: "⭐" },
      { name: "Linnea", entity: "sensor.linnea_harrastukset", icon: "🤸" },
    ];
  }

  _escape(value) {
    const div = document.createElement("div");
    div.textContent = value ?? "";
    return div.innerHTML;
  }

  _formatTime(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    return new Intl.DateTimeFormat("fi-FI", {
      hour: "2-digit",
      minute: "2-digit",
    }).format(date);
  }

  _formatDate() {
    return new Intl.DateTimeFormat("fi-FI", {
      weekday: "long",
      day: "numeric",
      month: "long",
    }).format(new Date());
  }

  _eventStatus(event) {
    const now = Date.now();
    const start = new Date(event.start).getTime();
    const end = new Date(event.end).getTime();
    if (!Number.isNaN(start) && !Number.isNaN(end) && now >= start && now <= end) {
      return "now";
    }
    if (!Number.isNaN(end) && end < now) return "past";
    return "future";
  }

  _eventHtml(event) {
    const summary = this._escape(event.summary || "Harrastus");
    const location = this._escape(event.location || "");
    const start = this._formatTime(event.start);
    const end = this._formatTime(event.end);
    const status = this._eventStatus(event);

    return `
      <div class="event ${status}">
        <div class="timeline">
          <span class="dot"></span>
          <span class="line"></span>
        </div>
        <div class="event-body">
          <div class="event-time">${start}${end ? `–${end}` : ""}</div>
          <div class="event-name">${summary}</div>
          ${location ? `
            <div class="location">
              <ha-icon icon="mdi:map-marker"></ha-icon>
              <span>${location}</span>
            </div>
          ` : ""}
          ${status === "now" ? `<div class="badge">Nyt</div>` : ""}
        </div>
      </div>
    `;
  }

  _childHtml(child) {
    const state = this._hass?.states?.[child.entity];
    const events = state?.attributes?.events || [];

    return `
      <section class="child-card">
        <header class="child-header">
          <div>
            <div class="child-name">${this._escape(child.name)}</div>
            <div class="count">${events.length ? `${events.length} tapahtumaa` : "Vapaa päivä"}</div>
          </div>
          <div class="child-icon">${child.icon}</div>
        </header>

        <div class="events">
          ${
            events.length
              ? events.map((event) => this._eventHtml(event)).join("")
              : `
                <div class="empty">
                  <ha-icon icon="mdi:calendar-check"></ha-icon>
                  <span>Ei harrastuksia tänään</span>
                </div>
              `
          }
        </div>
      </section>
    `;
  }

  _render() {
    if (!this.shadowRoot) return;

    const children = this._children();
    const title = this._escape(this._config?.title || "Harrastukset tänään");

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          width: 100%;
        }

        ha-card {
          padding: 22px;
          overflow: hidden;
        }

        .top {
          display: flex;
          justify-content: space-between;
          align-items: end;
          gap: 16px;
          margin-bottom: 20px;
        }

        .title {
          font-size: 28px;
          font-weight: 700;
          line-height: 1.15;
        }

        .date {
          margin-top: 5px;
          font-size: 14px;
          color: var(--secondary-text-color);
          text-transform: capitalize;
        }

        .refresh {
          color: var(--secondary-text-color);
          font-size: 12px;
          white-space: nowrap;
        }

        .grid {
          display: grid;
          grid-template-columns: repeat(5, minmax(0, 1fr));
          gap: 12px;
          align-items: stretch;
        }

        .child-card {
          min-width: 0;
          border: 1px solid var(--divider-color);
          border-radius: 18px;
          background: var(--card-background-color);
          overflow: hidden;
        }

        .child-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 16px 13px 16px;
          border-bottom: 1px solid var(--divider-color);
          background: color-mix(in srgb, var(--primary-color) 6%, var(--card-background-color));
        }

        .child-name {
          font-size: 21px;
          font-weight: 700;
        }

        .count {
          margin-top: 3px;
          font-size: 12px;
          color: var(--secondary-text-color);
        }

        .child-icon {
          font-size: 28px;
          line-height: 1;
        }

        .events {
          padding: 14px;
        }

        .event {
          display: grid;
          grid-template-columns: 18px minmax(0, 1fr);
          position: relative;
        }

        .event + .event {
          margin-top: 4px;
        }

        .timeline {
          position: relative;
          min-height: 94px;
        }

        .dot {
          position: absolute;
          top: 7px;
          left: 4px;
          width: 9px;
          height: 9px;
          border-radius: 50%;
          background: var(--primary-color);
        }

        .line {
          position: absolute;
          top: 20px;
          left: 8px;
          bottom: -3px;
          width: 1px;
          background: var(--divider-color);
        }

        .event:last-child .line {
          display: none;
        }

        .event-body {
          position: relative;
          padding: 0 2px 18px 7px;
          min-width: 0;
        }

        .event-time {
          font-size: 13px;
          font-weight: 700;
          color: var(--primary-color);
          margin-bottom: 5px;
        }

        .event-name {
          font-size: 15px;
          line-height: 1.3;
          font-weight: 650;
          overflow-wrap: anywhere;
        }

        .location {
          display: flex;
          align-items: flex-start;
          gap: 4px;
          margin-top: 8px;
          color: var(--secondary-text-color);
          font-size: 12px;
          line-height: 1.35;
        }

        .location ha-icon {
          --mdc-icon-size: 15px;
          flex: 0 0 auto;
          margin-top: 1px;
        }

        .past {
          opacity: 0.52;
        }

        .now .event-body {
          background: color-mix(in srgb, var(--primary-color) 8%, transparent);
          border-radius: 12px;
          padding: 9px 9px 15px 9px;
          margin: -9px 0 9px -2px;
        }

        .badge {
          display: inline-block;
          margin-top: 8px;
          padding: 3px 8px;
          border-radius: 999px;
          background: var(--primary-color);
          color: var(--text-primary-color);
          font-size: 11px;
          font-weight: 700;
        }

        .empty {
          min-height: 100px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 9px;
          color: var(--secondary-text-color);
          text-align: center;
          font-size: 13px;
        }

        .empty ha-icon {
          --mdc-icon-size: 30px;
          opacity: 0.7;
        }

        @media (max-width: 1200px) {
          .grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
          }
        }

        @media (max-width: 800px) {
          ha-card {
            padding: 14px;
          }

          .grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .title {
            font-size: 23px;
          }
        }

        @media (max-width: 520px) {
          .grid {
            grid-template-columns: 1fr;
          }

          .top {
            align-items: flex-start;
            flex-direction: column;
          }
        }
      </style>

      <ha-card>
        <div class="top">
          <div>
            <div class="title">${title}</div>
            <div class="date">${this._formatDate()}</div>
          </div>
          <div class="refresh">Päivittyy automaattisesti</div>
        </div>

        <div class="grid">
          ${children.map((child) => this._childHtml(child)).join("")}
        </div>
      </ha-card>
    `;
  }
}

class HarrastuskalenteriCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
  }

  _render() {
    this.innerHTML = `
      <div style="padding: 16px">
        <p><strong>Harrastuskalenteri</strong></p>
        <p>Kortti käyttää automaattisesti integraation viittä harrastussensoria.</p>
        <p>Otsikkoa voi muuttaa YAMLissa avaimella <code>title</code>.</p>
      </div>
    `;
  }
}

if (!customElements.get("harrastuskalenteri-card")) {
  customElements.define("harrastuskalenteri-card", HarrastuskalenteriCard);
}

if (!customElements.get("harrastuskalenteri-card-editor")) {
  customElements.define("harrastuskalenteri-card-editor", HarrastuskalenteriCardEditor);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "harrastuskalenteri-card")) {
  window.customCards.push({
    type: "harrastuskalenteri-card",
    name: "Harrastuskalenteri",
    description: "Perheen päivän harrastukset viidessä selkeässä sarakkeessa.",
    preview: true,
    documentationURL: "https://github.com/jokkee1-max/harrastuskalenteri",
  });
}

console.info(
  "%c HARRASTUSKALENTERI-CARD %c v0.2.0 ",
  "color: white; background: #03a9f4; font-weight: 700;",
  "color: #03a9f4; background: white; font-weight: 700;"
);
