import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from tinkoff.invest import Client

# === ВСТАВЬТЕ ВАШИ ДАННЫЕ СЮДА ===
TG_TOKEN = 8656921869:AAEYCTu2-Z0V_yeRarrtSLVPu2z51E69FSY
T_TOKEN = t.Tw5fPANXuZxDbiP_2Bj-VWP5vlVLd_0okt-DoC8Gf6LD6iLVz-LMm3M0BCizVXTT1gZ0IkOy93PfIb-XTq40JP-CQ
# ================================

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

def get_portfolio_data():
    """Функция для выгрузки реального портфеля из Т-Инвестиций"""
    portfolio_list = []
    with Client(T_TOKEN) as client:
        # 1. Получаем ID вашего основного счета
        accounts = client.users.get_accounts().accounts
        account_id = accounts[0].id # Берем первый попавшийся счет (обычно основной Брокерский)

        # 2. Получаем все позиции (акции, облигации) на этом счету
        positions = client.operations.get_portfolio(account_id=account_id).positions
        
        for p in positions:
            # Нам нужны только Акции (share) и Облигации (bond)
            if p.instrument_type in ['share', 'bond']:
                # Получаем тикер для красоты отображения
                inst = client.instruments.get_instrument_by(id_type=1, id=p.figi).instrument
                portfolio_list.append({
                    'figi': p.figi,
                    'ticker': inst.ticker,
                    'name': inst.name,
                    'quantity': float(p.quantity.units + p.quantity.nano / 1e9),
                    'type': p.instrument_type
                })
    return portfolio_list

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("🤖 Бот-синхронизатор с Т-Инвестициями готов!\n\n"
                         "Команды:\n"
                         "📅 /calendar — Построить календарь выплат по моему РЕАЛЬНОМУ портфелю\n"
                         "💼 /my_assets — Показать, что бот видит в вашем портфеле")

@dp.message(Command("my_assets"))
async def list_assets(message: types.Message):
    await message.answer("🔄 Загружаю данные из Т-Инвестиций...")
    try:
        assets = get_portfolio_data()
        text = "💼 **Ваши активы:**\n\n"
        for a in assets:
            text += f"• {a['name']} ({a['ticker']}): {a['quantity']} шт.\n"
        await message.answer(text)
    except Exception as e:
        await message.answer(f"❌ Ошибка доступа к API: {e}")

@dp.message(Command("calendar"))
async def show_calendar(message: types.Message):
    await message.answer("🔍 Собираю данные о ближайших выплатах (это может занять 10-20 сек)...")
    
    try:
        assets = get_portfolio_data()
        report = "📅 **Календарь выплат на 12 месяцев:**\n\n"
        found_any = False
        
        with Client(T_TOKEN) as client:
            for a in assets:
                # Ищем дивиденды для акций
                if a['type'] == 'share':
                    events = client.instruments.get_dividends(
                        figi=a['figi'], 
                        from_=datetime.now(), 
                        to=datetime.now() + timedelta(days=365)
                    ).dividends
                    for e in events:
                        date = e.payment_date.strftime('%d.%m.%Y')
                        val = e.dividend_net.units + e.dividend_net.nano / 1e9
                        total = val * a['quantity']
                        report += f"🔹 {date} | **{a['ticker']}**\n   Дивиденд: {val:.2f} ₽ (Всего: {total:.2f} ₽)\n\n"
                        found_any = True

                # Ищем купоны для облигаций
                elif a['type'] == 'bond':
                    events = client.instruments.get_bond_coupons(
                        figi=a['figi'], 
                        from_=datetime.now(), 
                        to=datetime.now() + timedelta(days=365)
                    ).events
                    for e in events:
                        date = e.coupon_date.strftime('%d.%m.%Y')
                        val = e.pay_one_bond.units + e.pay_one_bond.nano / 1e9
                        total = val * a['quantity']
                        report += f"🔸 {date} | **{a['ticker']}**\n   Купон: {val:.2f} ₽ (Всего: {total:.2f} ₽)\n\n"
                        found_any = True

        if not found_any:
            report = "📭 Ближайших выплат по вашим бумагам не найдено."
        
        await message.answer(report)

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
