import pandas as pd
import pytest

import ai.recommender as recommender


def valid_answers(**overrides):
    answers = {
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
    answers.update(overrides)
    return answers


def test_dataset_stats_and_questions_are_loaded():
    stats = recommender.get_dataset_stats()
    questions = recommender.get_questions()

    assert stats == {"plant_count": 30, "question_count": 10}
    assert len(questions) == 10
    assert questions[0]["variable"] == "cahaya"
    assert questions[0]["choices"] == [
        {"value": "rendah", "label": "Rendah"},
        {"value": "sedang", "label": "Sedang"},
        {"value": "tinggi", "label": "Tinggi"},
    ]


def test_validate_answers_accepts_complete_allowed_values():
    errors = recommender.validate_answers(valid_answers(), recommender.get_questions())

    assert errors == []


def test_validate_answers_reports_missing_and_invalid_values():
    answers = valid_answers(cahaya="", penyiraman="banjir")
    errors = recommender.validate_answers(answers, recommender.get_questions())

    assert any("belum dipilih" in error for error in errors)
    assert any("tidak valid" in error for error in errors)


def test_recommend_plants_returns_ranked_recommendations():
    result = recommender.recommend_plants(valid_answers())

    assert result["summary"] == "Sansevieria menjadi pilihan utama untuk kondisi cahaya Rendah dan posisi Indoor."
    assert [item["rank"] for item in result["recommendations"]]
    assert result["recommendations"][0]["name"] == "Sansevieria"
    assert result["recommendations"][0]["status"] == "Paling Disarankan"
    assert result["recommendations"][0]["image_filename"] == "img/flowers/sansevieria.jpg"
    assert len(result["recommendations"][0]["reasons"]) <= 5
    assert len(result["recommendations"][0]["badges"]) == len(recommender.BADGE_FIELDS)


def test_recommend_plants_handles_free_visual_preference():
    result = recommender.recommend_plants(valid_answers(jenis_tampilan="bebas", hewan_peliharaan="ya", nyaman_duri="ya"))

    assert 1 <= len(result["recommendations"]) <= recommender.MAX_RECOMMENDATIONS
    assert result["recommendations"][0]["name"]
    assert "Bebas" not in result["summary"]


def test_condition_matching_treats_free_values_as_wildcards():
    assert recommender._condition_matches("bebas", "daun")
    assert recommender._condition_matches("daun", "bebas")
    assert recommender._condition_matches("tidak_masalah", "tinggi")
    assert not recommender._condition_matches("daun", "bunga")


def test_parse_conditions_normalizes_rule_text():
    conditions = recommender._parse_conditions("cahaya=Rendah AND jenis_tampilan=daun AND invalid")

    assert conditions == {"cahaya": "rendah", "jenis_tampilan": "daun"}


def test_image_for_unknown_plant_uses_fallback():
    plant = pd.Series({"nama_tanaman": "Tanaman Tidak Ada"})

    assert recommender._image_for_plant(plant) == recommender.FALLBACK_PLANT_IMAGE


def test_dataset_validation_rejects_missing_columns():
    frame = pd.DataFrame({"kode_tanaman": ["T001"]})

    with pytest.raises(ValueError, match="Kolom sheet tanaman belum lengkap"):
        recommender._validate_columns(frame, recommender.REQUIRED_PLANT_COLUMNS, "tanaman")


def test_dataset_validation_rejects_invalid_rule_value():
    plants = pd.DataFrame(
        [
            {
                "kode_tanaman": "T001",
                "nama_tanaman": "Sansevieria",
                "nama_umum_lain": "Snake Plant",
                "deskripsi_singkat": "Tanaman daun.",
                "cahaya": "rendah",
                "penyiraman": "jarang",
                "posisi": "indoor",
                "ruang": "kecil",
                "perawatan": "mudah",
                "pet_safe": "tidak",
                "berduri_tajam": "tidak",
                "budget": "rendah",
                "jenis_tampilan": "daun",
                "ukuran": "kecil",
                "alasan_rekomendasi": "Cocok.",
            }
        ]
    )
    questions = pd.DataFrame(
        [
            {
                "kode_pertanyaan": "P001",
                "variabel": "cahaya",
                "pertanyaan": "Cahaya?",
                "pilihan": "rendah|sedang",
                "keterangan": "",
            }
        ]
    )
    rules = pd.DataFrame([{"kode_rule": "R001", "kondisi": "cahaya=tinggi", "hasil": "Sansevieria"}])

    with pytest.raises(ValueError, match="nilai di luar pilihan"):
        recommender._validate_dataset(plants, questions, rules, recommender._build_plant_key_map(plants))
