from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from core.constants import ButtonCallbackData, UserFlowState
from crud.order import CurrentOrder
from crud.worker import worker

from .misc import generate_booking_message
from .start import start_bot


async def booking_menu_show(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if query:
        await query.answer()
        await query.delete_message()

    keyboard = [
        [
            InlineKeyboardButton(
                '✅ Дата'
                if context.user_data['order'].from_date
                else 'Выбрать дату',
                callback_data=ButtonCallbackData.BOOKING_SELECT_DATE,
            ),
            InlineKeyboardButton(
                '✅ Кафе'
                if context.user_data['order'].cafe
                else 'Выбрать кафе',
                callback_data=ButtonCallbackData.BOOKING_SELECT_CAFE,
            ),
        ],
        [
            InlineKeyboardButton(
                '✅ Меню'
                if context.user_data['order'].menu
                else 'Выбрать меню',
                callback_data=ButtonCallbackData.BOOKING_SELECT_SETS,
            ),
        ],
        [
            InlineKeyboardButton(
                'Отмена', callback_data=ButtonCallbackData.BOOKING_CANCEL
            ),
            InlineKeyboardButton(
                'Оплатить', callback_data=ButtonCallbackData.BOOKING_OK
            ),
        ],
    ]

    current_order: CurrentOrder = context.user_data['order']

    # await worker.init_session()

    info_message = 'Вы выбрали:\n'
    info_message += await generate_booking_message(
        current_order, cafe_info=False
    )
    info_message += '\nВыберите следующее действие:'

    context.user_data['prev_stage'] = UserFlowState.BOOKING

    if update.message:
        await update.message.reply_text(
            info_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML',
            disable_web_page_preview=True,
        )
    else:
        await context.bot.send_message(
            update.effective_chat.id,
            info_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML',
            disable_web_page_preview=True,
        )

    return UserFlowState.BOOKING


async def booking_menu_cancel(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    await query.delete_message()

    current_order: CurrentOrder = context.user_data['order']
    current_order.clear()
    basket = context.user_data.get('basket')
    if basket:
        context.user_data['basket'].clear()

    await start_bot(update, context)

    return UserFlowState.START
