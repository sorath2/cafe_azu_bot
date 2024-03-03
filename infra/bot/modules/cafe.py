from telegram import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Update,
)
from telegram.ext import ContextTypes

from core.constants import ButtonCallbackData, UserFlowState
from crud.order import CurrentOrder
from crud.worker import worker

from .booking import booking_menu_show
from .start import start_bot


async def show_cafe(
    query: CallbackQuery,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    is_first_show: bool = True,
):
    cafe_select_id = context.user_data['cafe_select_id']

    # await worker.init_session()

    current_cafe = worker.cafes[cafe_select_id]

    keyboard = []
    key_line = []
    i = 0
    for cafe_id, cafe in worker.cafes.items():
        if i > 0 and i % 2 == 0:
            keyboard.append(key_line)
            key_line = []
        key_line.append(
            InlineKeyboardButton(
                text=f'✅ {cafe.name}'
                if cafe_select_id == cafe_id
                else f'{cafe.name}',
                callback_data=(
                    f'{ButtonCallbackData.CAFE_DETAIL_PREFIX.value}{cafe_id}'
                ),
            )
        )
        i += 1
    if key_line:
        keyboard.append(key_line)
        key_line = []
    key_line = [
        InlineKeyboardButton(
            text='Отменить',
            callback_data=f'{ButtonCallbackData.CAFE_CANCEL.value}',
        ),
        InlineKeyboardButton(
            text='Выбрать',
            callback_data=f'{ButtonCallbackData.CAFE_BOOK.value}',
        ),
    ]
    keyboard.append(key_line)

    # cafe_info = f'{current_cafe.name}\n' f'🏠 {current_cafe.address}\n'
    cafe_info = (
        f'{current_cafe.name}\n'
        f'🏠 {current_cafe.address}\n'
        f'☎️ {current_cafe.phone}\n'
        f'🌍 {current_cafe.map_link}'
    )

    free_places_data = await cafe_info_about_free_places(context)
    cafe_info += free_places_data['message']

    if is_first_show:
        await query.message.reply_photo(
            photo=open(f'media/{current_cafe.picture}', 'rb'),
            caption=cafe_info,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        await query.edit_message_media(
            InputMediaPhoto(
                media=open(f'media/{current_cafe.picture}', 'rb'),
                caption=cafe_info,
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def cafe_select_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    # await worker.init_session()

    if not worker.cafes:
        await query.message.reply_text(
            (
                'Приносим извинения, список кафе сейчас недоступен.\n'
                'Свяжитесь с администратором по ☎️.'
            ),
            disable_web_page_preview=True,
        )

        await query.delete_message()
        await start_bot(update, context)
        return UserFlowState.START

    await worker.load_data()

    # if 'cafe_select_id' not in context.user_data:
    cafe_keys = [key for key in worker.cafes.keys()]
    context.user_data['cafe_select_id'] = cafe_keys[0]

    await query.delete_message()
    await show_cafe(query, update, context)

    return UserFlowState.SELECT_CAFE


async def cafe_select_change_cafe(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    cafe_select_id = int(query.data.split('_')[2])
    context.user_data['cafe_select_id'] = cafe_select_id

    await show_cafe(query, update, context, False)

    return UserFlowState.SELECT_CAFE


async def cafe_select_cancel(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    prev_stage = context.user_data.get('prev_stage', UserFlowState.START)

    if prev_stage == UserFlowState.BOOKING:
        await booking_menu_show(update, context)
    else:
        await query.delete_message()

        await start_bot(update, context)

    return prev_stage


async def cafe_select_booking(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    current_order: CurrentOrder = context.user_data['order']
    free_places_data = await cafe_info_about_free_places(context)
    if not free_places_data['booking_allowed']:
        await query.answer((free_places_data['message']), show_alert=True)
        return UserFlowState.SELECT_CAFE

    await query.answer()
    cafe_select_id = context.user_data['cafe_select_id']

    # await worker.init_session()

    current_order.cafe = worker.cafes[cafe_select_id]

    await booking_menu_show(update, context)

    return UserFlowState.BOOKING


async def cafe_info_about_free_places(context: ContextTypes.DEFAULT_TYPE):
    cafe_select_id = context.user_data['cafe_select_id']
    # await worker.init_session()
    current_cafe = worker.cafes[cafe_select_id]
    current_order = context.user_data['order']

    basket = context.user_data.get('basket')
    seats_sum = 0
    if basket:
        for seat_count in basket.values():
            seats_sum += seat_count

    free_places = None
    free_places_data = {'message': '', 'booking_allowed': True}
    if current_order.from_date:
        free_places = await worker.get_free_places(
            current_cafe, current_order.from_date
        )
    if free_places and seats_sum <= free_places:
        free_places_data['message'] = (
            f'\n🙋‍♂️ На {current_order.from_date.strftime("%Y-%m-%d")} '
            f'cвободных мест: {free_places}, '
            f'выбрано мест: {seats_sum}'
        )
    elif free_places and seats_sum > free_places:
        free_places_data['message'] = (
            f'\n🙋‍♂️ Выбрано мест: {seats_sum}, '
            f'увы в кафе только {free_places} свободных мест '
            f'на {current_order.from_date.strftime("%Y-%m-%d")}'
        )
        free_places_data['booking_allowed'] = False
    return free_places_data
