from telegram import Update
from telegram.ext import ContextTypes

from core.constants import UserFlowState
from crud.order import CurrentOrder
from crud.worker import worker

from .booking import booking_menu_show


def build_guest_count_message(guest_count: int):
    if guest_count > 0:
        info_message = (
            f'Ранее выбрано `{guest_count}` гостей.\n'
            f'Введите новое количество гостей '
        )
    else:
        info_message = 'Введите количество гостей '
    info_message += 'или `0`, что бы вернуться назад без изменений.'

    return info_message


async def guests_count_show(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    await query.delete_message()

    current_order: CurrentOrder = context.user_data['order']

    info_message = build_guest_count_message(current_order.guest_count)

    message = await context.bot.send_message(
        update.effective_chat.id,
        info_message,
        disable_web_page_preview=True,
    )

    context.user_data['guest_count_message_id'] = message.id

    return UserFlowState.GUEST_COUNT


async def guests_count_process(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    try:
        guests_count = int(update.message.text)
    except Exception:
        guests_count = -1

    guests_count_message_id = context.user_data['guest_count_message_id']
    current_order: CurrentOrder = context.user_data['order']
    # await worker.init_session()

    await context.bot.delete_message(
        update.effective_chat.id,
        update.message.id,
    )

    if guests_count < 0:
        info_message = 'Количество гостей должно быть больше 0\n'
        info_message += build_guest_count_message(current_order.guest_count)
        await context.bot.editMessageText(
            info_message,
            chat_id=update.effective_chat.id,
            message_id=guests_count_message_id,
        )
        return UserFlowState.GUEST_COUNT

    if guests_count > 0:
        current_order.guest_count = guests_count

        if current_order.cafe and current_order.from_date:
            select_tables = await worker.get_tables_by_guests(
                guests_count, current_order.cafe, current_order.from_date
            )
            if select_tables:
                for t in select_tables:
                    current_order.add_table(t)
            else:
                current_order.guest_count = 0
                info_message = (
                    f'На {guests_count} гостей '
                    f'в кафе {current_order.cafe.name} '
                    f'на {current_order.from_date} '
                    f'нет мест.\n'
                )
                info_message += build_guest_count_message(
                    current_order.guest_count
                )
                await context.bot.editMessageText(
                    info_message,
                    chat_id=update.effective_chat.id,
                    message_id=guests_count_message_id,
                    disable_web_page_preview=True,
                )
                return UserFlowState.GUEST_COUNT

    await context.bot.delete_message(
        update.effective_chat.id,
        guests_count_message_id,
    )

    await booking_menu_show(update, context)

    return UserFlowState.BOOKING
