from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from core.constants import ButtonCallbackData, UserFlowState
from crud.order import CurrentOrder
from crud.worker import worker

from .misc import generate_booking_message
from .start import start_bot


async def booking_detail_show(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()
    await query.delete_message()

    user = context.user_data['user']
    # await worker.init_session()

    user_bookings = await worker.get_user_bookings(user)
    context.user_data['user_bookings'] = user_bookings

    current_booking_indx = context.user_data.get('current_booking_indx', 0)

    button_back = [
        InlineKeyboardButton(
            'Назад', callback_data=ButtonCallbackData.BOOKING_DETAIL_BACK
        )
    ]
    button_next = [
        InlineKeyboardButton(
            'Следующее бронирование ➡️',
            callback_data=ButtonCallbackData.BOOKING_DETAIL_NEXT,
        )
    ]
    button_previous = [
        InlineKeyboardButton(
            '⬅️ Предыдущее бронирование',
            callback_data=ButtonCallbackData.BOOKING_DETAIL_PREV,
        )
    ]

    if user_bookings:
        current_booking = user_bookings[current_booking_indx]

        def pluralize(number, forms):
            if number % 100 in {11, 12, 13, 14}:
                return forms[2]
            rem = number % 10
            if rem == 1:
                return forms[0]
            elif 2 <= rem <= 4:
                return forms[1]
            else:
                return forms[2]

        order_1 = "бронирование"
        order2_4 = "бронирования"
        orders = "бронирований"
        info_message = (
            f'\tУ Вас <b>{len(user_bookings)}</b> '
            f'{pluralize(len(user_bookings), [order_1, order2_4, orders])}.\n'
            f'Бронирование {current_booking_indx + 1} из '
            f'{len(user_bookings)}\n'
        )
        current_order = CurrentOrder()
        await current_order.load_data(current_booking.id)
        info_message += await generate_booking_message(current_order)
        info_message += 'Для отмены бронирования свяжитесь с администратором.'

        if len(user_bookings) > 1:
            keyboard = [button_next, button_previous, button_back]
        else:
            keyboard = [button_back]
    else:
        keyboard = [button_back]
        info_message = 'У вас нет активных бронирований.'

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

    return UserFlowState.BOOKING_DETAIL


async def bookings_switching(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    current_booking_indx = context.user_data.get('current_booking_indx', 0)
    user_bookings = context.user_data['user_bookings']

    if query.data == ButtonCallbackData.BOOKING_DETAIL_NEXT:
        current_booking_indx = (current_booking_indx + 1) % len(user_bookings)
    elif query.data == ButtonCallbackData.BOOKING_DETAIL_PREV:
        current_booking_indx = (current_booking_indx - 1) % len(user_bookings)

    context.user_data['current_booking_indx'] = current_booking_indx

    await booking_detail_show(update, context)

    return UserFlowState.BOOKING_DETAIL


async def booking_detail_back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    await query.delete_message()

    await start_bot(update, context)

    return UserFlowState.START
