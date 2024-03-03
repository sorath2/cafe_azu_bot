from crud.order import CurrentOrder
from crud.worker import worker
from models.models import Menu


async def generate_booking_message(order: CurrentOrder, cafe_info=True):
    """Генерирует сообщение с информацией о бронировнии."""

    # await worker.init_session()

    cafe = order.cafe
    menu = []
    for set_in_menu, quantity in order.menu.values():
        menu_in_order = Menu()
        menu_in_order.set_id = set_in_menu.id
        menu_in_order.quantity = quantity
        menu.append(menu_in_order)
    if order.order_id:
        message = f'Номер бронирования: <b>{order.order_id}</b>\n'
    else:
        message = ' '

    if cafe:
        message += f'Кафе: <b>{cafe.name} ({cafe.address})</b>\n'
    if cafe_info:
        message += f'☎️ {cafe.phone}\n' f'🌍 {cafe.map_link}\n'
    if order.from_date:
        message += f'Дата: <b>{order.from_date.strftime("%d.%m.%Y")}</b>\n'

    total_cost = 0
    total_quantity = 0

    if menu:
        menu_message = 'Выбранные сеты:\n'
        for menu_item in menu:
            set_info = await worker.get_sets_by_id(menu_item.set_id)

            menu_message += (
                f'\t- {set_info.name}  {menu_item.quantity} шт. '
                f'x {set_info.cost}руб. = '
                f'{menu_item.quantity * set_info.cost} руб.\n'
            )
            total_cost += menu_item.quantity * set_info.cost
            total_quantity += menu_item.quantity

        menu_message += (
            f'\tВсего <b>{total_quantity}</b> сет(а, ов) '
            f'на <b>{total_cost}</b> руб.\n'
        )
        message += menu_message

    return message
