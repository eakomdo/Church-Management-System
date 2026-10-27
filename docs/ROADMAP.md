# Roadmap

Build plan for the Church Management System API. Requirement IDs (FR-xx, NFR-xx) refer to the
[requirements specification](https://claude.ai/artifact/Qn1GtBYjSmosNtw41mxmEs).

**Order:** the API (Part A) is built first, phase by phase. Frontends (Part B) follow in their own repos.

**Stack:** Python 3.14, Django 5.2 LTS, Django Ninja, PostgreSQL 18, Celery + Redis, S3-compatible storage.

Tasks marked **(church)** depend on an answer from the church (spec section 4). We build around them and
adjust when the answer arrives.

---

## Part A: API

### Phase 0: Project setup

- [ ] 0.1 Repo and Django project skeleton: split settings, environment variables, `uv`, `ruff`, `pyright`, pre-commit
- [ ] 0.2 Docker Compose for local services: PostgreSQL, Redis, Mailpit, MinIO
- [ ] 0.3 Django Ninja: versioned `/api/v1`, OpenAPI docs, standard error format, pagination
- [ ] 0.4 Tests and CI: pytest-django, factory_boy, coverage, GitHub Actions
- [ ] 0.5 Shared model conventions: UUID keys, timestamps, `created_by`, branch-owned mixin
- [ ] 0.6 Celery worker and beat wired to Redis
- [ ] 0.7 File storage on S3/MinIO with upload validation
- [ ] 0.8 Architecture notes: app layout, service layer, conventions

### Phase 1: Branches, users and access (FR-01, FR-02, FR-29, FR-30, NFR-01, NFR-03, NFR-14)

- [ ] 1.1 Branch hierarchy: HQ, optional region/district, branch, sub-branch **(church: hierarchy depth)**
- [ ] 1.2 Branch API: name, location, pastor, contacts, status
- [ ] 1.3 Custom user model: login by email or phone, Argon2 hashing
- [ ] 1.4 Auth API: login, logout, tokens, password reset by email or SMS code, 30-minute idle expiry
- [ ] 1.5 Two-factor authentication (TOTP) with backup codes for admin roles
- [ ] 1.6 Roles and permissions: the seven spec roles, scoped to HQ, region, branch or group
- [ ] 1.7 Branch scoping: every query limited to the branches a user may see
- [ ] 1.8 PostgreSQL row-level security as a second layer, with cross-branch leak tests
- [ ] 1.9 Audit trail: before/after values on every change; financial records reversed, never deleted
- [ ] 1.10 User activity log, login throttling, security headers, CORS
- [ ] 1.11 Configurable settings: lookup lists (statuses, giving types, service types) per branch

### Phase 2: People (FR-03, FR-04, FR-07, NFR-02, NFR-04)

- [ ] 2.1 Member model: bio data, photo, encrypted Ghana Card number, class, status, date joined
- [ ] 2.2 Member API: create and update, trigram search, filters, pagination
- [ ] 2.3 Search performance check with 50,000 seeded members (under 2 seconds)
- [ ] 2.4 Data protection: consent records, personal data export, correction requests
- [ ] 2.5 Households and relationships; authorised pickup persons
- [ ] 2.6 Branch transfers with history
- [ ] 2.7 Excel/CSV import: column mapping, validation preview, error report, background processing
- [ ] 2.8 Member export to Excel/CSV, limited by permissions
- [ ] 2.9 Member ID card PDFs with QR codes, single and batch
- [ ] 2.10 Visitors and first-timers: public capture endpoint with spam protection, conversion to member

### Phase 3: Messaging and automation (FR-20, FR-21)

- [ ] 3.1 Messaging interface with pluggable SMS and email providers, plus a log-only provider **(church: SMS provider)**
- [ ] 3.2 Message templates with placeholders
- [ ] 3.3 Audience builder: branch, group, age, gender, status
- [ ] 3.4 Bulk and scheduled sending in batches, with retries
- [ ] 3.5 Delivery reports from provider callbacks; SMS credit balance per branch
- [ ] 3.6 Two-way SMS reply inbox
- [ ] 3.7 WhatsApp Cloud API provider
- [ ] 3.8 Push notification device registration (Firebase)
- [ ] 3.9 Automation rules: trigger, audience, channel, timing; daily scheduler
- [ ] 3.10 Automatic welcome SMS for first-timers

### Phase 4: Groups, attendance and follow-up (FR-08 to FR-11, FR-25, NFR-07)

- [ ] 4.1 Groups: departments, ministries, choirs, cell groups; leader-scoped access
- [ ] 4.2 Service types and service sessions, several per day
- [ ] 4.3 Attendance: headcount, individual, QR scan, self check-in
- [ ] 4.4 Offline sync endpoint: retry-safe batch upload with device-generated IDs
- [ ] 4.5 Absence detection job that opens follow-up cases
- [ ] 4.6 Follow-up cases: stages, assignment, notes, due dates, overdue escalation
- [ ] 4.7 New converts and discipleship: decisions, classes, progression to membership
- [ ] 4.8 Volunteer duty rosters, reminders, swap requests

### Phase 5: Children (FR-05, FR-06)

- [ ] 5.1 Sunday school classes by age group, teachers, rosters, lesson schedules
- [ ] 5.2 Medical and allergy notes (restricted); bulk class promotion
- [ ] 5.3 Child check-in with matching security codes and printable tag data **(church: label printer)**
- [ ] 5.4 Check-out verified against code and authorised guardian; parent SMS

### Phase 6: Giving and payments (FR-14 to FR-16, FR-18)

- [ ] 6.1 Giving records: cash, batch per service, bank transfer; reversal only, with a reason
- [ ] 6.2 Numbered receipts by SMS and email
- [ ] 6.3 Payment provider interface and Paystack: MoMo and card, verified webhooks, idempotency **(church: payment provider)**
- [ ] 6.4 Hubtel provider, if chosen
- [ ] 6.5 Payment links; USSD if required
- [ ] 6.6 Automatic matching of payments to member and branch; unmatched queue
- [ ] 6.7 Recurring giving
- [ ] 6.8 Refunds
- [ ] 6.9 Pledges and fundraising projects with reminders
- [ ] 6.10 Welfare: contributions, requests, approvals, payouts
- [ ] 6.11 Annual giving statement PDFs

### Phase 7: Finance (FR-17)

- [ ] 7.1 Expense categories; budgets per branch and department
- [ ] 7.2 Expenses with receipt uploads
- [ ] 7.3 Multi-level approvals with configurable thresholds
- [ ] 7.4 Branch remittances to HQ **(church: remittance rule)**
- [ ] 7.5 Petty cash
- [ ] 7.6 Bank reconciliation from statement imports
- [ ] 7.7 Income and expense reports per branch and consolidated

### Phase 8: Events (FR-19)

- [ ] 8.1 Events and conferences with capacity limits
- [ ] 8.2 Registration and ticket types; paid tickets
- [ ] 8.3 QR tickets and check-in
- [ ] 8.4 Attendee reports

### Phase 9: Sacraments and milestones (FR-12, FR-13)

- [ ] 9.1 Baptism: candidates, class attendance, services, officiating minister
- [ ] 9.2 Weddings, dedications, communion, ordinations, funerals
- [ ] 9.3 Certificates: per-type designs, numbering, public QR verification

### Phase 10: Pastoral care and content (FR-22 to FR-24)

- [ ] 10.1 Prayer requests and counselling bookings, visible only to the assigned pastor
- [ ] 10.2 Website content API: pages, branch pages, service times, news
- [ ] 10.3 Sermons and media: uploads, notes, livestream links

### Phase 11: Facilities (FR-26)

- [ ] 11.1 Asset inventory per branch with custodian and condition
- [ ] 11.2 Bookings of halls, vehicles and equipment; clashes blocked in the database

### Phase 12: Member self-service API (FR-27)

- [ ] 12.1 Member onboarding: SMS invite, profile claim by phone code
- [ ] 12.2 Member endpoints: profile, family, giving, statements, check-in, events, prayer, announcements

### Phase 13: Reports and dashboards (FR-28)

- [ ] 13.1 Pre-computed reporting views refreshed on a schedule
- [ ] 13.2 Dashboard endpoints per branch and consolidated for HQ
- [ ] 13.3 PDF and Excel export
- [ ] 13.4 Scheduled email reports

### Phase 14: Hardening and staging

- [ ] 14.1 Permission test matrix: every endpoint against every role
- [ ] 14.2 Load test: 100,000 members across 50 branches; index tuning (NFR-04, NFR-05)
- [ ] 14.3 Final API documentation and OpenAPI export for frontend and mobile
- [ ] 14.4 Data migration tooling **(church: existing data)**
- [ ] 14.5 Staging deployment, Sentry, uptime monitoring
- [ ] 14.6 Daily off-site backups kept 30 days, with a restore drill (NFR-08)

---

## Part B: Frontends (separate repos)

- [ ] B0 Choose the admin app approach (React app on this API, or server-rendered)
- [ ] B1 Shared UI: layout, design system, login and 2FA, branch switcher, role-based menus
- [ ] B2 Admin screens per module, in Phase 1 to 13 order, including the child check-in kiosk
- [ ] B3 Public website: branches with maps, events, sermons, blog, giving, forms; fast on 3G
- [ ] B4 Member web portal
- [ ] B5 Flutter app, including offline staff capture for attendance and giving **(church: phase 1 or 2)**
- [ ] B6 Accessibility (WCAG 2.1 AA), cross-browser and end-to-end tests
- [ ] B7 Launch: production deployment, data migration, user guides, handover
