# MedGuard AI demo

Local, synthetic-data medication safety workflow prototype. It includes role-aware dashboards, backend-checked demo sessions, patient-owned records, limited explainable screening, review workflows, and a feature coverage page.

## Run locally

Requires Python 3.10 or later. The backend and UI use the Python standard library; no package install is needed.

```powershell
python server.py
```

Open <http://127.0.0.1:8000>. The server binds to localhost and persists records in `medguard.sqlite3`. Set `PORT` to change the port or `MEDGUARD_DB` to change the SQLite path. For an HTTPS deployment behind a trusted TLS terminator, set `MEDGUARD_COOKIE_SECURE=1`. This demo is not hardened for internet-facing deployment.

## GitHub Pages preview

The GitHub Actions workflow publishes a static presentation preview at <https://sahithi2522.github.io/MedGuard-AI/> on every push to `main`. It contains the landing page and visual sections only; sign-in, dashboards, and interactive workflows require the local Python server. GitHub Pages does not run Python or provide a database.

The supplied `assetsmedical-background.mp4` is served as a muted, looping page background with a captured poster frame and subtle scroll parallax. The background respects the browser's reduced-motion preference.

The decorative TypeScript bundle is checked in as `decorations.js` and served by Python. To edit/rebuild its Lucide icons or animation layer, install Node.js/npm, then run:

```powershell
npm install
npm run build
```

`npm run typecheck` validates the TypeScript source without rebuilding.

## Demo accounts

All seeded synthetic dashboard accounts use password `12345678`:

| Role | Email |
| --- | --- |
| Patient | `patient@medguard.demo` |
| Doctor | `doctor@medguard.demo` |
| Pharmacist | `pharmacist@medguard.demo` |
| Administrator | `admin@medguard.demo` |
| Caregiver | `caregiver@medguard.demo` |

Public signup permits patient and caregiver only. Professional/admin roles are fixed demo accounts, not verified credentials. Use the patient workspace's Feature coverage link for the full 30-item implementation-status checklist.

## Implemented demo workflows

- Linked synthetic workflow for Alex Morgan: doctor/pharmacist review queues, doctor-entered medication records on the patient account, and caregiver-visible data only through seeded demo consent. Prescriptions are synthetic examples, not medical instructions.
- Salted PBKDF2-HMAC-SHA256 password hashes; random database-backed sessions; HttpOnly/SameSite cookies and eight-hour expiry; server-side role checks.
- SQLite persistence for users, medications, patient-entered allergies/conditions, checks, reports, review requests, schedules/adherence, appointments, scoped caregiver permissions, notifications, prescriptions, assistant history, and audit metadata.
- Explainable demo findings for exact duplicate ingredient text, incomplete records/instructions, and exact allergy-text matches. Findings include affected records, explanation, source status, uncertainty, and next step.
- Explicit `Unable to verify` results for interaction, drug-disease, and dose-risk assessment when validated reference rules are unavailable. A missing finding is not a safety result.
- What-If comparison against a baseline; simulated results are not saved as patient reports and are clearly marked preliminary.
- A graph view derived from real saved result records. Only exact duplicate-text edges are drawn; drug interaction edges are not invented.
- PDF/JPEG/PNG upload validation and private randomized file storage, followed by manual medication entry/confirmation. OCR/NLP is not configured.
- Simulated doctor/pharmacist review and appointments; scoped caregiver access with revocation; adherence logging; local in-app notifications; fixed, safety-bounded assistant responses.
- Patient JSON/CSV export, print-to-PDF, administrator aggregate counts and metadata audit view, responsive mobile layout, and a partial English/Telugu feature glossary.

## Clinical, integration, and production gaps

No licensed medication catalog, interaction or drug-disease dataset, dosage rule source, OCR engine, LLM retrieval system, real professional scheduling, timed notification delivery, full Telugu translation, or clinical validation is bundled. The checker cannot establish medicine identity, clinical equivalence, cross-reactivity, or safety. File storage is local, not encrypted object storage. Account recovery, email verification, MFA, rate limiting, production-grade logging, consent/legal authorization, and formal privacy/security review are not implemented. Do not enter real patient health data or use this demo for clinical decisions.

**MedGuard AI is an educational medication safety decision-support prototype. It is not a substitute for professional medical advice, diagnosis, or treatment. Medication analysis may be incomplete or uncertain. Consult a qualified healthcare professional for clinical decisions.**

## Validation

```powershell
python -m py_compile server.py
node --check features.js
```

`/api/health` reports local service status. Demo clinical findings are limited to the rules described above.
