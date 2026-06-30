# Unused for final demo; kept as comment in case project paths are needed later.
# from pathlib import Path

import os

from flask import Flask, redirect, render_template, request, url_for

from ai.recommender import get_dataset_stats, get_questions, recommend_plants, validate_answers


app = Flask(__name__)

# PROJECT_ROOT = Path(__file__).resolve().parent

REFERENCES = [
    {
        "title": "Implementasi Inferensi Forward Chaining Pada Sistem",
        "description": "Sebagai Jurnal Utama",
        "url": "https://jurnal.itg.ac.id/index.php/algoritma/article/view/1411",
    },
    {
        "title": "Sistem Pakar Pemilihan Bibit Padi Unggul dengan Metode Forward Chaining",
        "description": "Sebagai Jurnal Pendukung",
        "url": "https://ejurnal.seminar-id.com/index.php/josyc/article/view/4926",
    },
    {
        "title": "Growing Indoor Plants with Success",
        "description": "Sebagai Referensi Ilmiah Kondisi Tanaman",
        "url": "https://ucanr.edu/sites/default/files/2020-07/330400.pdf",
    },
]

MEMBERS = [
    ["Anggota 1", "Muhammad Raffi", "2411082039", "TRPL 2-D", "Ketua"],
    ["Anggota 2", "Wildan Hafidh", "2411082034", "TRPL 2-D", "Data Processing"],
    ["Anggota 3", "Restia Amelia", "2411081038", "TRPL 2-D", "Modeling"],
]

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'self'; "
        "form-action 'self'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
}


@app.context_processor
def inject_globals():
    return {"app_name": "FLORA", "tagline": "Flower & Leaf Ornamental Recommendation Assistant", "dataset_stats": get_dataset_stats()}


@app.after_request
def add_security_headers(response):
    for header, value in SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)
    if request.is_secure:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


@app.route("/")
def beranda():
    return render_template("beranda.html", active_page="beranda")


@app.route("/favicon.ico")
def favicon():
    return redirect(url_for("static", filename="img/icon.png"))


@app.route("/healthz")
def healthz():
    stats = get_dataset_stats()
    return {"status": "ok", "plants": stats["plant_count"], "questions": stats["question_count"]}


@app.route("/rekomendasi", methods=["GET", "POST"])
def rekomendasi():
    questions = get_questions()
    result = None
    errors = []
    answers = {}

    if request.method == "POST":
        answers = {question["variable"]: request.form.get(question["variable"], "").strip() for question in questions}
        errors = validate_answers(answers, questions)
        if not errors:
            result = recommend_plants(answers)

    return render_template(
        "rekomendasi.html",
        active_page="rekomendasi",
        questions=questions,
        result=result,
        errors=errors,
        answers=answers,
    )


@app.route("/tentang")
def tentang():
    return render_template(
        "tentang.html",
        active_page="tentang",
        references=REFERENCES,
        members=MEMBERS,
    )


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
