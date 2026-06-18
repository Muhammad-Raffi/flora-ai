# Unused for final demo; kept as comment in case project paths are needed later.
# from pathlib import Path

from flask import Flask, redirect, render_template, request, url_for

from ai.recommender import get_dataset_stats, get_questions, recommend_plants, validate_answers


app = Flask(__name__)

# PROJECT_ROOT = Path(__file__).resolve().parent

REFERENCES = [
    "Implementasi Inferensi Forward Chaining Pada Sistem - Sebagai Jurnal Utama",
    "Sistem Pakar Pemilihan Bibit Padi Unggul dengan Metode Forward Chaining - Sebagai Jurnal Pendukung",
    "Growing Indoor Plants with Success - Sebagai Referensi Ilmiah Kondisi Tanaman",
]

MEMBERS = [
    ["Anggota 1", "Muhammad Raffi", "2411082039", "TRPL 2-D", "Ketua"],
    ["Anggota 2", "Wildan Hafidh", "2411082034", "TRPL 2-D", "Data Processing"],
    ["Anggota 3", "Restia Amelia", "2411081038", "TRPL 2-D", "Modeling"],
    ["Anggota 4", "Long afternoon", "secret (?)", "secret (?)", "Support System"],
]


@app.context_processor
def inject_globals():
    return {"app_name": "FLORA", "tagline": "Flower & Leaf Ornamental Recommendation Assistant", "dataset_stats": get_dataset_stats()}


@app.route("/")
def beranda():
    return render_template("beranda.html", active_page="beranda")


@app.route("/favicon.ico")
def favicon():
    return redirect(url_for("static", filename="img/icon.png"))


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
    app.run(debug=True)
