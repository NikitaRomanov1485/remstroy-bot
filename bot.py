import logging
import threading
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from fpdf import FPDF
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, 
    MessageHandler, filters, CallbackQueryHandler, ConversationHandler
)

# ================= НАСТРОЙКИ =================
BOT_TOKEN = '8707599180:AAFjeddyCdiE8T1uA4CQe9QrWw3Vm7pGrEk'
# ID чата, КУДА ПРИХОДИТЬ ЗАЯВКАМ (ваш ID)
ADMIN_CHAT_ID = '7310945290' 

# Состояния для диалога
ASK_NAME, ASK_PHONE = range(2)

# ================= ПРАЙС-ЛИСТ =================
PRICE_LIST = {
    '1': {
        'name': '🔌 Монтаж точек и приборов',
        'items': {
            '110': {'name': 'Розетка под ключ (бетон)', 'price': 27, 'unit': 'шт.'},
            '111': {'name': 'Розетка под ключ (кирпич)', 'price': 22, 'unit': 'шт.'},
            '112': {'name': 'Выключатель под ключ (бетон)', 'price': 27, 'unit': 'шт.'},
            '113': {'name': 'Выключатель под ключ (кирпич)', 'price': 22, 'unit': 'шт.'},
            '101': {'name': 'Розетка / выключатель', 'price': 10, 'unit': 'шт.'},
            '102': {'name': 'Розетка для плиты', 'price': 15, 'unit': 'шт.'},
            '103': {'name': 'Люстра или бра', 'price': 15, 'unit': 'шт.'},
            '104': {'name': 'Точечный светильник', 'price': 10, 'unit': 'шт.'},
            '105': {'name': 'Монтаж подрозетника', 'price': 2, 'unit': 'шт.'},
            '106': {'name': 'Высверливание (ПГС)', 'price': 8, 'unit': 'шт.'},
            '107': {'name': 'Высверливание (бетон)', 'price': 15, 'unit': 'шт.'},
            '108': {'name': 'Высверливание (кирпич)', 'price': 10, 'unit': 'шт.'},
            '109': {'name': 'Распред. коробка', 'price': 20, 'unit': 'шт.'},
        }
    },
    '2': {
        'name': '🧵 Кабель и штробление',
        'items': {
            '201': {'name': 'Прокладка кабеля с крепежом', 'price': 2, 'unit': 'м.п.'},
            '202': {'name': 'Разводка в гофре', 'price': 2, 'unit': 'м.п.'},
            '203': {'name': 'Штробление в газосиликате', 'price': 6, 'unit': 'м.п.'},
            '204': {'name': 'Штробление в бетоне', 'price': 10, 'unit': 'м.п.'},
            '205': {'name': 'Штробление в кирпиче', 'price': 10, 'unit': 'м.п.'},
            '206': {'name': 'Монтаж гофры на клипсы', 'price': 3, 'unit': 'м.п.'},
            '207': {'name': 'Монтаж кабель-канала + кабель', 'price': 9, 'unit': 'м.п.'},
            '208': {'name': 'Протяжка кабеля в нише', 'price': 5, 'unit': 'м.п.'},
            '209': {'name': 'Замазывание штроб', 'price': 5, 'unit': 'м.п.'},
        }
    },
    '3': {
        'name': '⚙️ Электрощиты',
        'items': {
            '301': {'name': 'Ниша в газосиликате', 'price': 40, 'unit': 'шт.'},
            '302': {'name': 'Ниша в бетоне / кирпиче', 'price': 70, 'unit': 'шт.'},
            '303': {'name': 'Монтаж корпуса в нишу', 'price': 15, 'unit': 'шт.'},
            '304': {'name': 'Установка автомата', 'price': 8, 'unit': 'шт.'},
            '305': {'name': 'Реле напряжения', 'price': 18, 'unit': 'шт.'},
            '306': {'name': 'Дифавтомат / УЗО', 'price': 12, 'unit': 'шт.'},
        }
    },
    '4': {
        'name': '♨️ Тёплый пол',
        'items': {
            '409': {'name': 'Инфракрасная плёнка под ключ', 'price': 20, 'unit': 'м²'},
            '410': {'name': 'Кабель в стяжку под ключ', 'price': 26, 'unit': 'м²'},
            '411': {'name': 'Нагревательные маты под ключ', 'price': 33, 'unit': 'м²'},
            '401': {'name': 'Инфракрасная плёнка (работа)', 'price': 12, 'unit': 'м²'},
            '402': {'name': 'Кабель в стяжку (работа)', 'price': 18, 'unit': 'м²'},
            '403': {'name': 'Нагревательные маты (работа)', 'price': 25, 'unit': 'м²'},
            '404': {'name': 'Терморегулятор', 'price': 20, 'unit': 'шт.'},
            '405': {'name': 'Укладка подложки', 'price': 5, 'unit': 'м²'},
            '406': {'name': 'Датчик температуры', 'price': 12, 'unit': 'шт.'},
            '407': {'name': 'Клеммы и изоляция', 'price': 1, 'unit': 'шт.'},
            '408': {'name': 'Гидроизоляция', 'price': 3, 'unit': 'м²'},
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

# ================= ФУНКЦИЯ ГЕНЕРАЦИИ PDF =================
def generate_pdf(cart, total_sum, name, phone):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=14)
    
    # Заголовок
    pdf.cell(200, 10, txt="Смета на электромонтажные работы", ln=True, align='C')
    pdf.set_font("Helvetica", size=10)
    pdf.cell(200, 10, txt=f"Клиент: {name} | Тел: {phone}", ln=True, align='C')
    pdf.ln(10)
    
    # Таблица
    pdf.set_font("Helvetica", size=10)
    pdf.cell(100, 10, "Наименование", border=1)
    pdf.cell(30, 10, "Кол-во", border=1, align='C')
    pdf.cell(30, 10, "Цена", border=1, align='C')
    pdf.cell(30, 10, "Сумма", border=1, align='C', ln=True)
    
    for item in cart:
        pdf.cell(100, 10, item['name'][:40], border=1)
        pdf.cell(30, 10, f"{item['qty']} {item['unit']}", border=1, align='C')
        pdf.cell(30, 10, f"{item['price']} BYN", border=1, align='C')
        pdf.cell(30, 10, f"{item['total']} BYN", border=1, align='C', ln=True)
        
    pdf.ln(5)
    pdf.set_font("Helvetica", size=12, style='B')
    pdf.cell(200, 10, txt=f"ИТОГО (без материалов): {total_sum} BYN", ln=True, align='R')
    
    filename = f"Смета_{name.replace(' ', '_')}.pdf"
    pdf.output(filename)
    return filename

# ================= ОСНОВНАЯ ЛОГИКА =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_carts[user_id] = []
    context.user_data.clear()
    
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
    
    keyboard = [
        [InlineKeyboardButton('⚡ Электрика', callback_data='menu_electric')],
        [InlineKeyboardButton('🚰 Сантехника (скоро)', callback_data='menu_plumbing')]
    ]
    
    user_id = query.from_user.id
    if user_carts.get(user_id):
        keyboard.append([InlineKeyboardButton('🧾 Показать итог', callback_data='show_total')])
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        await query.edit_message_text("Выберите раздел:", reply_markup=reply_markup)
    except:
        pass

async def show_electric_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for cat_id, cat_data in PRICE_LIST.items():
        keyboard.append([InlineKeyboardButton(cat_data['name'], callback_data=f'cat_{cat_id}')])
        
    keyboard.append([InlineKeyboardButton('⬅️ Назад', callback_data='menu_main')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("⚡ Электрика: выберите категорию работ:", reply_markup=reply_markup)

async def show_plumbing_stub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton('⬅️ Назад', callback_data='menu_main')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("🚰 Раздел «Сантехника» пока в разработке.", reply_markup=reply_markup)

async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat_id = query.data.replace('cat_', '')
    category = PRICE_LIST.get(cat_id)
    if not category:
        return
    keyboard = []
    for item_id, item_data in category['items'].items():
        btn_text = f"{item_data['name']} — {item_data['price']} BYN"
        callback = f'item_{cat_id}_{item_id}'
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback)])
    keyboard.append([InlineKeyboardButton('⬅️ Назад', callback_data='menu_electric')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(f"Категория: {category['name']}\nВыберите позицию:", reply_markup=reply_markup)

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
        [InlineKeyboardButton('➕ Добавить ещё', callback_data='menu_electric')],
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
        [InlineKeyboardButton('📝 Оформить заявку', callback_data='checkout')],
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

# ================= ЛОГИКА ЗАЯВКИ (ConversationHandler) =================
async def start_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if not user_carts.get(user_id):
        await query.edit_message_text("Ваша корзина пуста. Добавьте услуги перед оформлением.")
        return ConversationHandler.END
        
    await query.edit_message_text("📝 Давайте оформим заявку.\n\nВведите ваше **Имя**:", parse_mode='Markdown')
    return ASK_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['client_name'] = update.message.text
    await update.message.reply_text("Отлично! Теперь введите ваш **номер телефона**:")
    return ASK_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    name = context.user_data.get('client_name', 'Не указано')
    user_id = update.effective_user.id
    cart = user_carts.get(user_id, [])
    total_sum = sum(item['total'] for item in cart)
    
    # 1. Генерируем PDF
    try:
        pdf_filename = generate_pdf(cart, total_sum, name, phone)
    except Exception as e:
        await update.message.reply_text(f"Ошибка при создании PDF: {e}")
        return ConversationHandler.END

    # 2. Формируем текст заявки для вас
    admin_text = f"🔔 НОВАЯ ЗАЯВКА С БОТА\n\n👤 Имя: {name}\n📞 Телефон: {phone}\n\n"
    for item in cart:
        admin_text += f"• {item['name']}: {item['qty']} {item['unit']} = {item['total']} BYN\n"
    admin_text += f"\n💰 ИТОГО: {total_sum} BYN"
    
    try:
        # Отправляем вам текст
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text)
        # Отправляем вам PDF
        with open(pdf_filename, 'rb') as pdf_file:
            await context.bot.send_document(chat_id=ADMIN_CHAT_ID, document=pdf_file)
            
        # Отправляем клиенту PDF
        with open(pdf_filename, 'rb') as pdf_file:
            await update.message.reply_document(document=pdf_file, caption="Ваша смета готова! Мы свяжемся с вами в ближайшее время для уточнения деталей.")
            
    except Exception as e:
        await update.message.reply_text(f"Заявка принята, но не удалось отправить файл. Ошибка: {e}")
        
    finally:
        if os.path.exists(pdf_filename):
            os.remove(pdf_filename)
    
    # Очищаем корзину
    user_carts[user_id] = []
    
    keyboard = [[InlineKeyboardButton('В главное меню', callback_data='menu_main')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✅ Спасибо! Ваша заявка принята и смета отправлена.", reply_markup=reply_markup)
    
    return ConversationHandler.END

# ================= ЗАПУСК =================
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
    
    # Обработчик заявки
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_checkout, pattern='^checkout$')],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        },
        fallbacks=[]
    )
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(show_main_menu, pattern='^menu_main$'))
    application.add_handler(CallbackQueryHandler(show_electric_menu, pattern='^menu_electric$'))
    application.add_handler(CallbackQueryHandler(show_plumbing_stub, pattern='^menu_plumbing$'))
    application.add_handler(CallbackQueryHandler(show_category, pattern='^cat_'))
    application.add_handler(CallbackQueryHandler(select_item, pattern='^item_'))
    application.add_handler(CallbackQueryHandler(show_total, pattern='^show_total$'))
    application.add_handler(CallbackQueryHandler(reset_cart, pattern='^reset_cart$'))
    
    # Обработка ввода количества (идет после select_item)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quantity))
    
    print("Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()