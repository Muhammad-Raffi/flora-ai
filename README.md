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
