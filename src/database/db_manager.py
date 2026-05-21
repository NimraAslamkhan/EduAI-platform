"""
Database Manager - SQLite initialization, schema, and all CRUD operations.
"""

import sqlite3
import hashlib
import os
import random
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), "../../../data/school.db")


class DatabaseManager:
    """Central manager for all SQLite database operations."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _hash_password(self, password: str) -> str:
        """Hash a password using PBKDF2-HMAC-SHA256 with a random salt.

        Format: pbkdf2$<iterations>$<salt_hex>$<hash_hex>
        For backwards compatibility, legacy SHA-256 hex strings (no prefix) are still accepted.
        """
        import hashlib, os
        iterations = 100000
        salt = os.urandom(16)
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations)
        return f"pbkdf2${iterations}${salt.hex()}${dk.hex()}"

    def verify_password(self, stored_hash: str, password: str) -> bool:
        """Verify a plaintext password against stored hash.

        Supports new PBKDF2 format and legacy plain SHA-256 hex.
        """
        import hashlib

        if not stored_hash:
            return False
        if stored_hash.startswith("pbkdf2$"):
            try:
                parts = stored_hash.split("$")
                _, iterations_s, salt_hex, hash_hex = parts
                iterations = int(iterations_s)
                salt = bytes.fromhex(salt_hex)
                expected = bytes.fromhex(hash_hex)
                dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations)
                import hmac
                return hmac.compare_digest(dk, expected)
            except Exception:
                return False
        else:
            # legacy SHA-256
            return hashlib.sha256(password.encode()).hexdigest() == stored_hash

    def initialize_database(self):
        """Create all tables if they don't exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Schools table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schools (
                    school_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT,
                    phone TEXT,
                    unique_school_id TEXT UNIQUE,
                    email TEXT,
                    established_year INTEGER,
                    logo_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Ensure unique_school_id column exists for older DBs
            cursor.execute("PRAGMA table_info(schools)")
            cols = [r[1] for r in cursor.fetchall()]
            if 'unique_school_id' not in cols:
                cursor.execute("ALTER TABLE schools ADD COLUMN unique_school_id TEXT")

            # Users table (all roles)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_id INTEGER,
                    full_name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('super_admin','principal','teacher','parent')),
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (school_id) REFERENCES schools(school_id)
                )
            """)

            # Classes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS classes (
                    class_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_id INTEGER NOT NULL,
                    class_name TEXT NOT NULL,
                    section TEXT NOT NULL,
                    academic_year TEXT NOT NULL,
                    teacher_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (school_id) REFERENCES schools(school_id),
                    FOREIGN KEY (teacher_id) REFERENCES users(user_id)
                )
            """)

            # Subjects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subjects (
                    subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_id INTEGER NOT NULL,
                    subject_name TEXT NOT NULL,
                    class_id INTEGER,
                    teacher_id INTEGER,
                    FOREIGN KEY (school_id) REFERENCES schools(school_id),
                    FOREIGN KEY (class_id) REFERENCES classes(class_id),
                    FOREIGN KEY (teacher_id) REFERENCES users(user_id)
                )
            """)

            # Teachers detail table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS teachers (
                    teacher_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    school_id INTEGER NOT NULL,
                    subject_expertise TEXT,
                    qualification TEXT,
                    experience_years INTEGER DEFAULT 0,
                    hire_date TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (school_id) REFERENCES schools(school_id)
                )
            """)

            # Students table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_id INTEGER NOT NULL,
                    class_id INTEGER,
                    parent_id INTEGER,
                    full_name TEXT NOT NULL,
                    age INTEGER,
                    gender TEXT,
                    address TEXT,
                    phone TEXT,
                    enrollment_date TEXT,
                    study_hours REAL DEFAULT 3.0,
                    status TEXT DEFAULT 'active' CHECK(status IN ('active','inactive','graduated')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (school_id) REFERENCES schools(school_id),
                    FOREIGN KEY (class_id) REFERENCES classes(class_id),
                    FOREIGN KEY (parent_id) REFERENCES users(user_id)
                )
            """)

            # Attendance table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    class_id INTEGER,
                    date TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('present','absent','late')),
                    marked_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(student_id),
                    FOREIGN KEY (marked_by) REFERENCES users(user_id)
                )
            """)

            # Marks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS marks (
                    mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    exam_type TEXT NOT NULL CHECK(exam_type IN ('mid_term','final','quiz','assignment')),
                    marks_obtained REAL NOT NULL,
                    total_marks REAL NOT NULL DEFAULT 100,
                    percentage REAL,
                    exam_date TEXT,
                    recorded_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(student_id),
                    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id),
                    FOREIGN KEY (recorded_by) REFERENCES users(user_id)
                )
            """)

            # Fees table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fees (
                    fee_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    fee_type TEXT NOT NULL CHECK(fee_type IN ('tuition','transport','library','lab','sports')),
                    amount REAL NOT NULL,
                    paid_amount REAL DEFAULT 0,
                    due_date TEXT,
                    paid_date TEXT,
                    status TEXT DEFAULT 'unpaid' CHECK(status IN ('paid','unpaid','partial')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(student_id)
                )
            """)

            # Notifications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_id INTEGER,
                    user_id INTEGER,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    type TEXT DEFAULT 'info' CHECK(type IN ('info','warning','alert','success')),
                    target_role TEXT,
                    is_read INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (school_id) REFERENCES schools(school_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

            # Ensure target_role column exists for older DBs
            cursor.execute("PRAGMA table_info(notifications)")
            notif_cols = [r[1] for r in cursor.fetchall()]
            if 'target_role' not in notif_cols:
                try:
                    cursor.execute("ALTER TABLE notifications ADD COLUMN target_role TEXT")
                except Exception:
                    pass

            # Assignments table (optional)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS assignments (
                    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_id INTEGER NOT NULL,
                    class_id INTEGER,
                    subject_id INTEGER,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date TEXT,
                    status TEXT DEFAULT 'open' CHECK(status IN ('open','submitted','graded')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (school_id) REFERENCES schools(school_id),
                    FOREIGN KEY (class_id) REFERENCES classes(class_id),
                    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
                )
            """)

            # AI Alerts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ai_alerts (
                    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_id INTEGER,
                    student_id INTEGER,
                    class_id INTEGER,
                    alert_type TEXT NOT NULL,
                    severity TEXT DEFAULT 'medium' CHECK(severity IN ('low','medium','high','critical')),
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    is_resolved INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (school_id) REFERENCES schools(school_id),
                    FOREIGN KEY (student_id) REFERENCES students(student_id),
                    FOREIGN KEY (class_id) REFERENCES classes(class_id)
                )
            """)

            # Password resets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS password_resets (
                    reset_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)

        logger.info("Database schema initialized")

    def seed_sample_data(self):
        """Seed the database with realistic sample data."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if already seeded
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] > 0:
                return

            logger.info("Seeding sample data...")

            # 1. School
            cursor.execute("""
                INSERT INTO schools (name, address, phone, email, established_year)
                VALUES (?, ?, ?, ?, ?)
            """, ("Green Valley Academy", "123 Education Lane, Knowledge City", "+1-555-0100",
                  "info@greenvalley.edu", 2005))
            school_id = cursor.lastrowid

            # 2. Users
            users_data = [
                (school_id, "System Administrator", "admin@school.com",
                 self._hash_password("admin123"), "super_admin"),
                (school_id, "Dr. Sarah Johnson", "principal@school.com",
                 self._hash_password("principal123"), "principal"),
                (school_id, "Mr. David Chen", "teacher@school.com",
                 self._hash_password("teacher123"), "teacher"),
                (school_id, "Mrs. Emily Rodriguez", "teacher2@school.com",
                 self._hash_password("teacher123"), "teacher"),
                (school_id, "Mr. James Wilson", "teacher3@school.com",
                 self._hash_password("teacher123"), "teacher"),
                (school_id, "Ms. Priya Patel", "teacher4@school.com",
                 self._hash_password("teacher123"), "teacher"),
                (school_id, "Mr. Ali Hassan", "teacher5@school.com",
                 self._hash_password("teacher123"), "teacher"),
                (school_id, "Michael Brown (Parent)", "parent@school.com",
                 self._hash_password("parent123"), "parent"),
                (school_id, "Jennifer Lee (Parent)", "parent2@school.com",
                 self._hash_password("parent123"), "parent"),
                (school_id, "Robert Taylor (Parent)", "parent3@school.com",
                 self._hash_password("parent123"), "parent"),
            ]
            cursor.executemany(
                "INSERT INTO users (school_id, full_name, email, password_hash, role) VALUES (?,?,?,?,?)",
                users_data
            )

            # Expenses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expenses (
                    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_id INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    amount REAL NOT NULL,
                    expense_date TEXT NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (school_id) REFERENCES schools(school_id)
                )
            """)

            # Salaries / payroll table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS salaries (
                    salary_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    school_id INTEGER NOT NULL,
                    month TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    paid_amount REAL DEFAULT 0,
                    status TEXT DEFAULT 'unpaid' CHECK(status IN ('paid','unpaid','partial')),
                    paid_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (school_id) REFERENCES schools(school_id)
                )
            """)

            # Get user IDs (teacher IDs start at index 2, parents at 7)
            cursor.execute("SELECT user_id, role FROM users ORDER BY user_id")
            all_users = cursor.fetchall()
            teacher_ids = [u["user_id"] for u in all_users if u["role"] == "teacher"]
            parent_ids = [u["user_id"] for u in all_users if u["role"] == "parent"]

            # 3. Teacher details
            teacher_details = [
                (teacher_ids[0], school_id, "Mathematics", "M.Sc Mathematics", 8, "2016-08-01"),
                (teacher_ids[1], school_id, "English", "MA English Literature", 5, "2019-01-15"),
                (teacher_ids[2], school_id, "Science", "M.Sc Physics", 12, "2012-06-01"),
                (teacher_ids[3], school_id, "Computer Science", "B.Tech CS", 3, "2021-09-01"),
                (teacher_ids[4], school_id, "History", "MA History", 7, "2017-03-10"),
            ]
            cursor.executemany(
                """INSERT INTO teachers (user_id, school_id, subject_expertise, qualification, experience_years, hire_date)
                   VALUES (?,?,?,?,?,?)""",
                teacher_details
            )

            # 4. Classes
            classes_data = [
                (school_id, "Class 6", "A", "2024-25", teacher_ids[0]),
                (school_id, "Class 7", "A", "2024-25", teacher_ids[1]),
                (school_id, "Class 7", "B", "2024-25", teacher_ids[2]),
                (school_id, "Class 8", "A", "2024-25", teacher_ids[3]),
                (school_id, "Class 8", "B", "2024-25", teacher_ids[4]),
                (school_id, "Class 9", "A", "2024-25", teacher_ids[0]),
            ]
            cursor.executemany(
                "INSERT INTO classes (school_id, class_name, section, academic_year, teacher_id) VALUES (?,?,?,?,?)",
                classes_data
            )
            cursor.execute("SELECT class_id FROM classes ORDER BY class_id")
            class_ids = [r["class_id"] for r in cursor.fetchall()]

            # 5. Subjects
            subject_names = ["Mathematics", "English", "Science", "Computer Science", "History", "Geography"]
            for class_id in class_ids:
                for i, subj in enumerate(subject_names):
                    tid = teacher_ids[i % len(teacher_ids)]
                    cursor.execute(
                        "INSERT INTO subjects (school_id, subject_name, class_id, teacher_id) VALUES (?,?,?,?)",
                        (school_id, subj, class_id, tid)
                    )

            cursor.execute("SELECT subject_id FROM subjects ORDER BY subject_id")
            subject_ids = [r["subject_id"] for r in cursor.fetchall()]

            # 6. Students (60 students across 6 classes)
            first_names_m = ["Ali", "James", "Carlos", "Ethan", "Noah", "Liam", "Omar", "Ryan",
                              "Kevin", "Daniel"]
            first_names_f = ["Fatima", "Emma", "Sofia", "Aisha", "Lily", "Maya", "Sara",
                              "Zoe", "Hannah", "Chloe"]
            last_names = ["Ahmed", "Johnson", "Garcia", "Williams", "Brown", "Taylor",
                          "Martinez", "Anderson", "Lee", "Wilson"]

            all_students = []
            for cls_idx, cls_id in enumerate(class_ids):
                parent_id = parent_ids[cls_idx % len(parent_ids)]
                for i in range(10):
                    gender = "Male" if i % 2 == 0 else "Female"
                    fname_list = first_names_m if gender == "Male" else first_names_f
                    name = f"{fname_list[i % len(fname_list)]} {last_names[i % len(last_names)]}"
                    age = 11 + cls_idx + random.randint(0, 1)
                    study_hours = round(random.uniform(1.5, 6.5), 1)
                    enrollment_date = f"2024-{random.randint(1,3):02d}-{random.randint(1,28):02d}"
                    all_students.append(
                        (school_id, cls_id, parent_id, name, age, gender,
                         "123 Main St", "+1-555-0200", enrollment_date, study_hours, "active")
                    )

            cursor.executemany(
                """INSERT INTO students (school_id, class_id, parent_id, full_name, age, gender,
                   address, phone, enrollment_date, study_hours, status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                all_students
            )

            cursor.execute("SELECT student_id, class_id FROM students ORDER BY student_id")
            students_data = cursor.fetchall()

            # 7. Attendance (last 60 days per student)
            today = datetime.now().date()
            attendance_records = []
            for student in students_data:
                sid = student["student_id"]
                # Each student has attendance pattern (some weak, some strong)
                base_attendance = random.uniform(0.55, 0.98)
                for days_ago in range(60):
                    date_val = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
                    # Skip weekends
                    d = today - timedelta(days=days_ago)
                    if d.weekday() >= 5:
                        continue
                    rand = random.random()
                    if rand < base_attendance:
                        status = "present"
                    elif rand < base_attendance + 0.05:
                        status = "late"
                    else:
                        status = "absent"
                    attendance_records.append((sid, student["class_id"], date_val, status, teacher_ids[0]))

            cursor.executemany(
                "INSERT INTO attendance (student_id, class_id, date, status, marked_by) VALUES (?,?,?,?,?)",
                attendance_records
            )

            # 8. Marks (3 exams per student per subject)
            marks_records = []
            for student in students_data:
                sid = student["student_id"]
                cls_id = student["class_id"]
                class_subjects = [s for idx, s in enumerate(subject_ids) if idx % len(class_ids) == class_ids.index(cls_id) % len(class_ids)]
                if not class_subjects:
                    class_subjects = subject_ids[:6]

                # Randomly assign student performance profile
                perf_profile = random.choice(["high", "medium", "low"])
                if perf_profile == "high":
                    base_score = random.uniform(72, 95)
                elif perf_profile == "medium":
                    base_score = random.uniform(50, 72)
                else:
                    base_score = random.uniform(25, 52)

                for subj_id in class_subjects[:6]:
                    for exam_type in ["mid_term", "final", "quiz"]:
                        variance = random.uniform(-10, 10)
                        obtained = max(0, min(100, base_score + variance))
                        total = 100
                        exam_date = (today - timedelta(days=random.randint(5, 90))).strftime("%Y-%m-%d")
                        marks_records.append(
                            (sid, subj_id, exam_type, round(obtained, 1), total,
                             round(obtained, 1), exam_date, teacher_ids[0])
                        )

            cursor.executemany(
                """INSERT INTO marks (student_id, subject_id, exam_type, marks_obtained, total_marks,
                   percentage, exam_date, recorded_by) VALUES (?,?,?,?,?,?,?,?)""",
                marks_records
            )

            # 9. Fees
            fee_records = []
            for student in students_data:
                sid = student["student_id"]
                for fee_type, amount in [("tuition", 1200), ("transport", 200), ("library", 50)]:
                    paid = random.choice([amount, 0, amount // 2])
                    status = "paid" if paid >= amount else ("partial" if paid > 0 else "unpaid")
                    due_date = (today + timedelta(days=random.randint(-30, 60))).strftime("%Y-%m-%d")
                    paid_date = today.strftime("%Y-%m-%d") if status == "paid" else None
                    fee_records.append((sid, fee_type, amount, paid, due_date, paid_date, status))

            cursor.executemany(
                """INSERT INTO fees (student_id, fee_type, amount, paid_amount, due_date, paid_date, status)
                   VALUES (?,?,?,?,?,?,?)""",
                fee_records
            )

            # 10. AI Alerts
            alert_templates = [
                ("attendance_drop", "high", "Attendance Alert",
                 "Attendance dropped below 60% this month. Immediate intervention required."),
                ("low_performance", "high", "Academic Performance Alert",
                 "Average score below 40%. Student at high risk of failure."),
                ("fee_overdue", "medium", "Fee Overdue Notice",
                 "School fees are overdue for more than 30 days."),
                ("attendance_warning", "medium", "Attendance Warning",
                 "Student attendance between 60-70%. Parent notification recommended."),
                ("class_performance", "medium", "Class Performance Decline",
                 "Class average dropped 15% compared to previous month."),
                ("dropout_risk", "critical", "Dropout Risk Detected",
                 "Multiple risk factors detected. Immediate counseling recommended."),
            ]

            for idx, student in enumerate(students_data[:15]):
                alert = alert_templates[idx % len(alert_templates)]
                cursor.execute(
                    """INSERT INTO ai_alerts (school_id, student_id, class_id, alert_type, severity, title, message)
                       VALUES (?,?,?,?,?,?,?)""",
                    (school_id, student["student_id"], student["class_id"],
                     alert[0], alert[1], alert[2], alert[3])
                )

            # 11. Notifications
            notif_data = [
                (school_id, None, "System Online", "EduAI Platform is now active and monitoring all students.", "success"),
                (school_id, None, "Mid-Term Results Ready", "Mid-term examination results have been uploaded.", "info"),
                (school_id, None, "Attendance Review", "Monthly attendance review completed. Check reports.", "warning"),
                (school_id, None, "Fee Reminder", "Quarterly fee collection deadline is approaching.", "alert"),
            ]
            cursor.executemany(
                "INSERT INTO notifications (school_id, user_id, title, message, type) VALUES (?,?,?,?,?)",
                notif_data
            )

        logger.info("Sample data seeded successfully")

    # ==================== USER REGISTRATION ====================

    def email_exists(self, email: str) -> bool:
        """Check if an email is already registered."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE email = ?", (email.strip().lower(),))
            return cursor.fetchone() is not None

    def register_user(self, full_name: str, email: str, password: str, role: str,
                      school_name: str = "", unique_school_id: str = None, phone: str = "", school_id: int = None) -> dict:
        """Register a new user. Returns dict with success/error."""
        try:
            email = email.strip().lower()
            if self.email_exists(email):
                return {"success": False, "error": "Email already registered. Please sign in."}

            password_hash = self._hash_password(password)

            with self.get_connection() as conn:
                cursor = conn.cursor()

                # If a specific school_id is provided, use it
                if school_id:
                    school_id = int(school_id)
                    cursor.execute("SELECT school_id FROM schools WHERE school_id = ?", (school_id,))
                    if not cursor.fetchone():
                        raise ValueError("Provided school_id does not exist")

                # If a unique_school_id is provided, try to create or find that school
                school_id = None
                if unique_school_id:
                    uid = unique_school_id.strip()
                    # Check if school with same unique id exists
                    cursor.execute("SELECT school_id FROM schools WHERE unique_school_id = ?", (uid,))
                    r = cursor.fetchone()
                    if r:
                        school_id = r["school_id"]
                    else:
                        # create new school record
                        sname = school_name.strip() or f"School {uid}"
                        cursor.execute(
                            "INSERT INTO schools (name, unique_school_id, email) VALUES (?,?,?)",
                            (sname, uid, email)
                        )
                        school_id = cursor.lastrowid
                # Fallback: if no school selected/created, pick first existing school or create default
                if not school_id:
                    cursor.execute("SELECT school_id FROM schools LIMIT 1")
                    row = cursor.fetchone()
                    if row:
                        school_id = row["school_id"]
                    else:
                        sname = school_name.strip() or "EduAI School"
                        cursor.execute(
                            "INSERT INTO schools (name, email) VALUES (?,?)",
                            (sname, email)
                        )
                        school_id = cursor.lastrowid

                cursor.execute(
                    "INSERT INTO users (school_id, full_name, email, password_hash, role) VALUES (?,?,?,?,?)",
                    (school_id, full_name.strip(), email, password_hash, role)
                )
                user_id = cursor.lastrowid

                # If teacher, add teacher record too
                if role == "teacher":
                    cursor.execute(
                        "INSERT INTO teachers (user_id, school_id, subject_expertise, qualification, experience_years, hire_date) VALUES (?,?,?,?,?,date('now'))",
                        (user_id, school_id, "General", "Not specified", 0)
                    )

                conn.commit()

                # Return user dict for immediate login
                cursor.execute("""
                    SELECT u.*, s.name as school_name, s.unique_school_id
                    FROM users u
                    LEFT JOIN schools s ON u.school_id = s.school_id
                    WHERE u.user_id = ?
                """, (user_id,))
                return {"success": True, "user": dict(cursor.fetchone())}

        except Exception as e:
            logger.error(f"Registration error: {e}")
            return {"success": False, "error": f"Registration failed: {e}"}

    # ==================== QUERY METHODS ====================

    def get_all_students(self, school_id: int = 1) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, c.class_name, c.section, u.full_name as parent_name
                FROM students s
                LEFT JOIN classes c ON s.class_id = c.class_id
                LEFT JOIN users u ON s.parent_id = u.user_id
                WHERE s.school_id = ? AND s.status = 'active'
                ORDER BY c.class_name, s.full_name
            """, (school_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_student_by_id(self, student_id: int) -> dict:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, c.class_name, c.section, u.full_name as parent_name
                FROM students s
                LEFT JOIN classes c ON s.class_id = c.class_id
                LEFT JOIN users u ON s.parent_id = u.user_id
                WHERE s.student_id = ?
            """, (student_id,))
            row = cursor.fetchone()
            return dict(row) if row else {}

    def get_students_by_parent(self, parent_id: int) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, c.class_name, c.section
                FROM students s
                LEFT JOIN classes c ON s.class_id = c.class_id
                WHERE s.parent_id = ?
            """, (parent_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_students_by_class(self, class_id: int) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, c.class_name, c.section
                FROM students s
                LEFT JOIN classes c ON s.class_id = c.class_id
                WHERE s.class_id = ?
                ORDER BY s.full_name
            """, (class_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_all_classes(self, school_id: int = 1) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, u.full_name as teacher_name,
                    (SELECT COUNT(*) FROM students s WHERE s.class_id = c.class_id AND s.status='active') as student_count
                FROM classes c
                LEFT JOIN users u ON c.teacher_id = u.user_id
                WHERE c.school_id = ?
                ORDER BY c.class_name, c.section
            """, (school_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_all_teachers(self, school_id: int = 1) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.user_id, u.full_name, u.email, u.created_at,
                       t.subject_expertise, t.qualification, t.experience_years, t.hire_date
                FROM users u
                LEFT JOIN teachers t ON u.user_id = t.user_id
                WHERE u.role = 'teacher' AND u.school_id = ?
            """, (school_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_student_marks(self, student_id: int) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.*, sub.subject_name
                FROM marks m
                JOIN subjects sub ON m.subject_id = sub.subject_id
                WHERE m.student_id = ?
                ORDER BY m.exam_date DESC
            """, (student_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_student_attendance(self, student_id: int, days: int = 30) -> list:
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM attendance
                WHERE student_id = ? AND date >= ?
                ORDER BY date DESC
            """, (student_id, cutoff))
            return [dict(r) for r in cursor.fetchall()]

    def get_attendance_rate(self, student_id: int, days: int = 30) -> float:
        records = self.get_student_attendance(student_id, days)
        if not records:
            return 0.0
        present = sum(1 for r in records if r["status"] in ("present", "late"))
        return round((present / len(records)) * 100, 1)

    def get_class_attendance_summary(self, school_id: int = 1, days: int = 30) -> list:
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.class_name || ' ' || c.section as class_label,
                    COUNT(a.attendance_id) as total_records,
                    SUM(CASE WHEN a.status IN ('present','late') THEN 1 ELSE 0 END) as present_count,
                    ROUND(100.0 * SUM(CASE WHEN a.status IN ('present','late') THEN 1 ELSE 0 END) / COUNT(a.attendance_id), 1) as attendance_rate
                FROM attendance a
                JOIN students s ON a.student_id = s.student_id
                JOIN classes c ON s.class_id = c.class_id
                WHERE s.school_id = ? AND a.date >= ?
                GROUP BY c.class_id
                ORDER BY attendance_rate
            """, (school_id, cutoff))
            return [dict(r) for r in cursor.fetchall()]

    def get_school_summary(self, school_id: int = 1) -> dict:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM students WHERE school_id=? AND status='active'", (school_id,))
            total_students = cursor.fetchone()["cnt"]

            cursor.execute("SELECT COUNT(*) as cnt FROM users WHERE school_id=? AND role='teacher'", (school_id,))
            total_teachers = cursor.fetchone()["cnt"]

            cursor.execute("SELECT COUNT(*) as cnt FROM classes WHERE school_id=?", (school_id,))
            total_classes = cursor.fetchone()["cnt"]

            # Overall attendance rate last 30 days
            cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            cursor.execute("""
                SELECT ROUND(100.0 * SUM(CASE WHEN a.status IN ('present','late') THEN 1 ELSE 0 END) / COUNT(*), 1) as rate
                FROM attendance a
                JOIN students s ON a.student_id = s.student_id
                WHERE s.school_id = ? AND a.date >= ?
            """, (school_id, cutoff))
            row = cursor.fetchone()
            attendance_rate = row["rate"] if row and row["rate"] else 0.0

            # Average marks
            cursor.execute("""
                SELECT ROUND(AVG(percentage), 1) as avg_marks
                FROM marks m
                JOIN students s ON m.student_id = s.student_id
                WHERE s.school_id = ?
            """, (school_id,))
            row = cursor.fetchone()
            avg_marks = row["avg_marks"] if row and row["avg_marks"] else 0.0

            # Alerts count
            cursor.execute("SELECT COUNT(*) as cnt FROM ai_alerts WHERE school_id=? AND is_resolved=0", (school_id,))
            active_alerts = cursor.fetchone()["cnt"]

            return {
                "total_students": total_students,
                "total_teachers": total_teachers,
                "total_classes": total_classes,
                "attendance_rate": attendance_rate,
                "avg_marks": avg_marks,
                "active_alerts": active_alerts,
            }

    def get_weak_students(self, school_id: int = 1, threshold: float = 50.0) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.student_id, s.full_name, c.class_name, c.section,
                    ROUND(AVG(m.percentage), 1) as avg_score
                FROM students s
                JOIN marks m ON s.student_id = m.student_id
                LEFT JOIN classes c ON s.class_id = c.class_id
                WHERE s.school_id = ?
                GROUP BY s.student_id
                HAVING avg_score < ?
                ORDER BY avg_score ASC
            """, (school_id, threshold))
            return [dict(r) for r in cursor.fetchall()]

    def get_top_students(self, school_id: int = 1, limit: int = 10) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.student_id, s.full_name, c.class_name, c.section,
                    ROUND(AVG(m.percentage), 1) as avg_score
                FROM students s
                JOIN marks m ON s.student_id = m.student_id
                LEFT JOIN classes c ON s.class_id = c.class_id
                WHERE s.school_id = ?
                GROUP BY s.student_id
                ORDER BY avg_score DESC
                LIMIT ?
            """, (school_id, limit))
            return [dict(r) for r in cursor.fetchall()]

    def get_ai_alerts(self, school_id: int = 1, resolved: bool = False) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT al.*, s.full_name as student_name, c.class_name
                FROM ai_alerts al
                LEFT JOIN students s ON al.student_id = s.student_id
                LEFT JOIN classes c ON al.class_id = c.class_id
                WHERE al.school_id = ? AND al.is_resolved = ?
                ORDER BY al.created_at DESC
            """, (school_id, 1 if resolved else 0))
            return [dict(r) for r in cursor.fetchall()]

    def resolve_alert(self, alert_id: int):
        with self.get_connection() as conn:
            conn.execute("UPDATE ai_alerts SET is_resolved=1 WHERE alert_id=?", (alert_id,))

    def add_student(self, school_id: int, class_id: int, parent_id, full_name: str,
                    age: int, gender: str, address: str, phone: str, study_hours: float) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO students (school_id, class_id, parent_id, full_name, age, gender,
                    address, phone, enrollment_date, study_hours, status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (school_id, class_id, parent_id, full_name, age, gender, address, phone,
                  datetime.now().strftime("%Y-%m-%d"), study_hours, "active"))
            return cursor.lastrowid

    def update_student(self, student_id: int, **kwargs):
        allowed = {"full_name", "age", "gender", "address", "phone", "study_hours",
                   "class_id", "status"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return
        set_clause = ", ".join(f"{k}=?" for k in updates)
        values = list(updates.values()) + [student_id]
        with self.get_connection() as conn:
            conn.execute(f"UPDATE students SET {set_clause} WHERE student_id=?", values)

    def delete_student(self, student_id: int):
        with self.get_connection() as conn:
            conn.execute("UPDATE students SET status='inactive' WHERE student_id=?", (student_id,))

    def add_marks(self, student_id: int, subject_id: int, exam_type: str,
                  marks_obtained: float, total_marks: float, exam_date: str, recorded_by: int):
        percentage = round((marks_obtained / total_marks) * 100, 1)
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO marks (student_id, subject_id, exam_type, marks_obtained, total_marks,
                    percentage, exam_date, recorded_by)
                VALUES (?,?,?,?,?,?,?,?)
            """, (student_id, subject_id, exam_type, marks_obtained, total_marks,
                  percentage, exam_date, recorded_by))

    def add_attendance(self, student_id: int, class_id: int, date: str,
                       status: str, marked_by: int):
        with self.get_connection() as conn:
            # Check if already exists
            cursor = conn.cursor()
            cursor.execute(
                "SELECT attendance_id FROM attendance WHERE student_id=? AND date=?",
                (student_id, date)
            )
            if cursor.fetchone():
                conn.execute(
                    "UPDATE attendance SET status=? WHERE student_id=? AND date=?",
                    (status, student_id, date)
                )
            else:
                conn.execute(
                    "INSERT INTO attendance (student_id, class_id, date, status, marked_by) VALUES (?,?,?,?,?)",
                    (student_id, class_id, date, status, marked_by)
                )

    def get_performance_data_for_ml(self, school_id: int = 1) -> list:
        """Get data formatted for ML pipeline."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    s.student_id,
                    s.age,
                    s.gender,
                    s.study_hours,
                    c.class_name,
                    ROUND(AVG(m.percentage), 1) as avg_score,
                    ROUND(100.0 * SUM(CASE WHEN a.status IN ('present','late') THEN 1 ELSE 0 END) /
                        NULLIF(COUNT(DISTINCT a.attendance_id), 0), 1) as attendance_rate
                FROM students s
                LEFT JOIN marks m ON s.student_id = m.student_id
                LEFT JOIN attendance a ON s.student_id = a.student_id
                LEFT JOIN classes c ON s.class_id = c.class_id
                WHERE s.school_id = ? AND s.status = 'active'
                GROUP BY s.student_id
                HAVING avg_score IS NOT NULL
            """, (school_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_subject_performance(self, school_id: int = 1) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sub.subject_name,
                    ROUND(AVG(m.percentage), 1) as avg_score,
                    COUNT(m.mark_id) as total_records,
                    SUM(CASE WHEN m.percentage < 40 THEN 1 ELSE 0 END) as failing_count
                FROM marks m
                JOIN subjects sub ON m.subject_id = sub.subject_id
                JOIN students s ON m.student_id = s.student_id
                WHERE s.school_id = ?
                GROUP BY sub.subject_name
                ORDER BY avg_score
            """, (school_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_attendance_trend(self, school_id: int = 1, days: int = 30) -> list:
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT a.date,
                    COUNT(*) as total,
                    SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present_count,
                    ROUND(100.0 * SUM(CASE WHEN a.status IN ('present','late') THEN 1 ELSE 0 END) / COUNT(*), 1) as rate
                FROM attendance a
                JOIN students s ON a.student_id = s.student_id
                WHERE s.school_id = ? AND a.date >= ?
                GROUP BY a.date
                ORDER BY a.date
            """, (school_id, cutoff))
            return [dict(r) for r in cursor.fetchall()]

    def get_fee_summary(self, school_id: int = 1) -> dict:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    SUM(f.amount) as total_expected,
                    SUM(f.paid_amount) as total_collected,
                    SUM(CASE WHEN f.status='unpaid' THEN f.amount ELSE 0 END) as total_pending,
                    COUNT(CASE WHEN f.status='paid' THEN 1 END) as paid_count,
                    COUNT(CASE WHEN f.status='unpaid' THEN 1 END) as unpaid_count,
                    COUNT(CASE WHEN f.status='partial' THEN 1 END) as partial_count
                FROM fees f
                JOIN students s ON f.student_id = s.student_id
                WHERE s.school_id = ?
            """, (school_id,))
            row = cursor.fetchone()
            return dict(row) if row else {}

    # ==================== FINANCIAL HELPERS ====================
    def add_expense(self, school_id: int, category: str, amount: float, expense_date: str, notes: str = None):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO expenses (school_id, category, amount, expense_date, notes) VALUES (?,?,?,?,?)",
                (school_id, category, amount, expense_date, notes)
            )

    def get_expenses_by_period(self, school_id: int, start_date: str, end_date: str) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM expenses WHERE school_id=? AND expense_date BETWEEN ? AND ? ORDER BY expense_date",
                (school_id, start_date, end_date)
            )
            return [dict(r) for r in cursor.fetchall()]

    def get_fees_for_student(self, student_id: int) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM fees WHERE student_id=? ORDER BY due_date DESC", (student_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_assignments_for_student(self, student_id: int) -> list:
        """Fetch assignments for the student's class and return open assignments."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT class_id FROM students WHERE student_id=?", (student_id,))
            row = cursor.fetchone()
            if not row:
                return []
            class_id = row[0]
            cursor.execute("SELECT a.*, s.subject_name FROM assignments a LEFT JOIN subjects s ON a.subject_id=s.subject_id WHERE a.class_id=? ORDER BY a.due_date", (class_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_monthly_expenses(self, school_id: int, months: int = 12) -> list:
        """Return list of {'month':'YYYY-MM','total':amount} for last `months` months."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT strftime('%Y-%m', expense_date) as month, SUM(amount) as total FROM expenses WHERE school_id=? AND expense_date >= date('now', ? || ' months') GROUP BY month ORDER BY month",
                (school_id, f'-{months}')
            )
            return [dict(r) for r in cursor.fetchall()]

    def get_yearly_expenses(self, school_id: int, years: int = 3) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT year(expense_date) as year, SUM(amount) as total FROM expenses WHERE school_id=? AND expense_date >= date('now', ? || ' years') GROUP BY year ORDER BY year",
                (school_id, f'-{years}')
            )
            return [dict(r) for r in cursor.fetchall()]

    # Salaries helpers
    def add_salary_record(self, user_id: int, school_id: int, month: str, year: int, amount: float):
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO salaries (user_id, school_id, month, year, amount) VALUES (?,?,?,?,?)",
                (user_id, school_id, month, year, amount)
            )

    def get_salary_status(self, school_id: int, month: str = None, year: int = None) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if month and year:
                cursor.execute("SELECT s.*, u.full_name FROM salaries s JOIN users u ON s.user_id=u.user_id WHERE s.school_id=? AND s.month=? AND s.year=?",
                               (school_id, month, year))
            else:
                cursor.execute("SELECT s.*, u.full_name FROM salaries s JOIN users u ON s.user_id=u.user_id WHERE s.school_id=? ORDER BY s.year DESC, s.month DESC",
                               (school_id,))
            return [dict(r) for r in cursor.fetchall()]

    def pay_salary(self, salary_id: int, paid_amount: float, paid_date: str = None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT amount FROM salaries WHERE salary_id=?", (salary_id,))
            row = cursor.fetchone()
            if not row:
                return False
            amount = row[0]
            status = 'paid' if paid_amount >= amount else ('partial' if paid_amount > 0 else 'unpaid')
            conn.execute("UPDATE salaries SET paid_amount=?, status=?, paid_date=? WHERE salary_id=?", (paid_amount, status, paid_date, salary_id))
            return True

    def get_subjects_by_class(self, class_id: int) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subjects WHERE class_id=?", (class_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_notifications(self, school_id: int = 1, limit: int = 20) -> list:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM notifications
                WHERE school_id=?
                ORDER BY created_at DESC
                LIMIT ?
            """, (school_id, limit))
            return [dict(r) for r in cursor.fetchall()]

    def get_notifications_for_role(self, school_id: int = 1, role: str = None, limit: int = 20) -> list:
        """Fetch notifications for a school, optionally filtered by target role (or null => all)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if role:
                cursor.execute("""
                    SELECT * FROM notifications
                    WHERE school_id=? AND (target_role IS NULL OR target_role=? )
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (school_id, role, limit))
            else:
                cursor.execute("""
                    SELECT * FROM notifications
                    WHERE school_id=?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (school_id, limit))
            return [dict(r) for r in cursor.fetchall()]

    def get_class_marks_summary(self, class_id: int) -> dict:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sub.subject_name, ROUND(AVG(m.percentage), 1) as avg_score
                FROM marks m
                JOIN students s ON m.student_id = s.student_id
                JOIN subjects sub ON m.subject_id = sub.subject_id
                WHERE s.class_id = ?
                GROUP BY sub.subject_name
            """, (class_id,))
            return {r["subject_name"]: r["avg_score"] for r in cursor.fetchall()}

    def add_ai_alert(self, school_id: int, student_id, class_id, alert_type: str,
                     severity: str, title: str, message: str):
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO ai_alerts (school_id, student_id, class_id, alert_type, severity, title, message)
                VALUES (?,?,?,?,?,?,?)
            """, (school_id, student_id, class_id, alert_type, severity, title, message))

    def assign_parent_to_student(self, student_id: int, parent_user_id: int) -> None:
        """Set the parent_id for a student to the given user id."""
        with self.get_connection() as conn:
            conn.execute("UPDATE students SET parent_id=? WHERE student_id=?", (parent_user_id, student_id))

    # ==================== PASSWORD RESET HELPERS ====================
    def create_password_reset(self, email: str, ttl_minutes: int = 60) -> dict:
        """Create a password reset token for a given email. Returns dict with success and message.
        For development convenience returns the token as well; in production you would not expose it.
        """
        import secrets
        from datetime import datetime, timedelta

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, email FROM users WHERE email = ? AND is_active=1", (email.strip().lower(),))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "error": "No active user with that email."}
            user_id = row["user_id"]

            token = secrets.token_urlsafe(32)
            expires_at = (datetime.now() + timedelta(minutes=ttl_minutes)).strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute(
                "INSERT INTO password_resets (user_id, token, expires_at) VALUES (?,?,?)",
                (user_id, token, expires_at)
            )
            return {"success": True, "token": token, "expires_at": expires_at}

    def verify_password_reset(self, email: str, token: str) -> bool:
        from datetime import datetime
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE email = ?", (email.strip().lower(),))
            user = cursor.fetchone()
            if not user:
                return False
            user_id = user["user_id"]

            cursor.execute(
                "SELECT reset_id, expires_at, used FROM password_resets WHERE user_id=? AND token=? ORDER BY created_at DESC LIMIT 1",
                (user_id, token)
            )
            row = cursor.fetchone()
            if not row:
                return False
            if row["used"]:
                return False
            expires_at = datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S")
            if datetime.now() > expires_at:
                return False
            return True

    def consume_password_reset(self, email: str, token: str, new_password: str) -> dict:
        """Verify token and set a new password. Returns success/error dict."""
        from datetime import datetime

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE email = ? AND is_active=1", (email.strip().lower(),))
            user = cursor.fetchone()
            if not user:
                return {"success": False, "error": "No active user with that email."}
            user_id = user["user_id"]

            cursor.execute(
                "SELECT reset_id, expires_at, used FROM password_resets WHERE user_id=? AND token=? ORDER BY created_at DESC LIMIT 1",
                (user_id, token)
            )
            row = cursor.fetchone()
            if not row:
                return {"success": False, "error": "Invalid token."}
            if row["used"]:
                return {"success": False, "error": "Token already used."}
            expires_at = datetime.strptime(row["expires_at"], "%Y-%m-%d %H:%M:%S")
            if datetime.now() > expires_at:
                return {"success": False, "error": "Token expired."}

            # Update password
            new_hash = self._hash_password(new_password)
            cursor.execute("UPDATE users SET password_hash=? WHERE user_id=?", (new_hash, user_id))
            # Mark token used
            cursor.execute("UPDATE password_resets SET used=1 WHERE reset_id=?", (row["reset_id"],))
            return {"success": True}
