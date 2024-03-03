"""Функции для обработки кнопок стартового сообщения."""
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, KeyboardButton, Update)
from telegram.ext import ContextTypes

from core.constants import ButtonCallbackData, UserFlowState
from core.db import get_async_session
from crud.order import CurrentOrder
from crud.worker import Worker

from .misc import generate_booking_message


async def start_menu_keyboard(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = context.user_data['user']
    worker: Worker = context.user_data['worker']

    user_bookings = await worker.get_user_bookings(user)
    context.user_data['user_bookings'] = user_bookings

    inline_keyboard = [
        [InlineKeyboardButton(
            'Забронировать',
            callback_data=ButtonCallbackData.MAIN_MENU_BOOKING.value,
        )]
    ]

    if user_bookings:
        inline_keyboard.append([InlineKeyboardButton(
            'Детали брони',
            callback_data=ButtonCallbackData.MAIN_MENU_BOOKING_DETAIL.value,
        )])

    return inline_keyboard


async def send_phone_request_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Отправляет запрос на ввод номера телефона"""
    message_text = (
        'Вас приветствует AZU-бот🌙\n'
        'Для продолжения бронирования введите '
        'свой номер телефона в формате 74951112233 или '
        'нажмите кнопку "Отправить номер телефона" ☎️'
    )

    markup_request = ReplyKeyboardMarkup(
        [[KeyboardButton("Отправить номер телефона", request_contact=True)]],
        one_time_keyboard=True,
        resize_keyboard=True,
    )

    if update.message:
        await update.message.reply_text(
            message_text,
            reply_markup=markup_request
        )
    else:
        await context.bot.send_message(
            update.effective_chat.id,
            message_text,
            reply_markup=markup_request
        )

    return UserFlowState.PHONE_REQUEST


async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выводит стартовое приветственное сообщение"""

    if update.message:
        bot_user = update.message.from_user
    else:
        bot_user = update.effective_user

    context.user_data['payment_message_id'] = None
    worker = context.user_data.get('worker', None)

    if not worker:
        a_gen = get_async_session()
        session = await anext(a_gen)
        worker = Worker(session)

    await worker.load_data()

    context.user_data['worker'] = worker
    user = await worker.get_user(str(bot_user.id))

    if not user:
        phone_number = context.user_data.get('phone_number')

        if phone_number is None:
            await send_phone_request_message(update, context)
            return UserFlowState.PHONE_REQUEST

        user = await worker.add_user(
            str(bot_user.id),
            bot_user.full_name,
            phone_number,
        )

        context.user_data['user'] = user

        if update.message:
            await update.message.reply_text(
                f'{user.name}, Вы успешно зарегистрированы!'
            )
        else:
            await context.bot.send_message(
                update.effective_chat.id,
                f'{user.name}, Вы успешно зарегистрированы!'
            )

    context.user_data['user'] = user

    not_paid_order = await worker.get_last_not_paid_user_booking(user)

    if not_paid_order:
        current_order = CurrentOrder()
        await current_order.load_data(not_paid_order.id, worker)
        context.user_data['order'] = current_order
        context.user_data['continue_booking'] = True

        keyboard = [
            [
                InlineKeyboardButton(
                    'Продолжить',
                    callback_data=ButtonCallbackData.BOOKING_OK,
                ),
            ],
            [
                InlineKeyboardButton(
                    'Отменить бронь',
                    callback_data=ButtonCallbackData.BOOKING_PAYMENT_CANCEL,
                ),
            ],
        ]
        info_message = (
            'Вас приветствует AZU-бот🌙\n'
            'У вас осталось незавершенное бронирование:\n'
        )
        info_message += await generate_booking_message(
            current_order, worker
        )

        await context.bot.send_message(
            update.effective_chat.id,
            info_message,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

        return UserFlowState.BOOKING

    else:
        current_order = CurrentOrder()
        current_order.user = user
        context.user_data['order'] = current_order
        context.user_data['continue_booking'] = False

        context.user_data['prev_stage'] = UserFlowState.START

        keyboard = await start_menu_keyboard(update, context)

        if update.message:
            await update.message.reply_text(
                'Выберите дальнейшее действие:',
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        else:
            await context.bot.send_message(
                update.effective_chat.id,
                'Выберите дальнейшее действие:',
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        return UserFlowState.START


async def contact_phone_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Обрабатывает контакт или номер телефона от пользователея."""
    phone_number = None

    if update.message and update.message.contact:
        phone_number = update.message.contact.phone_number
    elif update.message and update.message.text:
        phone_number = update.message.text.strip()
        if phone_number and (
            not phone_number.isdigit() or len(phone_number) != 11
        ):
            await update.message.reply_text(
                'Вы ввели некорректный номер телефона. '
                'Введите номер телефона в формате 74951112233 '
            )
            return UserFlowState.PHONE_REQUEST

    context.user_data['phone_number'] = phone_number

    await start_bot(update, context)

    return UserFlowState.START
