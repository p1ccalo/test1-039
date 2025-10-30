# clean_duplicates.py
"""
Скрипт для видалення/злиття дублікатів у таблиці Exercise.

Алгоритм:
- Нормалізує назву вправи (trim, lower, collapse spaces, remove trailing punctuation)
- Якщо нормалізоване ім'я вже зустрічалося — вважаємо поточний запис дублем
  і переносимо всі ProgramExercise зв'язки на canonical вправу.
  Якщо існує вже ProgramExercise з таким же (program_id, block, order_num) для canonical,
  то ми мерджимо інформацію (деталі/вага/повтори/підходи) і видаляємо дубль.
- Якщо нормалізованого імені ще не було — зберігаємо як canonical і (за бажанням)
  оновлюємо її назву у базі.
- Скрипт підтримує режим DRY_RUN (за замовчуванням True).
Перед запуском ОБОВ'ЯЗКОВО зробіть бекап бази.
"""

import re
from sqlalchemy.orm import Session
from db import SessionLocal
from models import Exercise, ProgramExercise  # підлаштуй шлях якщо потрібно

# ========== НАЛАШТУВАННЯ ==========
DRY_RUN = False  # True — тільки лог, False — застосовує зміни
# ==================================


def normalize_exercise_name(name: str) -> str:
    """Проста нормалізація — без розшифровки скорочень."""
    if not name:
        return ""
    s = name.strip().lower()
    s = re.sub(r'\s+', ' ', s)          # множинні пробіли -> один
    s = s.rstrip(' .,:;')               # прибираємо кінцеві знаки пунктуації
    return s


def clean_duplicates(dry_run: bool = True):
    db: Session = SessionLocal()
    try:
        exercises = db.query(Exercise).order_by(Exercise.id).all()
        seen = {}  # norm_name -> canonical Exercise object

        stats = {
            "total_exercises": len(exercises),
            "normalized": 0,
            "duplicates_found": 0,
            "duplicates_removed": 0,
            "reassigned_relations": 0,
            "merged_relations": 0,
        }

        print(f"Total exercises in DB: {stats['total_exercises']}")
        for ex in exercises:
            orig_name = ex.name or ""
            norm = normalize_exercise_name(orig_name)

            if not norm:
                print(f"[WARN] Exercise id={ex.id} has empty name -> skipping normalization.")
                continue

            if norm in seen:
                canonical = seen[norm]
                stats["duplicates_found"] += 1
                print(f"\n[DUPE] '{orig_name}' (id={ex.id}) → canonical '{canonical.name}' (id={canonical.id})")

                # Знаходимо всі ProgramExercise для цього дубля
                rels = db.query(ProgramExercise).filter(ProgramExercise.exercise_id == ex.id).all()
                print(f"  Found {len(rels)} ProgramExercise rows to reassign/merge.")

                for pe in rels:
                    # Перевіряємо, чи вже існує аналогічний запис для canonical у тій же програмі/блоці/порядку
                    exists = db.query(ProgramExercise).filter(
                        ProgramExercise.program_id == pe.program_id,
                        ProgramExercise.exercise_id == canonical.id,
                        ProgramExercise.block == pe.block,
                        ProgramExercise.order_num == pe.order_num
                    ).first()

                    if exists:
                        # Merge details (якщо у exists немає даних — беремо з pe)
                        changed = False
                        if (not exists.details or exists.details.strip() == "") and (pe.details and pe.details.strip()):
                            exists.details = pe.details
                            changed = True
                        if (exists.weight is None) and (pe.weight is not None):
                            exists.weight = pe.weight
                            changed = True
                        if (exists.repeats is None) and (pe.repeats is not None):
                            exists.repeats = pe.repeats
                            changed = True
                        if (exists.sets is None) and (pe.sets is not None):
                            exists.sets = pe.sets
                            changed = True

                        if dry_run:
                            print(f"    [MERGE-DRY] ProgramExercise id={pe.id} -> merged into id={exists.id}, changed={changed}")
                            stats["merged_relations"] += 1
                        else:
                            print(f"    [MERGE] ProgramExercise id={pe.id} -> merged into id={exists.id}, changed={changed}")
                            stats["merged_relations"] += 1
                            # видаляємо дубль
                            db.delete(pe)

                    else:
                        # Просто перепризначаємо на canonical.exercise_id
                        if dry_run:
                            print(f"    [REASSIGN-DRY] ProgramExercise id={pe.id} : exercise_id {pe.exercise_id} -> {canonical.id}")
                            stats["reassigned_relations"] += 1
                        else:
                            print(f"    [REASSIGN] ProgramExercise id={pe.id} : exercise_id {pe.exercise_id} -> {canonical.id}")
                            pe.exercise_id = canonical.id
                            stats["reassigned_relations"] += 1

                # Після того як всі зв'язки оброблені — можна видалити запис про вправу
                if dry_run:
                    print(f"  [DELETE-DRY] Would delete Exercise id={ex.id} ('{orig_name}')")
                    stats["duplicates_removed"] += 1
                else:
                    print(f"  [DELETE] Deleting Exercise id={ex.id} ('{orig_name}')")
                    db.delete(ex)
                    stats["duplicates_removed"] += 1

            else:
                # перший випадок зустрічі — зберігаємо canonical
                # якщо ім'я інше від нормалізованого — оновимо, щоб у DB була нормалізована назва
                if ex.name != norm:
                    print(f"[NORMALIZE] id={ex.id} '{ex.name}' -> '{norm}'")
                    stats["normalized"] += 1
                    if not dry_run:
                        ex.name = norm
                seen[norm] = ex

        # Комітимо зміни лише якщо dry_run == False
        if not dry_run:
            db.commit()
            print("\n[COMMIT] Changes committed to DB.")
        else:
            print("\n[DRY RUN] No changes were committed. Set DRY_RUN = False to apply changes.")

        # Підсумкова статистика
        print("\n=== Summary ===")
        print(f"Total exercises processed: {stats['total_exercises']}")
        print(f"Normalized names: {stats['normalized']}")
        print(f"Duplicate groups found: {stats['duplicates_found']}")
        print(f"Duplicate exercises removed: {stats['duplicates_removed']}")
        print(f"ProgramExercise relations reassigned: {stats['reassigned_relations']}")
        print(f"ProgramExercise relations merged: {stats['merged_relations']}")
        print("================")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Exception: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Starting clean_duplicates.py")
    print(f"DRY_RUN = {DRY_RUN}")
    print("!!! Make sure you have a backup of your database before running with DRY_RUN = False !!!\n")
    clean_duplicates(dry_run=DRY_RUN)
