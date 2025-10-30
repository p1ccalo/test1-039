
from aiogram import types, Dispatcher
from backend.utils import get_services

async def msg_services(message: types.Message):
    items = get_services()
    if not items:
        return await message.answer('Поки немає послуг.')
    chunks = []
    for s in items:
        price = s.get('price') or 0
        chunks.append(f"💼 *{s['title']}* — {price:.2f} грн\nКатегорія: {s.get('category') or '—'}\n{(s.get('description') or '')[:220]}" )
    await message.answer('\n\n'.join(chunks), parse_mode='Markdown')

def register_services(dp: Dispatcher):
    dp.register_message_handler(msg_services, lambda m: m.text == '💼 Послуги')
