from __future__ import annotations

import os
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fastlearnee.db")
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", "./storage"))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Module(Base):
    __tablename__ = "module"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))


class Material(Base):
    __tablename__ = "material"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    module_id: Mapped[str] = mapped_column(ForeignKey("module.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), default="processed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Question(Base):
    __tablename__ = "question"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    module_id: Mapped[str] = mapped_column(ForeignKey("module.id"), index=True)
    quiz_job_id: Mapped[str] = mapped_column(String(36), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[str] = mapped_column(Text)
    answer: Mapped[int] = mapped_column(Integer)
    question_type: Mapped[str] = mapped_column(String(30), default="mcq")
    bloom_level: Mapped[str] = mapped_column(String(30), default="Apply")
    difficulty: Mapped[str] = mapped_column(String(30), default="medium")


class QuizJob(Base):
    __tablename__ = "quiz_job"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    module_id: Mapped[str] = mapped_column(ForeignKey("module.id"))
    status: Mapped[str] = mapped_column(String(30), default="queued")
    question_count: Mapped[int] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class QuizAttempt(Base):
    __tablename__ = "quiz_attempt"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    quiz_job_id: Mapped[str] = mapped_column(ForeignKey("quiz_job.id"))
    score: Mapped[int] = mapped_column(Integer, default=0)
    total: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class QuizAnswer(Base):
    __tablename__ = "quiz_answer"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("quiz_attempt.id"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("question.id"))
    selected_option: Mapped[int] = mapped_column(Integer)
    is_correct: Mapped[int] = mapped_column(Integer)


class RevisionSheet(Base):
    __tablename__ = "revision_sheet"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    material_id: Mapped[str] = mapped_column(ForeignKey("material.id"))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class QuizRequest(BaseModel):
    module_id: str
    question_count: int = Field(default=10, ge=1, le=50)
    topics: list[str] = []
    format: str = "mcq"


class AnswerRequest(BaseModel):
    question_id: str
    selected_option: int = Field(ge=0, le=3)


class AttemptRequest(BaseModel):
    quiz_job_id: str
    answers: list[AnswerRequest]


app = FastAPI(title="FastLearnee API", version="0.1.0")
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["*"] , allow_headers=["*"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_modules(db: Session) -> None:
    if db.scalar(select(Module).limit(1)):
        return
    for code, name in (("CS201", "Algorithms & Complexity"), ("MATH301", "Linear Algebra & Statistics"), ("BIO105", "Molecular Physiology")):
        db.add(Module(id=str(uuid.uuid4()), code=code, name=name))
    db.commit()


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_modules(db)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "fastlearnee-backend"}


@app.get("/modules")
def list_modules(db: Session = Depends(get_db)) -> list[dict[str, str]]:
    return [{"id": item.id, "code": item.code, "name": item.name} for item in db.scalars(select(Module).order_by(Module.code))]


@app.post("/materials/upload", status_code=201)
def upload_material(module_id: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict[str, Any]:
    if not db.get(Module, module_id):
        raise HTTPException(404, "Module not found")
    material_id = str(uuid.uuid4())
    safe_name = Path(file.filename or "uploaded-material").name
    target = STORAGE_DIR / f"{material_id}-{safe_name}"
    with target.open("wb") as destination:
        shutil.copyfileobj(file.file, destination)
    material = Material(id=material_id, module_id=module_id, filename=safe_name, storage_path=str(target), status="processed")
    db.add(material)
    db.commit()
    return {"id": material.id, "filename": material.filename, "status": material.status}


def generate_questions(job_id: str) -> None:
    time.sleep(0.25)
    with SessionLocal() as db:
        job = db.get(QuizJob, job_id)
        if not job:
            return
        try:
            examples = [
                ("Which property guarantees that a dynamic programming solution can be assembled from smaller solutions?", ["Optimal substructure", "Random choice", "Matrix density", "Vertex count"], 0, "Understand", "easy"),
                ("What is the runtime of Floyd-Warshall on a graph with V vertices?", ["O(V)", "O(V^2)", "O(V^3)", "O(2V)"], 2, "Remember", "medium"),
                ("What ordering is required for greedy interval partitioning?", ["Start times", "Academic level", "Alphabetical order", "Room number"], 0, "Apply", "hard"),
            ]
            for index in range(job.question_count):
                prompt, options, answer, bloom, difficulty = examples[index % len(examples)]
                db.add(Question(id=str(uuid.uuid4()), module_id=job.module_id, quiz_job_id=job.id, prompt=prompt, options="|||".join(options), answer=answer, bloom_level=bloom, difficulty=difficulty))
            job.status = "ready"
            db.commit()
        except Exception as error:
            job.status = "failed"
            job.error = str(error)
            db.commit()


@app.post("/quiz-jobs", status_code=202)
def create_quiz(request: QuizRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> dict[str, str]:
    if not db.get(Module, request.module_id):
        raise HTTPException(404, "Module not found")
    job = QuizJob(id=str(uuid.uuid4()), module_id=request.module_id, question_count=request.question_count)
    db.add(job)
    db.commit()
    background_tasks.add_task(generate_questions, job.id)
    return {"job_id": job.id, "status": job.status}


@app.get("/quiz-jobs/{job_id}")
def get_quiz_job(job_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    job = db.get(QuizJob, job_id)
    if not job:
        raise HTTPException(404, "Quiz job not found")
    questions = db.scalars(select(Question).where(Question.quiz_job_id == job_id)).all()
    return {"job_id": job.id, "status": job.status, "error": job.error, "questions": [{"id": q.id, "prompt": q.prompt, "options": q.options.split("|||"), "bloom_level": q.bloom_level, "difficulty": q.difficulty} for q in questions]}


@app.post("/quiz-attempts", status_code=201)
def submit_attempt(request: AttemptRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    job = db.get(QuizJob, request.quiz_job_id)
    if not job or job.status != "ready":
        raise HTTPException(400, "Quiz is not ready")
    questions = {question.id: question for question in db.scalars(select(Question).where(Question.quiz_job_id == job.id))}
    attempt = QuizAttempt(id=str(uuid.uuid4()), quiz_job_id=job.id, total=len(request.answers))
    db.add(attempt)
    score = 0
    for answer in request.answers:
        question = questions.get(answer.question_id)
        if not question:
            raise HTTPException(400, f"Question {answer.question_id} does not belong to this quiz")
        correct = int(answer.selected_option == question.answer)
        score += correct
        db.add(QuizAnswer(id=str(uuid.uuid4()), attempt_id=attempt.id, question_id=question.id, selected_option=answer.selected_option, is_correct=correct))
    attempt.score = score
    db.commit()
    return {"attempt_id": attempt.id, "score": score, "total": attempt.total, "percentage": round(score / attempt.total * 100) if attempt.total else 0}


@app.get("/progress")
def progress(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    attempts = db.scalars(select(QuizAttempt).order_by(QuizAttempt.created_at.desc())).all()
    return [{"attempt_id": item.id, "score": item.score, "total": item.total, "percentage": round(item.score / item.total * 100) if item.total else 0, "created_at": item.created_at} for item in attempts]


@app.post("/revision-sheets", status_code=201)
def create_revision_sheet(material_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    material = db.get(Material, material_id)
    if not material:
        raise HTTPException(404, "Material not found")
    sheet = RevisionSheet(id=str(uuid.uuid4()), material_id=material.id, title=f"Revision sheet: {material.filename}", content="Core concepts extracted from the uploaded material. Replace this mock content with the C1 retrieval and Gemini summarization call.")
    db.add(sheet)
    db.commit()
    return {"id": sheet.id, "title": sheet.title, "content": sheet.content}
