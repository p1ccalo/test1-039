import re

# Паттерны для извлечения информации из сплошного текста
PATTERNS = {
    "name": r"(?:меня зовут|имя)\s+([А-Яа-яЁё]+)",
    "birth_date": r"(\d{1,2}\s+(?:января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)\s+\d{4})|(\d{2}\.\d{2}\.\d{4})",
    "age": r"(?:мне|возраст)\s+(\d+)\s+(?:лет|год|года)",
    "symptoms": r"(?:беспокоит|болит|жалуюсь на)\s+([^.,\n]+)",
    "symptoms_where": r"(?:болит в|в области|в районе)\s+([^.,\n]+)",
    "symptoms_how_long": r"(?:как давно|уже|в течени[еи])\s+([^.,\n]+)",
    "symptoms_pain_level": r"(?:боль по шкале|уровень боли|оцениваю боль в)\s+(\d+)\s*(?:из|до)\s*10",
}

def extract_answers(text: str) -> dict:
    """
    Извлекает ответы клиента из сплошного текста или текста формата "вопрос-ответ".
    """
    # Инициализируем все возможные ключи пустыми строками
    results = {
        "name": "", "birth_date": "", "age": "", "symptoms": "", "symptoms_where": "",
        "symptoms_how_long": "", "symptoms_pain_level": "", "blood_pressure": "",
        "activities": "", "research_feet": "", "research_knees": "", "research_pelvis": "",
        "research_posture": "", "func_back_thoracic": "", "func_back_lumbar": "",
        "func_back_neck": "", "func_hips": "", "func_knees": "", "func_ankles": "",
        "func_feet": "", "func_symmetry": "", "func_shoulders": "", "func_elbows": "",
        "func_wrists": "", "work_conditions": "", "sport": "", "supplements": "",
        "home_devices": "", "conclusion": "", "massage_recommendation": "", "insoles": "",
        "preventive_devices": ""
    }

    for key, pattern in PATTERNS.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Находим первое непустое совпадение из всех групп
            answer = next((g for g in match.groups() if g), None)
            if answer:
                results[key] = answer.strip()

    # Специальная логика для симптомов, если не нашлось по точному паттерну
    if not results["symptoms"]:
        match = re.search(r"болит\s+([^.,\n]+)", text, re.IGNORECASE)
        if match:
            results["symptoms"] = match.group(1).strip()

    # Если возраст был извлечен, добавим его в birth_date для информации
    if results["age"] and not results["birth_date"]:
        results["birth_date"] = f"Примерно {results['age']} лет"

    return results

