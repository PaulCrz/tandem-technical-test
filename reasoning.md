# Raw Reasoning *(No AI used, ~ 40 minutes)*

I decided that using a full RDBMS like PostgreSQL to store and process events data would take too much time to set up and implement queries given the short test time (2 hours). Instead, writing a single script capable of doing all the work—without relying on external services or tools—seems to be the best approach.

---

## Data Processing

1. **Group by `user_id`**
   Focus on each individual’s journey through the app. By experience, events related to a specific `session_id` must always match a single corresponding `user_id`. Checking for incoherence (e.g., a `session_id` linked to multiple `user_id`s) can be useful.

2. **Group by `session_id` (within each `user_id`)**
   - Identify how many sessions each user has.
   - Get insights based on events relative to a single session.

3. **Sort events by `event_time` (within each session)**
   - Order events in ascending timestamp order.
   - This makes it easy to reconstruct the user flow.
   - Calculate time spent on a specific page by taking the gap between two timestamps in the same session.

---

### Events Format

Before generating a report, I need to understand the structure and purpose of each event’s properties:

| Property       | Typical Content                                                                                      | Use in Analysis                                                                                             |
| -------------- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **`uuid`**     | A globally unique ID for **every single event**.                                                     | De-duplicate events, trace precise clicks (ideal primary key for storage).                                  |
| **`user_id`**  | Stable GUID representing **one person/account** across visits.                                        | Pivot on this to build per-user histories (lifetime value, cohort analysis, churn modeling).               |
| **`session_id`** | GUID that groups a contiguous browsing period (tab or login session).                               | Fundamental unit for **journey reconstruction**—order events inside a session to see flows and dwell-times. |
| **`event_time`** | ISO timestamp string (e.g., `2025-02-06 09:00:24`).                                                  | Provides chronology—sort by it to rebuild sequences, compute time-to-next-click, detect idle gaps/spikes.  |
| **`path`**     | URL path of the page where the event fired (no domain, e.g., `/checkout`).                            | Backbone of all **funnel/flow** metrics and drop-off analysis.                                              |
| **`css`**      | Front-end CSS selector or DOM ID the user interacted with (e.g., `#search-bar`, `.promo-banner`).     | Pinpoints exact UI element—useful for heat-maps, A/B testing, spotting broken selectors (`.error-message`).|
| **`text`**     | Human-readable inner text of that element (e.g., `"Add to cart"`, `"Logo"`).                         | Makes dashboards readable for PMs; can be mined for intent (“Subscribe”, “Cancel”).                         |
| **`value`**    | Any input value tied to the event (often empty, but could hold search queries like `"laptop"`).      | Surfaces **user intent**, reveals anomalies (e.g., unusually long strings, invalid formats).                |

---

### Top-level Paths

| Path                   | Role in the Product                                                                                                             |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **`/`**                | **Home / landing page** – Natural start of almost every flow.                                                                   |
| **`/account`**         | **Account dashboard** – Logged-in users see personal details, past orders, and can log out.                                     |
| **`/blog`**            | **Blog & news hub** – Long-form articles for users to read and comment on.                                                      |
| **`/cart`**            | **Shopping cart** – Shows items selected, quantities, and totals.                                                               |
| **`/checkout`**        | **Checkout funnel** – Collects shipping/payment info, places the order, surfaces payment-gateway errors.                        |
| **`/faq`**             | **FAQ self-service page** – Static answers to common questions.                                                                 |
| **`/help`**            | **Live help / pop-up assistant** – Launches “Need help?” widget.                                                                 |
| **`/login`**           | **Authentication gate** – Username/password (or SSO) entry point.                                                                |
| **`/products`**        | **Product catalogue** – Grid or list of all products, with filters and search bar.                                               |
| **`/products/<slug>`** | **Individual product page** – Photos, specs, reviews, “Add to cart” button. (There are 24 distinct slugs in the file.)          |
| **`/promo`**           | **Promotional landing page** – Banners like “Summer Sale”, “Flash Deal”, plus email-capture buttons.                            |
| **`/random`**          | **Experimental / “surprise-me” page** – Serves “Random Content” and lets users try arbitrary searches; useful for A/B or QA.    |
| **`/settings`**        | **User settings center** – Language selector, notification toggles, other preferences.                                           |

---

## Meaningful Report Generation *(No AI used, ~ 20 minutes)*

1. **Generate a Visual Report (HTML) for PMs**

2. **Funnel Analysis**
   - **Successful Purchase Funnels:**
     - Look for sessions that end with a successful `/checkout` event.
   - **Uncompleted Funnels:**
     - For sessions that do not end in `/checkout`, display the session’s last event to identify where the user dropped off.

3. **Anomaly Detection**
   - **Timeouts / User Confusion / Errors:**
     - Analyze long gaps between event timestamps within a session—indicates potential user confusion or page load issues.
     - Scan `css` or `text` for keywords like “error”, “404”, “timeout” and flag those events.

---

## Choosing the Right Stack *(No AI used, ~ 10 minutes)*

- I need a data structure capable of handling large volumes (anticipating millions of events) and flexible enough to sort and access nested data.
- I also need a language that is well-suited for data processing, has simple syntax, and supports external libraries.
- **Python** is the best choice:
  - Simple syntax, excellent for JSON and nested data.
  - Quick prototyping, vast ecosystem (Pandas, Jinja2, etc.).
  - Light setup—no need for low-level coding.
  - Performance is acceptable for prototyping; if I outgrow it, I can refactor to a faster language later.

---

# Implementation *(Use of AI, mostly for writing code quickly, ~ 50 minutes)*

**Plan:**

1. **Load the JSON Lines file**
   - Fetch from the AWS S3 URL:
     ```
     https://s3.eu-central-1.amazonaws.com/public.prod.usetandem.ai/sessions.json
     ```
   - Read all lines into memory as a list of Python dictionaries.
   - (For future scalability: implement “lazy loading” or stream parsing, but for now, load all 244 lines at once.)

2. **Sort all events by `event_time`**
   - Perform this once at the beginning—no need to re-sort later.

3. **Group events by `user_id`**
   - Create a dictionary keyed by `user_id`, where each value is a list of events belonging to that user.

4. **Within each `user_id`, group by `session_id`**
   - Each user bucket becomes a dictionary keyed by `session_id`, with a list of that session’s events.
   - Events are already sorted by time, so no additional sorting per session is necessary.

5. **Detect successful and uncompleted funnels for each session**
   - If a session ends with a `/checkout` event, mark it as a “successful funnel.”
   - Otherwise, record the last event’s path to see where the user dropped off.

6. **Detect anomalies across all sessions**
   - **Long Gaps:**
     - For each session, compute time differences between consecutive events. If any gap exceeds a threshold (e.g., 5 minutes), flag it.
   - **Error Keywords:**
     - Scan each event’s `css` or `text` fields for keywords: `"error"`, `"404"`, `"timeout"`. Flag those events.

7. **Generate a Visual HTML Report**
   - **Section 1: Funnel Success/Failure Statistics**
     - Total sessions, number (and %) that completed `/checkout`, number that dropped off.
     - Top 3 drop-off paths with counts.
   - **Section 2: Anomalies**
     - List sessions with long gaps (include `user_id`, `session_id`, gap duration).
     - List events with error keywords (include `user_id`, `session_id`, `event_time`, `path`, `css`/`text`).
   - Use an HTML template (e.g., Jinja2) with embedded tables and charts (optional, e.g., Plotly or Matplotlib).
