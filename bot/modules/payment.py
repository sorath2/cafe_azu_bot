import datetime
from asyncio import sleep
import urllib.parse

import pytz

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    # LabeledPrice,
    Update,
)
from telegram.ext import ContextTypes

from core.config import settings
from core.constants import ButtonCallbackData, UserFlowState
from crud.order import CurrentOrder
from crud.worker import Worker
from models import Payment

from .booking import booking_menu_show
from .misc import generate_booking_message
from .start import start_bot
from .timers import (
    timer_for_payment,
    remove_job_if_exists,
    reservation_reminder
)
from . import robokassa


async def payment_show_dialog(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
):
    payment_message_id = context.user_data.get('payment_message_id', None)

    query = update.callback_query

    if payment_message_id:
        await query.message.reply_text(
            'Похоже, что окно оплаты уже показано.\nПосмотрите выше.'
        )
        return UserFlowState.PAYMENT_CHOOSE

    current_order: CurrentOrder = context.user_data.get('order')
    worker: Worker = context.user_data.get('worker')

    empty_fields = []

    if not current_order.menu:
        empty_fields.append('составе заказа')
    if not current_order.cafe:
        empty_fields.append('кафе для бронирования')
    if not current_order.from_date:
        empty_fields.append('дате бронирования')

    if empty_fields:
        await query.answer(
            (
                'Вы указали не все детали бронирования.\n'
                'Не хватает информации о '
                + ', '.join(empty_fields) + '.'
            ),
            show_alert=True
        )
        await booking_menu_show(update, context)
        return UserFlowState.BOOKING

    free_places = await worker.get_free_places(current_order.cafe,
                                               current_order.from_date)
    if free_places <= 0:
        await query.answer(
            (
                ('Свободные места закончились, '
                 'измените детали бронирования')
            ),
            show_alert=True
        )
        await booking_menu_show(update, context)
        return UserFlowState.BOOKING

    await query.answer()
    await query.delete_message()

    if not context.user_data.get('continue_booking', False):
        await worker.save_order(current_order)

    booking_id = current_order.order_id

    basket = context.user_data.get('basket', None)
    if basket:
        context.user_data['basket'].clear()

    payment_price = 0
    for menu_item in current_order.menu.values():
        cur_cost = menu_item[1] * menu_item[0].cost
        payment_price += cur_cost

    payment_link = robokassa.generate_payment_link(
        merchant_login=settings.merchant_login,
        merchant_password_1=settings.merchant_password1,
        cost=payment_price,
        number=booking_id,
        description=urllib.parse.quote(f'Заказ {booking_id} на {current_order.from_date}'),
        is_test=1,
    )

    payment_keyboard = [
        [
            InlineKeyboardButton(
                f'Оплатить {payment_price} руб.',
                url=payment_link,
            ),
        ],
        [
            InlineKeyboardButton(
                'Отменить бронь',
                callback_data=ButtonCallbackData.PAYMENT_CANCEL,
            ),
        ],
    ]

    info_message = await generate_booking_message(
        current_order, worker, cafe_info=False
    )
    
    payment_message = await context.bot.send_message(
        update.effective_chat.id,
        info_message,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(payment_keyboard),
    )

    payment = Payment(
        chat_id=update.effective_chat.id,
        order_id=booking_id,
        payment_link=payment_link,
        payment_message_id=payment_message.message_id,
        payment_start=datetime.datetime.now()
    )
    await worker.save_to_control_payments(payment)
    
    text = "Для оплаты бронирования у вас есть 15 минут"
    message = await query.message.reply_text(text)
    await sleep(3)

    context.user_data['payment_message_id'] = payment_message.message_id
    chat_id = update.effective_message.chat_id
    current_message = message.id

    context.job_queue.run_once(
        timer_for_payment,
        settings.payment_timeout,
        chat_id=chat_id,
        name=f'PAYMENT_order_id_{booking_id}',
        data={
            'count': settings.payment_timeout,
            'message_id': update.effective_message.id,
            'payment_message_id': payment_message.message_id,
            'current_message': current_message,
            'worker': worker,
            'current_order': current_order
        },
    )

    return UserFlowState.PAYMENT_CHOOSE


async def payment_successful(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    await query.delete_message()

    payment_message_id = context.user_data.get('payment_message_id', None)

    if payment_message_id:
        # await context.bot.delete_message(     # Удаление сообщения с информацией о броне
        #     update.message.chat_id,
        #     payment_message_id - 1,
        # )
        # await context.bot.delete_message(
        #     update.message.chat_id,
        #     payment_message_id,
        # )
        # await context.bot.delete_message(     # Удаление сообщения с таймером
        #     update.message.chat_id,
        #     payment_message_id + 1,
        # )
        del context.user_data['payment_message_id']

    # current_order: CurrentOrder = context.user_data['order']
    # worker: Worker = context.user_data['worker']

    # current_order.is_paid = True

    # await worker.update_payment_status(
    #     order_id=current_order.order_id,
    #     is_paid=True,
    # )
    # info_message = 'Спасибо, оплата за бронирование прошла успешно!\n'
    # info_message += await generate_booking_message(current_order, worker)
    # await context.bot.send_message(
    #     update.effective_chat.id,
    #     info_message,
    #     parse_mode='HTML',
    # )

    # chat_id = update.effective_message.chat_id
    # remove_job_if_exists(str(chat_id), context)
    # data_order = current_order.from_date
    # tz_kazan = pytz.timezone('Europe/Moscow')
    # name_timer = f'Напоминание о бронировании {chat_id}'
    # time_message = data_order.replace(
    #     day=data_order.day - 1,
    #     hour=13,
    #     minute=0,
    #     second=0).astimezone(tz_kazan)

    # if (data_order - datetime.datetime.now()) > datetime.timedelta(hours=11):
    #     context.job_queue.run_once(
    #         reservation_reminder,
    #         time_message,
    #         chat_id=chat_id,
    #         name=name_timer,
    #         data={}
    #     )
    #     await worker.save_timer_job(
    #         chat_id=chat_id,
    #         name=name_timer,
    #         order_id = current_order.order_id,
    #         data={},
    #         scheduled_time=data_order
    #     )

    # context.user_data['last_order'] = current_order
    context.user_data['continue_booking'] = False
    await start_bot(update, context)

    return UserFlowState.START


async def payment_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.delete_message()
    
    payment_message_id = context.user_data.get('payment_message_id')
    if payment_message_id:
        del context.user_data['payment_message_id']

    current_order: CurrentOrder = context.user_data['order']
    worker: Worker = context.user_data['worker']

    order_status = await worker.get_cancelled_status(current_order.order_id)
    await worker.update_cancelled_status(
        order_id=current_order.order_id, is_cancelled=True
    )

    basket = context.user_data.get('basket')
    if basket:
        context.user_data['basket'].clear()

    chat_id = update.effective_message.chat_id

    if not order_status:
        remove_job_if_exists(f'PAYMENT_order_id_{current_order.order_id}', context)
        if payment_message_id:
            await context.bot.delete_message(
                chat_id,
                # update.effective_message.message_id + 1
                payment_message_id + 1
            )
        # else:
        #     order = await worker.get_order_by_id(order_id=current_order.order_id)
        #     cafe = await worker.get_cafe_by_id(cafe_id=order)

        # await worker.update_cancelled_status(
        #     order_id=current_order.order_id,
        #     is_cancelled=True
        # )
        info_message = '<b>Бронирование отменено!</b>\n'
        info_message += await generate_booking_message(current_order, worker)
        await context.bot.send_message(
            update.effective_chat.id,
            info_message,
            parse_mode='HTML',
        )

    context.user_data['continue_booking'] = False
    await start_bot(update, context)

    return UserFlowState.START


async def payment_precheckout(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Answers the PreQecheckoutQuery"""

    current_order: CurrentOrder = context.user_data['order']

    booking_id = current_order.order_id

    query = update.pre_checkout_query

    if query.invoice_payload != f'payment_booking_{booking_id}':
        await query.answer(ok=False, error_message="Что-то пошло не так...")
    else:
        await query.answer(ok=True)
