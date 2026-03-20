# PROJECT_BRIEF_RULES.md

**For: Adedamola Bello — demoladevop.com**
**Version: 2026.1**

> Drop this file into any project repo when you are ready to document it.
> Instruct your code editor AI:
> "Read the entire codebase and generate a Project Brief following every rule in PROJECT_BRIEF_RULES.md. Do not skip any section. Do not summarise. Be specific."

---

## The Purpose of This Document

Adedamola builds from instinct. He identifies a real operational problem Nigerian businesses face, builds a system to solve it, and ships it. He does not write briefs before building. He does not take client notes. The problem lives in his head.

This file exists to extract that knowledge after the fact — to read what was built and reconstruct the business narrative behind it. The output is a set of properly written project fields ready to be entered into the portfolio dashboard.

This is not documentation. This is a storefront for Productized Systems. Every word generated here will be read by a Nigerian business owner deciding whether to trust Adedamola to install this exact automation in their own business. Do not write as if this was a custom build for a specific client. Write as if this is an "Industry Blueprint" available for purchase.

---

## Absolute Rules Before You Begin

**Rule 1: Read the codebase before forming any opinion**
Do not guess what the system does. Read the schema, the API routes, the integrations, the auth config. The code tells the real story of what was built and what business problem it solves.

**Rule 2: Think like a business owner, not a developer**
The output of this file is not for developers. It is for a Lagos business owner who has never written a line of code. Every field must be written so that person feels seen — not impressed by the technology, but recognised in the problem.

**Rule 3: Ground the Nigerian business context**
Every project Adedamola builds solves a problem specific to how Nigerian businesses actually operate — WhatsApp-first communication, manual tracking, cash-based transactions, staff coordination via phone calls. The brief must reflect this reality specifically, not generically.

**Rule 4: Ditch "Past Results" for "System Capabilities"**
Adedamola is selling the Engine, not a past case study. Do not invent fake client metrics. Focus on the mathematical capabilities of the system (e.g., "Capable of processing 50+ concurrent requests," "Mathematically eliminates double-booking by syncing calendars"). Talk in absolutes.

**Rule 5: The competitor swap test**
Before finalising any field, ask: could this exact text appear on a different developer's portfolio? If yes, rewrite it with more specificity until the answer is no.

**Rule 6: Write in Adedamola's voice**
First-person singular. Direct. Short sentences. Active voice. No corporate language. No passive voice. No press release tone. Write as if telling the story to someone at a table in Lagos.

---

## Codebase Reading Instructions

Scan in this order before writing anything:

1. `package.json` — what is the full dependency list? Every integration is a business capability.
2. Prisma schema or equivalent — what does the system track? Every model is a real-world entity the business cares about.
3. API routes — what can the system do? Each route is a business action.
4. `.env.example` — what third-party services are connected? WhatsApp, payment gateways, email providers, SMS services.
5. Auth config — who uses the system? Owner only, staff, customers, or all three?
6. The most complex service file — where is the most interesting business logic?
7. README if it exists — any business context already written down?
8. Git history if accessible — what was built first? What changed? What was the hardest part?

---

## Nigerian Business Archetype Library

Before writing the brief, identify which business archetype this project was built for. Use the closest match. If none fit exactly, combine two.

**Service Business** — salons, tailors, repair shops, cleaning services, event planners. Problems: appointment chaos, no-shows, payment tracking, staff coordination.

**FMCG Distributor** — wholesalers, distributors supplying retailers across a region. Problems: order tracking, delivery confirmation, credit management, retailer communication.

**Retail / E-commerce** — physical or WhatsApp-based product sellers. Problems: inventory tracking, order management, customer follow-up, payment reconciliation.

**Reseller / Fintech** — airtime, data, utility bill payment resellers. Problems: wallet management, transaction tracking, customer balance disputes, real-time processing.

**Logistics / Delivery** — dispatch riders, small logistics operators. Problems: route management, delivery confirmation, driver tracking, customer updates.

**Professional Services** — accountants, lawyers, consultants. Problems: invoice management, client follow-up, document handling, payment collection.

**Food & Hospitality** — restaurants, caterers, food vendors. Problems: order taking, kitchen coordination, delivery tracking, daily reconciliation.

Use this archetype to ground the before state, the problem description, and the results in real Nigerian business operations.

---

## Output: Portfolio Project Fields

Generate content for every field below. These map directly to the Prisma Project model fields on demoladevop.com. Every field must be complete. If a field cannot be determined, write `[CONFIRM WITH ADEDAMOLA]`.

---

### Field 1: Title

**Audience:** Nigerian business owner
**Format:** [Fictional Demo Brand] ([System Descriptor])

Because these are Productized Blueprints, do not just name them "Booking System." Give the demo a professional, SaaS-like brand name. The descriptor in parentheses must tell the owner quickly what mechanical capability the engine provides. Maximum 60 characters.

**BAD:**

> Appointment Booking Bot

**GOOD:**

> QuickSlot (Automated WhatsApp Booking Engine)
> VaultFlow (B2B Invoicing & Recon Dashboard)

---

### Field 2: Category

One of: FULLSTACK / BACKEND / FRONTEND

---

### Field 3: Overview

**Length:** 2-3 sentences maximum
**Audience:** Nigerian business owner
**Format:** Problem → System → Outcome

Write what the system does and who it is for. No technical language. No framework names. No stack details. This is the first thing a business owner reads — it must make them feel like this was built for their exact situation.

**BAD:**

> "A full-stack Next.js application with Prisma ORM and PostgreSQL that handles appointment scheduling and payment processing for service businesses."

**GOOD:**

> "Lagos service businesses were managing bookings through WhatsApp groups and paper diaries. Staff double-booked clients. Payments went untracked. This system handles everything — bookings, reminders, and payments — and runs in the background without the owner having to manage it."

---

### Field 4: Problem

**Length:** 2-3 sentences maximum
**Audience:** Nigerian business owner
**Format:** Describe the specific operational chaos before this system existed

Name the exact manual process that was failing. WhatsApp threads, Excel files, paper records, phone calls. Be specific about the mechanical bottleneck — double-booking, dropped messages, lost payments. Do not use random numbers or demand metrics. Describe the absolute chaos of the un-automated state.

**BAD:**

> "The business lacked an efficient system for managing their operations."

**GOOD:**

> "Every booking came through WhatsApp. Staff tracked them in a shared notebook that three people wrote in differently. Double-bookings happened constantly. The owner spent every Sunday reconciling payments manually — a pure manual grind that destroyed their weekend."

---

### Field 5: Infrastructure & Reliability

**Length:** 3-5 sentences
**Audience:** Mixed — business owner and developer
**Format:** How the system handles Nigerian infrastructure constraints and compliance

Describe the real technical resiliency of the system. Nigerian SMEs fear digitizing because of unreliable electricity and poor internet. Address this explicitly. How does the system handle a power cut? Does it sync data when internet returns? Is the data architecture explicitly compliant with the Nigeria Data Protection Act (NDPA) 2023? Be honest about how the system protects the business owner from local infrastructure failure.

---

### Field 6: Approach

**Length:** 4-6 sentences
**Audience:** Mixed — business owner and developer
**Format:** How the system was designed and why those decisions were made

Explain the key design decisions in plain language. Not "I used Redis for caching" but "Every action the owner takes — booking a client, sending a reminder — triggers automatically without them needing to do anything again." Include the trigger → action → outcome pattern where possible. Reference the integrations that matter most to business owners: WhatsApp, Paystack, Flutterwave, automated emails, SMS.

---

### Field 7: Results

**Length:** 2-4 sentences or bullet points
**Audience:** Nigerian business owner
**Format:** System Capabilities & Projected Outcomes — what the system physically prevents or automates

Because this is a System Blueprint, do not invent past client numbers. Instead, describe exactly what the system is mathematically capable of doing. What manual processes does it physically eliminate? Speak in system limits and absolutes.
**CRITICAL:** You must frame capabilities around "Payroll Efficiency" and "Admin Elimination." The goal is increasing business output without adding human headcount.

**BAD:**

> "The system significantly improved the business's operational efficiency and helped a client save 20 hours a week."

**GOOD:**

> "Staff never touch an invoice — the system follows up automatically every 3 days until paid. It mathematically eliminates double-booking by locking synced Google Calendar slots instantly. Capable of processing 50+ concurrent WhatsApp inquiries without human intervention."

---

### Field 8: Technologies

List every technology used. Pull from `package.json` and `.env`. Format as an array of strings.

---

### Field 9: Live URL

Pull from README or deployment config. If not available write `[ADD LIVE URL]`.

---

### Field 10: SolutionCategory

Based on the system's core functionality, select EXACTLY ONE of the following:
`BOOKING`, `PAYMENTS`, `MESSAGING`, `AI`, `DASHBOARD`, `WORKFLOW`.
If the system spans multiple, choose the primary business driver.

---

### Field 11: Golden Nuggets

After generating all portfolio fields, generate 3-5 Golden Nuggets. These are single sentences — under 200 characters each — that capture the most compelling, specific, human truth about this project. They feed the caption generator and the Knowledge Document. Format as a JSON array or a Markdown list.

**Rules for Golden Nuggets:**

- Never start with "I"
- Never use forbidden words — game-changer, revolutionary, seamless, innovative, etc.
- Must pass the competitor swap test — cannot belong to any other project
- Must reference a specific Nigerian business context — city, industry, or business type
- Emphasize "WhatsApp-Native", "No New Headcount", or "Zero Technical Skill Required" where applicable.
- Must sound like something a person would say out loud, not write in a press release

**Examples of good Golden Nuggets:**

- "A Lagos distributor was tracking 40+ retailer orders in a WhatsApp group. The system handles invoicing natively inside WhatsApp."
- "Nigerian service businesses lose bookings every week. This system locks Google Calendar slots automatically, requiring zero technical skill from the staff."
- "The hardest part of this build was not the payments integration. It was ensuring NDPA 2023 compliance for a clinic that handles highly sensitive patient records."

---

## Distribution Readiness Check

Before presenting the output, verify every item below. Mark each as PASS or FAIL. Fix every FAIL before presenting.

- [ ] Every field is complete — no blanks, only `[CONFIRM WITH ADEDAMOLA]` placeholders where real data is missing — PASS / FAIL
- [ ] Overview does not contain any technical language — no framework names, no database names — PASS / FAIL
- [ ] Infrastructure explicitly addresses how the system handles internet/power failure or NDPA 2023 compliance — PASS / FAIL
- [ ] Problem field describes a specific manual process, not a vague inefficiency — PASS / FAIL
- [ ] Results field contains at least one specific claim — not "improved efficiency" — PASS / FAIL
- [ ] All five Golden Nuggets pass the competitor swap test — PASS / FAIL
- [ ] No Golden Nugget starts with "I" — PASS / FAIL
- [ ] Nigerian business context appears in at least three fields — city, industry, or business type — PASS / FAIL
- [ ] Every sentence passes the reading aloud test — no press release language — PASS / FAIL
- [ ] No forbidden words anywhere in the output — PASS / FAIL

---

_PROJECT_BRIEF_RULES.md — Version 2026.1 — demoladevop.com_
_Run this after every project build. Feed the output into the portfolio dashboard, then run KNOWLEDGE_RULES.md for the full Knowledge Document._
_Cross-reference with KNOWLEDGE_RULES.md, brand-persona.md, and ANTI_AI_WRITING.md._
