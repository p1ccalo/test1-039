from aiogram.dispatcher.filters.state import State, StatesGroup

# class AddClientStates(StatesGroup):
#     name = State()
#     photo = State()
#     confirm = State()

class AddExerciseStates(StatesGroup):
    name = State()
    details = State()

class AddProgramStates(StatesGroup):
    choose_client = State()
    choose_course = State()
    choose_type = State()  # з шаблону чи з нуля
    add_exercises = State()
    confirm = State()

class EditProgramStates(StatesGroup):
    start=State()
    choosing_exercise = State()
    editing_order = State()
    editing_reps = State()
    editing_weight = State()

class TemplateStates(StatesGroup):
    choose = State()
    edit_exercise = State()
    confirm = State()

class SearchClientStates(StatesGroup):
    query = State()


class EditExerciseStates(StatesGroup):
    edit_name = State()
    details = State()
    photos = State()


class EditClientStates(StatesGroup):
    card = State()
    name = State()
    age = State()
    symptoms = State()
    activities = State()
    research = State()
    massage = State()
    photos = State()
    finish = State()
