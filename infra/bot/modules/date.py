from datetime import date, datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from telegram_bot_calendar import DetailedTelegramCalendar

from core.constants import ButtonCallbackData, UserFlowState
from crud.order import CurrentOrder
from crud.worker import worker

from .booking import booking_menu_show

RSTEP = {'y': 'год', 'm': 'месяц', 'd': 'день'}
IFTAR_BEGIN = date(2024, 3, 11)
IFTAR_END = date(2024, 4, 10)
CALENDAR_CANCEL_BUTTON = {
    'text': 'Отмена',
    'callback_data': ButtonCallbackData.DATE_SELECT_PREFIX + 'cancel',
}


class MyStyleCalendar(DetailedTelegramCalendar):
    empty_nav_button = '🚫'
    prev_button = "⬅️"
    next_button = "➡️"
    empty_year_button = ""
    empty_month_button = ""


CALENDAR = MyStyleCalendar(
    locale='ru',
    min_date=IFTAR_BEGIN if IFTAR_BEGIN > date.today() else date.today(),
    max_date=IFTAR_END,
    additional_buttons=[CALENDAR_CANCEL_BUTTON],
)


async def date_select_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.delete_message()

    if IFTAR_END > date.today():
        calendar, step = CALENDAR.build()
        message_text = f'Выберите {RSTEP[step]}'
        reply_markup = calendar

    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    'Назад',
                    callback_data=ButtonCallbackData.DATE_SELECT_PREFIX
                    + 'cancel',
                ),
            ]
        ]
        message_text = 'Ифтар закончился, приходите в следующем году'
        reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        text=message_text,
        reply_markup=reply_markup,
        disable_web_page_preview=True,
    )

    return UserFlowState.SELECT_DATA


async def date_select_button(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    await query.answer()

    if query.data == CALENDAR_CANCEL_BUTTON['callback_data']:
        await booking_menu_show(update, context)
        return UserFlowState.BOOKING

    result, key, step = CALENDAR.process(query.data)

    if not result and key:
        await query.edit_message_text(
            f'Выберите {RSTEP[step]}',
            reply_markup=key,
            disable_web_page_preview=True,
        )
    elif result:
        current_order: CurrentOrder = context.user_data['order']

        current_order.from_date = datetime(
            result.year, result.month, result.day
        )

        if current_order.cafe:
            # await worker.init_session()
            free_places = await worker.get_free_places(
                current_order.cafe, current_order.from_date
            )

            basket = context.user_data.get('basket')
            seats_sum = 0
            if basket:
                for seat_count in basket.values():
                    seats_sum += seat_count

            if not free_places or seats_sum > free_places:
                await query.edit_message_text(
                    (
                        f'На дату {result} мест нет.\n'
                        f'Выберите другой {RSTEP[step]}',
                    ),
                    reply_markup=query.message.reply_markup,
                    disable_web_page_preview=True,
                )
                return UserFlowState.SELECT_DATA

        await booking_menu_show(update, context)

        return UserFlowState.BOOKING

    return UserFlowState.SELECT_DATA
