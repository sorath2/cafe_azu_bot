from django.core.validators import MinValueValidator
from django.db import models


# Create your models here.
class Cafe(models.Model):
    name = models.CharField(
        max_length=50, unique=True, null=False, verbose_name='Название кафе'
    )
    description = models.TextField(verbose_name='Описание кафе')
    phone = models.CharField(
        max_length=20, null=False, blank=False, verbose_name='Телефон'
    )
    address = models.CharField(
        max_length=200, null=False, verbose_name='Адрес кафе'
    )
    map_link = models.URLField(verbose_name='Ссылка на карту')
    picture = models.ImageField(
        upload_to='cafe/', blank=True, verbose_name='Картинка'
    )

    class Meta:
        verbose_name_plural = 'Кафе'
        verbose_name = 'Кафе'

    def __str__(self):
        return f'Кафе {self.name}'


class Table(models.Model):
    cafe = models.ForeignKey(
        Cafe,
        on_delete=models.CASCADE,
        to_field='id',
        verbose_name='Кафе',
    )
    table_number = models.PositiveIntegerField(
        verbose_name='Номер стола',
        null=False,
        blank=False,
        default=1,
    )
    seats_count = models.PositiveIntegerField(
        verbose_name='Посадочные места',
        null=False,
        blank=False,
        default=1,
        validators=[
            MinValueValidator(
                1,
                'Время приготовления должно быть больше или равно 1',
            )
        ],
    )
    available = models.BooleanField(
        verbose_name='Доступность',
        help_text='Доступность стола для бронирования',
        default=True,
        null=False,
        blank=False,
    )
    description = models.TextField(
        null=False, blank=True, verbose_name='Описание стола'
    )

    class Meta:
        verbose_name_plural = 'Столы'
        verbose_name = 'Стол'
        constraints = (
            models.UniqueConstraint(
                fields=('cafe', 'table_number'),
                name='table_cafe_table_number_unique',
            ),
        )

    def __str__(self):
        return (
            f'{self.cafe} Стол № {self.table_number} '
            f'({self.seats_count} '
            f'мест)'
        )


class Category(models.Model):
    name = models.CharField(
        max_length=50,
        null=False,
        unique=True,
        verbose_name='Название категории',
    )
    description = models.TextField(
        null=False, blank=True, verbose_name='Описание категории'
    )

    class Meta:
        verbose_name_plural = 'Категории сетов'
        verbose_name = 'Категория сетов'

    def __str__(self):
        return f'Категория {self.name}'


class Set(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        to_field='id',
        verbose_name='Категория сета',
    )
    name = models.CharField(
        max_length=50,
        null=False,
        unique=True,
        verbose_name='Название сета',
    )
    description = models.TextField(
        null=False, blank=True, verbose_name='Описание сета'
    )
    picture = models.ImageField(
        upload_to='sets/', blank=True, verbose_name='Картинка'
    )
    cost = models.PositiveIntegerField(
        default=1,
        null=False,
        blank=False,
        verbose_name='Стоимость сета',
        validators=[
            MinValueValidator(
                1,
                'Время приготовления должно быть больше или равно 1',
            )
        ],
    )

    class Meta:
        verbose_name_plural = 'Сеты'
        verbose_name = 'Сет'

    def __str__(self):
        return f'Сет {self.name} {self.cost} руб.'


class User(models.Model):
    telegram_id = models.CharField(
        default='1',
        max_length=200,
        null=False,
        verbose_name='Телеграмм ID покупателя',
    )
    name = models.CharField(
        null=False,
        blank=True,
        max_length=1000,
        verbose_name='Имя покупателя',
    )
    phone_number = models.CharField(
        null=False, blank=False, max_length=12, verbose_name='Телефон'
    )
    admin = models.BooleanField(
        default=False,
        verbose_name='Администратор?',
    )
    superuser = models.BooleanField(
        default=False,
        verbose_name='Супер пользователь?',
    )

    class Meta:
        verbose_name_plural = 'Покупатели'
        verbose_name = 'Покупатель'

    def __str__(self):
        return f'{self.telegram_id} ({self.name})'


class Order(models.Model):
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='buyer_id',
        verbose_name='Покупатель',
    )
    date = models.DateTimeField(
        auto_now_add=True,
        null=False,
        blank=False,
        verbose_name='Дата создания бронирования',
    )
    from_date = models.DateTimeField(
        null=False, blank=False, verbose_name='Дата начала бронирования'
    )
    to_date = models.DateTimeField(
        null=False, blank=False, verbose_name='Дата окончания бронирования'
    )
    guests = models.PositiveIntegerField(
        default=1,
        verbose_name='Количество гостей',
        validators=[
            MinValueValidator(
                1,
                'Время приготовления должно быть больше или равно 1',
            )
        ],
    )
    cafe = models.ForeignKey(
        Cafe,
        on_delete=models.CASCADE,
        verbose_name='Кафе',
    )
    is_paid = models.BooleanField(
        default=False,
        verbose_name='Оплачено?',
    )
    is_cancelled = models.BooleanField(
        default=False,
        verbose_name='Отменено?',
    )
    description = models.TextField(
        null=False, blank=True, verbose_name='Комментарии'
    )
    admin_booking = models.BooleanField(
        default=False,
    )

    class Meta:
        verbose_name_plural = 'Бронирования'
        verbose_name = 'Бронирование'

    def __str__(self):
        return f'{self.from_date} на {self.guests} гостей'


class Booking(models.Model):
    table = models.ForeignKey(
        Table, on_delete=models.CASCADE, verbose_name='Стол'
    )
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, verbose_name='Заказ (бронь)'
    )

    class Meta:
        verbose_name_plural = 'Бронирование столов'
        verbose_name = 'Бронирование стола'

    def __str__(self):
        return (
            f'Заказ (бронь) № {self.order.id} стол '
            f'№ {self.table.table_number}'
        )


class Menu(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, verbose_name='Заказ (бронь)'
    )
    set = models.ForeignKey(Set, on_delete=models.CASCADE, verbose_name='Сет')
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name='Количество',
        validators=[
            MinValueValidator(
                1,
                'Время приготовления должно быть больше или равно 1',
            )
        ],
    )

    class Meta:
        verbose_name_plural = 'Меню'
        verbose_name = 'Меню'

    def __str__(self):
        return (
            f'Заказ (бронь) № {self.order.id} сет '
            f'№ {self.set} {self.quantity} шт.'
        )


class Job(models.Model):
    name = models.CharField(
        max_length=50,
        blank=False,
        null=False,
        unique=True,
        verbose_name='Название',
    )
    chat_id = models.BigIntegerField(
        default=1,
    )
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name='job'
    )
    data = models.TextField()
    scheduled_time = models.DateTimeField(
        null=False, blank=False, verbose_name='Дата начала бронирования'
    )
    remind_show = models.BooleanField(
        default=False,
    )


class Payment(models.Model):
    chat_id = models.BigIntegerField(
        default=1,
    )
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name='payment'
    )
    payment_link = models.TextField()
    payment_start = models.DateTimeField(
        null=False, blank=False, verbose_name='Дата начала оплаты'
    )
    payment_message_id = models.PositiveIntegerField(
        default=1,
        verbose_name='ID сообщения об оплате',
    )
