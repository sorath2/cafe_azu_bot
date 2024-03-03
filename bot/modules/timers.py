import datetime
from asyncio import sleep
from datetime import datetime, timedelta

import pytz

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes

from core.config import settings
from core.db import get_async_session
from crud.order import CurrentOrder
from crud.worker import Worker
from core.constants import ButtonCallbackData

from .misc import generate_booking_message


async def reservation_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    await context.bot.send_message(
        text='Напоминание о бронировании',
        chat_id=job.chat_id,
    )


def remove_job_if_exists(
        name: str,
        context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    """Remove job with given name. Returns whether job was removed."""

    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def timer_for_payment(context: ContextTypes.DEFAULT_TYPE, ) -> None:
    """Отправляет таймер для оплаты"""

    job = context.job
    timer_count = job.data['count']
    timer_message = job.data['current_message']
    payment_message = job.data['payment_message_id']
    worker = job.data['worker']
    current_order = job.data['current_order']

    while timer_count > 5:
        timer_count -= 1
        order_status = await worker.get_cancelled_status(current_order.order_id)
        if order_status:
            break
        else:
            await context.bot.edit_message_text(
                text=f'До отмены бронирования осталось '
                     f'<b> {timer_count} минут </b>',
                chat_id=job.chat_id,
                message_id=timer_message,
                parse_mode='HTML'
            )
            await sleep(60)
            

    seconds = timer_count * 60
    while seconds > 0:
        seconds -= 1
        order_status = await worker.get_cancelled_status(current_order.order_id)
        if order_status:
            break
        else:
            m, s = divmod(seconds, 60)
            await context.bot.edit_message_text(
                text=f'До отмены бронирования осталось '
                     f'<b> {m} минут {s:02} секунд </b>',
                chat_id=job.chat_id,
                message_id=timer_message,
                parse_mode='HTML'
            )
            await sleep(1)
            

    if seconds == 0:
        # await context.bot.delete_message(job.chat_id, payment_message - 1)
        await context.bot.delete_message(job.chat_id, payment_message)
        await context.bot.delete_message(job.chat_id, timer_message)

        info_message = await generate_booking_message(current_order, worker)

        await context.bot.send_message(
            text=f'Ваше бронирование отменено, т.к. истекло время на оплату\n'
                 f'{info_message}',
            chat_id=job.chat_id,
            parse_mode='HTML'
        )

        await worker.update_cancelled_status(
            order_id=current_order.order_id,
            is_cancelled=True
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    'Начать сначала',
                    callback_data=ButtonCallbackData.PAYMENT_CANCEL,
                ),
            ],
        ]
        await context.bot.send_message(
            job.chat_id,
            'Выберите дальнейшее действие:',
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def update_timers(
    context: ContextTypes.DEFAULT_TYPE,
):
    """Функция для периодического обновления таймеров."""

    job = context.job
    chat_id = job.chat_id
    a_gen = get_async_session()
    session = await anext(a_gen)
    worker = Worker(session)
    # await worker.load_data()

    for timer in job.data['timers']:
        remove_job_if_exists(timer.name, context)
        is_paid, is_cancelled = await worker.get_order_status(timer.order_id)

        if not is_cancelled and timer.scheduled_time - datetime.now() >= timedelta(hours=11):
                scheduled_time = timer.scheduled_time
                one_day = timedelta(days=1)
                scheduled_time -= one_day
                scheduled_time = scheduled_time.replace(
                    hour=13,
                    minute=00,
                    second=00
                )
                
                context.job_queue.run_once(
                    reservation_reminder,
                    name=timer.name,
                    when=scheduled_time - datetime.now(),
                    chat_id=timer.chat_id,
                    data=timer.data,
                )

async def timer_checking_payment_status(context: ContextTypes.DEFAULT_TYPE,):
    job = context.job
    worker = job.data['worker']
    payments_control = await worker.get_control_payments()
    for payment in payments_control:
        is_paid, is_canceled = await worker.get_order_status(payment.order_id)
        if is_canceled:
            await worker.remove_from_control_payments(payment)
            continue

        if is_paid:
            # Выводим сообщение об успешной оплате бронирования
            await context.bot.delete_message(
               payment.chat_id,
               payment.payment_message_id
            )
            await context.bot.delete_message(
               payment.chat_id,
               payment.payment_message_id + 1
            )

            current_order: CurrentOrder = CurrentOrder()
            await current_order.load_data(payment.order_id, worker)
            info_message = 'Спасибо, оплата за бронирование прошла успешно!\n'
            info_message += await generate_booking_message(current_order, worker)
            await context.bot.send_message(
                payment.chat_id,
                info_message,
                parse_mode='HTML',
            )

            remove_job_if_exists(
                f'PAYMENT_order_id_{payment.order_id}',
                context
            )

            if current_order.from_date - datetime.now() >= timedelta(hours=11):
                timer_name = f'REMAING_order_id_{payment.order_id}'

                scheduled_time = current_order.from_date
                one_day = timedelta(days=1)
                scheduled_time -= one_day
                scheduled_time = scheduled_time.replace(
                    hour=13,
                    minute=00,
                    second=00
                )

                context.job_queue.run_once(
                    reservation_reminder,
                    name=timer_name,
                    when=scheduled_time - datetime.now(),
                    chat_id=payment.chat_id,
                    data={'order_id': payment.order_id}
                )

                await worker.save_timer_job(
                    payment.chat_id,
                    name=timer_name,
                    order_id = current_order.order_id,
                    data={},
                    scheduled_time=current_order.from_date
                )
            
            keyboard = [
                [
                    InlineKeyboardButton(
                        'Начать сначала',
                        callback_data=ButtonCallbackData.PAYMENT_OK,
                    ),
                ],
            ]
            await context.bot.send_message(
                payment.chat_id,
                'Выберите дальнейшее действие:',
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

            await worker.remove_from_control_payments(payment)
            continue

        if datetime.now() - payment.payment_start > timedelta(minutes=settings.payment_timeout):
            await worker.remove_from_control_payments(payment)
            continue

async def timers_for_start_bot(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Функция для обновления таймеров."""

    worker = context.user_data.get('worker', None)
    if not worker:
        a_gen = get_async_session()
        session = await anext(a_gen)
        worker = Worker(session)
    await worker.load_data()

    context.user_data['worker'] = worker

    timers = await worker.get_all_timer_jobs()
    job = context.job_queue.run_repeating(
        update_timers,
        interval=1800,
        chat_id=update.effective_message.chat_id,
        data={'timers': timers}
    )
    await job.run(context.application)

    # Запуск таймера для проверки состояния оплаты
    context.job_queue.run_repeating(
        timer_checking_payment_status,
        interval=60, # 1 minute
        data={'worker': worker},
        chat_id=update.effective_message.chat_id,
    )
