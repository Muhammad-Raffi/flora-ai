# FLORA-AI

FLORA-AI adalah aplikasi web rekomendasi tanaman hias berbasis Flask dan Python.
FLORA berarti Forward Logic Ornamental Recommendation Assistant.

## Fitur

- Halaman Beranda dengan animasi teks FLORA per huruf dan underline responsif.
- Halaman Rekomendasi dengan form step-by-step yang ringan untuk diisi berulang.
- Logic rekomendasi Python terpisah di `ai/recommender.py`.
- Dataset Excel dibaca dari `References/dataset_FLORA.xlsx` tanpa menampilkan data mentah ke user.
- Halaman Tentang berisi referensi dan anggota kelompok.
- Header responsif dengan menu tengah di desktop dan burger menu di mobile.

## Cara Menjalankan

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app app run --debug
```

Buka aplikasi di:

```text
http://127.0.0.1:5000
```

Jika `py` tidak tersedia, gunakan path Python yang terpasang di komputer.

## Quality Gate Pra-Hosting

Install dependency test:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm install
npx playwright install chromium
```

Jalankan pemeriksaan:

```powershell
.\.venv\Scripts\python.exe -m compileall app.py ai
.\.venv\Scripts\python.exe -m pytest -q --cov=ai --cov=app --cov-fail-under=80
.\.venv\Scripts\python.exe -m pip_audit
npm run test:e2e
npm run lighthouse
```

Endpoint smoke test untuk hosting:

```text
/healthz
/
/rekomendasi
/tentang
```

Untuk production hosting Linux, gunakan WSGI server seperti:

```bash
gunicorn app:app
```

Untuk Windows hosting lokal, gunakan:

```powershell
waitress-serve --call app:app
```
