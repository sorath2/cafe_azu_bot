"""Функции для обработки кнопок стартового сообщения."""
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from core.constants import ButtonCallbackData, UserFlowState
from crud.order import CurrentOrder
from crud.worker import worker

from .misc import generate_booking_message
from .timers import timers_for_start_bot


async def start_menu_keyboard(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    user = context.user_data['user']
    # await worker.init_session()

    user_bookings = await worker.get_user_bookings(user)
    context.user_data['user_bookings'] = user_bookings

    inline_keyboard = [
        [
            InlineKeyboardButton(
                'Забронировать',
                callback_data=ButtonCallbackData.MAIN_MENU_BOOKING.value,
            )
        ]
    ]

    if user_bookings:
        inline_keyboard.append(
            [
                InlineKeyboardButton(
                    'Детали брони',
                    callback_data=ButtonCallbackData.MAIN_MENU_BOOKING_DETAIL.value,
                )
            ]
        )

    return inline_keyboard


async def send_phone_request_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
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
            reply_markup=markup_request,
            disable_web_page_preview=True,
        )
    else:
        await context.bot.send_message(
            update.effective_chat.id,
            message_text,
            reply_markup=markup_request,
            disable_web_page_preview=True,
        )

    return UserFlowState.PHONE_REQUEST


async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выводит стартовое приветственное сообщение"""

    await worker.load_data()
    
    # Проверяем, что запущены таймеры
    if context.job_queue:
        is_remaind_timer = context.job_queue.get_jobs_by_name(
            'SYSTEM_update_remaind_timers'
        )
        is_payment_timer = context.job_queue.get_jobs_by_name(
            'SYSTEM_payment_check_timers'
        )

        if not is_payment_timer or not is_remaind_timer:
            await timers_for_start_bot(update, context)

    if update.message:
        bot_user = update.message.from_user
    else:
        bot_user = update.effective_user

    context.user_data['payment_message_id'] = None
    # await worker.init_session()

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
                f'{user.name}, Вы успешно зарегистрированы!',
                disable_web_page_preview=True,
            )
        else:
            await context.bot.send_message(
                update.effective_chat.id,
                f'{user.name}, Вы успешно зарегистрированы!',
                disable_web_page_preview=True,
            )

    context.user_data['user'] = user

    not_paid_order = await worker.get_last_not_paid_user_booking(user)

    if not_paid_order:
        current_order = CurrentOrder()
        await current_order.load_data(not_paid_order.id)
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
        info_message += await generate_booking_message(current_order)

        await context.bot.send_message(
            update.effective_chat.id,
            info_message,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True,
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
                disable_web_page_preview=True,
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
