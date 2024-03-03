from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from core.db import Base


class Cafe(Base):
    name = Column(String, nullable=False)
    description = Column(Text)
    phone = Column(String)
    address = Column(String)
    map_link = Column(String)
    picture = Column(String)
    tables = relationship('Table', cascade='delete')
    orders = relationship('Order', cascade='delete')


class Table(Base):
    cafe_id = Column(Integer, ForeignKey('azucafe_cafe.id'))
    table_number = Column(Integer, nullable=False)
    seats_count = Column(Integer, default=1)
    available = Column(Boolean, default=True)
    description = Column(Text)


class Category(Base):
    name = Column(String, nullable=False)
    description = Column(Text)
    sets = relationship('Set', cascade='delete')


class Set(Base):
    name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey('azucafe_category.id'))
    picture = Column(String)
    cost = Column(Integer, default=0)
    description = Column(Text)
    menus = relationship('Menu', cascade='delete')


class User(Base):
    telegram_id = Column(String, default='1')
    name = Column(String)
    phone_number = Column(String)
    admin = Column(Boolean, default=False)
    superuser = Column(Boolean, default=False)
    orders = relationship('Order', cascade='delete')


class Order(Base):
    date = Column(DateTime, nullable=False)
    buyer_id = Column(Integer, ForeignKey('azucafe_user.id'))
    guests = Column(Integer)
    from_date = Column(DateTime)
    to_date = Column(DateTime)
    is_cancelled = Column(Boolean, default=False)
    is_paid = Column(Boolean, default=False)
    description = Column(Text)
    menus = relationship('Menu', cascade='delete')
    cafe_id = Column(Integer, ForeignKey('azucafe_cafe.id'))
    admin_booking = Column(Boolean, default=False)


class Booking(Base):
    order_id = Column(Integer, ForeignKey('azucafe_order.id'))
    table_id = Column(Integer, ForeignKey('azucafe_table.id'))


class Menu(Base):
    order_id = Column(Integer, ForeignKey('azucafe_order.id'))
    set_id = Column(Integer, ForeignKey('azucafe_set.id'))
    quantity = Column(Integer, default=1)


class Job(Base):
    id = Column(Integer, primary_key=True)
    chat_id = Column(BigInteger, nullable=False)
    order_id = Column(Integer, ForeignKey('azucafe_order.id'))
    name = Column(String, nullable=False)
    data = Column(JSON)
    scheduled_time = Column(DateTime, nullable=False)
    remind_show = Column(Boolean, default=False)


class Payment(Base):
    chat_id = Column(BigInteger, nullable=False)
    order_id = Column(Integer, ForeignKey('azucafe_order.id'))
    payment_link = Column(String, nullable=False)
    payment_start = Column(DateTime, nullable=False)
    payment_message_id = Column(Integer, nullable=False)
