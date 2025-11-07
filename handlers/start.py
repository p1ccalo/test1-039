from aiogram import types, Dispatcher
from backend.models import Client, Admin, User
from backend.db import SessionLocal  # Используем централизованную сессию
from client_bot.handlers.common import cmd_start as client_cmd_start
from admin_bot.handlers.start import cmd_start as admin_cmd_start

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def set_admin(message: types.Message):
    tg_id = message.from_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == tg_id).first()
    user.role = 'admin'
    if not user.admin:
        admin = Admin(user_id=user.id)
        db.add(admin)
        db.commit()
        db.close()
    await message.answer('Ви стали адміном')
    return await admin_cmd_start(message)
    
    

async def set_client(message: types.Message):
    tg_id = message.from_user.id
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == tg_id).first()
    if not user:
        user = User(telegram_id=tg_id, telegram_username=message.from_user.username, first_name=message.from_user.first_name, last_name=message.from_user.last_name)
        db.add(user)
        db.commit()
        db.refresh(user)
    if not user.client:
        client = Client(name=user.first_name, user_id=user.id)
        db.add(client)
        db.commit()
        db.refresh(client)
    user.role = 'client'
    db.commit()
    db.close()
    await message.answer('Ви стали клієнтом')
    return await client_cmd_start(message)


async def start(message: types.Message):
    

    print('message: ', message)
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
    print('user: ', user)
    if not user:
        user = User(telegram_id=message.from_user.id, telegram_username=message.from_user.username, first_name=message.from_user.first_name, last_name=message.from_user.last_name)
        db.add(user)
        db.commit()
        db.close
        ('new user created: ', user)
        return await client_cmd_start(message)
    if user.role == 'client':
        print('user is client')
        return await client_cmd_start(message)
    elif user.role == 'admin':
        print('user is admin')
        return await admin_cmd_start(message)
    else:
        return await message.answer('Немає такого користувача')

def register_handlers_start(dp: Dispatcher):
    dp.register_message_handler(start, commands=['start'])
    dp.register_message_handler(set_admin, commands=['admin'])
    dp.register_message_handler(set_client, commands=['client'])