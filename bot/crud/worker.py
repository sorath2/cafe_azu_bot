from collections import defaultdict
from datetime import datetime
from typing import List

from sqlalchemy import desc, not_
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from core.db import AsyncSession
from models import Cafe, Category, Menu, Order, User, Job, Payment

from .order import CurrentOrder


class Worker:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.cafes = defaultdict(int)
        self.tables = defaultdict(int)
        self.sets = defaultdict(int)
        self.category = defaultdict(int)

    async def _load_cafes_info(self):
        cafes_data = await self._session.execute(
            select(Cafe).options(selectinload(Cafe.tables))
        )
        cafes_data = cafes_data.scalars().all()
        for cafe in cafes_data:
            self.cafes[cafe.id] = cafe
            self.tables[cafe.id] = cafe.tables

    async def _load_sets_info(self):
        category_data = await self._session.execute(
            select(Category).options(selectinload(Category.sets))
        )

        category_data = category_data.scalars().all()

        for category in category_data:
            self.category[category.id] = category
            for set in category.sets:
                self.sets[set.id] = set

    async def load_data(self):
        self.cafes.clear()
        self.tables.clear()
        self.sets.clear()
        await self._load_cafes_info()
        await self._load_sets_info()

    async def get_user(self, telegram_id: str) -> User:
        users = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return users.scalars().first()

    async def get_user_by_id(self, user_id: str) -> User:
        users = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        return users.scalars().first()

    async def add_user(
        self,
        telegram_id: str,
        name: str,
        phone_number: str,
        is_admin: bool = False,
        is_superuser: bool = False,
    ) -> User:
        new_user = User(
            telegram_id=telegram_id,
            name=name,
            phone_number=phone_number,
            admin=is_admin,
            superuser=is_superuser,
        )

        self._session.add(new_user)
        await self._session.commit()
        await self._session.refresh(new_user)
        return new_user

    async def save_order(self, current_order: CurrentOrder):
        order = Order(
            date=datetime.now(),
            buyer_id=current_order.user.id,
            guests=current_order.guest_count,
            from_date=current_order.from_date,
            to_date=current_order.from_date,
            cafe_id=current_order.cafe.id,
            is_cancelled=False,
            is_paid=False,
            description='Заказ',
        )
        self._session.add(order)
        await self._session.commit()
        await self._session.refresh(order)

        menus = [
            Menu(
                order_id=order.id,
                set_id=set_id,
                quantity=menu_item[1],
            )
            for set_id, menu_item in current_order.menu.items()
        ]

        self._session.add_all(menus)
        await self._session.commit()

        # bookings = [
        #     Booking(
        #         order_id=order.id,
        #         table_id=table_id,
        #     )
        #     for table_id in current_order.tables.keys()
        # ]

        # self._session.add_all(bookings)
        # await self._session.commit()

        current_order.order_id = order.id

    async def get_free_places(self, cafe: Cafe, date: datetime):
        total_places = 0
        menus_quantity = 0

        orders_on_date = await self._session.execute(
            select(Order)
            .options(selectinload(Order.menus))
            .where(Order.from_date == date,
                   not_(Order.is_cancelled),
                   Order.cafe_id == cafe.id)
        )

        orders_on_date = orders_on_date.scalars().all()

        for order in orders_on_date:
            for menu in order.menus:
                menus_quantity += menu.quantity

        for table in self.tables[cafe.id]:
            total_places += table.seats_count
        return (total_places - menus_quantity)

    async def update_payment_status(
        self, order_id: int, is_paid: bool
    ) -> bool:
        order = await self._session.execute(
            select(Order).where(Order.id == order_id, not_(Order.is_cancelled))
        )

        order: Order = order.scalars().first()
        if not order:
            return False

        order.is_paid = is_paid

        self._session.add(order)
        await self._session.commit()

        return True

    async def get_cancelled_status(self, order_id: int) -> bool:
        order = await self._session.execute(
            select(Order).where(Order.id == order_id))

        order: Order = order.scalars().first()
        if not order:
            return False

        if order.is_cancelled or order.is_paid:
            return True

        return False
    
    async def get_order_status(self, order_id: int) -> List[bool]:
        order = await self._session.execute(
            select(Order).where(Order.id == order_id))

        order: Order = order.scalars().first()
        if not order:
            return [False, False]

        return [order.is_paid, order.is_cancelled]

    async def update_cancelled_status(
        self, order_id: int, is_cancelled: bool

    ) -> bool:
        order = await self._session.execute(
            select(Order).where(Order.id == order_id)
        )

        order: Order = order.scalars().first()
        if not order:
            return False

        order.is_cancelled = is_cancelled

        self._session.add(order)
        await self._session.commit()
        await self._session.refresh(order)

        return True

    async def save_timer_job(
            self,
            chat_id: int,
            order_id:int,
            name: str,
            data: dict,
            scheduled_time: datetime
    ):
        timer = Job(
            chat_id=chat_id,
            name=name,
            order_id=order_id,
            data=data,
            scheduled_time=scheduled_time
        )
        self._session.add(timer)
        await self._session.commit()
        await self._session.refresh(timer)

    async def get_all_timer_jobs(self):
        timers = await self._session.execute(select(Job))
        timer_all = timers.scalars().all()
        return timer_all

    async def get_user_bookings(self, user: User) -> List[Order]:
        """Получение всех бронирований пользователя."""
        current_date = datetime.now().date()

        bookings = await self._session.execute(
            select(Order).filter(
                Order.buyer_id == user.id,
                Order.is_paid == True,
                Order.is_cancelled == False,
                Order.from_date >= current_date,
            )
        )

        return bookings.scalars().all()

    async def get_cafe_by_id(self, cafe_id: int):
        """Получение кафе по идентификатору."""
        return self.cafes.get(cafe_id, None)

    async def get_menu_by_id(self, order_id: int) -> List[Menu]:
        """Получение меню по номеру заказа."""
        menu = await self._session.execute(
            select(Menu).filter(
                Menu.order_id == order_id,
            )
        )
        return menu.scalars().all()

    async def get_order_by_id(self, order_id: int):
        """Получение заказа по идентификатору."""
        order = await self._session.execute(
            select(Order).filter(
                Order.id == order_id,
            )
        )
        return order.scalars().first()

    async def get_sets_by_id(self, set_id: int):
        """Получение сетов по идентификатору меню."""
        return self.sets.get(set_id, None)

    async def get_last_not_paid_user_booking(self, user: User) -> List[Order]:
        """Получение последнего непроплаченного заказа пользователя."""

        order = await self._session.execute(
            select(Order).filter(
                Order.buyer_id == user.id,
                Order.is_paid == False,
                Order.is_cancelled == False,
            ).order_by(desc(Order.date))
        )

        return order.scalars().first()

    # Methods for payments work
    async def save_to_control_payments(self, payment: Payment):
        self._session.add(payment)
        await self._session.commit()
        await self._session.refresh(payment)

    async def get_control_payments(self) -> List[Payment]:
        payments = await self._session.execute(
            select(Payment)
        )

        return payments.scalars().all()
    
    async def remove_from_control_payments(self, payment: Payment):
        await self._session.delete(payment)
        await self._session.commit()
