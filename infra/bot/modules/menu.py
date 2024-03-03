from collections import defaultdict

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


async def menu_show(
    query: CallbackQuery,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    is_first_show: bool = True,
):
    set_of_sets = context.user_data['set_of_sets']
    currrent_set_id = context.user_data['currrent_set_id']
    basket = context.user_data['basket']
    # await worker.init_session()
    current_order: CurrentOrder = context.user_data['order']

    set_info = (
        f'Сет "{set_of_sets[currrent_set_id].name}" '
        f'({currrent_set_id + 1}/{len(set_of_sets)})\n'
        f'Стоимость {set_of_sets[currrent_set_id].cost} руб.\n'
    )

    if set_of_sets[currrent_set_id].id in basket:
        set_info += f'Выбрано {basket[set_of_sets[currrent_set_id].id]} шт.\n'

    total_cost = 0
    total_quantity = 0
    basket_info = ''
    for set_id, quantity in basket.items():
        total_quantity += quantity
        total_cost += worker.sets[set_id].cost * quantity
    if total_cost > 0 and total_quantity > 0:
        basket_info += (
            f'Всего выбрано {total_quantity} сетов на {total_cost} руб.'
        )

    free_places_data = await menu_info_about_free_places(current_order, basket)
    basket_info += free_places_data['message']

    keyboard = [
        [
            InlineKeyboardButton(
                'Предыдущий сет', callback_data=ButtonCallbackData.SET_PREV
            ),
            InlineKeyboardButton(
                'Следующий сет', callback_data=ButtonCallbackData.SET_NEXT
            ),
        ],
        [
            InlineKeyboardButton(
                '- 1', callback_data=ButtonCallbackData.SET_REMOVE_FROM_CART
            ),
            InlineKeyboardButton(
                '+ 1', callback_data=ButtonCallbackData.SET_ADD_TO_CART
            ),
        ],
        [
            InlineKeyboardButton(
                'Отменить', callback_data=ButtonCallbackData.SET_CANCEL
            ),
            InlineKeyboardButton(
                'Очистить корзину',
                callback_data=ButtonCallbackData.SET_CLEAR_CART,
            ),
        ],
        [
            InlineKeyboardButton(
                'Заказать', callback_data=ButtonCallbackData.SET_ORDER
            ),
        ],
    ]

    if is_first_show:
        await query.message.reply_photo(
            photo=open(f'media/{set_of_sets[currrent_set_id].picture}', 'rb'),
            caption=set_info + basket_info,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    else:
        await query.edit_message_media(
            InputMediaPhoto(
                media=open(
                    f'media/{set_of_sets[currrent_set_id].picture}', 'rb'
                ),
                caption=set_info + basket_info,
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def build_menu_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # await worker.init_session()
    # set_of_sets = context.user_data.get('set_of_sets', None)
    await worker.load_data()

    # if not set_of_sets or (len(set_of_sets) != len(worker.sets)):
    set_of_sets = [set for set in worker.sets.values()]
    context.user_data['set_of_sets'] = set_of_sets
    context.user_data['currrent_set_id'] = 0

    if not set_of_sets:
        await query.message.reply_text(
            (
                'Приносим извинения, меню сейчас недоступно.\n'
                'Свяжитесь с администратором по ☎️.'
            ),
            disable_web_page_preview=True,
        )
        await query.delete_message()
        await start_bot(update, context)
        return UserFlowState.START

    current_order: CurrentOrder = context.user_data['order']
    basket = defaultdict(int)
    for menu_item in current_order.menu.values():
        basket[menu_item[0].id] = menu_item[1]
    context.user_data['basket'] = basket

    await query.delete_message()
    await menu_show(query, update, context)

    return UserFlowState.BUILD_MENU


async def menu_switching_sets(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    set_of_sets = context.user_data['set_of_sets']
    currrent_set_id = context.user_data['currrent_set_id']

    if query.data == ButtonCallbackData.SET_NEXT:
        currrent_set_id = (currrent_set_id + 1) % len(set_of_sets)
    elif query.data == ButtonCallbackData.SET_PREV:
        currrent_set_id = (currrent_set_id - 1) % len(set_of_sets)

    context.user_data['currrent_set_id'] = currrent_set_id

    await menu_show(query, update, context, False)

    return UserFlowState.BUILD_MENU


async def menu_clear_basket(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    basket = context.user_data['basket']
    basket.clear()

    await menu_show(query, update, context, False)

    return UserFlowState.BUILD_MENU


async def menu_add_to_basket(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    set_of_sets = context.user_data['set_of_sets']
    currrent_set_id = context.user_data['currrent_set_id']
    current_set = set_of_sets[currrent_set_id]

    basket = context.user_data['basket']
    if current_set.id in basket:
        basket[current_set.id] += 1
    else:
        basket[current_set.id] += 1

    await menu_show(query, update, context, False)

    return UserFlowState.BUILD_MENU


async def menu_remove_from_basket(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    set_of_sets = context.user_data['set_of_sets']
    currrent_set_id = context.user_data['currrent_set_id']
    current_set = set_of_sets[currrent_set_id]

    basket = context.user_data['basket']
    if current_set.id in basket:
        if basket[current_set.id] == 1:
            basket.pop(current_set.id)
        else:
            basket[current_set.id] -= 1

        await menu_show(query, update, context, False)

    return UserFlowState.BUILD_MENU


async def menu_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    basket = context.user_data['basket']
    basket.clear()

    prev_stage = context.user_data.get('prev_stage', UserFlowState.START)

    if prev_stage == UserFlowState.BOOKING:
        await booking_menu_show(update, context)
    else:
        await query.delete_message()
        await start_bot(update, context)

    return prev_stage


async def menu_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    basket = context.user_data['basket']
    # await worker.init_session()
    current_order: CurrentOrder = context.user_data['order']

    free_places_data = await menu_info_about_free_places(current_order, basket)
    if not free_places_data['booking_allowed']:
        await query.answer((free_places_data['message']), show_alert=True)
        return UserFlowState.BUILD_MENU

    await query.answer()

    current_order.clear_menu()
    seats_sum = 0

    for set_id, quantity in basket.items():
        current_order.add_to_menu(worker.sets[set_id], quantity)
        seats_sum += quantity
    current_order.guest_count = seats_sum

    await booking_menu_show(update, context)

    return UserFlowState.BOOKING


async def menu_info_about_free_places(
    current_order: CurrentOrder, basket: dict
):
    free_places_data = {'message': '', 'booking_allowed': True}
    if current_order.from_date and current_order.cafe:
        free_places = await worker.get_free_places(
            current_order.cafe, current_order.from_date
        )

        seats_sum = 0
        if basket:
            for seat_count in basket.values():
                seats_sum += seat_count

        if free_places and seats_sum <= free_places:
            free_places_data['message'] = (
                f'\nНа {current_order.from_date.strftime("%Y-%m-%d")} '
                f'cвободных мест: {free_places}'
            )
        elif free_places and seats_sum > free_places:
            free_places_data['message'] = (
                f'\nНа {current_order.from_date.strftime("%Y-%m-%d")} '
                f'только {free_places} cвободных мест, уменьшете кол-во '
                'сетов, или выберите другой день'
            )
            free_places_data['booking_allowed'] = False
    return free_places_data
