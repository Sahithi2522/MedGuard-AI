from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("MEDGUARD_DB", ROOT / "medguard.sqlite3"))
UPLOAD_DIR = Path(os.environ.get("MEDGUARD_UPLOAD_DIR", ROOT / "private_uploads"))
COOKIE_SECURE = os.environ.get("MEDGUARD_COOKIE_SECURE", "0") == "1"
SESSION_SECONDS = 8 * 60 * 60
ROLES = {"patient", "doctor", "pharmacist", "admin", "caregiver"}
PUBLIC_ROLES = {"patient", "caregiver"}
PBKDF2_ROUNDS = 600_000
DEMO_PASSWORD = "12345678"


def connect_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return f"{salt.hex()}:{digest.hex()}"


def password_matches(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split(":", 1)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), PBKDF2_ROUNDS)
        return hmac.compare_digest(actual.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def initialize() -> None:
    with connect_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('patient','doctor','pharmacist','admin','caregiver')),
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                expires_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS medications (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                ingredient TEXT NOT NULL,
                strength TEXT NOT NULL DEFAULT '',
                schedule TEXT NOT NULL DEFAULT 'As prescribed',
                dose TEXT NOT NULL DEFAULT '',
                frequency TEXT NOT NULL DEFAULT '',
                route TEXT NOT NULL DEFAULT '',
                duration TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'Patient-entered',
                prescribed_by INTEGER REFERENCES users(id),
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS conditions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'Patient-entered',
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS allergies (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                ingredient TEXT NOT NULL,
                reaction TEXT NOT NULL DEFAULT '',
                severity TEXT NOT NULL DEFAULT 'Unknown',
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY,
                patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                requested_by INTEGER NOT NULL REFERENCES users(id),
                review_type TEXT NOT NULL CHECK(review_type IN ('doctor','pharmacist')),
                status TEXT NOT NULL DEFAULT 'Pending',
                note TEXT NOT NULL DEFAULT '',
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                message TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'system',
                is_read INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS safety_checks (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                inputs_json TEXT NOT NULL,
                results_json TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                medication_id INTEGER NOT NULL REFERENCES medications(id) ON DELETE CASCADE,
                time_label TEXT NOT NULL,
                reminder_enabled INTEGER NOT NULL DEFAULT 0,
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS adherence_logs (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                schedule_id INTEGER NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
                status TEXT NOT NULL CHECK(status IN ('taken','missed','skipped')),
                note TEXT NOT NULL DEFAULT '',
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY,
                patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                professional_role TEXT NOT NULL CHECK(professional_role IN ('doctor','pharmacist')),
                requested_for TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Requested',
                note TEXT NOT NULL DEFAULT '',
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS caregiver_consents (
                id INTEGER PRIMARY KEY,
                patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                caregiver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                permission TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at INTEGER NOT NULL,
                UNIQUE(patient_id, caregiver_id, permission)
            );
            CREATE TABLE IF NOT EXISTS prescriptions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                filename TEXT NOT NULL,
                storage_key TEXT NOT NULL DEFAULT '',
                content_type TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Needs manual review',
                extraction_json TEXT NOT NULL DEFAULT '{}',
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY,
                actor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                question TEXT NOT NULL,
                response TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS sessions_expiry_idx ON sessions(expires_at);
            CREATE INDEX IF NOT EXISTS medications_user_idx ON medications(user_id);
            CREATE INDEX IF NOT EXISTS reviews_status_idx ON reviews(status);
            CREATE INDEX IF NOT EXISTS safety_checks_user_idx ON safety_checks(user_id, created_at);
            CREATE INDEX IF NOT EXISTS audit_logs_created_idx ON audit_logs(created_at);
        """)
        notification_columns = {row[1] for row in db.execute("PRAGMA table_info(notifications)")}
        if "category" not in notification_columns:
            db.execute("ALTER TABLE notifications ADD COLUMN category TEXT NOT NULL DEFAULT 'system'")
        medication_columns = {row[1] for row in db.execute("PRAGMA table_info(medications)")}
        for column in ("dose", "frequency", "route", "duration"):
            if column not in medication_columns:
                db.execute(f"ALTER TABLE medications ADD COLUMN {column} TEXT NOT NULL DEFAULT ''")
        if "source" not in medication_columns:
            db.execute("ALTER TABLE medications ADD COLUMN source TEXT NOT NULL DEFAULT 'Patient-entered'")
        if "prescribed_by" not in medication_columns:
            db.execute("ALTER TABLE medications ADD COLUMN prescribed_by INTEGER REFERENCES users(id)")
        prescription_columns = {row[1] for row in db.execute("PRAGMA table_info(prescriptions)")}
        for column in ("storage_key", "content_type"):
            if column not in prescription_columns:
                db.execute(f"ALTER TABLE prescriptions ADD COLUMN {column} TEXT NOT NULL DEFAULT ''")
        demos = [
            ("Alex Morgan", "patient@medguard.demo", "patient"),
            ("Dr. Jordan Lee", "doctor@medguard.demo", "doctor"),
            ("Sam Rivera", "pharmacist@medguard.demo", "pharmacist"),
            ("Morgan Chen", "admin@medguard.demo", "admin"),
            ("Taylor Quinn", "caregiver@medguard.demo", "caregiver"),
        ]
        for name, email, role in demos:
            exists = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if not exists:
                cursor = db.execute(
                    "INSERT INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)",
                    (name, email, password_hash(DEMO_PASSWORD), role, int(time.time())),
                )
                if role == "patient":
                    db.execute("INSERT INTO medications(user_id,name,ingredient,strength,schedule,created_at) VALUES(?,?,?,?,?,?)",
                               (cursor.lastrowid, "Sample medicine A", "sample ingredient a", "10 mg", "Morning", int(time.time())))
            else:
                db.execute("UPDATE users SET password_hash=? WHERE id=?", (password_hash(DEMO_PASSWORD), exists["id"]))
        patient_id = db.execute("SELECT id FROM users WHERE email='patient@medguard.demo'").fetchone()["id"]
        doctor_id = db.execute("SELECT id FROM users WHERE email='doctor@medguard.demo'").fetchone()["id"]
        caregiver_id = db.execute("SELECT id FROM users WHERE email='caregiver@medguard.demo'").fetchone()["id"]
        seed_time = int(time.time())
        if not db.execute("SELECT 1 FROM medications WHERE user_id=? AND source='Synthetic doctor demo sample'", (patient_id,)).fetchone():
            db.execute(
                """INSERT INTO medications(user_id,name,ingredient,strength,schedule,dose,frequency,source,prescribed_by,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (patient_id, "Sample medicine B", "sample ingredient b", "Sample strength", "Demo only", "Demo only", "Demo only", "Synthetic doctor demo sample", doctor_id, seed_time),
            )
        for review_type in ("doctor", "pharmacist"):
            db.execute(
                """INSERT INTO reviews(patient_id,requested_by,review_type,status,note,created_at)
                   SELECT ?,?,?, 'Pending','Synthetic linked demo sample',?
                   WHERE NOT EXISTS (SELECT 1 FROM reviews WHERE patient_id=? AND review_type=?)""",
                (patient_id, patient_id, review_type, seed_time, patient_id, review_type),
            )
        for permission in ("medications", "schedule", "reports"):
            db.execute(
                """INSERT INTO caregiver_consents(patient_id,caregiver_id,permission,active,created_at)
                   SELECT ?,?,?,1,? WHERE NOT EXISTS
                   (SELECT 1 FROM caregiver_consents WHERE patient_id=? AND caregiver_id=? AND permission=?)""",
                (patient_id, caregiver_id, permission, seed_time, patient_id, caregiver_id, permission),
            )
        for professional_role in ("doctor", "pharmacist"):
            db.execute(
                """INSERT INTO appointments(patient_id,professional_role,requested_for,status,note,created_at)
                   SELECT ?,?,'Demo appointment','Requested','Synthetic linked demo sample',?
                   WHERE NOT EXISTS (SELECT 1 FROM appointments WHERE patient_id=? AND professional_role=? AND note='Synthetic linked demo sample')""",
                (patient_id, professional_role, seed_time, patient_id, professional_role),
            )
        for role in ("patient", "doctor", "pharmacist", "admin", "caregiver"):
            account = db.execute("SELECT id FROM users WHERE role=? ORDER BY id LIMIT 1", (role,)).fetchone()
            if account:
                db.execute(
                    """INSERT INTO notifications(user_id,message,category,created_at)
                       SELECT ?, 'Synthetic dashboard sample data is linked by patient review and consent.', 'demo', ?
                       WHERE NOT EXISTS (SELECT 1 FROM notifications WHERE user_id=? AND category='demo')""",
                    (account["id"], seed_time, account["id"]),
                )


def public_user(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "name": row["name"], "email": row["email"], "role": row["role"]}


def audit_event(db: sqlite3.Connection, actor_id: int, action: str, resource_type: str) -> None:
    db.execute("INSERT INTO audit_logs(actor_id,action,resource_type,created_at) VALUES(?,?,?,?)",
               (actor_id, action[:80], resource_type[:80], int(time.time())))


def analyze_medications(medications: list[dict], allergies: list[dict], conditions: list[dict]) -> dict:
    ingredients = [str(item.get("ingredient", "")).strip().casefold() for item in medications]
    duplicate_ingredients = sorted({value for value in ingredients if value and ingredients.count(value) > 1})
    alerts = []
    for ingredient in duplicate_ingredients:
        affected = [str(item.get("name", "Medicine")) for item in medications if str(item.get("ingredient", "")).strip().casefold() == ingredient]
        alerts.append({"category": "Duplicate ingredient", "severity": "Review", "medicines": affected, "patient_factor": "Ingredient text entered in the medication list", "explanation": f"The same active-ingredient text, {ingredient}, appears on more than one entered record. Confirm the packages; brand, formulation, and ingredient equivalence are not verified.", "evidence_source": "Patient-entered medication records", "verification_status": "Text match only", "uncertainty": "Product equivalence has not been confirmed.", "next_step": "Ask a pharmacist or prescriber to review the product labels."})
    incomplete_records = []
    for item in medications:
        name = str(item.get("name", "Unknown medicine"))
        ingredient = str(item.get("ingredient", "")).strip().casefold()
        if not ingredient:
            incomplete_records.append(name)
            alerts.append({"category": "Incomplete medicine record", "severity": "Unable to verify", "medicines": [name], "patient_factor": "Missing active ingredient", "explanation": "The active ingredient is not recorded, so ingredient-based screening cannot be performed.", "evidence_source": "Patient-entered medication records", "verification_status": "Incomplete", "uncertainty": "Medicine identity cannot be established from the available fields.", "next_step": "Confirm the medicine from its package or prescription with a healthcare professional."})
        if not item.get("dose") or not item.get("frequency"):
            alerts.append({"category": "Prescription completeness", "severity": "Unable to verify", "medicines": [name], "patient_factor": "Dose or frequency not recorded", "explanation": "Dose and frequency information is incomplete. This check cannot infer or validate instructions.", "evidence_source": "Patient-entered medication records", "verification_status": "Incomplete", "uncertainty": "No dose-limit reference or patient-specific dosing rules are configured.", "next_step": "Refer to the confirmed prescription and ask the prescriber or pharmacist about missing instructions."})
    for medication in medications:
        ingredient = str(medication.get("ingredient", "")).strip().casefold()
        for allergy in allergies:
            allergy_text = str(allergy.get("ingredient", "")).strip().casefold()
            if ingredient and allergy_text and ingredient == allergy_text:
                alerts.append({"category": "Possible allergy text match", "severity": "Unable to verify", "medicines": [str(medication.get("name", "Medicine"))], "patient_factor": f"Recorded allergy: {allergy.get('ingredient')}; reaction: {allergy.get('reaction') or 'not recorded'}", "explanation": "The entered active-ingredient text matches the entered allergy text. This text match does not establish an allergy or clinical cross-reactivity.", "evidence_source": "Patient-entered allergy and medication records", "verification_status": "Unverified text match", "uncertainty": "Reaction history and ingredient equivalence require professional review.", "next_step": "Contact a healthcare professional for review; do not change treatment based only on this automated flag."})
    if len(medications) > 1:
        alerts.append({"category": "Drug-drug interaction screening", "severity": "Unable to verify", "medicines": [str(item.get("name", "Medicine")) for item in medications], "patient_factor": "Multiple medication records", "explanation": "No interaction reference dataset is configured, so these medicines have not been assessed for interactions.", "evidence_source": "No verified interaction source configured", "verification_status": "Not assessed", "uncertainty": "Absence of a finding must not be interpreted as safety.", "next_step": "Ask a pharmacist or prescriber to check the complete medication list."})
    if medications and conditions:
        alerts.append({"category": "Drug-disease screening", "severity": "Unable to verify", "medicines": [str(item.get("name", "Medicine")) for item in medications], "patient_factor": ", ".join(str(item.get("name", "Condition")) for item in conditions), "explanation": "Recorded conditions are present, but no verified drug-disease rules are configured.", "evidence_source": "No verified drug-disease source configured", "verification_status": "Not assessed", "uncertainty": "No contraindication or precaution conclusion can be made.", "next_step": "Ask a prescriber or pharmacist to review medicines alongside the recorded conditions."})
    if medications:
        alerts.append({"category": "Dosage screening", "severity": "Unable to verify", "medicines": [str(item.get("name", "Medicine")) for item in medications], "patient_factor": "Patient-specific dosing factors and validated dose rules unavailable", "explanation": "Dosages are not compared with therapeutic limits because no validated dosage reference rules are configured.", "evidence_source": "No verified dosage source configured", "verification_status": "Not assessed", "uncertainty": "A dose cannot be considered usual or safe from this screening.", "next_step": "Follow the confirmed prescription and consult a qualified healthcare professional with dosing questions."})
    nodes = [{"id": index, "label": str(item.get("name", "Medicine")), "ingredient": str(item.get("ingredient", ""))} for index, item in enumerate(medications)]
    edges = []
    for ingredient in duplicate_ingredients:
        matches = [node["id"] for node in nodes if node["ingredient"].strip().casefold() == ingredient]
        for first in matches:
            for second in matches:
                if first < second:
                    edges.append({"source": first, "target": second, "category": "Duplicate ingredient"})
    return {"alerts": alerts, "duplicate_ingredients": duplicate_ingredients, "incomplete_records": incomplete_records, "network": {"nodes": nodes, "edges": edges}, "data_completeness": {"medication_records": len(medications), "allergies_recorded": len(allergies), "conditions_recorded": len(conditions)}, "reference_status": "No licensed clinical reference data configured", "disclaimer": "Automated screening summary only. Not a diagnosis, treatment recommendation, or assurance of safety."}


class Handler(BaseHTTPRequestHandler):
    server_version = "MedGuardDemo/1.0"

    def log_message(self, fmt: str, *args) -> None:
        # Avoid logging request bodies or patient-specific data.
        super().log_message(fmt, *args)

    def send_json(self, status: int, data: dict, headers: dict | None = None) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def read_json(self, max_size: int = 64_000) -> dict:
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size > max_size:
                raise ValueError("Request is too large")
            value = json.loads(self.rfile.read(size) or b"{}")
            if not isinstance(value, dict):
                raise ValueError("Expected a JSON object")
            return value
        except (ValueError, json.JSONDecodeError):
            raise ValueError("Invalid request data")

    def current_user(self):
        cookie = self.headers.get("Cookie", "")
        token = next((part.split("=", 1)[1] for part in cookie.split(";") if part.strip().startswith("mg_session=")), None)
        if not token:
            return None
        hashed = hashlib.sha256(token.encode()).hexdigest()
        with connect_db() as db:
            row = db.execute("SELECT users.* FROM sessions JOIN users ON users.id=sessions.user_id WHERE sessions.token_hash=? AND sessions.expires_at>?", (hashed, int(time.time()))).fetchone()
            return row

    def require_user(self, roles: set[str] | None = None):
        user = self.current_user()
        if not user:
            self.send_json(401, {"error": "Please sign in to continue."})
            return None
        if roles and user["role"] not in roles:
            self.send_json(403, {"error": "Your account does not have permission for this action."})
            return None
        return user

    def do_GET(self) -> None:
        route = urlparse(self.path).path
        if route == "/api/health":
            return self.send_json(200, {"ok": True, "mode": "synthetic demo"})
        if route == "/api/auth/me":
            user = self.current_user()
            return self.send_json(200, {"user": public_user(user) if user else None})
        if route == "/api/dashboard":
            user = self.require_user()
            if not user:
                return
            with connect_db() as db:
                if user["role"] == "patient":
                    medication_count = db.execute("SELECT count(*) FROM medications WHERE user_id=?", (user["id"],)).fetchone()[0]
                    review_count = db.execute("SELECT count(*) FROM reviews WHERE patient_id=? AND status='Pending'", (user["id"],)).fetchone()[0]
                    check_count = db.execute("SELECT count(*) FROM safety_checks WHERE user_id=?", (user["id"],)).fetchone()[0]
                    medications = [dict(row) for row in db.execute("SELECT medications.id,medications.name,medications.ingredient,medications.strength,medications.schedule,medications.dose,medications.frequency,medications.source,COALESCE(prescriber.name,'') AS prescriber_name FROM medications LEFT JOIN users AS prescriber ON prescriber.id=medications.prescribed_by WHERE medications.user_id=? ORDER BY medications.id DESC", (user["id"],))]
                    return self.send_json(200, {"metrics": {"medications": medication_count, "pending_reviews": review_count, "checks": check_count, "alerts": 0}, "medications": medications, "reviews": [dict(row) for row in db.execute("SELECT id,review_type,status,created_at FROM reviews WHERE patient_id=? ORDER BY id DESC LIMIT 8", (user["id"],))]})
                if user["role"] in {"doctor", "pharmacist"}:
                    kind = user["role"]
                    reviews = [dict(row) for row in db.execute("SELECT reviews.id,reviews.review_type,reviews.status,reviews.created_at,users.name AS patient_name FROM reviews JOIN users ON users.id=reviews.patient_id WHERE reviews.review_type=? ORDER BY reviews.id DESC LIMIT 20", (kind,))]
                    patients = []
                    patient_rows = db.execute("SELECT DISTINCT users.id,users.name FROM reviews JOIN users ON users.id=reviews.patient_id WHERE reviews.review_type=? AND users.role='patient' ORDER BY users.name", (kind,)).fetchall()
                    for patient in patient_rows:
                        patient_reviews = [dict(row) for row in db.execute("SELECT id,status,created_at FROM reviews WHERE patient_id=? AND review_type=? ORDER BY id DESC", (patient["id"], kind))]
                        patient_medications = [dict(row) for row in db.execute("SELECT medications.id,medications.name,medications.ingredient,medications.strength,medications.schedule,medications.dose,medications.frequency,medications.source,COALESCE(prescriber.name,'') AS prescriber_name FROM medications LEFT JOIN users AS prescriber ON prescriber.id=medications.prescribed_by WHERE medications.user_id=? ORDER BY medications.id DESC", (patient["id"],))]
                        patients.append({"id": patient["id"], "name": patient["name"], "reviews": patient_reviews, "medications": patient_medications})
                    pending = sum(1 for item in reviews if item["status"] == "Pending")
                    return self.send_json(200, {"metrics": {"pending_reviews": pending, "completed_reviews": len(reviews)-pending, "patients": len(patients), "alerts": 0}, "reviews": reviews, "patients": patients})
                if user["role"] == "admin":
                    counts = {"users": db.execute("SELECT count(*) FROM users").fetchone()[0], "patients": db.execute("SELECT count(*) FROM users WHERE role='patient'").fetchone()[0], "reviews": db.execute("SELECT count(*) FROM reviews").fetchone()[0], "medications": db.execute("SELECT count(*) FROM medications").fetchone()[0]}
                    return self.send_json(200, {"metrics": counts, "recent_users": [dict(row) for row in db.execute("SELECT id,name,email,role,created_at FROM users ORDER BY id DESC LIMIT 12")]})
                if user["role"] == "caregiver":
                    dependents = db.execute("SELECT count(DISTINCT patient_id) FROM caregiver_consents WHERE caregiver_id=? AND active=1", (user["id"],)).fetchone()[0]
                    reminders = db.execute("SELECT count(DISTINCT schedules.id) FROM schedules JOIN caregiver_consents ON caregiver_consents.patient_id=schedules.user_id WHERE caregiver_consents.caregiver_id=? AND caregiver_consents.permission='schedule' AND caregiver_consents.active=1", (user["id"],)).fetchone()[0]
                    return self.send_json(200, {"metrics": {"dependents": dependents, "reminders": reminders}, "reviews": []})
                return self.send_json(200, {"metrics": {"dependents": 0, "reminders": 0}, "reviews": []})
        if route == "/api/reviews":
            user = self.require_user()
            if not user:
                return
            with connect_db() as db:
                if user["role"] == "patient":
                    rows = db.execute("SELECT id,review_type,status,note,created_at FROM reviews WHERE patient_id=? ORDER BY id DESC", (user["id"],)).fetchall()
                elif user["role"] in {"doctor", "pharmacist"}:
                    rows = db.execute("SELECT reviews.id,reviews.review_type,reviews.status,reviews.note,reviews.created_at,users.name AS patient_name FROM reviews JOIN users ON users.id=reviews.patient_id WHERE reviews.review_type=? ORDER BY reviews.id DESC", (user["role"],)).fetchall()
                else:
                    return self.send_json(403, {"error": "Review access is not enabled for this role."})
            return self.send_json(200, {"reviews": [dict(row) for row in rows]})
        if route == "/api/profile":
            user = self.require_user({"patient"})
            if not user:
                return
            with connect_db() as db:
                medications = [dict(row) for row in db.execute("SELECT medications.id,medications.name,medications.ingredient,medications.strength,medications.schedule,medications.dose,medications.frequency,medications.route,medications.duration,medications.source,COALESCE(prescriber.name,'') AS prescriber_name,medications.created_at FROM medications LEFT JOIN users AS prescriber ON prescriber.id=medications.prescribed_by WHERE medications.user_id=? ORDER BY medications.id DESC", (user["id"],))]
                allergies = [dict(row) for row in db.execute("SELECT id,ingredient,reaction,severity,created_at FROM allergies WHERE user_id=? ORDER BY id DESC", (user["id"],))]
                conditions = [dict(row) for row in db.execute("SELECT id,name,source,created_at FROM conditions WHERE user_id=? ORDER BY id DESC", (user["id"],))]
                audit_event(db, user["id"], "view_profile", "patient_profile")
            return self.send_json(200, {"medications": medications, "allergies": allergies, "conditions": conditions, "verification": "patient-entered"})
        if route == "/api/caregiver-consents":
            user = self.require_user({"patient"})
            if not user:
                return
            with connect_db() as db:
                consents = [dict(row) for row in db.execute("SELECT caregiver_consents.id,users.name AS caregiver_name,users.email,caregiver_consents.permission,caregiver_consents.active,caregiver_consents.created_at FROM caregiver_consents JOIN users ON users.id=caregiver_consents.caregiver_id WHERE caregiver_consents.patient_id=? ORDER BY caregiver_consents.id DESC", (user["id"],))]
                audit_event(db, user["id"], "view_caregiver_permissions", "caregiver_consent")
            return self.send_json(200, {"consents": consents})
        if route == "/api/safety/history" or route == "/api/reports":
            user = self.require_user({"patient"})
            if not user:
                return
            with connect_db() as db:
                rows = db.execute("SELECT id,results_json,created_at FROM safety_checks WHERE user_id=? ORDER BY id DESC LIMIT 50", (user["id"],)).fetchall()
            return self.send_json(200, {"checks": [{"id": row["id"], "results": json.loads(row["results_json"]), "created_at": row["created_at"]} for row in rows]})
        if route.startswith("/api/reports/"):
            user = self.require_user({"patient"})
            if not user:
                return
            report_id = route.rsplit("/", 1)[-1]
            with connect_db() as db:
                row = db.execute("SELECT id,results_json,created_at FROM safety_checks WHERE id=? AND user_id=?", (report_id, user["id"])).fetchone()
            if not row:
                return self.send_json(404, {"error": "Safety report not found."})
            return self.send_json(200, {"id": row["id"], "results": json.loads(row["results_json"]), "created_at": row["created_at"], "disclaimer": "Automated screening summary; not a diagnosis or treatment recommendation."})
        if route == "/api/schedules":
            user = self.require_user({"patient"})
            if not user:
                return
            with connect_db() as db:
                rows = db.execute("SELECT schedules.id,schedules.time_label,schedules.reminder_enabled,medications.name,medications.dose,medications.frequency FROM schedules JOIN medications ON medications.id=schedules.medication_id WHERE schedules.user_id=? ORDER BY schedules.id DESC", (user["id"],)).fetchall()
            return self.send_json(200, {"schedules": [dict(row) for row in rows]})
        if route == "/api/appointments":
            user = self.require_user()
            if not user:
                return
            if user["role"] == "patient":
                query, args = "SELECT id,professional_role,requested_for,status,note,created_at FROM appointments WHERE patient_id=? ORDER BY id DESC", (user["id"],)
            elif user["role"] in {"doctor", "pharmacist"}:
                query, args = "SELECT id,professional_role,requested_for,status,note,created_at FROM appointments WHERE professional_role=? ORDER BY id DESC", (user["role"],)
            else:
                return self.send_json(403, {"error": "Appointment access is not enabled for this role."})
            with connect_db() as db:
                rows = db.execute(query, args).fetchall()
            return self.send_json(200, {"appointments": [dict(row) for row in rows]})
        if route == "/api/caregiver/dependents":
            user = self.require_user({"caregiver"})
            if not user:
                return
            with connect_db() as db:
                consents = db.execute("SELECT caregiver_consents.patient_id,caregiver_consents.permission,users.name FROM caregiver_consents JOIN users ON users.id=caregiver_consents.patient_id WHERE caregiver_consents.caregiver_id=? AND caregiver_consents.active=1", (user["id"],)).fetchall()
                dependents = []
                for consent in consents:
                    entry = {"patient_id": consent["patient_id"], "name": consent["name"], "permission": consent["permission"]}
                    if consent["permission"] in {"medications", "schedule"}:
                        entry["medications"] = [dict(row) for row in db.execute("SELECT medications.name,medications.strength,medications.schedule,medications.source,COALESCE(prescriber.name,'') AS prescriber_name FROM medications LEFT JOIN users AS prescriber ON prescriber.id=medications.prescribed_by WHERE medications.user_id=?", (consent["patient_id"],))]
                    if consent["permission"] == "schedule":
                        entry["schedules"] = [dict(row) for row in db.execute("SELECT schedules.id,schedules.time_label,medications.name,medications.dose,medications.frequency FROM schedules JOIN medications ON medications.id=schedules.medication_id WHERE schedules.user_id=?", (consent["patient_id"],))]
                    elif consent["permission"] == "reports":
                        entry["reports"] = [{"id": row["id"], "created_at": row["created_at"], "results": json.loads(row["results_json"])} for row in db.execute("SELECT id,created_at,results_json FROM safety_checks WHERE user_id=? ORDER BY id DESC LIMIT 20", (consent["patient_id"],))]
                    audit_event(db, user["id"], "view_authorized_dependent_data", "caregiver_consent")
                    dependents.append(entry)
            return self.send_json(200, {"dependents": dependents})
        if route == "/api/notifications":
            user = self.require_user()
            if not user:
                return
            with connect_db() as db:
                rows = db.execute("SELECT id,message,category,is_read,created_at FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 100", (user["id"],)).fetchall()
            return self.send_json(200, {"notifications": [dict(row) for row in rows]})
        if route == "/api/prescriptions":
            user = self.require_user({"patient"})
            if not user:
                return
            with connect_db() as db:
                rows = db.execute("SELECT id,filename,status,created_at FROM prescriptions WHERE user_id=? ORDER BY id DESC", (user["id"],)).fetchall()
            return self.send_json(200, {"prescriptions": [dict(row) for row in rows], "ocr_available": False})
        if route.startswith("/api/prescriptions/") and route.endswith("/file"):
            user = self.require_user({"patient"})
            if not user:
                return
            prescription_id = route.split("/")[3]
            with connect_db() as db:
                record = db.execute("SELECT filename,storage_key,content_type FROM prescriptions WHERE id=? AND user_id=?", (prescription_id, user["id"])).fetchone()
                if record:
                    audit_event(db, user["id"], "view_prescription", "prescription_document")
            if not record or not record["storage_key"]:
                return self.send_json(404, {"error": "Prescription file not found."})
            path = (UPLOAD_DIR / record["storage_key"]).resolve()
            if path.parent != UPLOAD_DIR.resolve() or not path.is_file():
                return self.send_json(404, {"error": "Prescription file not found."})
            content = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", record["content_type"])
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Content-Disposition", "inline")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            return self.wfile.write(content)
        if route == "/api/evidence":
            user = self.require_user()
            if not user:
                return
            return self.send_json(200, {"configured": False, "sources": [], "message": "No licensed clinical evidence source is configured. Clinical interaction, disease, dose-limit, and therapeutic-duplication rules are unavailable."})
        if route == "/api/admin/analytics":
            user = self.require_user({"admin"})
            if not user:
                return
            with connect_db() as db:
                metrics = {"users": db.execute("SELECT count(*) FROM users").fetchone()[0], "medications": db.execute("SELECT count(*) FROM medications").fetchone()[0], "safety_checks": db.execute("SELECT count(*) FROM safety_checks").fetchone()[0], "reviews": db.execute("SELECT count(*) FROM reviews").fetchone()[0], "appointments": db.execute("SELECT count(*) FROM appointments").fetchone()[0]}
            return self.send_json(200, {"aggregate_metrics": metrics, "patient_details_included": False})
        if route == "/api/admin/audit-logs":
            user = self.require_user({"admin"})
            if not user:
                return
            with connect_db() as db:
                rows = db.execute("SELECT audit_logs.id,users.role AS actor_role,audit_logs.action,audit_logs.resource_type,audit_logs.created_at FROM audit_logs LEFT JOIN users ON users.id=audit_logs.actor_id ORDER BY audit_logs.id DESC LIMIT 200").fetchall()
            return self.send_json(200, {"audit_logs": [dict(row) for row in rows]})
        return self.serve_file(route)

    def serve_file(self, route: str) -> None:
        if route == "/features.js":
            path = ROOT / "features.js"
            content_type = "application/javascript; charset=utf-8"
        elif route == "/decorations.js":
            path = ROOT / "decorations.js"
            content_type = "application/javascript; charset=utf-8"
        elif route == "/assetsmedical-background.mp4":
            path = ROOT / "assetsmedical-background.mp4"
            content_type = "video/mp4"
        elif route in {"/", "/index.html"}:
            path = ROOT / "index.html"
            content_type = "text/html; charset=utf-8"
        else:
            return self.send_json(404, {"error": "Page not found."})
        content = path.read_bytes()
        if content_type == "video/mp4":
            range_header = self.headers.get("Range", "")
            byte_range = range_header.removeprefix("bytes=").split("-", 1) if range_header.startswith("bytes=") else []
            if byte_range:
                try:
                    start = int(byte_range[0] or 0)
                    end = min(int(byte_range[1]) if byte_range[1] else len(content) - 1, len(content) - 1)
                except ValueError:
                    return self.send_json(416, {"error": "Invalid video byte range."})
                if start > end or start >= len(content):
                    self.send_response(416)
                    self.send_header("Content-Range", f"bytes */{len(content)}")
                    self.end_headers()
                    return
                content = content[start:end + 1]
                self.send_response(206)
                self.send_header("Content-Range", f"bytes {start}-{end}/{path.stat().st_size}")
            else:
                self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Cache-Control", "public, max-age=3600")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            return self.wfile.write(content)
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        route = urlparse(self.path).path
        try:
            data = self.read_json(7_100_000 if route == "/api/prescriptions" else 64_000)
            if route == "/api/auth/register":
                name, email, password, role = (str(data.get(k, "")).strip() for k in ("name", "email", "password", "role"))
                if not name or len(name) > 100 or "@" not in email or len(email) > 200 or len(password) < 10 or role not in PUBLIC_ROLES:
                    return self.send_json(400, {"error": "Enter a name, valid email, password of at least 10 characters, and choose patient or caregiver."})
                with connect_db() as db:
                    try:
                        db.execute("INSERT INTO users(name,email,password_hash,role,created_at) VALUES(?,?,?,?,?)", (name, email, password_hash(password), role, int(time.time())))
                    except sqlite3.IntegrityError:
                        return self.send_json(409, {"error": "An account with that email already exists."})
                return self.login(email, password)
            if route == "/api/auth/login":
                email, password = str(data.get("email", "")).strip(), str(data.get("password", ""))
                with connect_db() as db:
                    user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
                if not user or not password_matches(password, user["password_hash"]):
                    return self.send_json(401, {"error": "Email or password is incorrect."})
                return self.create_session(user)
            if route == "/api/auth/logout":
                cookie = self.headers.get("Cookie", "")
                token = next((part.split("=", 1)[1] for part in cookie.split(";") if part.strip().startswith("mg_session=")), None)
                if token:
                    with connect_db() as db:
                        db.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),))
                return self.send_json(200, {"ok": True}, {"Set-Cookie": "mg_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"})
            if route == "/api/prescriptions":
                user = self.require_user({"patient"})
                if not user:
                    return
                filename = Path(str(data.get("filename", ""))).name
                extension = Path(filename).suffix.lower()
                encoded = str(data.get("content_base64", ""))
                if not filename or extension not in {".pdf", ".png", ".jpg", ".jpeg"} or not encoded:
                    return self.send_json(400, {"error": "Upload a PDF, PNG, or JPEG prescription file."})
                try:
                    content = base64.b64decode(encoded, validate=True)
                except ValueError:
                    return self.send_json(400, {"error": "The uploaded file data is invalid."})
                if not content or len(content) > 5_000_000:
                    return self.send_json(413, {"error": "Prescription files must be smaller than 5 MB."})
                signatures = {".pdf": content.startswith(b"%PDF-"), ".png": content.startswith(b"\x89PNG\r\n\x1a\n"), ".jpg": content.startswith(b"\xff\xd8\xff"), ".jpeg": content.startswith(b"\xff\xd8\xff")}
                if not signatures[extension]:
                    return self.send_json(400, {"error": "The file contents do not match the selected file type."})
                content_type = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}[extension]
                storage_key = secrets.token_hex(24) + extension
                UPLOAD_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
                (UPLOAD_DIR / storage_key).write_bytes(content)
                with connect_db() as db:
                    cursor = db.execute("INSERT INTO prescriptions(user_id,filename,storage_key,content_type,status,created_at) VALUES(?,?,?,?,?,?)", (user["id"], filename[:200], storage_key, content_type, "Stored; OCR unavailable; manual review required", int(time.time())))
                    audit_event(db, user["id"], "upload_prescription", "prescription_document")
                    prescription_id = cursor.lastrowid
                return self.send_json(201, {"id": prescription_id, "status": "Stored; OCR unavailable; manual review required", "ocr_available": False})
            if route == "/api/schedules":
                user = self.require_user({"patient"})
                if not user:
                    return
                medication_id = data.get("medication_id")
                time_label = str(data.get("time_label", "")).strip()
                if not time_label or len(time_label) > 80:
                    return self.send_json(400, {"error": "Enter a schedule label or time."})
                with connect_db() as db:
                    medication = db.execute("SELECT id FROM medications WHERE id=? AND user_id=?", (medication_id, user["id"])).fetchone()
                    if not medication:
                        return self.send_json(404, {"error": "Medication record not found."})
                    cursor = db.execute("INSERT INTO schedules(user_id,medication_id,time_label,reminder_enabled,created_at) VALUES(?,?,?,?,?)", (user["id"], medication_id, time_label, int(bool(data.get("reminder_enabled"))), int(time.time())))
                    if data.get("reminder_enabled"):
                        db.execute("INSERT INTO notifications(user_id,message,category,created_at) VALUES(?,?,?,?)", (user["id"], "A reminder preference is set. This demo does not deliver timed notifications.", "reminder", int(time.time())))
                    audit_event(db, user["id"], "create_schedule", "medication_schedule")
                return self.send_json(201, {"id": cursor.lastrowid, "reminders_delivered": False})
            if route == "/api/adherence":
                user = self.require_user({"patient"})
                if not user:
                    return
                try:
                    schedule_id = int(data.get("schedule_id"))
                except (TypeError, ValueError):
                    return self.send_json(400, {"error": "Choose a valid schedule."})
                status = str(data.get("status", ""))
                if status not in {"taken", "missed", "skipped"}:
                    return self.send_json(400, {"error": "Choose taken, missed, or skipped."})
                with connect_db() as db:
                    schedule = db.execute("SELECT id FROM schedules WHERE id=? AND user_id=?", (schedule_id, user["id"])).fetchone()
                    if not schedule:
                        return self.send_json(404, {"error": "Schedule not found."})
                    db.execute("INSERT INTO adherence_logs(user_id,schedule_id,status,note,created_at) VALUES(?,?,?,?,?)", (user["id"], schedule_id, status, str(data.get("note", ""))[:500], int(time.time())))
                    audit_event(db, user["id"], "record_adherence", "adherence_log")
                return self.send_json(201, {"ok": True})
            if route == "/api/caregiver/adherence":
                user = self.require_user({"caregiver"})
                if not user:
                    return
                try:
                    schedule_id = int(data.get("schedule_id"))
                except (TypeError, ValueError):
                    return self.send_json(400, {"error": "Choose a valid schedule."})
                status = str(data.get("status", ""))
                if status not in {"taken", "missed", "skipped"}:
                    return self.send_json(400, {"error": "Choose taken, missed, or skipped."})
                with connect_db() as db:
                    schedule = db.execute("SELECT schedules.id,schedules.user_id FROM schedules JOIN caregiver_consents ON caregiver_consents.patient_id=schedules.user_id WHERE schedules.id=? AND caregiver_consents.caregiver_id=? AND caregiver_consents.permission='schedule' AND caregiver_consents.active=1", (schedule_id, user["id"])).fetchone()
                    if not schedule:
                        return self.send_json(403, {"error": "No active schedule permission for this record."})
                    db.execute("INSERT INTO adherence_logs(user_id,schedule_id,status,note,created_at) VALUES(?,?,?,?,?)", (schedule["user_id"], schedule_id, status, str(data.get("note", ""))[:500], int(time.time())))
                    audit_event(db, user["id"], "record_dependent_adherence", "adherence_log")
                return self.send_json(201, {"ok": True})
            if route == "/api/appointments":
                user = self.require_user({"patient"})
                if not user:
                    return
                professional_role = str(data.get("professional_role", ""))
                if professional_role not in {"doctor", "pharmacist"}:
                    return self.send_json(400, {"error": "Choose a doctor or pharmacist review."})
                requested_for = str(data.get("requested_for", "")).strip()[:80]
                with connect_db() as db:
                    cursor = db.execute("INSERT INTO appointments(patient_id,professional_role,requested_for,note,created_at) VALUES(?,?,?,?,?)", (user["id"], professional_role, requested_for, str(data.get("note", ""))[:500], int(time.time())))
                    db.execute("INSERT INTO notifications(user_id,message,category,created_at) VALUES(?,?,?,?)", (user["id"], "Your simulated professional appointment request was recorded.", "appointment", int(time.time())))
                    audit_event(db, user["id"], "request_appointment", "appointment")
                return self.send_json(201, {"id": cursor.lastrowid, "status": "Requested", "real_professional_scheduling": False})
            if route.startswith("/api/appointments/") and route.endswith("/cancel"):
                user = self.require_user({"patient"})
                if not user:
                    return
                appointment_id = route.split("/")[3]
                with connect_db() as db:
                    result = db.execute("UPDATE appointments SET status='Cancelled' WHERE id=? AND patient_id=? AND status='Requested'", (appointment_id, user["id"]))
                    if not result.rowcount:
                        return self.send_json(404, {"error": "Cancelable appointment request not found."})
                    audit_event(db, user["id"], "cancel_appointment", "appointment")
                return self.send_json(200, {"ok": True})
            if route.startswith("/api/caregiver-consents/") and route.endswith("/revoke"):
                user = self.require_user({"patient"})
                if not user:
                    return
                consent_id = route.split("/")[3]
                with connect_db() as db:
                    result = db.execute("UPDATE caregiver_consents SET active=0 WHERE id=? AND patient_id=?", (consent_id, user["id"]))
                    if not result.rowcount:
                        return self.send_json(404, {"error": "Caregiver permission not found."})
                    audit_event(db, user["id"], "revoke_caregiver_access", "caregiver_consent")
                return self.send_json(200, {"ok": True})
            if route == "/api/caregiver-consents":
                user = self.require_user({"patient"})
                if not user:
                    return
                email = str(data.get("email", "")).strip()
                permission = str(data.get("permission", ""))
                if permission not in {"medications", "schedule", "reports"}:
                    return self.send_json(400, {"error": "Choose a permission scope."})
                with connect_db() as db:
                    caregiver = db.execute("SELECT id FROM users WHERE email=? AND role='caregiver'", (email,)).fetchone()
                    if not caregiver:
                        return self.send_json(404, {"error": "No caregiver demo account matches that email."})
                    cursor = db.execute("INSERT INTO caregiver_consents(patient_id,caregiver_id,permission,active,created_at) VALUES(?,?,?,1,?) ON CONFLICT(patient_id,caregiver_id,permission) DO UPDATE SET active=1", (user["id"], caregiver["id"], permission, int(time.time())))
                    audit_event(db, user["id"], "grant_caregiver_access", "caregiver_consent")
                return self.send_json(201, {"ok": True})
            if route.startswith("/api/notifications/") and route.endswith("/read"):
                user = self.require_user()
                if not user:
                    return
                notification_id = route.split("/")[3]
                with connect_db() as db:
                    result = db.execute("UPDATE notifications SET is_read=1 WHERE id=? AND user_id=?", (notification_id, user["id"]))
                    if not result.rowcount:
                        return self.send_json(404, {"error": "Notification not found."})
                return self.send_json(200, {"ok": True})
            if route == "/api/chat":
                user = self.require_user()
                if not user:
                    return
                question = str(data.get("question", "")).strip()[:1000]
                if not question:
                    return self.send_json(400, {"error": "Enter a question."})
                lowered = question.casefold()
                if any(term in lowered for term in ("emergency", "can't breathe", "chest pain", "overdose")):
                    response = "If this may be an emergency, contact local emergency services or poison control now. This prototype cannot assess urgent symptoms."
                elif any(term in lowered for term in ("interaction", "safe together", "combine")):
                    response = "No verified interaction reference is connected to this demo. It cannot determine whether medicines are safe together; ask a pharmacist or prescriber to review the complete list."
                elif any(term in lowered for term in ("allergy", "allergic")):
                    response = "The demo can compare entered ingredient text with recorded allergy text only. A text match is not a diagnosis or proof of cross-reactivity. Please ask a healthcare professional."
                elif any(term in lowered for term in ("duplicate", "ingredient")):
                    response = "The limited checker compares exact active-ingredient text in your entered records. It does not confirm product identity, formulation, or therapeutic equivalence."
                else:
                    response = "I can explain this demo's duplicate-text check and its limitations, but I do not have verified medicine references or patient-specific clinical advice."
                with connect_db() as db:
                    db.execute("INSERT INTO chat_messages(user_id,question,response,created_at) VALUES(?,?,?,?)", (user["id"], question, response, int(time.time())))
                return self.send_json(200, {"response": response, "grounded_sources": [], "assistant_mode": "Fixed safety FAQ; no LLM or clinical references configured"})
            if route.startswith("/api/patients/") and route.endswith("/medications"):
                user = self.require_user({"doctor"})
                if not user:
                    return
                try:
                    patient_id = int(route.split("/")[3])
                except (IndexError, ValueError):
                    return self.send_json(404, {"error": "Linked patient not found."})
                name = str(data.get("name", "")).strip()
                ingredient = str(data.get("ingredient", "")).strip()
                if not name or not ingredient or len(name) > 120 or len(ingredient) > 120:
                    return self.send_json(400, {"error": "Medicine name and active ingredient are required."})
                with connect_db() as db:
                    linked_patient = db.execute("SELECT id FROM users WHERE id=? AND role='patient'", (patient_id,)).fetchone()
                    active_review = db.execute("SELECT 1 FROM reviews WHERE patient_id=? AND review_type='doctor' AND status IN ('Pending','In review')", (patient_id,)).fetchone()
                    if not linked_patient or not active_review:
                        return self.send_json(404, {"error": "An active doctor review is required for this patient."})
                    cursor = db.execute(
                        """INSERT INTO medications(user_id,name,ingredient,strength,schedule,dose,frequency,route,duration,source,prescribed_by,created_at)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (patient_id, name, ingredient.casefold(), str(data.get("strength", ""))[:40], str(data.get("schedule", "As prescribed"))[:80], str(data.get("dose", ""))[:60], str(data.get("frequency", ""))[:60], str(data.get("route", ""))[:60], str(data.get("duration", ""))[:60], "Doctor-prescribed (demo)", user["id"], int(time.time())),
                    )
                    db.execute("INSERT INTO notifications(user_id,message,category,created_at) VALUES(?,?,?,?)", (patient_id, f"{user['name']} added {name} to your medication list. Confirm details with your healthcare professional.", "medication", int(time.time())))
                    audit_event(db, user["id"], "prescribe_demo_medication", "medication")
                return self.send_json(201, {"ok": True, "id": cursor.lastrowid, "patient_id": patient_id, "source": "Doctor-prescribed (demo)"})
            if route == "/api/medications":
                user = self.require_user({"patient"})
                if not user:
                    return
                name = str(data.get("name", "")).strip()
                ingredient = str(data.get("ingredient", "")).strip()
                if not name or not ingredient or len(name) > 120 or len(ingredient) > 120:
                    return self.send_json(400, {"error": "Medicine name and active ingredient are required."})
                with connect_db() as db:
                    cursor = db.execute("INSERT INTO medications(user_id,name,ingredient,strength,schedule,dose,frequency,route,duration,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)", (user["id"], name, ingredient.casefold(), str(data.get("strength", ""))[:40], str(data.get("schedule", "As prescribed"))[:80], str(data.get("dose", ""))[:60], str(data.get("frequency", ""))[:60], str(data.get("route", ""))[:60], str(data.get("duration", ""))[:60], int(time.time())))
                    audit_event(db, user["id"], "create_medication", "medication")
                return self.send_json(201, {"ok": True, "id": cursor.lastrowid})
            if route in {"/api/safety/check", "/api/safety/simulate"}:
                user = self.require_user({"patient", "doctor", "pharmacist"})
                if not user:
                    return
                supplied = data.get("medications")
                if supplied is not None and (not isinstance(supplied, list) or len(supplied) > 50):
                    return self.send_json(400, {"error": "Provide no more than 50 medicine records."})
                baseline_result = None
                with connect_db() as db:
                    if user["role"] == "patient":
                        names = [dict(row) for row in db.execute("SELECT name,ingredient,strength,dose,frequency,route,duration FROM medications WHERE user_id=?", (user["id"],))]
                        proposed = data.get("proposed_medicine")
                        if proposed and isinstance(proposed, dict):
                            if route == "/api/safety/simulate":
                                baseline_result = analyze_medications(names, [dict(row) for row in db.execute("SELECT ingredient,reaction,severity FROM allergies WHERE user_id=?", (user["id"],))], [dict(row) for row in db.execute("SELECT name FROM conditions WHERE user_id=?", (user["id"],))])
                            names.append(proposed)
                        allergies = [dict(row) for row in db.execute("SELECT ingredient,reaction,severity FROM allergies WHERE user_id=?", (user["id"],))]
                        conditions = [dict(row) for row in db.execute("SELECT name FROM conditions WHERE user_id=?", (user["id"],))]
                    else:
                        names = supplied or []
                        allergies = data.get("allergies", []) if isinstance(data.get("allergies", []), list) else []
                        conditions = data.get("conditions", []) if isinstance(data.get("conditions", []), list) else []
                    if len(names) > 50:
                        return self.send_json(400, {"error": "Provide no more than 50 medicine records."})
                    result = analyze_medications(names, allergies, conditions)
                    if route == "/api/safety/check":
                        check_cursor = db.execute("INSERT INTO safety_checks(user_id,inputs_json,results_json,created_at) VALUES(?,?,?,?)", (user["id"], json.dumps({"medication_count": len(names)}), json.dumps(result), int(time.time())))
                        check_id = check_cursor.lastrowid
                        audit_event(db, user["id"], "run_safety_check", "safety_check")
                        db.execute("INSERT INTO notifications(user_id,message,category,created_at) VALUES(?,?,?,?)", (user["id"], "A medication screening summary is ready. Review the uncertainty and source status.", "safety_report", int(time.time())))
                    else:
                        check_id = None
                        result["simulated"] = True
                        result["simulation_notice"] = "Preliminary simulation only; proposed medication has not been approved."
                        result["baseline"] = baseline_result
                if check_id is not None:
                    result["check_id"] = check_id
                return self.send_json(200, result)
            if route in {"/api/profile/allergies", "/api/profile/conditions"}:
                user = self.require_user({"patient"})
                if not user:
                    return
                with connect_db() as db:
                    if route.endswith("allergies"):
                        ingredient = str(data.get("ingredient", "")).strip()
                        if not ingredient or len(ingredient) > 120:
                            return self.send_json(400, {"error": "Enter an allergy ingredient or substance name."})
                        db.execute("INSERT INTO allergies(user_id,ingredient,reaction,severity,created_at) VALUES(?,?,?,?,?)", (user["id"], ingredient, str(data.get("reaction", ""))[:250], str(data.get("severity", "Unknown"))[:40], int(time.time())))
                        action, resource = "create_allergy", "allergy"
                    else:
                        name = str(data.get("name", "")).strip()
                        if not name or len(name) > 120:
                            return self.send_json(400, {"error": "Enter a condition name."})
                        db.execute("INSERT INTO conditions(user_id,name,created_at) VALUES(?,?,?)", (user["id"], name, int(time.time())))
                        action, resource = "create_condition", "condition"
                    audit_event(db, user["id"], action, resource)
                return self.send_json(201, {"ok": True})
            if route == "/api/reviews":
                user = self.require_user({"patient"})
                if not user:
                    return
                review_type = str(data.get("review_type", ""))
                if review_type not in {"doctor", "pharmacist"}:
                    return self.send_json(400, {"error": "Choose a doctor or pharmacist review."})
                with connect_db() as db:
                    cursor = db.execute("INSERT INTO reviews(patient_id,requested_by,review_type,created_at) VALUES(?,?,?,?)", (user["id"], user["id"], review_type, int(time.time())))
                    db.execute("INSERT INTO notifications(user_id,message,category,created_at) VALUES(?,?,?,?)", (user["id"], f"Your {review_type} review request was recorded.", "review", int(time.time())))
                    audit_event(db, user["id"], "request_professional_review", "review")
                return self.send_json(201, {"id": cursor.lastrowid, "status": "Pending"})
            if route.startswith("/api/reviews/") and route.endswith("/status"):
                user = self.require_user({"doctor", "pharmacist"})
                if not user:
                    return
                review_id = route.split("/")[3]
                status = str(data.get("status", ""))
                if status not in {"In review", "Completed", "Escalated"}:
                    return self.send_json(400, {"error": "Choose a valid review status."})
                with connect_db() as db:
                    if "note" in data:
                        result = db.execute("UPDATE reviews SET status=?,note=? WHERE id=? AND review_type=?", (status, str(data["note"])[:2000], review_id, user["role"]))
                    else:
                        result = db.execute("UPDATE reviews SET status=? WHERE id=? AND review_type=?", (status, review_id, user["role"]))
                    if not result.rowcount:
                        return self.send_json(404, {"error": "Review not found."})
                    audit_event(db, user["id"], "update_professional_review", "review")
                return self.send_json(200, {"ok": True})
            if route == "/api/schedules":
                user = self.require_user({"patient"})
                if not user:
                    return
                try:
                    medication_id = int(data.get("medication_id"))
                except (TypeError, ValueError):
                    return self.send_json(400, {"error": "Choose a saved medication."})
                time_label = str(data.get("time_label", "")).strip()
                if not time_label or len(time_label) > 80:
                    return self.send_json(400, {"error": "Enter a schedule label or time."})
                with connect_db() as db:
                    if not db.execute("SELECT id FROM medications WHERE id=? AND user_id=?", (medication_id, user["id"])).fetchone():
                        return self.send_json(404, {"error": "Medication record not found."})
                    cursor = db.execute("INSERT INTO schedules(user_id,medication_id,time_label,reminder_enabled,created_at) VALUES(?,?,?,?,?)", (user["id"], medication_id, time_label, int(bool(data.get("reminder_enabled"))), int(time.time())))
                    if data.get("reminder_enabled"):
                        db.execute("INSERT INTO notifications(user_id,message,category,created_at) VALUES(?,?,?,?)", (user["id"], "A reminder preference is set. This demo does not deliver timed notifications.", "reminder", int(time.time())))
                    audit_event(db, user["id"], "create_schedule", "medication_schedule")
                return self.send_json(201, {"id": cursor.lastrowid, "reminders_delivered": False})
            if route == "/api/adherence":
                user = self.require_user({"patient"})
                if not user:
                    return
                try:
                    schedule_id = int(data.get("schedule_id"))
                except (TypeError, ValueError):
                    return self.send_json(400, {"error": "Choose a valid schedule."})
                status = str(data.get("status", ""))
                if status not in {"taken", "missed", "skipped"}:
                    return self.send_json(400, {"error": "Choose taken, missed, or skipped."})
                with connect_db() as db:
                    if not db.execute("SELECT id FROM schedules WHERE id=? AND user_id=?", (schedule_id, user["id"])).fetchone():
                        return self.send_json(404, {"error": "Schedule not found."})
                    db.execute("INSERT INTO adherence_logs(user_id,schedule_id,status,note,created_at) VALUES(?,?,?,?,?)", (user["id"], schedule_id, status, str(data.get("note", ""))[:500], int(time.time())))
                    audit_event(db, user["id"], "record_adherence", "adherence_log")
                return self.send_json(201, {"ok": True})
            if route == "/api/appointments":
                user = self.require_user({"patient"})
                if not user:
                    return
                professional_role = str(data.get("professional_role", ""))
                if professional_role not in {"doctor", "pharmacist"}:
                    return self.send_json(400, {"error": "Choose a doctor or pharmacist."})
                with connect_db() as db:
                    cursor = db.execute("INSERT INTO appointments(patient_id,professional_role,requested_for,note,created_at) VALUES(?,?,?,?,?)", (user["id"], professional_role, str(data.get("requested_for", ""))[:80], str(data.get("note", ""))[:500], int(time.time())))
                    db.execute("INSERT INTO notifications(user_id,message,category,created_at) VALUES(?,?,?,?)", (user["id"], "Your simulated professional review request was recorded.", "appointment", int(time.time())))
                    audit_event(db, user["id"], "request_appointment", "appointment")
                return self.send_json(201, {"id": cursor.lastrowid, "status": "Requested", "real_professional_scheduling": False})
            if route.startswith("/api/appointments/") and route.endswith("/cancel"):
                user = self.require_user({"patient"})
                if not user:
                    return
                appointment_id = route.split("/")[3]
                with connect_db() as db:
                    result = db.execute("UPDATE appointments SET status='Cancelled' WHERE id=? AND patient_id=? AND status='Requested'", (appointment_id, user["id"]))
                    if not result.rowcount:
                        return self.send_json(404, {"error": "Cancelable request not found."})
                    audit_event(db, user["id"], "cancel_appointment", "appointment")
                return self.send_json(200, {"ok": True})
            if route.startswith("/api/appointments/") and route.endswith("/status"):
                user = self.require_user({"doctor", "pharmacist"})
                if not user:
                    return
                appointment_id = route.split("/")[3]
                status = str(data.get("status", ""))
                if status not in {"Confirmed", "Completed", "Cancelled"}:
                    return self.send_json(400, {"error": "Choose a valid appointment status."})
                with connect_db() as db:
                    result = db.execute("UPDATE appointments SET status=? WHERE id=? AND professional_role=?", (status, appointment_id, user["role"]))
                    if not result.rowcount:
                        return self.send_json(404, {"error": "Appointment request not found."})
                    audit_event(db, user["id"], "update_appointment_status", "appointment")
                return self.send_json(200, {"ok": True})
            if route.startswith("/api/caregiver-consents/") and route.endswith("/revoke"):
                user = self.require_user({"patient"})
                if not user:
                    return
                consent_id = route.split("/")[3]
                with connect_db() as db:
                    result = db.execute("UPDATE caregiver_consents SET active=0 WHERE id=? AND patient_id=?", (consent_id, user["id"]))
                    if not result.rowcount:
                        return self.send_json(404, {"error": "Caregiver permission not found."})
                    audit_event(db, user["id"], "revoke_caregiver_access", "caregiver_consent")
                return self.send_json(200, {"ok": True})
            if route == "/api/caregiver-consents":
                user = self.require_user({"patient"})
                if not user:
                    return
                email = str(data.get("email", "")).strip()
                permission = str(data.get("permission", ""))
                if permission not in {"medications", "schedule", "reports"}:
                    return self.send_json(400, {"error": "Choose a permission scope."})
                with connect_db() as db:
                    caregiver = db.execute("SELECT id FROM users WHERE email=? AND role='caregiver'", (email,)).fetchone()
                    if not caregiver:
                        return self.send_json(404, {"error": "No caregiver demo account matches that email."})
                    db.execute("INSERT INTO caregiver_consents(patient_id,caregiver_id,permission,active,created_at) VALUES(?,?,?,1,?) ON CONFLICT(patient_id,caregiver_id,permission) DO UPDATE SET active=1", (user["id"], caregiver["id"], permission, int(time.time())))
                    audit_event(db, user["id"], "grant_caregiver_access", "caregiver_consent")
                return self.send_json(201, {"ok": True})
            if route.startswith("/api/notifications/") and route.endswith("/read"):
                user = self.require_user()
                if not user:
                    return
                notification_id = route.split("/")[3]
                with connect_db() as db:
                    result = db.execute("UPDATE notifications SET is_read=1 WHERE id=? AND user_id=?", (notification_id, user["id"]))
                    if not result.rowcount:
                        return self.send_json(404, {"error": "Notification not found."})
                return self.send_json(200, {"ok": True})
            if route.startswith("/api/prescriptions/") and route.endswith("/confirm"):
                user = self.require_user({"patient"})
                if not user:
                    return
                prescription_id = route.split("/")[3]
                entries = data.get("medications", [])
                if not isinstance(entries, list) or len(entries) > 50 or any(not isinstance(item, dict) or not str(item.get("name", "")).strip() or not str(item.get("ingredient", "")).strip() for item in entries):
                    return self.send_json(400, {"error": "Each confirmed medicine needs a name and active ingredient."})
                with connect_db() as db:
                    if not db.execute("SELECT id FROM prescriptions WHERE id=? AND user_id=?", (prescription_id, user["id"])).fetchone():
                        return self.send_json(404, {"error": "Prescription not found."})
                    for item in entries:
                        db.execute("INSERT INTO medications(user_id,name,ingredient,strength,schedule,dose,frequency,route,duration,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)", (user["id"], str(item["name"]).strip()[:120], str(item["ingredient"]).strip().casefold()[:120], str(item.get("strength", ""))[:40], str(item.get("schedule", "As prescribed"))[:80], str(item.get("dose", ""))[:60], str(item.get("frequency", ""))[:60], str(item.get("route", ""))[:60], str(item.get("duration", ""))[:60], int(time.time())))
                    db.execute("UPDATE prescriptions SET status='User confirmed manual entry; OCR unavailable' WHERE id=? AND user_id=?", (prescription_id, user["id"]))
                    audit_event(db, user["id"], "confirm_manual_prescription_entries", "prescription")
                return self.send_json(200, {"ok": True, "created_records": len(entries), "automated_approval": False})
            if route == "/api/chat":
                user = self.require_user()
                if not user:
                    return
                question = str(data.get("question", "")).strip()[:1000]
                if not question:
                    return self.send_json(400, {"error": "Enter a question."})
                lowered = question.casefold()
                if any(term in lowered for term in ("emergency", "can't breathe", "chest pain", "overdose")):
                    response = "If this may be an emergency, contact local emergency services or poison control now. This prototype cannot assess urgent symptoms."
                elif any(term in lowered for term in ("interaction", "safe together", "combine")):
                    response = "No verified interaction reference is connected to this demo. It cannot determine whether medicines are safe together; ask a pharmacist or prescriber to review the complete list."
                elif any(term in lowered for term in ("allergy", "allergic")):
                    response = "The demo can compare entered ingredient text with recorded allergy text only. A text match is not a diagnosis or proof of cross-reactivity. Please ask a healthcare professional."
                elif any(term in lowered for term in ("duplicate", "ingredient")):
                    response = "The limited checker compares exact active-ingredient text in entered records. It does not confirm product identity, formulation, or therapeutic equivalence."
                else:
                    response = "I can explain this demo's duplicate-text check and limitations, but I do not have verified medicine references or patient-specific clinical advice."
                with connect_db() as db:
                    db.execute("INSERT INTO chat_messages(user_id,question,response,created_at) VALUES(?,?,?,?)", (user["id"], question, response, int(time.time())))
                return self.send_json(200, {"response": response, "grounded_sources": [], "assistant_mode": "Fixed safety FAQ; no LLM or clinical references configured"})
            if route == "/api/reviews":
                user = self.require_user({"patient"})
                if not user:
                    return
                review_type = str(data.get("review_type", ""))
                if review_type not in {"doctor", "pharmacist"}:
                    return self.send_json(400, {"error": "Choose a doctor or pharmacist review."})
                with connect_db() as db:
                    db.execute("INSERT INTO reviews(patient_id,requested_by,review_type,created_at) VALUES(?,?,?,?)", (user["id"], user["id"], review_type, int(time.time())))
                return self.send_json(201, {"ok": True})
            if route.startswith("/api/reviews/") and route.endswith("/status"):
                user = self.require_user({"doctor", "pharmacist"})
                if not user:
                    return
                review_id = route.split("/")[3]
                status = str(data.get("status", ""))
                if status not in {"In review", "Completed", "Escalated"}:
                    return self.send_json(400, {"error": "Choose a valid review status."})
                with connect_db() as db:
                    result = db.execute("UPDATE reviews SET status=?,note=? WHERE id=? AND review_type=?", (status, str(data.get("note", ""))[:2000], review_id, user["role"]))
                    if not result.rowcount:
                        return self.send_json(404, {"error": "Review not found."})
                return self.send_json(200, {"ok": True})
            return self.send_json(404, {"error": "Endpoint not found."})
        except ValueError as error:
            return self.send_json(400, {"error": str(error)})

    def login(self, email: str, password: str) -> None:
        with connect_db() as db:
            user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if not user or not password_matches(password, user["password_hash"]):
            return self.send_json(401, {"error": "Email or password is incorrect."})
        self.create_session(user)

    def create_session(self, user: sqlite3.Row) -> None:
        token = secrets.token_urlsafe(32)
        with connect_db() as db:
            db.execute("DELETE FROM sessions WHERE expires_at<=?", (int(time.time()),))
            db.execute("INSERT INTO sessions(token_hash,user_id,expires_at) VALUES(?,?,?)", (hashlib.sha256(token.encode()).hexdigest(), user["id"], int(time.time()) + SESSION_SECONDS))
        secure = "; Secure" if COOKIE_SECURE else ""
        self.send_json(200, {"user": public_user(user)}, {"Set-Cookie": f"mg_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={SESSION_SECONDS}{secure}"})


if __name__ == "__main__":
    initialize()
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "127.0.0.1")
    print(f"MedGuard AI demo listening on {host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
