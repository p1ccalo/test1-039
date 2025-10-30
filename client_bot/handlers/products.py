
from aiogram import types, Dispatcher
from backend.utils import get_products

async def msg_products(message: types.Message):
    items = get_products()
    if not items:
        return await message.answer('Поки немає товарів.')
    chunks = []
    for p in items:
        chunks.append(f"✨ *{p['title']}*\nКатегорія: {p['category']}\n{(p.get('description') or '')[:220]}" )
    await message.answer('\n\n'.join(chunks), parse_mode='Markdown')

def register_products(dp: Dispatcher):
    dp.register_message_handler(msg_products, lambda m: m.text == '✨ Корисне приладдя')
