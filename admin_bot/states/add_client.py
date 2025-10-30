from aiogram.dispatcher.filters.state import State, StatesGroup

class AddClient(StatesGroup):
    name = State()
    birth_date = State()

    symptoms = State()
    symptoms_where = State()
    symptoms_how_long = State()
    symptoms_pain_level = State()
    blood_pressure = State()

    activities = State()
    research_feet = State()
    research_knees = State()
    research_pelvis = State()
    research_posture = State()

    func_back_thoracic = State()
    func_back_lumbar = State()
    func_back_neck = State()
    func_hips = State()
    func_knees = State()
    func_ankles = State()
    func_feet = State()
    func_symmetry = State()
    func_shoulders = State()
    func_elbows = State()
    func_wrists = State()

    work_conditions = State()
    sport = State()
    supplements = State()
    home_devices = State()

    conclusion = State()
    massage_recommendation = State()

    insoles = State()
    preventive_devices = State()
    photos = State()
    finish = State()


STATE_TITLES = {
    "name": "ім'я клієнта",
    "birth_date": "дату народження",

    "symptoms": "що турбує",
    "symptoms_where": "де турбує",
    "symptoms_how_long": "як давно турбує",
    "symptoms_pain_level": "больові відчуття (0–10)",
    "blood_pressure": "артеріальний тиск",

    "activities": "чим займається / які обстеження проходив(ла)",
    "research_feet": "результати огляду — стопи",
    "research_knees": "результати огляду — коліна",
    "research_pelvis": "результати огляду — таз",
    "research_posture": "результати огляду — постава",

    "func_back_thoracic": "тригери спини — грудний відділ",
    "func_back_lumbar": "тригери спини — поперековий відділ",
    "func_back_neck": "тригери спини — шия",
    "func_hips": "кульшові суглоби",
    "func_knees": "колінні суглоби",
    "func_ankles": "гомілковостопні суглоби",
    "func_feet": "стопи",
    "func_symmetry": "симетрію нижніх кінцівок",
    "func_shoulders": "плечі",
    "func_elbows": "лікті",
    "func_wrists": "зап’ястя",

    "work_conditions": "умови роботи",
    "sport": "заняття спортом/фітнесом",
    "supplements": "використання БАДів у харчуванні",
    "home_devices": "домашні масажери/тренажери",

    "conclusion": "висновок",
    "massage_recommendation": "рекомендації щодо масажу",
    "insoles": "виготовлення індивідуальних устілок",
    "preventive_devices": "запобіжні прилади для дому",
    "photos": "фото клієнта",
}

