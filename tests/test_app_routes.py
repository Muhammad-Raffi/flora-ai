from ai.recommender import get_questions


def valid_answers():
    values = {
        "cahaya": "rendah",
        "penyiraman": "jarang",
        "posisi": "indoor",
        "ruang": "kecil",
        "perawatan": "mudah",
        "hewan_peliharaan": "tidak",
        "nyaman_duri": "tidak",
        "budget": "rendah",
        "jenis_tampilan": "daun",
        "ukuran": "kecil",
    }
    return {question["variable"]: values[question["variable"]] for question in get_questions()}


def assert_security_headers(response):
    assert response.headers["Content-Security-Policy"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers["Permissions-Policy"]


def test_main_routes_render_successfully(client):
    for path, expected in [
        ("/", b"Mulai Rekomendasi"),
        ("/rekomendasi", b"Jawab satu per satu"),
        ("/tentang", b"Anggota Kelompok"),
    ]:
        response = client.get(path)

        assert response.status_code == 200
        assert expected in response.data
        assert_security_headers(response)


def test_healthz_reports_dataset_status(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json == {"status": "ok", "plants": 30, "questions": 10}
    assert_security_headers(response)


def test_favicon_redirects_to_static_icon(client):
    response = client.get("/favicon.ico")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/static/img/icon.png")


def test_rekomendasi_empty_post_shows_validation_errors(client):
    response = client.post("/rekomendasi", data={})

    assert response.status_code == 200
    assert b"Belum bisa diproses" in response.data
    assert b"belum dipilih" in response.data
    assert_security_headers(response)


def test_rekomendasi_rejects_invalid_value_without_raw_script(client):
    payload = valid_answers()
    payload["cahaya"] = "<script>alert(1)</script>"

    response = client.post("/rekomendasi", data=payload)

    assert response.status_code == 200
    assert b"tidak valid" in response.data
    assert b"<script>alert" not in response.data


def test_rekomendasi_valid_post_returns_result(client):
    response = client.post("/rekomendasi", data=valid_answers())

    assert response.status_code == 200
    assert b"Hasil rekomendasi" in response.data
    assert b"Sansevieria" in response.data
    assert b"Foto tanaman Sansevieria" in response.data


def test_rekomendasi_ignores_extra_fields(client):
    payload = valid_answers()
    payload["unexpected"] = "<script>alert(1)</script>"

    response = client.post("/rekomendasi", data=payload)

    assert response.status_code == 200
    assert b"Hasil rekomendasi" in response.data
    assert b"<script>alert" not in response.data


def test_method_not_allowed_and_404_are_safe(client):
    method_response = client.put("/rekomendasi")
    missing_response = client.get("/not-found-check")

    assert method_response.status_code == 405
    assert missing_response.status_code == 404
    assert b"Traceback" not in missing_response.data
    assert b"Werkzeug Debugger" not in missing_response.data
