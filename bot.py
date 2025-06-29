

import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    Message, FSInputFile, BotCommand,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.bot import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

BOT_TOKEN = "7986564347:AAGjujddckjP3O0kbWA0o5lAP9d4zm5S3wM"
ADMIN_IDS = {5508167146, 1386843093}
ADMIN_PIN = "0503"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- Состояния пользователей ---
class UserStates(StatesGroup):
    waiting_support_message = State()
    waiting_cooperation_message = State()
    waiting_faq_message = State()
    waiting_faq_custom_message = State()

# --- Состояния админа ---
class AdminStates(StatesGroup):
    waiting_for_pin = State()
    admin_panel = State()
    waiting_for_broadcast = State()
    waiting_reply_user_id = State()
    waiting_reply_text = State()

# --- Клавиатуры ---
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🆘 Связаться с поддержкой")],
            [KeyboardButton(text="💼 Сотрудничество")],
            [KeyboardButton(text="📖 FAQ")]
        ],
        resize_keyboard=True
    )

def support_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔚 Закончить диалог")]],
        resize_keyboard=True
    )

def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Управление"), KeyboardButton(text="Рассылка")],
            [KeyboardButton(text="Ответить пользователю"), KeyboardButton(text="Блокировка")],
            [KeyboardButton(text="Выйти из админ-панели")]
        ],
        resize_keyboard=True
    )

def get_avatar():
    path = os.path.join("media", "avatar.jpg")
    if os.path.exists(path):
        return FSInputFile(path)
    return None

async def set_main_menu():
    commands = [
        BotCommand(command="help", description="ℹ️ Информация и поддержка"),
        BotCommand(command="start", description="🚀 Начать"),
        BotCommand(command="admin", description="🔐 Админ панель (требуется пин)")
    ]
    await bot.set_my_commands(commands)

# --- Обработчики ---

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    avatar = get_avatar()
    text = (
        "👋 <b>Привет!</b> Это техническая поддержка проекта <b><a href='https://t.me/Waltrosbet'>Waltros</a></b>.\n\n"
        "Чтоб обратиться к поддержке, нажмите на кнопку <b>«Связаться с поддержкой»</b>.\n"
        "Если у вас есть вопросы по проекту, вы можете нажать на кнопку <b>FAQ</b>.\n\n"
        "⏳ Мы работаем 24/7!"
    )
    if avatar:
        await message.answer_photo(photo=avatar, caption=text, reply_markup=get_main_keyboard())
    else:
        await message.answer(text, reply_markup=get_main_keyboard())

@dp.message(lambda m: m.text == "🆘 Связаться с поддержкой")
async def contact_support(message: Message, state: FSMContext):
    await state.set_state(UserStates.waiting_support_message)
    await message.answer(
        "✅ Связь с поддержкой активирована. Опишите проблему.\nЧтобы выйти, нажмите «🔚 Закончить диалог».",
        reply_markup=support_keyboard()
    )

@dp.message(UserStates.waiting_support_message)
async def handle_support_message(message: Message, state: FSMContext):
    if message.text == "🔚 Закончить диалог":
        await state.clear()
        await message.answer("Диалог завершён. Возвращаемся в меню.", reply_markup=get_main_keyboard())
        return

    text_to_admin = (
        f"📩 <b>Новое сообщение от пользователя в поддержку:</b>\n"
        f"👤 Имя: {message.from_user.full_name}\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"📝 Сообщение:\n{message.text}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text_to_admin)
        except Exception as e:
            logger.error(f"Ошибка отправки админам {admin_id}: {e}")

    await message.answer("✅ Ваше сообщение отправлено в поддержку. Мы ответим как можно скорее.")

@dp.message(lambda m: m.text == "💼 Сотрудничество")
async def cooperation(message: Message, state: FSMContext):
    await state.set_state(UserStates.waiting_cooperation_message)
    await message.answer(
        "💼 Предложение о сотрудничестве. Опишите вашу идею.\n«🔚 Закончить диалог» — выйти.",
        reply_markup=support_keyboard()
    )

@dp.message(UserStates.waiting_cooperation_message)
async def handle_cooperation_message(message: Message, state: FSMContext):
    if message.text == "🔚 Закончить диалог":
        await state.clear()
        await message.answer("Диалог завершён. Возвращаемся в меню.", reply_markup=get_main_keyboard())
        return

    text_to_admin = (
        f"📩 <b>Новое предложение по сотрудничеству:</b>\n"
        f"👤 Имя: {message.from_user.full_name}\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"📝 Сообщение:\n{message.text}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text_to_admin)
        except Exception as e:
            logger.error(f"Ошибка отправки админам {admin_id}: {e}")

    await message.answer("✅ Ваше сообщение отправлено менеджерам. Мы ответим как можно скорее.")

@dp.message(lambda m: m.text == "📖 FAQ")
async def faq(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎲 Проблема со ставкой?")],
            [KeyboardButton(text="💵 Проблема с выплатой?")],
            [KeyboardButton(text="🕹 Как играть?")],
            [KeyboardButton(text="🛡 Честность проекта?")],
            [KeyboardButton(text="✉️ Связаться с FAQ")],
            [KeyboardButton(text="🔚 Назад")]
        ],
        resize_keyboard=True
    )
    await message.answer("FAQ — Часто задаваемые вопросы", reply_markup=keyboard)

@dp.message(lambda m: m.text in ["🎲 Проблема со ставкой?", "💵 Проблема с выплатой?", "🕹 Как играть?", "🛡 Честность проекта?"])
async def faq_preset_answers(message: Message):
    answers = {
        "🎲 Проблема со ставкой?": "Опишите детали вашей ставки и что произошло. Мы поможем.",
        "💵 Проблема с выплатой?": "Укажите сумму, способ вывода и примерное время заявки.",
        "🕹 Как играть?": "Выберите игру в разделе Waltros и следуйте инструкциям.",
        "🛡 Честность проекта?": "Мы гарантируем честность и прозрачность игры.",
    }
    await message.answer(answers[message.text])
    await message.answer(
        "Если у вас есть дополнительный вопрос по этому разделу, напишите его ниже или нажмите «🔚 Закончить диалог» для выхода.",
        reply_markup=support_keyboard()
    )
    await UserStates.waiting_faq_custom_message.set()

@dp.message(UserStates.waiting_faq_custom_message)
async def handle_faq_custom_message(message: Message, state: FSMContext):
    if message.text == "🔚 Закончить диалог":
        await state.clear()
        await cmd_start(message, state)
        return

    text_to_admin = (
        f"📩 <b>Пользовательский вопрос по FAQ:</b>\n"
        f"👤 Имя: {message.from_user.full_name}\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"📝 Вопрос:\n{message.text}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text_to_admin)
        except Exception as e:
            logger.error(f"Ошибка отправки админам {admin_id}: {e}")

    await message.answer("✅ Ваш вопрос отправлен. Мы ответим как можно скорее.")

@dp.message(lambda m: m.text == "✉️ Связаться с FAQ")
async def contact_faq(message: Message, state: FSMContext):
    await state.set_state(UserStates.waiting_faq_message)
    await message.answer(
        "✅ Связь с FAQ активирована. Напишите вопрос.\n«🔚 Закончить диалог» — выйти.",
        reply_markup=support_keyboard()
    )

@dp.message(UserStates.waiting_faq_message)
async def handle_faq_message(message: Message, state: FSMContext):
    if message.text == "🔚 Закончить диалог":
        await state.clear()
        await cmd_start(message, state)
        return

    text_to_admin = (
        f"📩 <b>Вопрос от пользователя по FAQ:</b>\n"
        f"👤 Имя: {message.from_user.full_name}\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"📝 Вопрос:\n{message.text}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text_to_admin)
        except Exception as e:
            logger.error(f"Ошибка отправки админам {admin_id}: {e}")

    await message.answer("✅ Ваш вопрос отправлен. Мы ответим как можно скорее.")

@dp.message(lambda m: m.text in ["🔚 Закончить диалог", "🔚 Назад"])
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await cmd_start(message, state)

# --- Админ панель ---

@dp.message(Command("admin"))
async def admin_command(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к админ панели.")
        return
    await state.set_state(AdminStates.waiting_for_pin)
    await message.answer("Введите пин-код для входа в админ панель:")

@dp.message(AdminStates.waiting_for_pin)
async def check_pin(message: Message, state: FSMContext):
    if message.text == ADMIN_PIN:
        await state.set_state(AdminStates.admin_panel)
        avatar = get_avatar()
        await message.answer("✅ Добро пожаловать в админ панель!", reply_markup=admin_keyboard())
        if avatar:
            await message.answer_photo(photo=avatar, caption="Админ панель Waltros")
    else:
        await message.answer("❌ Неверный пин-код. Попробуйте ещё раз.")

@dp.message(AdminStates.admin_panel)
async def admin_panel_handler(message: Message, state: FSMContext):
    text = message.text.lower()

    if text == "выйти из админ-панели":
        await state.clear()
        await message.answer("Вы вышли из админ панели.", reply_markup=get_main_keyboard())

    elif text == "рассылка":
        await message.answer("Введите текст для рассылки всем администраторам:")
        await state.set_state(AdminStates.waiting_for_broadcast)

    elif text == "ответить пользователю":
        await message.answer("Введите ID пользователя, которому хотите ответить:")
        await state.set_state(AdminStates.waiting_reply_user_id)

    elif text == "блокировка":
        await message.answer("Функция блокировки пока не реализована.")

    elif text == "управление":
        await message.answer("Вы в разделе управления. Здесь можно добавить команды.")

    else:
        await message.answer("Выберите действие из меню админа.", reply_markup=admin_keyboard())

@dp.message(AdminStates.waiting_for_broadcast)
async def admin_broadcast(message: Message, state: FSMContext):
    text_to_send = message.text
    await message.answer("Начинаю рассылку...")
    errors = 0
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, f"📢 Рассылка от админа:\n\n{text_to_send}")
        except Exception as e:
            errors += 1
            logger.error(f"Ошибка при рассылке администратору {admin_id}: {e}")
    await message.answer(f"Рассылка завершена. Ошибок: {errors}")
    await state.set_state(AdminStates.admin_panel)

@dp.message(AdminStates.waiting_reply_user_id)
async def admin_waiting_reply_user_id(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await state.update_data(reply_user_id=user_id)
        await message.answer("Введите текст ответа пользователю:")
        await state.set_state(AdminStates.waiting_reply_text)
    except ValueError:
        await message.answer("Ошибка: ID должен быть числом. Введите ID заново:")

@dp.message(AdminStates.waiting_reply_text)
async def admin_waiting_reply_text(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("reply_user_id")
    if not user_id:
        await message.answer("Ошибка: не найден ID пользователя.")
        await state.set_state(AdminStates.admin_panel)
        return

    try:
        await bot.send_message(user_id, f"📩 Ответ от администрации:\n\n{message.text}")
        await message.answer("Сообщение отправлено пользователю.")
    except Exception as e:
        await message.answer(f"Ошибка при отправке пользователю: {e}")

    await state.set_state(AdminStates.admin_panel)

# --- Запуск ---

async def main():
    await set_main_menu()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())