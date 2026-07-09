# plan.md — Stanvard School ERP (Multi-Branch) Development Plan (Updated)

## 1) Objectives
- Deliver a production-ready, multi-branch School ERP + Parent Portal for Stanvard School with **3 initial branches** (Kanpur, Ganesh Nagar, Ayar) and unlimited future branches.
- Ensure **multi-branch isolation** with independent data per school + a robust **school switcher**.
- Prove the **core workflow** is solid before mobile app build: **Fee collection → Razorpay order → verification/webhook → receipt PDF**.
- Build a modern, responsive web UI (React + shadcn/ui + Tailwind) with role-based UX (Super Admin, Admin, Accountant, Teacher, Parent).
- Provide fee-first visibility: **fee analytics, receipts, transaction history, and downloadable reports** for any selected date range and selected classes/sections.
- Move from MVP/demo to production readiness:
  - Import and operate on **real student data**
  - Remove demo credentials
  - Enable parents to log in using **mobile number** and support **multiple children per parent account**
- Ensure security, auditability, and “no hard deletes” across modules.

---

## 2) Implementation Steps (Phased)

### Phase 1 — Core POC (Isolation): Razorpay + Receipt PDF (must pass before Phase 2)
**Goal:** Validate payment lifecycle + server-side PDF generation with real Razorpay sandbox behavior.

Steps
1. Web-search Razorpay best practices (Orders API, signature verification, webhooks, idempotency, receipt/order refs, test cards/UPI flows).
2. Create minimal Python POC (no FastAPI yet):
   - Create Razorpay Order for ₹5000.
   - Simulate/accept payment response payload and verify signature.
   - (If feasible locally) implement webhook handler function and verify webhook signature.
3. Generate server-side **Fee Receipt PDF** using reportlab:
   - Receipt no, student info, fee heads/amounts, payment mode, txn id, timestamps, school branding.
4. Store POC outputs locally (json logs + generated PDFs) and document exact payload fields needed for main app.

Status
- ✅ Completed earlier as part of MVP integration: Razorpay order generation + server-side PDF receipt generation exists in the FastAPI app.
- ⚠️ Note: Production-grade online payment capture/finalization is still a future task (see Next Actions).

User stories (Phase 1)
1. As an accountant, I can create a Razorpay order for ₹5000 and receive a valid order_id.
2. As the system, I can verify Razorpay payment signature and mark a payment as verified.
3. As the system, I can validate webhook signatures and ignore forged callbacks.
4. As an accountant, I can generate a receipt PDF that matches the payment details.
5. As a developer, I can rerun the script and get deterministic logs and a new receipt number each run.

---

### Phase 2 — V1 App Development (MVP around proven core; delay auth to Phase 4)
**Goal:** Working end-to-end ERP V1 for one branch + switcher-ready structure, with strongest modules first.

Backend (FastAPI + Motor/Mongo)
1. Multi-tenant foundation:
   - `schools` collection + `school_id` scoping on every entity.
   - Repository helpers enforce `school_id` filters; add indexes.
2. Core domain models + APIs (school-scoped):
   - Students (CRUD + search/filter), Classes/Sections.
   - Fees: fee heads, fee plans (frequency/installments), student fee assignment.
   - Collections: payment records (offline modes + online placeholder endpoints that call POC logic).
   - Receipts: sequential receipt numbers per school + PDF endpoint.
3. Razorpay integration inside backend:
   - create order endpoint, verify payment endpoint, webhook endpoint.
4. Audit log middleware:
   - Log key actions (fee structure changes, receipt create/cancel, attendance edits, logins later).
5. Seed data:
   - 3 schools + sample classes/sections + sample students + sample fee structures + sample attendance.

Frontend (React + shadcn/ui + Tailwind)
1. Apply design_agent guidelines; responsive layouts and role-ready navigation.
2. School switcher UI (temporary local selection stored in app state; used in all API calls).
3. Key screens (V1):
   - Dashboard (school-scoped cards + graphs placeholders where needed).
   - Students list + student profile view/add/edit.
   - Fee setup (fee heads/plans/assignments).
   - Collect fees (offline + online via Razorpay checkout flow).
   - Receipts list + receipt PDF download.

Status
- ✅ Completed as part of current MVP: multi-branch architecture, RBAC authentication, school switcher, student management, advanced fee management, Razorpay order generation, PDF receipts, reports dashboard.
- ✅ **Production Data Migration COMPLETE** (see Phase 4 status for details).

Testing checkpoint
- ✅ Completed: repeated testing via `testing_agent_v3` with zero failing flows across prior iterations.

User stories (Phase 2)
1. As a school admin, I can switch schools and see different dashboards and student lists instantly.
2. As an accountant, I can collect an offline payment and instantly download a receipt PDF.
3. As a parent (demo flow without auth), I can open a payment page and complete Razorpay test payment.
4. As a school admin, I can create fee plans (monthly/annual) and assign them to a class.
5. As management, I can view today/month collection and recent payments for the selected school.

---

### Phase 3 — Expand Modules + Reports (production-lean, modularize)
**Goal:** Fill core ERP breadth: attendance, homework, circulars, events, gallery, notifications, reports exports.

Steps
1. Attendance: daily/monthly student attendance + teacher attendance + reports + export.
2. Homework + attachments + parent view.
3. Timetable (class-wise/teacher-wise) + printable view.
4. Circulars/events/gallery with scheduling, priority, attachments.
5. Reports: daily/monthly/yearly collection, pending fees, discounts, **transactions**; export PDF/CSV/Excel.
6. Strengthen audit log coverage across all new modules.
7. Run testing_agent_v3: E2E on attendance + homework + circulars + reports + fees regression.

Status
- ✅ Analytics Dashboard redesigned to be 100% fee-focused.
- ✅ **Task 1 COMPLETE:** Transactions on Analytics Dashboard.
  - Backend: `/api/analytics/fees` returns rich `transactions` array scoped to selected date range + filters.
  - Frontend: Analytics shows **“Transactions in Selected Range”** with in-card search, mode filter, pagination (10/25/50/100), CSV download, empty state, colored mode badges.
  - Filters supported: date presets + custom range + class + section + payment mode.
  - ✅ Tested via `testing_agent_v3` (iteration_7: Backend 73/73, Frontend 27/27; no regressions).

- ✅ **Reports Enhancement COMPLETE:** Student Fee Status — multi-class/section + exports.
  - Backend:
    - `/api/reports/fee-status` supports `class_sections` (comma-separated `class_id:section` pairs; blank section means *all* sections of that class).
    - `min_due` / `max_due` filters removed.
    - Added export endpoints: `/api/reports/fee-status.pdf`, `/api/reports/fee-status.xlsx`, `/api/reports/fee-status.csv`.
    - All exports respect `class_sections` and `status_filter`.
  - Frontend:
    - Reports > Student Fee Status uses a Popover multi-select (per-class master checkbox + per-section chips) with removable selection chips.
    - Added download buttons: **PDF / XLSX / CSV**.
    - Min/Max Due inputs removed.
  - ✅ Tested via `testing_agent_v3` (iteration_8: Backend 39/39, Frontend 100%; no regressions incl. Fee Collection tab and Analytics transactions).

User stories (Phase 3)
1. As a teacher, I can mark today’s attendance for my class and it reflects in the dashboard.
2. As a parent, I can see homework with attachments and due dates.
3. As an admin, I can publish a circular with a PDF attachment and schedule it.
4. As an accountant, I can export monthly collection to Excel/CSV.
5. As management, I can view pending fees by class/section and drill down to students.
6. As an accountant/admin, I can select **multiple classes with specific sections** and download a **Student Fee Status** report in **PDF/XLSX/CSV**.

---

### Phase 4 — Authentication + RBAC + Parent Portal Hardening (email/password)
**Goal:** Secure production-ready access control + full role UX.

Steps
1. Implement JWT auth (email/password), password hashing, refresh strategy, account lockout basics.
2. RBAC policies per endpoint + UI route guards.
3. Seed accounts for: super admin, school admins, accountants, teachers, parents.
4. Parent portal: single-child/multi-child support (if needed), fee payment + receipts + attendance/homework views.
5. Security: rate limiting basics, input validation, file upload constraints, audit log for auth events.
6. Run testing_agent_v3: full role-based E2E regression.

Status (Updated)
- ✅ Authentication + RBAC already implemented in MVP (Super Admin, Admin, Accountant, Teacher, Parent).
- ✅ **Login supports email OR mobile number**:
  - Backend `LoginRequest.email` is now a string identifier.
  - `/api/auth/login` attempts email match, then phone match (digits-only; supports `+91` and spaces via last-10-digits matching).
- ✅ **Multi-child parent accounts supported**:
  - User model adds `linked_student_ids: List[str]` while keeping legacy `linked_student_id` for backward compatibility.
  - Parent access checks refactored to authorize against the merged child ID set.
- ✅ **Parent Portal Child Switcher added**:
  - `ChildContext` persists active child in localStorage.
  - `ChildSwitcher`:
    - Single-child: static badge.
    - Multi-child: popover to switch children.
  - Implemented on Parent Home and Parent Pay pages.
- ✅ **Admin UI supports linking multiple students to a parent**:
  - Users page edit dialog includes “Linked Children” block with chips + search + add/remove.
  - Fixed a school-context timing race that previously caused linked-child names to appear missing on initial load.
- ✅ **Demo data and demo credentials removed**:
  - Login page no longer displays demo accounts.

**Production credentials (current):**
- Super Admin: `superadmin@stanvard.school` / `Stanvard@2026`
- Accountant: `accountant@stanvard.school` / `Accountant@2026`
- Parents: username = mobile number (10-digit) | password = last 6 digits of the same mobile

**Production data migration (complete):**
- Real FY 2026-27 Excel imported into **Kanpur** branch:
  - 375 students
  - 13 classes (LKG, UKG, PREP, Class I–X), section = `A`
  - 375 fee assignments (Tuition Fee)
  -  >100 imported payment records (opening balances) where “paid” existed in Excel
  - ~298 parent accounts created (unique mobiles); 12 students without mobile → no parent account
- Ganesh Nagar and Ayar branches preserved as **empty shells** (0 students) for future onboarding.

Testing
- ✅ `testing_agent_v3` iteration_9:
  - Backend: 100% (37/37)
  - Frontend: critical flows verified (mobile login, multi-child parent switcher, Users linking UI, Pay page switching)

User stories (Phase 4)
1. As a super admin, I can log in and manage schools and users across all branches.
2. As a school admin, I can only access my assigned school’s data and modules.
3. As a teacher, I can only see my assigned classes for attendance/homework.
4. As a parent, I can see **one or multiple children** in the portal and pay fees online.
5. As admin, I can link **two or more kids** to the same parent account (siblings) and the parent can switch children.
6. As an auditor, I can review an action trail for fee edits and receipt generation.

---

## 3) Next Actions (Immediate)
1. **Productionize payments (P1):** finalize Razorpay payment lifecycle for go-live (webhook-driven status updates, idempotency, retries, reconciliation reports). Avoid any real capture during testing.
2. **Refactor backend structure (P2):** split monolithic `server.py` into FastAPI routers (students, fees, analytics, reports, auth, etc.).
3. **Resolve pending code-review technical debt (P2):**
   - Refactor high-complexity functions: `server.py` (`analytics()`, `dashboard_summary()`), `pdf_utils.py` (`generate_receipt_pdf()`)
   - Frontend complexity: `AssignFeeDialog.jsx`, `FeeCollection.jsx`, `EditStudentDialog.jsx`
   - Note: `Reports.jsx` was rewritten during fee-status enhancement; keep an eye on modularizing it further if it grows.
4. **Security hardening (P1/P2):** secure token storage (move from localStorage to httpOnly cookies or equivalent mitigation), tighten CSP, and review XSS exposure.
5. **Operational readiness (P1/P2):**
   - Add a safe “backup/export database” + restore procedure
   - Add admin UI for correcting parent mobile numbers and reissuing passwords
6. **Extend reporting (optional):** server-side export endpoints for Analytics transactions (PDF/XLSX/CSV) and/or “download filtered transactions” for management.

---

## 4) Success Criteria
- Phase 1: Razorpay order creation + signature verification + webhook verification + valid receipt PDF generation works reliably.
- Phase 2: Multi-school scoping works end-to-end; fee collection (offline + Razorpay) generates immutable receipts + PDFs.
- Phase 3: Attendance/homework/circulars/reports functional with exports; **analytics includes drill-down transaction history by filter**; **fee-status reports support multi-class/section selection with PDF/XLSX/CSV exports**; no cross-school data leakage.
- Phase 4: RBAC enforced on backend and UI; parent portal fully usable for **single-child and multi-child** parents; audit logs cover critical operations; regression tests pass.
- Production readiness: real data imported, demo content removed, production credentials established, parents can log in by mobile and view their linked children.

---

## Appendix — Current Status Snapshot (Production Data Live)
- ✅ Multi-branch preserved: Kanpur (active real data), Ganesh Nagar (empty), Ayar (empty) + school switcher.
- ✅ Real data imported: 375 students, 13 classes, 375 fee assignments,  >100 opening-balance payments.
- ✅ Role-based access: Super Admin, Admin, Accountant, Teacher, Parent.
- ✅ Parent auth: login with mobile number; password = last 6 digits; supports `+91` prefix.
- ✅ Parent portal: child switcher + multi-child support.
- ✅ Users admin: multi-child linking UI for parent accounts.
- ✅ Fee Management: custom assignments, Razorpay order generation, server-side PDF receipt generation.
- ✅ Analytics: fee-focused KPIs + charts + transaction history by selected date range (iteration_7 100% pass).
- ✅ Reports:
  - Fee Collection exports (existing)
  - Student Fee Status: multi-class/section selection + PDF/XLSX/CSV exports; Min/Max Due removed (iteration_8 100% pass).
- ✅ Testing: `testing_agent_v3` iterations 1–9 (latest: iteration_9 backend 100% pass; frontend critical flows verified).
- ⚠️ Deferred: refactors + secure token storage + payment go-live hardening.
