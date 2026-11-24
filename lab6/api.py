"""Среднее №7, повышенные №2 и №6: JSON, SQLite CRUD, WebSocket."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response, WebSocket, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from lab6.chat import ConnectionManager, run_chat
from lab6.database import connection, initialize
from lab6.schemas import Student, StudentInput

ROOT = Path(__file__).resolve().parent.parent


def create_app(database_path: str | Path | None = None) -> FastAPI:
    path = Path(
        database_path
        if database_path is not None
        else os.getenv("LAB6_DB_PATH", str(ROOT / "data" / "students.sqlite3"))
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        initialize(path)
        app.state.chat = ConnectionManager()
        yield

    app = FastAPI(
        title="Лабораторная №6 — вариант 2",
        description="JSON endpoint, CRUD студентов в SQLite и WebSocket-чат.",
        lifespan=lifespan,
    )
    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

    @app.get("/")
    @app.get("/api/info")
    def info() -> dict:
        return {
            "message": "Привет, FastAPI!",
            "student": "Мовчан Александр Дмитриевич",
            "group": "221341",
            "variant": 2,
            "lab": 6,
        }

    @app.get("/api/students", response_model=list[Student])
    def list_students():
        with connection(path) as db:
            return [
                dict(row) for row in db.execute("SELECT * FROM students ORDER BY id")
            ]

    @app.get("/api/students/{student_id}", response_model=Student)
    def get_student(student_id: int):
        with connection(path) as db:
            row = db.execute(
                "SELECT * FROM students WHERE id = ?", (student_id,)
            ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Студент не найден")
        return dict(row)

    @app.post(
        "/api/students", response_model=Student, status_code=status.HTTP_201_CREATED
    )
    def create_student(student: StudentInput):
        with connection(path) as db:
            cursor = db.execute(
                "INSERT INTO students (name, age, group_name) VALUES (?, ?, ?)",
                (student.name, student.age, student.group_name),
            )
            return {"id": cursor.lastrowid, **student.model_dump()}

    @app.put("/api/students/{student_id}", response_model=Student)
    def update_student(student_id: int, student: StudentInput):
        with connection(path) as db:
            cursor = db.execute(
                "UPDATE students SET name = ?, age = ?, group_name = ? WHERE id = ?",
                (student.name, student.age, student.group_name, student_id),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Студент не найден")
        return {"id": student_id, **student.model_dump()}

    @app.delete("/api/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_student(student_id: int):
        with connection(path) as db:
            cursor = db.execute("DELETE FROM students WHERE id = ?", (student_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Студент не найден")
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get("/chat", response_class=FileResponse)
    def chat_page():
        return FileResponse(ROOT / "templates" / "chat.html")

    @app.websocket("/ws/chat")
    async def chat_endpoint(websocket: WebSocket):
        await run_chat(websocket, app.state.chat)

    return app
