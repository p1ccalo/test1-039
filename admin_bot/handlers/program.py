from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from admin_bot.states.states import AddProgramStates, EditProgramStates, EditClientStates
from admin_bot.keyboards.keyboards import build_program_edit_kb, back_btn
from backend.db import SessionLocal
from backend.models import Client, Program, Exercise, Course, ProgramExercise
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# 🛠️ Хелпер для побудови клавіатури
def build_exercises_keyboard(all_exercises, selected_ids):
    kb = InlineKeyboardMarkup(row_width=2)
    for ex in all_exercises:
        if ex.id not in selected_ids:
            kb.insert(InlineKeyboardButton(ex.name, callback_data=f"add_ex:{ex.id}"))
    kb.add(InlineKeyboardButton("✅ Готово", callback_data="done_selecting"))
    return kb

async def add_program(message: types.Message, state: FSMContext):
    clients = SessionLocal().query(Client).all()
    kb = InlineKeyboardMarkup(row_width=2)
    for cl in clients:
        kb.insert(InlineKeyboardButton(cl.name, callback_data=f"add_program:{cl.id}"))
    await message.answer("Оберіть клієнта:", reply_markup=kb)
    await AddProgramStates.choose_client.set()


async def add_program_start(callback: types.CallbackQuery, state: FSMContext):
    client_id = int(callback.data.split(":")[-1])
    print('client_id: ', client_id)
    await state.update_data(client_id=client_id)
    client=SessionLocal().query(Client).get(client_id)
    await state.update_data(client_name=client.name)
    kb = types.InlineKeyboardMarkup(resize_keyboard=True)
    courses = SessionLocal().query(Course).all()
    for course in courses:
        kb.insert(InlineKeyboardButton(text=course.name, callback_data=f"course:{course.id}"))
    await AddProgramStates.choose_course.set()
    if callback.message.photo:
        return await callback.message.answer(f"Оберіть курс для {client.name}", reply_markup=kb)
    await callback.message.edit_text(f"Оберіть курс для {client.name}", reply_markup=kb)

async def add_program_course(callback: types.CallbackQuery, state: FSMContext):
    print('callback.data: ', callback.data)
    course_id = int(callback.data.split(":")[-1])
    course = SessionLocal().query(Course).get(course_id)
    if course:
        await state.update_data(course_id=int(course.id))
        await state.update_data(course_name=course.name)
        data = await state.get_data()
        client_name = data.get("client_name")
        kb = types.InlineKeyboardMarkup(resize_keyboard=True)
        kb.add(InlineKeyboardButton(text="📑 З шаблону", callback_data='from_template'))
        kb.add(InlineKeyboardButton(text='З нуля', callback_data='from_scratch'))
        await callback.message.edit_text(f"""Створення нової програми {course.name} для {client_name}.
Створити програму з шаблону чи з нуля?""", reply_markup=kb)
        await AddProgramStates.choose_type.set()

async def add_program_type(callback: types.CallbackQuery, state: FSMContext):
    if "from_template" in callback.data:
        await callback.message.edit_text("📑 Тут буде список шаблонів")
        await AddProgramStates.confirm.set()
    else:
        data = await state.get_data()
        course_id = data.get("course_id")
        course_name = data.get("course_name")
        client_name = data.get("client_name")
        await state.update_data(selected_exercises=[])

        db = SessionLocal()
        exercises = db.query(Exercise).filter(Exercise.course_id == course_id).all()
        db.close()

        text = f'Створення нової програми {course_name} для {client_name}.\n\nДодайте вправи'
        kb = build_exercises_keyboard(exercises, [])
        await callback.message.edit_text(text, reply_markup=kb)
        await AddProgramStates.add_exercises.set()

async def add_program_exercise(call: types.CallbackQuery, state: FSMContext):
    print('call.data: ', call.data)
    data = await state.get_data()
    course_id = data.get("course_id")
    print('course_id: ', course_id)
    db = SessionLocal()
    ex_id = int(call.data.split(":")[1])
    selected = data.get("selected_exercises", [])
    if ex_id not in selected:
        selected.append(ex_id)
    await state.update_data(selected_exercises=selected)

    exercises = db.query(Exercise).filter(Exercise.course_id == course_id).all()
    selected_objs = db.query(Exercise).filter(Exercise.id.in_(selected)).all()
    db.close()

    text_lines = [f"Додано вправ: {len(selected)}"]
    for i, ex in enumerate(selected_objs, 1):
        text_lines.append(f"{i}. {ex.name}")
    text_lines.append("---")

    kb = build_exercises_keyboard(exercises, selected)
    await call.message.edit_text("\n".join(text_lines), reply_markup=kb)

async def edit_program_add_exercise(call: types.CallbackQuery, state: FSMContext):
    print('call.data: ', call.data)
    data = await state.get_data()
    program_id = data.get('program_id')
    ex_id = call.data.split(":")[1]
    if ex_id:
        ex_id = int(ex_id)
    db = SessionLocal()
    
    program = db.query(Program).get(program_id)
    if program:
        course_id = program.course.id
        exercises = db.query(Exercise).filter(Exercise.course_id == course_id).all()
        if ex_id and ex_id not in [ex.exercise.id for ex in program.exercises]:
            new_ex = ProgramExercise(program_id=program_id, exercise_id=ex_id)
            db.add(new_ex)
            db.commit()

        available_exercises = []
        for ex in exercises:
            if ex not in program.exercises:
                available_exercises.append(ex)
        selected_ids = [ex.exercise.id for ex in program.exercises]
        kb = build_exercises_keyboard(available_exercises, selected_ids)
        text_lines = [f"Всього вправ: {len(program.exercises)}"]
        for i, ex in enumerate(program.exercises, 1):
            text_lines.append(f"{i}. {ex.exercise.name}")
        text_lines.append("---")
        await EditProgramStates.choosing_exercise.set()
        await call.message.edit_text("\n".join(text_lines), reply_markup=kb)
        db.close()


async def add_program_confirm(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    client_id = data["client_id"]
    course_id = data["course_id"]
    selected = data.get("selected_exercises", [])

    db = SessionLocal()
    client = db.query(Client).get(client_id)
    course = db.query(Course).get(course_id)

    # Створюємо програму
    program = Program(client_id=client_id, course_id=course_id)
    db.add(program)
    db.commit()
    db.refresh(program)

    # Додаємо вправи
    for order, ex_id in enumerate(selected, 1):
        pe = ProgramExercise(program_id=program.id, exercise_id=ex_id, order_num=order)
        db.add(pe)
    db.commit()

    selected_objs = db.query(Exercise).filter(Exercise.id.in_(selected)).all()

    # Формуємо текст
    text_lines = [
        "✅ Програму створено!",
        f"Клієнт: {client.name}",
        f"Курс: {course.name}",
        "Вправи:"
    ]
    for i, ex in enumerate(selected_objs, 1):
        text_lines.append(f"{i}. {ex.name}")

    # Кнопки: редагувати + додати програму по іншим курсам
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("✏️ Редагувати програму", callback_data=f"edit_program:{program.id}"))

    other_courses = db.query(Course).filter(Course.id != course_id).all()
    for oc in other_courses:
        kb.add(InlineKeyboardButton(f"+ {oc.name}", callback_data=f"add_course:{program.id}:{oc.id}"))

    db.close()

    await call.message.edit_text("\n".join(text_lines), reply_markup=kb)
    await state.finish()


async def edit_program(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    program_id = call.data.split(":")[1] if ":" in call.data else data.get("program_id")
    print('program_id: ', program_id)
    if program_id not in data:
        await state.update_data(program_id=program_id)
    
    db = SessionLocal()
    pes = db.query(ProgramExercise).filter(ProgramExercise.program_id == program_id).order_by(ProgramExercise.order_num).all()
    exercises = [db.query(Exercise).get(pe.exercise_id) for pe in pes]
    client_id = db.query(Program).get(program_id).client_id
    print('client_id: ', client_id)
    db.close()

    text = "✏️ Редагування програми\n\nПересуньте або видаліть вправи:"
    print('text: ', text)
    kb = build_program_edit_kb(exercises, program_id, client_id)
    await call.message.edit_text(text, reply_markup=kb)
    await EditProgramStates.start.set()


# async def edit_program_add_exercise(call: types.CallbackQuery, state: FSMContext):
#     program_id = int(call.data.split(":")[1])
#     await state.update_data(program_id=program_id)
#     kb = InlineKeyboardMarkup()
#     db = SessionLocal()
#     program = db.query(Program).get(program_id)
#     if program:
#         exercises = db.query(Exercise).filter(Exercise.course_id == program.course_id).all()
#         for ex in exercises:
#             if ex not in program.exercises:
#                 kb.add(InlineKeyboardButton(ex.name, callback_data=f"add_exercise:{ex.id}_{program_id}"))
#     db.close()
# )

#     text = "✏️ Редагування програми\n\nДодати вправу:"
#     kb = build_exercises_keyboard(exercises, [])
#     await call.message.edit_text(text, reply_markup=kb) 




async def move_exercise(call: types.CallbackQuery, state: FSMContext):
    print('call.data: ', call.data)
    action, ex_data = call.data.split(":")
    ex_id = int(ex_data.split("_")[1])
    program_id = int(ex_data.split("_")[0])
    print('action: ', action)
    print('ex_id: ', ex_id)
    print('program_id: ', program_id)

    db = SessionLocal()
    pes = db.query(ProgramExercise).filter(ProgramExercise.program_id == program_id).order_by(ProgramExercise.order_num).all()
    print('pes: ', pes)
    for i, pe in enumerate(pes):
        if pe.exercise_id == ex_id:
            if action == "move_up" and i > 0:
                pes[i].order_num, pes[i-1].order_num = pes[i-1].order_num, pes[i].order_num
            elif action == "move_down" and i < len(pes)-1:
                pes[i].order_num, pes[i+1].order_num = pes[i+1].order_num, pes[i].order_num
            elif action == "delete_ex":
                db.delete(pes[i])
            break
    db.commit()
    pes = db.query(ProgramExercise).filter(ProgramExercise.program_id == program_id).order_by(ProgramExercise.order_num).all()
    exercises = [db.query(Exercise).get(pe.exercise_id) for pe in pes]
    print('exercises: ', exercises)
    program = db.query(Program).get(program_id)
    client_id = program.client_id

    text = "✏️ Редагування програми\n\nПересуньте або видаліть вправи:"
    kb = build_program_edit_kb(exercises, program_id, client_id)
    db.close()
    await call.message.edit_text(text, reply_markup=kb)


async def delete_program(call: types.CallbackQuery, state: FSMContext):
    program_id = int(call.data.split(":")[1])
    db = SessionLocal()
    program = db.query(Program).get(program_id)
    
    db.delete(program)
    db.commit()
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Назад", callback_data=f"edit_programs:{program.client_id}"))
    db.close()
    await call.message.edit_text("✅ Програма видалена!", reply_markup=kb)



def register_handlers(dp: Dispatcher):
    dp.register_message_handler(add_program, lambda m: m.text == "📋 Додати програму", state='*')
    dp.register_callback_query_handler(add_program_course, lambda c: c.data.startswith("course:"), state=AddProgramStates.choose_course)
    dp.register_callback_query_handler(add_program_type, lambda c: c.data in ['from_template', 'from_scratch'], state=AddProgramStates.choose_type)
    dp.register_callback_query_handler(add_program_exercise,lambda c: c.data.startswith("add_ex:"), state=AddProgramStates.add_exercises)
    dp.register_callback_query_handler(add_program_confirm, lambda c: c.data.startswith("done_selecting"), state=AddProgramStates.add_exercises)
    dp.register_callback_query_handler(edit_program_add_exercise, lambda c: c.data.startswith("add_ex:"), state=[EditProgramStates.start, EditProgramStates.choosing_exercise])
    dp.register_callback_query_handler(move_exercise, lambda c: c.data.startswith("move_up") or c.data.startswith("move_down") or c.data.startswith("delete_ex:"), state=EditProgramStates.start)
    dp.register_callback_query_handler(delete_program, lambda c: c.data.startswith("delete_program:"), state=EditProgramStates.start)
    dp.register_callback_query_handler(edit_program, lambda c: c.data.startswith("done_selecting"), state=EditProgramStates.choosing_exercise)
    dp.register_callback_query_handler(add_program_start, lambda c: c.data.startswith("add_program:"), state=EditClientStates.card)
    dp.register_callback_query_handler(edit_program, lambda c: c.data.startswith("edit_program:"), state='*')