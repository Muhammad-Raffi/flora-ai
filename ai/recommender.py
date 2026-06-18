from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import re
from typing import Any

import pandas as pd

DATASET_PATH = Path(__file__).resolve().parents[1] / "References" / "dataset_FLORA.xlsx"
STATIC_DIR = Path(__file__).resolve().parents[1] / "static"

REQUIRED_SHEETS = {"tanaman", "pertanyaan", "rules"}
REQUIRED_PLANT_COLUMNS = {
    "kode_tanaman",
    "nama_tanaman",
    "nama_umum_lain",
    "deskripsi_singkat",
    "cahaya",
    "penyiraman",
    "posisi",
    "ruang",
    "perawatan",
    "pet_safe",
    "berduri_tajam",
    "budget",
    "jenis_tampilan",
    "ukuran",
    "alasan_rekomendasi",
}
REQUIRED_QUESTION_COLUMNS = {"kode_pertanyaan", "variabel", "pertanyaan", "pilihan", "keterangan"}
REQUIRED_RULE_COLUMNS = {"kode_rule", "kondisi", "hasil"}

FREE_VALUES = {"bebas", "tidak_masalah"}
PET_VARIABLE = "hewan_peliharaan"
THORN_COMFORT_VARIABLE = "nyaman_duri"
THORN_PLANT_ATTRIBUTE = "berduri_tajam"
# Unused by final recommendation template; kept in comments for easy restore.
# QUESTION_HINTS = {
#     "cahaya": "rendah=minim cahaya langsung; sedang=cahaya tidak langsung; tinggi=terang atau terkena matahari pagi/sore.",
#     "penyiraman": "jarang=1-2 kali seminggu; sedang=2-4 kali seminggu; sering=hampir setiap hari sesuai kebutuhan.",
#     "posisi": "indoor=di dalam ruangan; outdoor=teras, balkon, halaman, atau area luar.",
#     "ruang": "kecil=meja/rak; sedang=sudut ruangan/teras; besar=halaman atau sudut ruangan luas.",
#     "perawatan": "mudah=cocok untuk pemula; sedang=perlu perhatian rutin; sulit=perlu perawatan lebih teliti.",
#     "hewan_peliharaan": "ya=ada hewan peliharaan; tidak=tidak ada atau tidak akan menyentuh tanaman.",
#     "nyaman_duri": "ya=nyaman dengan duri atau bagian tajam; tidak=hindari duri atau bagian tajam.",
#     "budget": "rendah=terjangkau; sedang=menengah; tinggi=lebih mahal atau ukuran lebih besar.",
#     "jenis_tampilan": "bebas=tidak ada preferensi; daun=fokus daun; bunga=fokus bunga; kaktus=tampilan kaktus.",
#     "ukuran": "kecil=meja/rak; sedang=pot lantai kecil/teras; besar=sudut ruangan luas/halaman.",
# }
FLOWER_IMAGE_DIR = "img/flowers"
FALLBACK_PLANT_IMAGE = f"{FLOWER_IMAGE_DIR}/default.jpg"
FLOWER_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
MAX_RECOMMENDATIONS = 3

STATUS_LABELS = ["Paling Disarankan", "Alternatif Terbaik", "Alternatif Lain yang Cocok"]
BADGE_FIELDS = [
    "cahaya",
    "penyiraman",
    "posisi",
    "ruang",
    "perawatan",
    "budget",
    "jenis_tampilan",
    "ukuran",
    "pet_safe",
    "berduri_tajam",
]


def _normalize(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def _title_value(value: Any) -> str:
    return _normalize(value).replace("_", " ").replace("-", " ").title()


def _split_choices(value: Any) -> list[str]:
    return [_normalize(choice) for choice in str(value).split("|") if str(choice).strip()]


@lru_cache(maxsize=1)
def _load_dataset() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, str], dict[str, str]]:
    book = pd.ExcelFile(DATASET_PATH)
    missing_sheets = REQUIRED_SHEETS.difference(book.sheet_names)
    if missing_sheets:
        raise ValueError(f"Sheet dataset belum lengkap: {', '.join(sorted(missing_sheets))}.")

    plants = pd.read_excel(DATASET_PATH, sheet_name="tanaman").fillna("")
    questions = pd.read_excel(DATASET_PATH, sheet_name="pertanyaan").fillna("")
    rules = pd.read_excel(DATASET_PATH, sheet_name="rules").fillna("")

    _validate_columns(plants, REQUIRED_PLANT_COLUMNS, "tanaman")
    _validate_columns(questions, REQUIRED_QUESTION_COLUMNS, "pertanyaan")
    _validate_columns(rules, REQUIRED_RULE_COLUMNS, "rules")

    plant_keys = _build_plant_key_map(plants)
    rule_display_names = _build_rule_display_names(plants, rules, plant_keys)
    _validate_dataset(plants, questions, rules, plant_keys)
    return questions, plants, rules, plant_keys, rule_display_names


def _validate_columns(frame: pd.DataFrame, required_columns: set[str], sheet_name: str) -> None:
    missing_columns = required_columns.difference(frame.columns)
    if missing_columns:
        raise ValueError(
            f"Kolom sheet {sheet_name} belum lengkap: {', '.join(sorted(missing_columns))}."
        )


def _build_plant_key_map(plants: pd.DataFrame) -> dict[str, str]:
    plant_keys: dict[str, str] = {}
    for _, plant in plants.iterrows():
        key = _normalize(plant["kode_tanaman"])
        names = {plant["kode_tanaman"], plant["nama_tanaman"], plant["nama_umum_lain"]}
        for name in names:
            normalized_name = _normalize(name)
            if normalized_name:
                plant_keys[normalized_name] = key
    return plant_keys


def _build_rule_display_names(
    plants: pd.DataFrame,
    rules: pd.DataFrame,
    plant_keys: dict[str, str],
) -> dict[str, str]:
    return {
        _normalize(plant["kode_tanaman"]): str(plant["nama_tanaman"]).strip()
        for _, plant in plants.iterrows()
    }


def _validate_dataset(
    plants: pd.DataFrame,
    questions: pd.DataFrame,
    rules: pd.DataFrame,
    plant_keys: dict[str, str],
) -> None:
    question_variables = {_normalize(variable) for variable in questions["variabel"]}

    question_choices = {
        _normalize(row["variabel"]): set(_split_choices(row["pilihan"]))
        for _, row in questions.iterrows()
    }


    invalid_results: list[str] = []
    invalid_variables: list[str] = []
    invalid_values: list[str] = []

    for _, rule in rules.iterrows():
        conditions = _parse_conditions(str(rule["kondisi"]))

        if not _resolve_plant_key(rule["hasil"], plants, plant_keys):
            invalid_results.append(str(rule["hasil"]))

        for variable, expected in conditions.items():

            if variable not in question_variables:
                invalid_variables.append(variable)
                continue
            if expected not in question_choices.get(variable, set()):
                invalid_values.append(f"{variable}={expected}")


    if invalid_variables:
        raise ValueError(f"Rules memakai variabel yang tidak ada di pertanyaan: {', '.join(sorted(set(invalid_variables)))}.")
    if invalid_values:
        raise ValueError(f"Rules memakai nilai di luar pilihan pertanyaan: {', '.join(sorted(set(invalid_values)))}.")
    if invalid_results:
        raise ValueError(f"Rules menghasilkan tanaman yang tidak ada di sheet tanaman: {', '.join(sorted(set(invalid_results)))}.")


def get_dataset_stats() -> dict[str, int]:
    questions, plants, _, _, _ = _load_dataset()
    return {"plant_count": len(plants), "question_count": len(questions)}


def get_questions() -> list[dict[str, Any]]:
    questions, _, _, _, _ = _load_dataset()
    mapped_questions: list[dict[str, Any]] = []

    for index, row in questions.iterrows():
        choices = _split_choices(row["pilihan"])
        mapped_questions.append(
            {
                "code": str(row["kode_pertanyaan"]),
                "variable": str(row["variabel"]),
                "question": str(row["pertanyaan"]),
                # "hint": QUESTION_HINTS.get(_normalize(row["variabel"]), str(row["keterangan"])),
                "choices": [{"value": choice, "label": _title_value(choice)} for choice in choices],
                "step": index + 1,
            }
        )

    return mapped_questions


def validate_answers(answers: dict[str, str], questions: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    allowed = {question["variable"]: {choice["value"] for choice in question["choices"]} for question in questions}

    for question in questions:
        variable = question["variable"]
        value = _normalize(answers.get(variable, ""))
        if not value:
            errors.append(f"Jawaban untuk '{question['question']}' belum dipilih.")
            continue
        if value not in allowed[variable]:
            errors.append(f"Pilihan untuk {variable.replace('_', ' ')} tidak valid.")

    return errors


def recommend_plants(answers: dict[str, str]) -> dict[str, Any]:
    _, plants, rules, plant_keys, rule_display_names = _load_dataset()
    normalized_answers = {key: _normalize(value) for key, value in answers.items()}
    evaluated_rules = _evaluate_rules(rules, plants, plant_keys, normalized_answers)

    active_rules = [rule for rule in evaluated_rules if rule["is_active"]]
    selected_rules = active_rules or evaluated_rules
    selected_rules.sort(
        key=lambda rule: (
            rule["matched_count"],
            rule["attribute_matches"],
            rule["total_conditions"],
        ),
        reverse=True,
    )

    recommendations = _build_recommendations(
        selected_rules,
        plants,
        rule_display_names,
        normalized_answers,
    )

    return {
        "answers": normalized_answers,
        "recommendations": recommendations,
        "summary": _build_summary(normalized_answers, recommendations),
    }


def _evaluate_rules(
    rules: pd.DataFrame,
    plants: pd.DataFrame,
    plant_keys: dict[str, str],
    answers: dict[str, str],
) -> list[dict[str, Any]]:
    evaluated: list[dict[str, Any]] = []

    for _, rule in rules.iterrows():
        conditions = _parse_conditions(str(rule["kondisi"]))
        plant_key = _resolve_plant_key(rule["hasil"], plants, plant_keys)
        if not plant_key or not conditions:
            continue

        matched_conditions = [
            (variable, expected)
            for variable, expected in conditions.items()
            if _condition_matches(answers.get(variable, ""), expected)
        ]
        plant = _get_plant_by_key(plants, plant_key)
        attribute_matches, _ = _count_plant_attributes(plant, answers)

        evaluated.append(
            {
                "rule_code": str(rule["kode_rule"]),
                "plant_key": plant_key,
                "rule_result": str(rule["hasil"]).strip(),
                "conditions": conditions,
                "matched_conditions": matched_conditions,
                "matched_count": len(matched_conditions),
                "total_conditions": len(conditions),
                "attribute_matches": attribute_matches,
                "is_active": len(matched_conditions) == len(conditions),
            }
        )

    return evaluated


def _condition_matches(actual: str, expected: str) -> bool:
    if actual in FREE_VALUES or expected in FREE_VALUES:
        return True
    return actual == expected


def _parse_conditions(condition_text: str) -> dict[str, str]:
    conditions: dict[str, str] = {}
    for chunk in condition_text.split(" AND "):
        if "=" not in chunk:
            continue
        variable, expected = chunk.split("=", 1)
        conditions[_normalize(variable)] = _normalize(expected)
    return conditions


def _resolve_plant_key(rule_result: Any, plants: pd.DataFrame, plant_keys: dict[str, str]) -> str | None:
    normalized_result = _normalize(rule_result)
    if normalized_result in plant_keys:
        return plant_keys[normalized_result]

    for _, plant in plants.iterrows():
        plant_key = _normalize(plant["kode_tanaman"])
        aliases = [_normalize(plant["nama_tanaman"]), _normalize(plant["nama_umum_lain"])]
        if any(alias and alias in normalized_result for alias in aliases):
            return plant_key
        if any(normalized_result and normalized_result in alias for alias in aliases):
            return plant_key
    return None


def _get_plant_by_key(plants: pd.DataFrame, plant_key: str) -> pd.Series:
    match = plants[plants["kode_tanaman"].map(_normalize) == plant_key]
    if match.empty:
        raise ValueError(f"Tanaman dengan kode {plant_key} tidak ditemukan.")
    return match.iloc[0]


def _build_recommendations(
    selected_rules: list[dict[str, Any]],
    plants: pd.DataFrame,
    rule_display_names: dict[str, str],
    answers: dict[str, str],
) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    used_plant_keys: set[str] = set()

    for rule in selected_rules:
        plant_key = rule["plant_key"]
        if plant_key in used_plant_keys:
            continue

        plant = _get_plant_by_key(plants, plant_key)
        matched_count, matched_attributes = _count_plant_attributes(plant, answers)
        reasons = _build_reason_list(rule, plant, matched_attributes)
        index = len(recommendations)
        recommendations.append(
            {
                "rank": index + 1,
                "status": STATUS_LABELS[index],
                "name": rule_display_names.get(plant_key, _format_plant_name(plant)),
                "description": str(plant["deskripsi_singkat"]),
                "care": str(plant["alasan_rekomendasi"]),
                "reasons": reasons,
                "badges": _build_badges(plant),
                "image_filename": _image_for_plant(plant),
                "matched_rule": rule["rule_code"],
            }
        )
        used_plant_keys.add(plant_key)

        if len(recommendations) == MAX_RECOMMENDATIONS:
            break

    return recommendations


def _count_plant_attributes(plant: pd.Series, answers: dict[str, str]) -> tuple[int, list[str]]:
    matched_attributes: list[str] = []
    plant_map = {_normalize(key): _normalize(value) for key, value in plant.to_dict().items()}

    for variable, answer in answers.items():
        if not answer or answer in FREE_VALUES:
            continue

        if variable == PET_VARIABLE:
            pet_safe = plant_map.get("pet_safe", "")
            if answer == "ya" and pet_safe == "ya":
                matched_attributes.append("aman untuk rumah dengan hewan peliharaan")
            elif answer == "tidak":
                matched_attributes.append("tidak membutuhkan prioritas aman untuk hewan")
            continue

        if variable == THORN_COMFORT_VARIABLE:
            has_thorns = plant_map.get(THORN_PLANT_ATTRIBUTE, "")
            if answer == "tidak" and has_thorns == "tidak":
                matched_attributes.append("tidak berduri atau tajam")
            elif answer == "ya":
                matched_attributes.append("sesuai untuk pengguna yang nyaman dengan duri")
            continue

        if variable in plant_map and plant_map[variable] == answer:
            matched_attributes.append(f"{_field_label(variable)} sesuai")

    return len(matched_attributes), matched_attributes[:5]


def _build_reason_list(rule: dict[str, Any], plant: pd.Series, matched_attributes: list[str]) -> list[str]:
    reasons = [
        f"{_field_label(variable)} {_title_value(expected)} sesuai pilihan."
        for variable, expected in rule["matched_conditions"][:4]
    ]

    for attribute in matched_attributes:
        sentence = f"{attribute[:1].upper()}{attribute[1:]}."
        if sentence not in reasons:
            reasons.append(sentence)

    if not reasons:
        reasons.append(str(plant["alasan_rekomendasi"]))
    return reasons[:5]


def _build_badges(plant: pd.Series) -> list[str]:
    badges: list[str] = []
    for field in BADGE_FIELDS:
        value = _normalize(plant[field])
        if not value:
            continue
        if field == "pet_safe":
            label = "Aman untuk hewan"
        elif field == THORN_PLANT_ATTRIBUTE:
            label = "Berduri/tajam"
        else:
            label = _field_label(field)
        badges.append(f"{label}: {_title_value(value)}")
    return badges


def _format_plant_name(plant: pd.Series) -> str:
    return str(plant["nama_tanaman"]).strip()


def _slugify_image_name(value: Any) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", _normalize(value))
    return slug.strip("-")


def _image_for_plant(plant: pd.Series) -> str:
    slug = _slugify_image_name(plant["nama_tanaman"])
    for extension in FLOWER_IMAGE_EXTENSIONS:
        image_filename = f"{FLOWER_IMAGE_DIR}/{slug}{extension}"
        if (STATIC_DIR / image_filename).exists():
            return image_filename
    return FALLBACK_PLANT_IMAGE


def _field_label(field: str) -> str:
    labels = {
        "cahaya": "Cahaya",
        "penyiraman": "Penyiraman",
        "posisi": "Posisi",
        "ruang": "Ruang",
        "perawatan": "Perawatan",
        "hewan_peliharaan": "Hewan Peliharaan",
        "nyaman_duri": "Kenyamanan Duri",
        "budget": "Budget",
        "jenis_tampilan": "Jenis Tampilan",
        "ukuran": "Ukuran",
        "pet_safe": "Aman Untuk Hewan",
        "berduri_tajam": "Berduri/Tajam",
    }
    return labels.get(field, field.replace("_", " ").title())


def _build_summary(answers: dict[str, str], recommendations: list[dict[str, Any]]) -> str:
    if not recommendations:
        return "Belum ada rekomendasi yang cukup kuat. Coba ubah beberapa pilihan utama."

    top = recommendations[0]
    light = _title_value(answers.get("cahaya", ""))
    position = _title_value(answers.get("posisi", ""))
    return f"{top['name']} menjadi pilihan utama untuk kondisi cahaya {light} dan posisi {position}."
