from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Generator, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy import (Column, DateTime, Float, ForeignKey, Index, Integer, String, Text,
                        create_engine, event, func, select)
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
DATA_DIR = Path(os.getenv("CODESTUDIO_DATA_DIR", str(ROOT / "data"))).resolve()
REPO_DIR = DATA_DIR / "repos"
DATA_DIR.mkdir(parents=True, exist_ok=True)
REPO_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_DB = f"sqlite:///{(DATA_DIR / 'codingal_studio.db').as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB)
RUNNER_IMAGE = os.getenv("CODESTUDIO_RUNNER_IMAGE", "codingal-runner:local")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    grade = Column(String(40), nullable=False)
    class_name = Column(String(120), nullable=False, index=True)
    teacher = Column(String(120), nullable=False)
    mastery = Column(Integer, default=70, nullable=False)
    mastery_delta = Column(Integer, default=0, nullable=False)
    completion = Column(Integer, default=70, nullable=False)
    last_active = Column(DateTime, default=utcnow, nullable=False)
    streak_days = Column(Integer, default=0, nullable=False)
    concepts_json = Column(Text, default="{}", nullable=False)
    joined_at = Column(DateTime, default=utcnow, nullable=False)
    submissions = relationship("Submission", back_populates="student", cascade="all, delete-orphan")


class Assignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    language = Column(String(40), nullable=False)
    class_name = Column(String(120), nullable=False, index=True)
    description = Column(Text, default="", nullable=False)
    due_date = Column(String(30), default="", nullable=False)
    status = Column(String(30), default="active", nullable=False)
    created_by = Column(String(120), default="Demo Teacher", nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    submissions = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")


class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted_at = Column(DateTime, default=utcnow, nullable=False)
    status = Column(String(30), default="submitted", nullable=False)
    score = Column(Float, default=0, nullable=False)
    tests_passed = Column(Integer, default=0, nullable=False)
    tests_total = Column(Integer, default=0, nullable=False)
    bugs_found = Column(Integer, default=0, nullable=False)
    bugs_resolved = Column(Integer, default=0, nullable=False)
    runtime_seconds = Column(Float, default=0, nullable=False)
    student = relationship("Student", back_populates="submissions")
    assignment = relationship("Assignment", back_populates="submissions")


class TeacherNote(Base):
    __tablename__ = "teacher_notes"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="SET NULL"), nullable=True, index=True)
    class_name = Column(String(120), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    body = Column(Text, default="", nullable=False)
    owner = Column(String(120), default="Unassigned", nullable=False)
    priority = Column(String(20), default="medium", nullable=False)
    status = Column(String(30), default="open", nullable=False, index=True)
    author = Column(String(120), default="Demo Teacher", nullable=False)
    due_date = Column(String(30), default="", nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    comments = relationship("NoteComment", back_populates="note", cascade="all, delete-orphan", order_by="NoteComment.created_at")


class NoteComment(Base):
    __tablename__ = "note_comments"
    id = Column(Integer, primary_key=True)
    note_id = Column(Integer, ForeignKey("teacher_notes.id", ondelete="CASCADE"), nullable=False, index=True)
    author = Column(String(120), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    note = relationship("TeacherNote", back_populates="comments")


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    language = Column(String(40), nullable=False)
    class_name = Column(String(120), default="Python Foundations", nullable=False)
    owner_student_id = Column(Integer, ForeignKey("students.id", ondelete="SET NULL"), nullable=True)
    repo_path = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)


class RunRecord(Base):
    __tablename__ = "runs"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)
    language = Column(String(40), nullable=False)
    status = Column(String(30), nullable=False)
    output = Column(Text, default="", nullable=False)
    duration_ms = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


Index("ix_submissions_student_assignment", Submission.student_id, Submission.assignment_id)
Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(title="Codingal Code Studio", version="0.9.0", description="Local standalone learning intelligence and teacher collaboration prototype")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Cache-Control", "no-store" if request.url.path.startswith("/api") else "no-cache")
    return response


class AssignmentIn(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    language: str = Field(default="Python", max_length=40)
    class_name: str = Field(default="Python Foundations", max_length=120)
    description: str = Field(default="", max_length=3000)
    due_date: str = Field(default="", max_length=30)
    created_by: str = Field(default="Demo Teacher", max_length=120)


class NoteIn(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    body: str = Field(default="", max_length=6000)
    student_id: Optional[int] = None
    class_name: str = Field(default="Python Foundations", max_length=120)
    owner: str = Field(default="Unassigned", max_length=120)
    priority: str = Field(default="medium", pattern="^(low|medium|high|urgent)$")
    due_date: str = Field(default="", max_length=30)
    author: str = Field(default="Demo Teacher", max_length=120)


class NotePatch(BaseModel):
    student_id: Optional[int] = None
    class_name: Optional[str] = Field(default=None, max_length=120)
    status: Optional[str] = Field(default=None, pattern="^(open|in_progress|resolved)$")
    owner: Optional[str] = Field(default=None, max_length=120)
    priority: Optional[str] = Field(default=None, pattern="^(low|medium|high|urgent)$")
    due_date: Optional[str] = Field(default=None, max_length=30)
    title: Optional[str] = Field(default=None, min_length=2, max_length=200)
    body: Optional[str] = Field(default=None, max_length=6000)


class CommentIn(BaseModel):
    author: str = Field(default="Demo Teacher", max_length=120)
    body: str = Field(min_length=1, max_length=3000)


class ProjectIn(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    language: str = Field(default="Python", pattern="^(Python|Java|C\\+\\+|HTML/CSS/JS)$")
    class_name: str = Field(default="Python Foundations", max_length=120)
    owner_student_id: Optional[int] = None


class FileIn(BaseModel):
    content: str = Field(max_length=50000)


class CommitIn(BaseModel):
    message: str = Field(min_length=2, max_length=200)
    author: str = Field(default="Demo Teacher", max_length=120)


class RestoreIn(BaseModel):
    commit_hash: str = Field(pattern="^[a-fA-F0-9]{7,40}$")
    author: str = Field(default="Demo Teacher", max_length=120)


class RunIn(BaseModel):
    language: str = Field(pattern="^(Python|Java|C\\+\\+|HTML/CSS/JS)$")
    code: str = Field(max_length=25000)
    stdin: str = Field(default="", max_length=3000)
    project_id: Optional[int] = None


def safe_name(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", name) or name in {".", "..", ".git"} or name.startswith("."):
        raise HTTPException(status_code=400, detail="Use a simple file name with letters, numbers, dots, underscores or hyphens.")
    return name


def git(*args: str, cwd: Path, timeout: int = 8) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=timeout, check=False,
                          env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1"})


def init_repo(path: Path, title: str, language: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(["git", "init", "-b", "main", str(path)], capture_output=True, text=True, timeout=8, check=False)
    if p.returncode != 0:
        subprocess.run(["git", "init", str(path)], capture_output=True, text=True, timeout=8, check=True)
        git("checkout", "-b", "main", cwd=path)
    if language == "Python":
        starter = 'name = "Coder"\nprint(f"Hello, {name}!")\nprint("Welcome to Codingal Code Studio.")\n'
        filename = "main.py"
    elif language == "Java":
        starter = 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, Codingal!");\n    }\n}\n'
        filename = "Main.java"
    elif language == "C++":
        starter = '#include <iostream>\nint main() { std::cout << "Hello, Codingal!\\n"; return 0; }\n'
        filename = "main.cpp"
    else:
        starter = '<!doctype html>\n<html><head><meta charset="utf-8"><title>My project</title><style>body{font-family:Arial;padding:2rem}h1{color:#ff5948}</style></head><body><h1>Hello, Codingal!</h1><p>Build something great.</p><button onclick="document.querySelector(\'p\').textContent=\'You made it interactive!\'">Try me</button></body></html>\n'
        filename = "index.html"
    (path / filename).write_text(starter, encoding="utf-8")
    (path / "README.md").write_text(f"# {title}\n\nCreated in Codingal Code Studio.\n\nLanguage: {language}\n", encoding="utf-8")
    git("add", "-A", cwd=path)
    git("-c", "user.name=Codingal Studio", "-c", "user.email=studio@localhost", "commit", "-m", "Initial project", cwd=path)


def serialize_student(s: Student) -> dict:
    last = s.last_active or utcnow()
    inactive = max(0, (utcnow() - last).days)
    if s.mastery < 60 or s.mastery_delta <= -8:
        risk = "high"
    elif s.mastery < 72 or inactive >= 7:
        risk = "watch"
    else:
        risk = "on_track"
    return {
        "id": s.id, "name": s.name, "grade": s.grade, "class_name": s.class_name,
        "teacher": s.teacher, "mastery": s.mastery, "mastery_delta": s.mastery_delta,
        "completion": s.completion, "last_active": s.last_active.isoformat() + "Z",
        "days_inactive": inactive, "streak_days": s.streak_days, "risk": risk,
        "concepts": json.loads(s.concepts_json or "{}")
    }


def serialize_note(n: TeacherNote, include_comments: bool = True) -> dict:
    data = {"id": n.id, "student_id": n.student_id, "class_name": n.class_name, "title": n.title,
            "body": n.body, "owner": n.owner, "priority": n.priority, "status": n.status,
            "author": n.author, "due_date": n.due_date, "created_at": n.created_at.isoformat() + "Z",
            "updated_at": n.updated_at.isoformat() + "Z"}
    if include_comments:
        data["comments"] = [{"id": c.id, "author": c.author, "body": c.body, "created_at": c.created_at.isoformat() + "Z"} for c in n.comments]
    return data


def serialize_assignment(a: Assignment, db: Session) -> dict:
    submissions = db.scalars(select(Submission).where(Submission.assignment_id == a.id)).all()
    students = db.scalar(select(func.count(Student.id)).where(Student.class_name == a.class_name)) or 0
    submitted = sum(1 for x in submissions if x.status in {"submitted", "reviewed", "complete"})
    scores = [x.score for x in submissions if x.score is not None and x.status in {"submitted", "reviewed", "complete"}]
    return {"id": a.id, "title": a.title, "language": a.language, "class_name": a.class_name,
            "description": a.description, "due_date": a.due_date, "status": a.status,
            "created_by": a.created_by, "created_at": a.created_at.isoformat() + "Z",
            "submission_count": submitted, "student_count": students,
            "completion": round(submitted / students * 100) if students else 0,
            "average_score": round(sum(scores) / len(scores)) if scores else None,
            "submissions": [{"id": x.id, "student_id": x.student_id, "student": x.student.name,
                             "status": x.status, "score": x.score, "tests_passed": x.tests_passed,
                             "tests_total": x.tests_total, "bugs_found": x.bugs_found,
                             "bugs_resolved": x.bugs_resolved, "submitted_at": x.submitted_at.isoformat() + "Z"}
                            for x in submissions]}


def serialize_project(p: Project) -> dict:
    return {"id": p.id, "title": p.title, "language": p.language, "class_name": p.class_name,
            "owner_student_id": p.owner_student_id, "updated_at": p.updated_at.isoformat() + "Z"}


def seed_if_empty() -> None:
    db = SessionLocal()
    try:
        if (db.scalar(select(func.count(Student.id))) or 0) > 0:
            return
        now = utcnow()
        names = [
            ("Aarav Mehta", "Grade 5", 82, 4, 94, 2, 5),
            ("Mira Shah", "Grade 5", 74, 2, 88, 1, 2),
            ("Ishaan Rao", "Grade 5", 56, -9, 61, 0, 9),
            ("Anaya Das", "Grade 5", 91, 6, 97, 5, 1),
            ("Kabir Nair", "Grade 5", 67, -4, 72, 1, 4),
            ("Tara Iyer", "Grade 5", 79, 3, 86, 3, 1),
            ("Rohan Sen", "Grade 5", 61, -7, 58, 0, 8),
            ("Diya Kapoor", "Grade 5", 88, 5, 92, 4, 0),
            ("Neil Thomas", "Grade 5", 70, -1, 75, 2, 6),
            ("Sana Ali", "Grade 5", 84, 4, 89, 3, 2),
            ("Vihaan Bose", "Grade 6", 77, 2, 82, 2, 1),
            ("Kiara Jain", "Grade 6", 63, -6, 67, 0, 7),
        ]
        concepts = ["Sequences", "Loops", "Conditionals", "Debugging", "Variables"]
        students = []
        for i, (name, grade, mastery, delta, completion, streak, inactive) in enumerate(names):
            scores = {c: max(30, min(100, mastery + offset)) for c, offset in zip(concepts, [6, -8, 2, -4, 5])}
            if i in (2, 6, 11): scores["Debugging"] = max(30, mastery - 19)
            if i in (1, 4, 8): scores["Loops"] = max(30, mastery - 17)
            s = Student(name=name, grade=grade, class_name="Python Foundations" if grade == "Grade 5" else "Creative Coding",
                        teacher="Priya Sharma" if i % 2 == 0 else "Rahul Verma", mastery=mastery, mastery_delta=delta,
                        completion=completion, last_active=now - timedelta(days=inactive, hours=(i % 5) * 2),
                        streak_days=streak, concepts_json=json.dumps(scores), joined_at=now - timedelta(days=90 + i * 3))
            students.append(s)
            db.add(s)
        db.flush()
        assignment_data = [
            ("Loops: Pattern Builder", "Python", "Python Foundations", "Use a loop to draw a repeating pattern.", "active"),
            ("Debug the Robot", "Python", "Python Foundations", "Find and resolve the logic errors in a small program.", "active"),
            ("Interactive Story Page", "HTML/CSS/JS", "Python Foundations", "Create a web page with one interactive action.", "active"),
            ("Conditionals Challenge", "Java", "Creative Coding", "Use if/else logic to solve three simple cases.", "active"),
        ]
        assignments = []
        for title, lang, cls, desc, status in assignment_data:
            a = Assignment(title=title, language=lang, class_name=cls, description=desc,
                           due_date=(now + timedelta(days=3 + len(assignments))).date().isoformat(), status=status,
                           created_by="Priya Sharma", created_at=now - timedelta(days=len(assignments) * 3 + 1))
            assignments.append(a); db.add(a)
        db.flush()
        for ai, a in enumerate(assignments):
            candidates = [s for s in students if s.class_name == a.class_name]
            limit = max(4, len(candidates) - (ai % 3) * 2)
            for j, s in enumerate(candidates[:limit]):
                score = max(35, min(100, s.mastery + ((j * 7 + ai * 3) % 17) - 8))
                passed = max(1, round(score / 100 * 8))
                db.add(Submission(assignment_id=a.id, student_id=s.id, submitted_at=now - timedelta(days=(j + ai) % 8),
                                  status="reviewed" if j % 3 == 0 else "submitted", score=score,
                                  tests_passed=passed, tests_total=8, bugs_found=(j % 4) + 1,
                                  bugs_resolved=max(0, (j % 4) + 1 - (1 if j % 3 == 0 else 0)),
                                  runtime_seconds=round(0.08 + (j % 6) * .07, 2)))
        db.flush()
        seeded_notes = [
            (students[2].id, "Debugging confidence dipped", "Ishaan's debugging concept score is below the class target and mastery has dropped 9 points. Try guided trace tables before the next loop exercise.", "Priya Sharma", "high", "open", now + timedelta(days=1)),
            (students[6].id, "Agree on a short catch-up plan", "Rohan has low recent completion. Please align on a 10-minute starter task and review one worked example next class.", "Rahul Verma", "urgent", "in_progress", now),
            (students[4].id, "Review loops misconception", "Kabir completes most work but repeated loop errors suggest the concept needs reinforcement. Compare notes after the next session.", "Priya Sharma", "medium", "open", now + timedelta(days=3)),
            (students[11].id, "Re-engage after a quiet week", "Kiara has been inactive for a week. Check whether the assignment is clear and agree on a low-friction next step.", "Rahul Verma", "medium", "open", now + timedelta(days=2)),
        ]
        for sid, title, body, owner, priority, status, due in seeded_notes:
            db.add(TeacherNote(student_id=sid, class_name=students[[s.id for s in students].index(sid)].class_name,
                               title=title, body=body, owner=owner, priority=priority, status=status,
                               author="Priya Sharma", due_date=due.date().isoformat(), created_at=now - timedelta(days=2)))
        db.flush()
        note = db.scalar(select(TeacherNote).where(TeacherNote.title == "Debugging confidence dipped"))
        if note:
            db.add(NoteComment(note_id=note.id, author="Rahul Verma", body="I can prepare a worked example and review it in our next planning sync.", created_at=now - timedelta(hours=4)))
        db.commit()
        if not (db.scalar(select(func.count(Project.id))) or 0):
            path = REPO_DIR / f"project_{uuid.uuid4().hex[:10]}"
            init_repo(path, "Loops & Patterns Lab", "Python")
            db.add(Project(title="Loops & Patterns Lab", language="Python", class_name="Python Foundations",
                           owner_student_id=students[0].id, repo_path=str(path), updated_at=now))
            db.commit()
    finally:
        db.close()


seed_if_empty()


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok", "product": "Codingal Code Studio", "version": app.version,
            "mode": "local-standalone", "database": "connected", "runner_image": RUNNER_IMAGE,
            "docker_available": shutil.which("docker") is not None}


@app.get("/api/overview")
def overview(db: Session = Depends(get_db)):
    students = db.scalars(select(Student)).all()
    notes = db.scalars(select(TeacherNote)).all()
    assignments = db.scalars(select(Assignment).where(Assignment.status != "archived")).all()
    subs = db.scalars(select(Submission)).all()
    student_rows = [serialize_student(s) for s in students]
    avg_mastery = round(sum(s["mastery"] for s in student_rows) / len(student_rows)) if student_rows else 0
    avg_completion = round(sum(s["completion"] for s in student_rows) / len(student_rows)) if student_rows else 0
    risk_count = sum(s["risk"] != "on_track" for s in student_rows)
    week_ago = utcnow() - timedelta(days=7)
    recent_subs = [x for x in subs if x.submitted_at >= week_ago]
    concept_totals: dict[str, list[int]] = {}
    for s in students:
        for key, value in json.loads(s.concepts_json or "{}").items():
            concept_totals.setdefault(key, []).append(int(value))
    concept_rows = [{"name": k, "score": round(sum(v) / len(v)), "student_count": len(v)} for k, v in concept_totals.items()]
    concept_rows.sort(key=lambda x: x["score"])
    priority_students = sorted([s for s in student_rows if s["risk"] != "on_track"],
                              key=lambda x: (0 if x["risk"] == "high" else 1, x["mastery"]))[:6]
    note_open = [n for n in notes if n.status != "resolved"]
    recommendations = []
    for c in concept_rows[:2]:
        if c["score"] < 75:
            recommendations.append({"title": f"Reinforce {c['name'].lower()}", "detail": f"Class average is {c['score']}%. Plan one worked example and a short practice task.", "priority": "high" if c["score"] < 65 else "medium", "type": "concept"})
    overdue = [n for n in note_open if n.due_date and n.due_date < utcnow().date().isoformat()]
    if overdue:
        recommendations.append({"title": "Review overdue teacher follow-ups", "detail": f"{len(overdue)} collaboration item(s) have passed their target date.", "priority": "high", "type": "collaboration"})
    if risk_count and not any(r["type"] == "concept" for r in recommendations):
        recommendations.append({"title": "Check in with learners needing support", "detail": f"{risk_count} learners are marked watch or high support based on demo mastery, trend and activity signals.", "priority": "medium", "type": "learner"})
    assignment_rows = [serialize_assignment(a, db) for a in assignments]
    return {"generated_at": utcnow().isoformat() + "Z", "demo_data": True,
            "class_name": "All demo classes", "metrics": {"students": len(students), "average_mastery": avg_mastery,
            "average_completion": avg_completion, "learners_to_support": risk_count,
            "open_followups": len(note_open), "submissions_7d": len(recent_subs),
            "assignments": len(assignments)},
            "concepts": concept_rows, "learners_to_support": priority_students,
            "recommendations": recommendations, "assignments": assignment_rows,
            "recent_submissions": [{"id": s.id, "student": s.student.name, "student_id": s.student_id,
                                     "assignment": s.assignment.title, "assignment_id": s.assignment_id,
                                     "score": s.score, "status": s.status, "submitted_at": s.submitted_at.isoformat() + "Z"}
                                    for s in sorted(subs, key=lambda x: x.submitted_at, reverse=True)[:7]]}


@app.get("/api/students")
def get_students(search: str = Query(default="", max_length=100), risk: str = Query(default="all"),
                 class_name: str = Query(default="all"), db: Session = Depends(get_db)):
    students = [serialize_student(s) for s in db.scalars(select(Student).order_by(Student.name)).all()]
    if search:
        q = search.strip().casefold()
        students = [s for s in students if q in s["name"].casefold() or q in s["class_name"].casefold()]
    if risk in {"high", "watch", "on_track"}:
        students = [s for s in students if s["risk"] == risk]
    if class_name != "all":
        students = [s for s in students if s["class_name"] == class_name]
    return {"items": students, "total": len(students), "demo_data": True}


@app.get("/api/students/{student_id}")
def get_student(student_id: int, db: Session = Depends(get_db)):
    s = db.get(Student, student_id)
    if not s:
        raise HTTPException(status_code=404, detail="Learner not found")
    row = serialize_student(s)
    subs = db.scalars(select(Submission).where(Submission.student_id == student_id).order_by(Submission.submitted_at.desc())).all()
    notes = db.scalars(select(TeacherNote).where(TeacherNote.student_id == student_id).order_by(TeacherNote.updated_at.desc())).all()
    row["submissions"] = [{"id": x.id, "assignment": x.assignment.title, "score": x.score, "status": x.status,
                            "tests_passed": x.tests_passed, "tests_total": x.tests_total,
                            "bugs_found": x.bugs_found, "bugs_resolved": x.bugs_resolved,
                            "submitted_at": x.submitted_at.isoformat() + "Z"} for x in subs]
    row["notes"] = [serialize_note(n) for n in notes]
    return row


@app.get("/api/assignments")
def get_assignments(db: Session = Depends(get_db)):
    rows = db.scalars(select(Assignment).order_by(Assignment.created_at.desc())).all()
    return {"items": [serialize_assignment(a, db) for a in rows], "total": len(rows)}


@app.post("/api/assignments", status_code=201)
def create_assignment(payload: AssignmentIn, db: Session = Depends(get_db)):
    a = Assignment(title=payload.title.strip(), language=payload.language, class_name=payload.class_name,
                   description=payload.description.strip(), due_date=payload.due_date, created_by=payload.created_by)
    db.add(a); db.commit(); db.refresh(a)
    return serialize_assignment(a, db)


@app.patch("/api/assignments/{assignment_id}")
def update_assignment(assignment_id: int, payload: dict, db: Session = Depends(get_db)):
    a = db.get(Assignment, assignment_id)
    if not a: raise HTTPException(status_code=404, detail="Assignment not found")
    status = payload.get("status")
    if status not in {"active", "review", "archived"}: raise HTTPException(status_code=400, detail="Invalid status")
    a.status = status; db.commit(); db.refresh(a)
    return serialize_assignment(a, db)


@app.get("/api/notes")
def get_notes(status: str = Query(default="all"), db: Session = Depends(get_db)):
    q = select(TeacherNote).order_by(TeacherNote.updated_at.desc())
    if status != "all": q = q.where(TeacherNote.status == status)
    rows = db.scalars(q).all()
    return {"items": [serialize_note(n) for n in rows], "total": len(rows)}


@app.post("/api/notes", status_code=201)
def create_note(payload: NoteIn, db: Session = Depends(get_db)):
    if payload.student_id is not None and not db.get(Student, payload.student_id):
        raise HTTPException(status_code=404, detail="Learner not found")
    n = TeacherNote(student_id=payload.student_id, class_name=payload.class_name,
                    title=payload.title.strip(), body=payload.body.strip(), owner=payload.owner,
                    priority=payload.priority, status="open", author=payload.author, due_date=payload.due_date)
    db.add(n); db.commit(); db.refresh(n)
    return serialize_note(n)


@app.patch("/api/notes/{note_id}")
def update_note(note_id: int, payload: NotePatch, db: Session = Depends(get_db)):
    n = db.get(TeacherNote, note_id)
    if not n: raise HTTPException(status_code=404, detail="Follow-up not found")
    data = payload.model_dump(exclude_unset=True)
    if data.get("student_id") is not None and not db.get(Student, data["student_id"]):
        raise HTTPException(status_code=404, detail="Learner not found")
    for key, value in data.items(): setattr(n, key, value)
    n.updated_at = utcnow(); db.commit(); db.refresh(n)
    return serialize_note(n)


@app.post("/api/notes/{note_id}/comments", status_code=201)
def comment_note(note_id: int, payload: CommentIn, db: Session = Depends(get_db)):
    n = db.get(TeacherNote, note_id)
    if not n: raise HTTPException(status_code=404, detail="Follow-up not found")
    c = NoteComment(note_id=note_id, author=payload.author, body=payload.body.strip())
    n.updated_at = utcnow(); db.add(c); db.commit(); db.refresh(n)
    return serialize_note(n)


@app.get("/api/projects")
def get_projects(db: Session = Depends(get_db)):
    items = db.scalars(select(Project).order_by(Project.updated_at.desc())).all()
    return {"items": [serialize_project(x) for x in items], "total": len(items)}


@app.post("/api/projects", status_code=201)
def create_project(payload: ProjectIn, db: Session = Depends(get_db)):
    if payload.owner_student_id is not None and not db.get(Student, payload.owner_student_id):
        raise HTTPException(status_code=404, detail="Learner not found")
    path = REPO_DIR / f"project_{uuid.uuid4().hex}"
    try:
        init_repo(path, payload.title, payload.language)
    except Exception as e:
        shutil.rmtree(path, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Could not initialise local Git repository: {str(e)[:180]}")
    p = Project(title=payload.title.strip(), language=payload.language, class_name=payload.class_name,
                owner_student_id=payload.owner_student_id, repo_path=str(path), updated_at=utcnow())
    db.add(p); db.commit(); db.refresh(p)
    return serialize_project(p)


def project_or_404(project_id: int, db: Session) -> tuple[Project, Path]:
    p = db.get(Project, project_id)
    if not p: raise HTTPException(status_code=404, detail="Project not found")
    path = Path(p.repo_path).resolve()
    if REPO_DIR not in path.parents:
        raise HTTPException(status_code=500, detail="Project repository path is outside configured storage")
    path.mkdir(parents=True, exist_ok=True)
    return p, path


@app.get("/api/projects/{project_id}/files")
def list_project_files(project_id: int, db: Session = Depends(get_db)):
    p, path = project_or_404(project_id, db)
    items = []
    for f in sorted(path.iterdir()):
        if f.is_file() and f.name != ".git" and not f.name.startswith("."):
            items.append({"name": f.name, "size": f.stat().st_size})
    return {"project": serialize_project(p), "items": items}


@app.get("/api/projects/{project_id}/files/{filename}")
def read_project_file(project_id: int, filename: str, db: Session = Depends(get_db)):
    name = safe_name(filename)
    _, path = project_or_404(project_id, db)
    f = path / name
    if not f.is_file() or ".git" in f.parts: raise HTTPException(status_code=404, detail="File not found")
    return {"name": name, "content": f.read_text(encoding="utf-8", errors="replace")}


@app.put("/api/projects/{project_id}/files/{filename}")
def save_project_file(project_id: int, filename: str, payload: FileIn, db: Session = Depends(get_db)):
    name = safe_name(filename)
    p, path = project_or_404(project_id, db)
    (path / name).write_text(payload.content, encoding="utf-8")
    p.updated_at = utcnow(); db.commit()
    return {"ok": True, "name": name, "saved_at": p.updated_at.isoformat() + "Z", "storage": "local filesystem"}


@app.post("/api/projects/{project_id}/commit")
def commit_project(project_id: int, payload: CommitIn, db: Session = Depends(get_db)):
    p, path = project_or_404(project_id, db)
    add = git("add", "-A", cwd=path)
    if add.returncode != 0: raise HTTPException(status_code=500, detail=add.stderr[-500:])
    result = git("-c", f"user.name={payload.author}", "-c", "user.email=teacher@localhost", "commit", "-m", payload.message.strip(), cwd=path)
    if result.returncode != 0:
        if "nothing to commit" in (result.stdout + result.stderr).lower():
            return {"ok": True, "unchanged": True, "message": "No changes to commit. Save a file first."}
        raise HTTPException(status_code=500, detail=(result.stderr or result.stdout)[-500:])
    p.updated_at = utcnow(); db.commit()
    head = git("rev-parse", "HEAD", cwd=path)
    return {"ok": True, "commit_hash": head.stdout.strip(), "short_hash": head.stdout.strip()[:8], "message": payload.message, "author": payload.author}


@app.get("/api/projects/{project_id}/versions")
def list_versions(project_id: int, db: Session = Depends(get_db)):
    _, path = project_or_404(project_id, db)
    result = git("log", "--pretty=format:%H%x1f%h%x1f%an%x1f%ad%x1f%s", "--date=iso-strict", "-n", "30", cwd=path)
    if result.returncode != 0:
        return {"items": [], "message": "No Git history available yet."}
    items = []
    for line in result.stdout.splitlines():
        fields = line.split("\x1f", 4)
        if len(fields) == 5:
            items.append({"hash": fields[0], "short_hash": fields[1], "author": fields[2], "date": fields[3], "message": fields[4]})
    return {"items": items}


@app.post("/api/projects/{project_id}/restore")
def restore_version(project_id: int, payload: RestoreIn, db: Session = Depends(get_db)):
    p, path = project_or_404(project_id, db)
    check = git("cat-file", "-t", payload.commit_hash, cwd=path)
    if check.returncode != 0 or check.stdout.strip() != "commit": raise HTTPException(status_code=404, detail="Commit not found in this repository")
    # Restore the selected snapshot as a new commit, preserving later history.
    target_tree = git("ls-tree", "-r", "--name-only", payload.commit_hash, cwd=path)
    current_tree = git("ls-files", cwd=path)
    if target_tree.returncode != 0 or current_tree.returncode != 0:
        raise HTTPException(status_code=500, detail="Could not inspect repository tree for restore")
    target_files = set(target_tree.stdout.splitlines())
    current_files = set(current_tree.stdout.splitlines())
    # Remove tracked paths introduced after the target snapshot; untracked files are not touched.
    for rel in sorted(current_files - target_files):
        candidate = (path / rel).resolve()
        if path not in candidate.parents and candidate != path:
            raise HTTPException(status_code=500, detail="Unsafe path in repository index")
        if candidate.is_file(): candidate.unlink()
    checkout = git("checkout", payload.commit_hash, "--", ".", cwd=path)
    if checkout.returncode != 0: raise HTTPException(status_code=500, detail=checkout.stderr[-500:])
    git("add", "-A", cwd=path)
    commit = git("-c", f"user.name={payload.author}", "-c", "user.email=teacher@localhost", "commit", "-m", f"Restore snapshot {payload.commit_hash[:8]}", cwd=path)
    if commit.returncode != 0 and "nothing to commit" not in (commit.stdout + commit.stderr).lower():
        raise HTTPException(status_code=500, detail=(commit.stderr or commit.stdout)[-500:])
    p.updated_at = utcnow(); db.commit()
    return {"ok": True, "message": "Snapshot restored as a new commit; previous history was preserved."}


def execute_in_docker(language: str, code: str, stdin: str) -> tuple[str, str, int]:
    docker = shutil.which("docker")
    if not docker:
        return "unavailable", "Secure local runner is not enabled because Docker was not found. Install Docker, then build the runner image using the README instructions. No code was executed.", 0
    inspect = subprocess.run([docker, "image", "inspect", RUNNER_IMAGE], capture_output=True, text=True, timeout=4)
    if inspect.returncode != 0:
        return "unavailable", f"Runner image '{RUNNER_IMAGE}' is not built yet. Follow the README to build it. No code was executed.", 0
    filename = {"Python": "main.py", "Java": "Main.java", "C++": "main.cpp"}[language]
    with tempfile.TemporaryDirectory(prefix="codingal-run-") as temp:
        folder = Path(temp)
        # Docker runs as UID 10001; permit traversal/read of this ephemeral input folder.
        os.chmod(folder, 0o755)
        (folder / filename).write_text(code, encoding="utf-8")
        cid_file = folder / "container.cid"
        common = [docker, "run", "--rm", "--cidfile", str(cid_file), "-i", "--network=none", "--memory=256m", "--cpus=0.75", "--pids-limit=64",
                  "--read-only", "--tmpfs", "/tmp:rw,nosuid,size=32m,uid=10001,gid=10001",
                  "--security-opt=no-new-privileges:true", "--cap-drop=ALL", "--user=10001:10001",
                  "-v", f"{folder}:/input:ro", "-w", "/tmp", RUNNER_IMAGE]
        if language == "Python":
            cmd = common + ["python3", "-I", "/input/main.py"]
        elif language == "Java":
            cmd = common + ["sh", "-lc", "javac -d /tmp /input/Main.java && java -cp /tmp Main"]
        else:
            cmd = common + ["sh", "-lc", "g++ -std=c++17 -O0 -pipe /input/main.cpp -o /tmp/main && /tmp/main"]
        started = time.monotonic()
        # Drain both pipes continuously but retain only bounded output, so output-spam code
        # cannot make the host app accumulate unbounded stdout/stderr in memory.
        out_buffer, err_buffer = bytearray(), bytearray()
        output_cap = 12000
        def drain(pipe, sink):
            while True:
                chunk = pipe.read(4096)
                if not chunk: break
                remaining = output_cap - len(sink)
                if remaining > 0: sink.extend(chunk[:remaining])
        try:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            return "error", f"Could not start the Docker runner: {str(e)[:300]}", int((time.monotonic() - started) * 1000)
        out_thread = threading.Thread(target=drain, args=(proc.stdout, out_buffer), daemon=True)
        err_thread = threading.Thread(target=drain, args=(proc.stderr, err_buffer), daemon=True)
        out_thread.start(); err_thread.start()
        try:
            try:
                proc.stdin.write(stdin.encode("utf-8"))
                proc.stdin.close()
            except (BrokenPipeError, OSError):
                pass
            timed_out = False
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                timed_out = True
                proc.kill()
                proc.wait(timeout=2)
                # Killing the Docker CLI can leave a daemon-managed container running. Remove it explicitly.
                try:
                    cid = cid_file.read_text(encoding="utf-8").strip() if cid_file.exists() else ""
                    if re.fullmatch(r"[a-fA-F0-9]{12,64}", cid):
                        subprocess.run([docker, "rm", "-f", cid], capture_output=True, timeout=3, check=False)
                except Exception:
                    pass
            out_thread.join(timeout=2); err_thread.join(timeout=2)
            duration = int((time.monotonic() - started) * 1000)
            if timed_out:
                return "timeout", "Execution exceeded the 10-second local prototype timeout. The runner was terminated and cleanup was requested.", duration
            output = out_buffer.decode("utf-8", errors="replace")
            errors = err_buffer.decode("utf-8", errors="replace")
            combined = (output + ("\n" if output and errors else "") + errors).strip()
            if len(out_buffer) >= output_cap or len(err_buffer) >= output_cap:
                combined += "\n… output truncated by the local runner limit."
            combined = combined[-14000:]
            return ("succeeded" if proc.returncode == 0 else "failed", combined or ("Program completed with no output." if proc.returncode == 0 else f"Process exited with code {proc.returncode}."), duration)
        finally:
            for stream in (proc.stdin, proc.stdout, proc.stderr):
                try:
                    if stream and not stream.closed: stream.close()
                except OSError:
                    pass


@app.post("/api/runs", status_code=201)
def run_code(payload: RunIn, db: Session = Depends(get_db)):
    if payload.language == "HTML/CSS/JS":
        return {"status": "preview_only", "output": "HTML/CSS/JavaScript is previewed in the browser sandbox. Use the Preview control in the editor.", "duration_ms": 0, "executed": False}
    if payload.project_id is not None and not db.get(Project, payload.project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    status, output, duration = execute_in_docker(payload.language, payload.code, payload.stdin)
    rec = RunRecord(project_id=payload.project_id, language=payload.language, status=status, output=output[:15000], duration_ms=duration)
    db.add(rec); db.commit(); db.refresh(rec)
    return {"id": rec.id, "status": status, "output": output, "duration_ms": duration,
            "executed": status in {"succeeded", "failed", "timeout", "error"}, "created_at": rec.created_at.isoformat() + "Z"}


@app.get("/api/runs")
def list_runs(limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    rows = db.scalars(select(RunRecord).order_by(RunRecord.created_at.desc()).limit(limit)).all()
    return {"items": [{"id": r.id, "project_id": r.project_id, "language": r.language, "status": r.status,
                       "output": r.output, "duration_ms": r.duration_ms, "created_at": r.created_at.isoformat() + "Z"} for r in rows]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")), reload=False)
