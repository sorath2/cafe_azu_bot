from collections import defaultdict
from datetime import datetime

from models import Cafe, Order, Set, Table, User

from .worker import worker


class CurrentOrder:
    def __init__(self) -> None:
        self._order_id: int = None
        self._user: User = None
        self._cafe: Cafe = None
        self._tables = defaultdict(int)
        self._guests_count: int = 0
        self._from_date: datetime = None
        self._to_date: datetime = None
        self._menu = defaultdict(int)
        self._is_paid: bool = False
        self._is_cancelled: bool = False

    @property
    def order_id(self):
        return self._order_id

    @order_id.setter
    def order_id(self, order_id: int):
        self._order_id = order_id

    @property
    def guest_count(self):
        return self._guests_count

    @guest_count.setter
    def guest_count(self, count: int):
        if count < 0:
            raise ValueError('Count must be >0')
        self._guests_count = count
        if count == 0:
            self.clear_table()

    @property
    def user(self):
        return self._user

    @user.setter
    def user(self, user: User):
        if not self._order_id:
            self._user = user

    @property
    def cafe(self):
        return self._cafe

    @cafe.setter
    def cafe(self, cafe: Cafe):
        if not self._order_id:
            if self._cafe is not cafe:
                self._cafe = cafe
                self.clear_table()

    @property
    def tables(self):
        return self._tables

    def add_table(self, table: Table):
        if table.id not in self._tables:
            self._tables[table.id] = table

    def clear_table(self):
        self._tables.clear()

    @property
    def from_date(self):
        return self._from_date

    @from_date.setter
    def from_date(self, date: datetime):
        self._from_date = date

    @property
    def to_date(self):
        return self._to_date

    @to_date.setter
    def to_date(self, date: datetime):
        self._to_date = date

    @property
    def is_paid(self):
        return self._is_paid

    @is_paid.setter
    def is_paid(self, is_paid: bool):
        self._is_paid = is_paid

    @property
    def is_cancelled(self):
        return self._is_cancelled

    @is_cancelled.setter
    def is_cancelled(self, is_cancelled: bool):
        self._is_cancelled = is_cancelled

    @property
    def menu(self):
        return self._menu

    def add_to_menu(self, set: Set, quantity: int = 1):
        if quantity < 1:
            raise ValueError('Quantity must be > 0')
        self._menu[set.id] = (set, quantity)

    def remove_from_menu(self, set: Set):
        if set.id in self._menu:
            self._menu.pop(set.id)

    def clear_menu(self):
        self._menu.clear()

    def clear(self):
        self._order_id: int = None
        self._user: User = None
        self._cafe: Cafe = None
        self._tables = defaultdict(int)
        self._guests_count: int = 0
        self._from_date: datetime = None
        self._to_date: datetime = None
        self._menu = defaultdict(int)
        self._is_paid: bool = False
        self._is_cancelled: bool = False

    def __str__(self):
        info_message = ''
        if self._order_id:
            info_message += f'Номер бронирования: <b>{self._order_id}</b>\n'

        if self._cafe:
            info_message += (
                f'Кафе: <b>{self._cafe.name} ' f'({self._cafe.address})</b>\n'
            )

        if self._from_date:
            str_date = self._from_date.strftime("%d.%m.%Y")
            info_message += f'Дата: <b>{str_date}</b>\n'

        if self._guests_count > 0:
            info_message += f'Количество гостей: <b>{self._guests_count}</b>\n'

        if len(self._menu) > 0:
            menu_message = 'Выбранные сеты:\n'
            total_cost = 0
            total_quantity = 0
            for set_quantity_info in self.menu.values():
                menu_message += (
                    f'\t- {set_quantity_info[0].name} '
                    f'{set_quantity_info[1]} шт. '
                    f'x {set_quantity_info[0].cost}руб. = '
                    f'{set_quantity_info[1] * set_quantity_info[0].cost} '
                    f'руб.\n'
                )
                total_cost += set_quantity_info[1] * set_quantity_info[0].cost
                total_quantity += set_quantity_info[1]
            menu_message += (
                f'\tВсего <b>{total_quantity}</b> сет(а, ов) на '
                f'<b>{total_cost}</b> '
                f'руб.\n'
            )

            info_message += menu_message

        return info_message

    async def load_data(self, order_id: int):
        self.clear()
        # await worker.init_session()
        order: Order = await worker.get_order_by_id(order_id)

        if not order:
            return

        self._order_id = order.id
        self._user = await worker.get_user_by_id(order.buyer_id)
        self._cafe = await worker.get_cafe_by_id(order.cafe_id)
        self._guests_count = order.guests
        self._from_date = order.from_date
        self._to_date = order.to_date
        self._is_paid = order.is_paid
        self._is_cancelled = order.is_cancelled

        for menu in await worker.get_menu_by_id(order.id):
            menu_set = await worker.get_sets_by_id(menu.set_id)
            self.add_to_menu(menu_set, menu.quantity)
