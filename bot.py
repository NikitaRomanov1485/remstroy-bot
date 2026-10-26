import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, 
    MessageHandler, filters, CallbackQueryHandler
)

# ================= НАСТРОЙКИ =================
BOT_TOKEN = '8707599180:AAFjeddyCdiE8T1uA4CQe9QrWw3Vm7pGrEk'

# ================= ПРАЙС-ЛИСТ =================
PRICE_LIST = {
    '1': {
        'name': '🔌 Монтаж точек и приборов',
        'items': {
            '101': {'name': 'Розетка под ключ (бетон)', 'price': 27, 'unit': 'шт.'},
            '102': {'name': 'Розетка под ключ (кирпич)', 'price': 22, 'unit': 'шт.'},
            '103': {'name': 'Выключатель под ключ (бетон)', 'price': 27, 'unit': 'шт.'},
            '104': {'name': 'Выключатель под ключ (кирпич)', 'price': 22, 'unit': 'шт.'},
            '105': {'name': 'Установка розетки', 'price': 10, 'unit': 'шт.'},
            '106': {'name': 'Установка выключателя', 'price': 10, 'unit': 'шт.'},
            '107': {'name': 'Высверливание подрозетника (бетон)', 'price': 15, 'unit': 'шт.'},
            '108': {'name': 'Высверливание подрозетника (кирпич)', 'price': 10, 'unit': 'шт.'},
            '109': {'name': 'Высверливание подрозетника (ПГС)', 'price': 8, 'unit': 'шт.'},
            '110': {'name': 'Монтаж подрозетника', 'price': 2, 'unit': 'шт.'},
            '111': {'name': 'Распределительная коробка', 'price': 20, 'unit': 'шт.'},
        }
    },
    '2': {
        'name': '🧵 Кабель и штробление',
        'items': {
            '201': {'name': 'Прокладка кабеля', 'price': 2, 'unit': 'м.п.'},
            '202': {'name': 'Кабель-канал', 'price': 9, 'unit': 'м.п.'},
            '203': {'name': 'Штробление (бетон)', 'price': 10, 'unit': 'м.п.'},
            '204': {'name': 'Штробление (кирпич)', 'price': 6, 'unit': 'м.п.'},
            '205': {'name': 'Демонтаж проводки', 'price': 3, 'unit': 'м.п.'},
        }
    },
    '3': {
        'name': '⚙️ Электрощиты',
        'items': {
            '301': {'name': 'Автомат', 'price': 8, 'unit': 'шт.'},
            '302': {'name': 'Дифавтомат', 'price': 12, 'unit': 'шт.'},
            '303': {'name': 'Реле напряжения', 'price': 18, 'unit': 'шт.'},
            '304': {'name': 'Сборка щита', 'price': 150, 'unit': 'шт.'},
        }
    },
    '4': {
        'name': '♨️ Тёплый пол',
        'items': {
            '401': {'name': 'ИК плёнка', 'price': 12, 'unit': 'м²'},
            '402': {'name': 'Кабель в стяжку', 'price': 18, 'unit': 'м²'},
            '403': {'name': 'Маты', 'price': 25, 'unit': 'м²'},
            '404': {'name': 'Терморегулятор', 'price': 20, 'unit': 'шт.'},
        }
    },
    '5': {
        'name': '💡 Освещение',
        'items': {
            '501': {'name': 'Люстра', 'price': 15, 'unit': 'шт.'},
            '502': {'name': 'Точечный светильник', 'price': 10, 'unit': 'шт.'},
            '503': {'name': 'Линейный светильник', 'price': 30, 'unit': 'шт.'},
            '504': {'name': 'Светодиодная панель', 'price': 20, 'unit': 'шт.'},
        }
    }
}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
user_carts = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_carts[user_id] = []
    keyboard = [[InlineKeyboardButton('Перейти в меню', callback_data='menu_main')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Привет! Я бот-калькулятор RemStroy.\n\n"
        "Выберите категорию, затем позицию и укажите количество.",
        reply_markup=reply_markup
    )

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = []
    for cat_id, cat_data in PRICE_LIST.items():
        keyboard.append([InlineKeyboardButton(cat_data['name'], callback_data=f'cat_{cat_id}')])
    user_id = query.from_user.id
    if user_carts.get(user_id):
        keyboard.append([InlineKeyboardButton('🧾 Показать итог', callback_data='show_total')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await query.edit_message_text("Выберите категорию работ:", reply_markup=reply_markup)
    except:
        pass

async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_id = query.data.replace('cat_', '')
    category = PRICE_LIST.get(cat_id)
    if not category:
        await query.answer("Категория не найдена", show_alert=True)
        return
    keyboard = []
    for item_id, item_data in category['items'].items():
        btn_text = f"{item_data['name']} — {item_data['price']} BYN"
        callback = f'item_{cat_id}_{item_id}'
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback)])
    keyboard.append([InlineKeyboardButton('⬅️ Назад', callback_data='menu_main')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"Категория: {category['name']}\nВыберите позицию:",
        reply_markup=reply_markup
    )

async def select_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        parts = query.data.split('_')
        cat_id = parts[1]
        item_id = parts[2]
        item = PRICE_LIST[cat_id]['items'][item_id]
    except (IndexError, KeyError):
        await query.answer("Ошибка выбора. Попробуйте снова.", show_alert=True)
        return
    context.user_data['waiting_qty'] = {'cat_id': cat_id, 'item_id': item_id}
    await query.edit_message_text(
        f"Вы выбрали: {item['name']} (от {item['price']} BYN / {item['unit']})\n\n"
        f"Введите количество (только число):"
    )

async def handle_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if 'waiting_qty' not in context.user_data:
        return
    try:
        qty = float(update.message.text.replace(',', '.'))
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число (например, 5 или 2.5).")
        return
    item_info = context.user_data['waiting_qty']
    cat_id = item_info['cat_id']
    item_id = item_info['item_id']
    item = PRICE_LIST[cat_id]['items'][item_id]
    total_item_price = qty * item['price']
    if user_id not in user_carts:
        user_carts[user_id] = []
    user_carts[user_id].append({
        'name': item['name'],
        'qty': qty,
        'price': item['price'],
        'total': total_item_price,
        'unit': item['unit']
    })
    del context.user_data['waiting_qty']
    keyboard = [
        [InlineKeyboardButton('➕ Добавить ещё', callback_data='menu_main')],
        [InlineKeyboardButton('🧾 Показать итог', callback_data='show_total')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"✅ Добавлено: {item['name']} — {qty} {item['unit']} × {item['price']} BYN = {total_item_price} BYN\n\n"
        f"Что делаем дальше?",
        reply_markup=reply_markup
    )

async def show_total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    cart = user_carts.get(user_id, [])
    if not cart:
        await query.edit_message_text("Ваша корзина пуста.")
        return
    text = "🧾 Ваш расчет:\n\n"
    total_sum = 0
    for item in cart:
        text += f"• {item['name']}: {item['qty']} {item['unit']} × {item['price']} = {item['total']} BYN\n"
        total_sum += item['total']
    text += f"\n💰 ИТОГО: {total_sum} BYN (без учета материалов)\n\n"
    keyboard = [
        [InlineKeyboardButton('🔄 Сбросить', callback_data='reset_cart')],
        [InlineKeyboardButton('⬅️ В меню', callback_data='menu_main')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

async def reset_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user_carts[user_id] = []
    await query.answer("Корзина сброшена!")
    await show_main_menu(update, context)

def main():
    class HealthCheckHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            
    def run_health_server():
        port = 8080
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        server.serve_forever()
        
    threading.Thread(target=run_health_server, daemon=True).start()
    
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(show_main_menu, pattern='^menu_main$'))
    application.add_handler(CallbackQueryHandler(show_category, pattern='^cat_'))
    application.add_handler(CallbackQueryHandler(select_item, pattern='^item_'))
    application.add_handler(CallbackQueryHandler(show_total, pattern='^show_total$'))
    application.add_handler(CallbackQueryHandler(reset_cart, pattern='^reset_cart$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quantity))
    
    print("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()