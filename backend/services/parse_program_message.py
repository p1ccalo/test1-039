import re
from sqlalchemy.orm import Session
from backend.models import Client, Exercise, ProgramExercise
from backend.utils import get_or_create_program

def _extract_blocks(txt: str):
    """
    Повертає список (block_num:int, block_text:str).
    Підтримує варіанти: "БЛОК №1", "БЛОК 1", "Блок№1", "БЛОК № 1" і т.д.
    Обрізає блок, якщо перед ним йде 'Д/З' (щоб блока не захопити далі).
    """
    header_re = re.compile(r'(?i)БЛОК\s*(?:№|#|No)?\s*(\d+)\b')  # case-insensitive
    matches = list(header_re.finditer(txt))
    if not matches:
        return []

    blocks = []
    for idx, m in enumerate(matches):
        block_num = int(m.group(1))
        start = m.end()
        # кінець — або початок наступного блоку, або кінець тексту
        next_start = matches[idx+1].start() if idx+1 < len(matches) else len(txt)

        # якщо між start і next_start є "Д/З" — обріжаємо до неї
        dz_rel = re.search(r'\bД/?З\b[:\s]', txt[start:next_start], flags=re.I)
        if dz_rel:
            end = start + dz_rel.start()
        else:
            end = next_start

        block_text = txt[start:end].strip()
        blocks.append((block_num, block_text))
    return blocks

from sqlalchemy import func

def parse_and_save_rehab_program(db: Session, client: Client, message_text: str, dry_run: bool = False):
    if dry_run:
        print("\n--- DRY RUN: Parsing Rehab Program ---")
        program = None # В сухом режиме не получаем программу из БД
    else:
        program, created = get_or_create_program(db, client.id, 2)  # курс 2 — Кінезіологія

    blocks = _extract_blocks(message_text)
    print("blocks:", blocks)
     # 4) парсинг рядків у блоці
    parsed_items = []
    stats = {"blocks_parsed": 0, "lines_parsed": 0, "ex_created": 0, "ex_found": 0}

    # Патерн: цифра. потім решта. Ми дозволяємо відсутність пробілу після крапки
    leading_num_re = re.compile(r'^\s*(\d+)\.\s*(.*)$')

    # Патерн для чисел у кінці: weight / repeats / sets
    tail_nums_re = re.compile(r'(?P<w>\d+(?:-\d+)?)\s*[/\\]\s*(?P<r>\d+)\s*[/\\]\s*(?P<s>\d+)\s*$', flags=re.U)

    for block_num, block_text in blocks:
        stats["blocks_parsed"] += 1
        if not block_text:
            continue
        lines = [ln.strip() for ln in block_text.splitlines() if ln.strip()]
        order_in_block = 1
        for line in lines:
            stats["lines_parsed"] += 1
            # Ігноруємо заголовки всередині блоку (наприклад, "Розминка: ...")
            # Обробляємо лише рядки що починаються з числа "1." або схожі, але також допускаємо
            # випадки без номера (на свій ризик).
            m = leading_num_re.match(line)
            if m:
                rest = m.group(2).strip()
            else:
                # Якщо рядок не починається з номера — все одно обробимо (іноді зустрічаються)
                rest = line

            # знайти в кінці параметри W/R/S
            tail = tail_nums_re.search(rest)
            if tail:
                weight = tail.group("w")
                repeats = tail.group("r")
                sets = tail.group("s")
                name = rest[:tail.start()].strip()
                order_num = order_in_block
            else:
                weight = None
                repeats = None
                sets = None
                name = rest
                order_num = None

            # Розбити name_part по символу '+'
            parts = [p.strip() for p in re.split(r'\s*\+\s*', name) if p.strip()]
            if not parts:
                continue

            for part in parts:
                # Нормалізуємо назву для пошуку (без видалення скорочень)
                search_name = part.strip()
                if not search_name:
                    continue

                # Шукаємо впраy (case-insensitive exact). Можна замінити на normalize_name логіку.
                exercise = db.query(Exercise).filter(func.lower(Exercise.name) == search_name.lower()).first()
                if not exercise:
                    if dry_run:
                        print(f"  [DRY-RUN] Would create new exercise (kinesio): '{name}'")
                    else:
                        exercise = Exercise(name=name, course_id=2)
                        db.add(exercise)
                        db.commit() # Коммитим сразу, чтобы получить ID для ProgramExercise
                        db.refresh(exercise)
                        print(f"✅ Додано нову вправу (кінезіо): {name}")
                    stats["ex_created"] += 1
                else:
                    stats["ex_found"] += 1
                
                if dry_run:
                    print(f"  [DRY-RUN] Would add exercise '{name}' to program. Details: W:{weight}, R:{repeats}, S:{sets}, Block:{block_num}")
                else:
                    # Проверяем, есть ли уже такая связка в программе
                    program_exercise = db.query(ProgramExercise).filter_by(program_id=program.id, exercise_id=exercise.id).first()
                    if not program_exercise:
                        program_exercise = ProgramExercise(
                            program_id=program.id,
                            exercise_id=exercise.id,
                            weight=weight,
                            repeats=repeats,
                            sets=sets,
                            block=int(block_num),
                            order_num=order_num
                        )
                        db.add(program_exercise)
                        print(f"✅ Додано вправу (кінезіо) '{name}' до програми")
                    else:
                        print(f"⚠️ Вправа (кінезіо) '{name}' вже існує у програмі, оновлюємо деталі.")
                        # Опционально: можно обновлять детали, если упражнение уже есть
                        program_exercise.weight = weight
                        program_exercise.repeats = repeats
                        program_exercise.sets = sets
                        program_exercise.block = int(block_num)
                        program_exercise.order_num = order_num

                order_in_block += 1
            
    print('stats:', stats)
    if not dry_run:
        db.commit()
        print("✅ Програма кінезіології збережена")
    else:
        print("--- DRY RUN Finished ---")

def parse_and_save_homework_program(db: Session, client: Client, message_text: str, dry_run: bool = False):
    if dry_run:
        print("\n--- DRY RUN: Parsing Homework Program ---")
        program = None # В сухом режиме не получаем программу из БД
    else:
        program, created = get_or_create_program(db, client.id, 1)  # курс 1 — Д/З
        if not created:
            # Если программа уже есть, и это не сухой запуск, выходим, чтобы не дублировать
            return

    homework_match = re.search(r"Д/З:\s*([\s\S]*?)(?:\n\n|\Z)", message_text)
    if not homework_match:
        print("⚠️ Д/З не знайдено")
        return
    
    homework_text = homework_match.group(1).strip()
    lines = [line.strip() for line in homework_text.splitlines() if line.strip()]
    if not lines:
        print("⚠️ Порожній блок Д/З")
        return

    order = 1
    for line in lines:
        line = re.sub(r"^\d+\.\s*", "", line).strip()  # прибираємо "1." "2." ...
        parts = [p.strip() for p in line.split("+") if p.strip()]

        for part in parts:
            exercises = []
            if re.search(r"\d,\d", part):  # якщо є перелік через кому (тільки особливий випадок)
                base = re.match(r"([^\d]+)\s*(.*)", part)
                if base:
                    name = base.group(1).strip()
                    numbers = base.group(2).replace(" ", "")
                    for n in numbers.split(","):
                        exercises.append(f"{name} {n}")
                else:
                    exercises.append(part)
            else:
                exercises.append(part)

            for ex_name in exercises:
                if dry_run:
                    print(f"  [DRY-RUN] Would find or create exercise (Д/З): '{ex_name}'")
                    print(f"  [DRY-RUN] Would add exercise '{ex_name}' to homework program.")
                else:
                    exercise = db.query(Exercise).filter(Exercise.name == ex_name).first()
                    if not exercise:
                        exercise = Exercise(name=ex_name, course_id=1)
                        db.add(exercise)
                        db.commit() # Коммитим сразу, чтобы получить ID
                        db.refresh(exercise)
                        print(f"✅ Додано нову вправу (Д/З): {ex_name}")

                    program_exercise = ProgramExercise(
                        program_id=program.id,
                        exercise_id=exercise.id,
                        repeats=5, # По умолчанию для Д/З
                        order_num=order
                    )
                    db.add(program_exercise)

                order += 1

    if not dry_run:
        db.commit()
        print("✅ Програма Д/З збережена")
    else:
        print("--- DRY RUN Finished ---")
