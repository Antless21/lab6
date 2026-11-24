"""Средние задания №2 и №4: форма и таблица на Flask/Jinja2."""

from flask import Flask, render_template, request

app = Flask(__name__, template_folder="templates", static_folder="static")

STUDENTS = [
    {"id": 1, "name": "Анна Иванова", "group": "221341", "age": 19},
    {"id": 2, "name": "Иван Петров", "group": "221341", "age": 20},
    {"id": 3, "name": "Мария Смирнова", "group": "221342", "age": 19},
]


@app.route("/", methods=["GET", "POST"])
def greeting():
    """Получить имя из формы и передать его в шаблон с экранированием."""
    name = ""
    error = None
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not 1 <= len(name) <= 50:
            error = "Введите имя длиной от 1 до 50 символов."
    return render_template("greeting.html", name=name, error=error), (
        400 if error else 200
    )


@app.get("/students")
def students():
    """Таблица демонстрационных данных, сформированная циклом Jinja2."""
    return render_template("students.html", students=STUDENTS)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
