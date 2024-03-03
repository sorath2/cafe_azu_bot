from collections import defaultdict
from datetime import datetime
from typing import List

from sqlalchemy import desc, not_
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from core.config import settings
from core.db import DatabaseSessionManager
from models import Cafe, Category, Job, Menu, Order, Payment, User, Table, Set


class Worker:
    def __init__(self):
        self._db_manager = DatabaseSessionManager()
        self._db_manager.init(settings.database_url)
        self._cafes = defaultdict(int)
        self._tables = defaultdict(int)
        self._sets = defaultdict(int)

    async def close(self):
        await self._db_manager.close()

    @property
    def cafes(self):
        return self._cafes

    @property
    def tables(self):
        return self._tables

    @property
    def sets(self):
        return self._sets

    async def load_data(self):
        self._cafes.clear()
        self._sets.clear()
        self._tables.clear()
        
        async with self._db_manager.session() as session:
            cafes_data = await session.execute(
                select(Cafe)
            )

            cafes_data = cafes_data.scalars().all()
            cafes_data.sort(key=lambda item: item.id)

            for cafe in cafes_data:
                self._cafes[cafe.id] = cafe
                tables_data = await session.execute(
                    select(Table).where(Table.cafe_id == cafe.id)
                )
                self._tables[cafe.id] = tables_data.scalars().all()

            sets_data = await session.execute(
                select(Set)
            )
            sets_data = sets_data.scalars().all()
            sets_data.sort(key=lambda item: item.id)
            
            for set_data in sets_data:
                self._sets[set_data.id] = set_data

    async def get_user(self, telegram_id: str) -> User:
        user = None
        async with self._db_manager.session() as session:
            user = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = user.scalars().first()

        return user

    async def get_user_by_id(self, user_id: str) -> User:
        user = None
        async with self._db_manager.session() as session:
            user = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = user.scalars().first()

        return user

    async def add_user(
            self,
            telegram_id: str,
            name: str,
            phone_number: str,
            is_admin: bool = False,
            is_superuser: bool = False,
    ) -> User:
        new_user = None
        async with self._db_manager.session() as session:
            new_user = User(
                telegram_id=telegram_id,
                name=name,
                phone_number=phone_number,
                admin=is_admin,
                superuser=is_superuser,
            )

            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

        return new_user

    async def save_order(self, current_order: 'CurrentOrder'):
        async with self._db_manager.session() as session:
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
                admin_booking=False,
            )
            session.add(order)
            await session.commit()
            await session.refresh(order)

            menus = [
                Menu(
                    order_id=order.id,
                    set_id=set_id,
                    quantity=menu_item[1],
                )
                for set_id, menu_item in current_order.menu.items()
            ]

            session.add_all(menus)
            await session.commit()

            current_order.order_id = order.id

    async def get_free_places(self, cafe: Cafe, date: datetime):
        total_places = 0
        menus_quantity = 0

        async with self._db_manager.session() as session:
            orders_on_date = await session.execute(
                select(Order)
                .options(selectinload(Order.menus))
                .where(
                    Order.from_date == date,
                    not_(Order.is_cancelled),
                    Order.cafe_id == cafe.id,
                )
            )

            orders_on_date = orders_on_date.scalars().all()

            for order in orders_on_date:
                for menu in order.menus:
                    menus_quantity += menu.quantity

            for table in self._tables[cafe.id]:
                total_places += table.seats_count

        return max(total_places - menus_quantity, 0)

    async def update_payment_status(
            self, order_id: int, is_paid: bool
    ) -> bool:
        async with self._db_manager.session() as session:
            order = await session.execute(
                select(Order).where(
                    Order.id == order_id,
                    not_(Order.is_cancelled)
                )
            )

            order: Order = order.scalars().first()
            if not order:
                return False

            order.is_paid = is_paid

            session.add(order)
            await session.commit()

        return True

    async def get_cancelled_status(self, order_id: int) -> bool:
        order = None
        async with self._db_manager.session() as session:
            order = await session.execute(
                select(Order).where(Order.id == order_id)
            )

            order: Order = order.scalars().first()
        if not order:
            return False

        if order.is_cancelled or order.is_paid:
            return True

        return False

    async def get_order_status(self, order_id: int) -> List[bool]:
        order = None
        async with self._db_manager.session() as session:
            order = await session.execute(
                select(Order).where(Order.id == order_id)
            )

            order: Order = order.scalars().first()

        if not order:
            return [False, False]

        return [order.is_paid, order.is_cancelled]

    async def update_cancelled_status(
            self, order_id: int, is_cancelled: bool
    ) -> bool:
        async with self._db_manager.session() as session:
            order = await session.execute(
                select(Order).where(Order.id == order_id)
            )

            order: Order = order.scalars().first()
            if not order:
                return False

            order.is_cancelled = is_cancelled

            session.add(order)
            await session.commit()
            await session.refresh(order)

        return True

    async def save_timer_job(
            self,
            chat_id: int,
            order_id: int,
            name: str,
            data: dict,
            scheduled_time: datetime,
            remind_show: bool = False,
    ):
        async with self._db_manager.session() as session:
            timer = Job(
                chat_id=chat_id,
                name=name,
                order_id=order_id,
                data=data,
                scheduled_time=scheduled_time,
                remind_show=remind_show,
            )
            session.add(timer)
            await session.commit()
            await session.refresh(timer)

    async def update_timer_job(self, timer: Job):
        async with self._db_manager.session() as session:
            session.add(timer)
            await session.commit()
            await session.refresh(timer)

    async def get_all_timer_jobs(self):
        timers = None
        async with self._db_manager.session() as session:
            timers = await session.execute(
                select(Job).where(Job.remind_show == False)
            )

        return timers.scalars().all() if timers else []

    async def get_timer_by_order_id(self, order_id: int):
        timer = None
        async with self._db_manager.session() as session:
            timer = await session.execute(
                select(Job).where(Job.order_id == order_id)
            )

        return timer.scalars().first() if timer else None

    async def get_user_bookings(self, user: User) -> List[Order]:
        """Получение всех бронирований пользователя."""
        current_date = datetime.now().date()
        bookings = None

        async with self._db_manager.session() as session:
            bookings = await session.execute(
                select(Order).filter(
                    Order.buyer_id == user.id,
                    Order.is_paid == True,
                    Order.is_cancelled == False,
                    Order.from_date >= current_date,
                )
            )

        return bookings.scalars().all() if bookings else []

    async def get_cafe_by_id(self, cafe_id: int):
        """Получение кафе по идентификатору."""
        return self.cafes.get(cafe_id, None)

    async def get_menu_by_id(self, order_id: int) -> List[Menu]:
        """Получение меню по номеру заказа."""
        menu = None
        async with self._db_manager.session() as session:
            menu = await session.execute(
                select(Menu).filter(
                    Menu.order_id == order_id,
                )
            )
        return menu.scalars().all() if menu else []

    async def get_order_by_id(self, order_id: int):
        """Получение заказа по идентификатору."""
        order = None
        async with self._db_manager.session() as session:
            order = await session.execute(
                select(Order).filter(
                    Order.id == order_id,
                )
            )
        return order.scalars().first() if order else None

    async def get_sets_by_id(self, set_id: int):
        """Получение сетов по идентификатору меню."""
        return self.sets.get(set_id, None)

    async def get_last_not_paid_user_booking(self, user: User) -> List[Order]:
        """Получение последнего непроплаченного заказа пользователя."""
        order = None
        async with self._db_manager.session() as session:
            order = await session.execute(
                select(Order)
                .filter(
                    Order.buyer_id == user.id,
                    Order.is_paid == False,
                    Order.is_cancelled == False,
                )
                .order_by(desc(Order.date))
            )

        return order.scalars().first() if order else None

    # Methods for payments work
    async def save_to_control_payments(self, payment: Payment):
        async with self._db_manager.session() as session:
            session.add(payment)
            await session.commit()
            await session.refresh(payment)

    async def get_control_payments(self) -> List[Payment]:
        payments = None
        async with self._db_manager.session() as session:
            payments = await session.execute(select(Payment))

        return payments.scalars().all() if payments else []

    async def remove_from_control_payments(self, payment: Payment):
        async with self._db_manager.session() as session:
            await session.delete(payment)
            await session.commit()


worker = Worker()
