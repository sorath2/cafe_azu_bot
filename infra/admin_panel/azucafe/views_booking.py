import datetime
import re
from urllib.parse import quote

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect

from .models import Cafe, Menu, Order, Set, User

pattern = re.compile(r'^\+79\d{9}$')


@csrf_protect
def booking_create(request):
    start_date = datetime.datetime(2024, 3, 11).strftime("%Y-%m-%d")
    end_date = datetime.datetime(2024, 4, 9).strftime("%Y-%m-%d")
    current_date = max(datetime.date.today().strftime("%Y-%m-%d"), start_date)
    date = current_date if current_date >= start_date else start_date
    sets = Set.objects.all()
    menus = {}
    for set in sets:
        menus[set.id] = {'name': set.name, 'quantity': ''}
    if request.method == 'POST':
        cafe = Cafe.objects.get(id=request.POST.get('selected_cafe'))
        from_date = to_date = request.POST.get('date')
        guest_name = request.POST.get('guest_name')
        guest_phone = request.POST.get('guest_phone')
        sets = Set.objects.all()
        sets_data = []
        guests = 0
        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                set_id = int(key.split('quantity_')[1])
                request_set_quantities = request.POST.get(
                    f'quantity_{set_id}', ''
                )
                if (
                    request_set_quantities.isdecimal()
                    and int(request_set_quantities) > 0
                ):
                    set_quantities = request.POST.get(f'quantity_{set_id}')
                    sets_data.append((set_id, set_quantities))
                    guests += int(set_quantities)
        if not guest_name or not guest_phone or not from_date or not sets_data:
            return render(
                request,
                'azucafe/booking.html',
                {
                    'cafes': Cafe.objects.all(),
                    'current_date': current_date,
                    'start_date': start_date,
                    'end_date': end_date,
                    'menus': menus,
                    'date': from_date if from_date is not None else None,
                    'date_indicator': True if not from_date else False,
                    'date_message': 'Вы не ввели дату бронирования',
                    'guest_name': guest_name
                    if guest_name is not None
                    else None,
                    'guest_name_indicator': True if not guest_name else False,
                    'guest_name_message': 'Вы не ввели имя гостя',
                    'guest_phone': guest_phone
                    if guest_phone is not None
                    else None,
                    'guest_phone_indicator': True
                    if not guest_phone
                    else False,
                    'guest_phone_message': 'Вы не ввели номер телефона',
                    'sets_indicator': True,
                    'sets_message': 'Добавьте хотя бы один сет',
                },
            )
        if not pattern.match(guest_phone):
            return render(
                request,
                'azucafe/booking.html',
                {
                    'cafes': Cafe.objects.all(),
                    'current_date': current_date,
                    'start_date': start_date,
                    'end_date': end_date,
                    'menus': menus,
                    'date': from_date if from_date is not None else None,
                    'date_indicator': True if not from_date else False,
                    'date_message': 'Вы не ввели дату бронирования',
                    'guest_name': guest_name
                    if guest_name is not None
                    else None,
                    'guest_name_indicator': True if not guest_name else False,
                    'guest_name_message': 'Вы не ввели имя гостя',
                    'guest_phone_indicator': True,
                    'guest_phone_message': (
                        'Введите телефон в формате +79005552233'
                    ),
                },
            )
        description = request.POST.get('description')
        buyer = User.objects.get_or_create(
            name=guest_name, phone_number=guest_phone
        )[0]
        order = Order.objects.create(
            buyer=buyer,
            from_date=from_date,
            to_date=to_date,
            guests=guests,
            cafe=cafe,
            description=description,
            admin_booking=True,
        )
        for set_id, set_quantities in sets_data:
            Menu.objects.create(
                order=order,
                set=Set.objects.get(id=set_id),
                quantity=set_quantities,
            )
        url = reverse('azucafe:cafe_detail', kwargs={'cafe_id': cafe.id})
        url_date = quote(from_date)

        return redirect(f'{url}?date={url_date}')

    return render(
        request,
        'azucafe/booking.html',
        {
            'cafes': Cafe.objects.all(),
            'date': date,
            'current_date': current_date,
            'start_date': start_date,
            'end_date': end_date,
            'menus': menus,
        },
    )


@csrf_protect
def booking_update(request, order_id):
    start_date = datetime.datetime(2024, 3, 10).strftime("%Y-%m-%d")
    end_date = datetime.datetime(2024, 4, 9).strftime("%Y-%m-%d")
    if request.method == 'GET':
        order = get_object_or_404(Order, id=order_id)
        cafe = order.cafe
        date = order.from_date.strftime("%Y-%m-%d")
        name = order.buyer.name
        phone = order.buyer.phone_number
        description = order.description
        order_menus = order.menu_set.all()
        order_sets_quantity = (
            (order_menu.set.id, order_menu.quantity)
            for order_menu in order_menus
        )
        cafes = Cafe.objects.all()
        sets = Set.objects.all()
        menus = {}
        for set in sets:
            menus[set.id] = {'name': set.name, 'quantity': ''}
        for set_id, quantity in order_sets_quantity:
            if set_id in menus:
                menus[set_id]['quantity'] = quantity
        return render(
            request,
            'azucafe/booking.html',
            {
                'cafes': cafes,
                'cafe_id': cafe.id,
                'date': date,
                'guest_name': name,
                'guest_phone': phone,
                'menus': menus,
                'description': description,
                'start_date': start_date,
                'end_date': end_date,
                'is_edit': True,
                'order_id': order_id,
                'selected_cafe_id': cafe.id,
            },
        )
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        order.cafe = Cafe.objects.get(id=request.POST.get('selected_cafe'))
        cafe = Cafe.objects.get(id=request.POST.get('selected_cafe'))
        from_date = request.POST.get('date')
        order.from_date = order.to_date = request.POST.get('date')
        guest_name = request.POST.get('guest_name')
        guest_phone = request.POST.get('guest_phone')
        order_menus = order.menu_set.all()
        order_menus.delete()
        sets_data = []
        guests = 0
        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                set_id = int(key.split('quantity_')[1])
                request_set_quantities = request.POST.get(
                    f'quantity_{set_id}', ''
                )
                if (
                    request_set_quantities.isdecimal()
                    and int(request_set_quantities) > 0
                ):
                    set_quantities = request.POST.get(f'quantity_{set_id}')
                    sets_data.append((set_id, set_quantities))
                    guests += int(set_quantities)
                else:
                    for menu_object in order_menus:
                        if menu_object.set.id == set_id:
                            menu_object.delete()
        order.guests = guests
        for set_id, set_quantities in sets_data:
            Menu.objects.create(
                order=order,
                set=Set.objects.get(id=set_id),
                quantity=set_quantities,
            )
        order_menus = order.menu_set.all()
        order_sets_quantity = (
            (order_menu.set.id, order_menu.quantity)
            for order_menu in order_menus
        )
        sets = Set.objects.all()
        menus = {}
        for set in sets:
            menus[set.id] = {'name': set.name, 'quantity': ''}
        for set_id, quantity in order_sets_quantity:
            if set_id in menus:
                menus[set_id]['quantity'] = quantity
        if not guest_name or not guest_phone or not from_date or not sets_data:
            return render(
                request,
                'azucafe/booking.html',
                {
                    'cafes': Cafe.objects.all(),
                    'start_date': start_date,
                    'end_date': end_date,
                    'menus': menus,
                    'date': from_date if from_date is not None else None,
                    'date_indicator': True if not from_date else False,
                    'date_message': 'Вы не ввели дату бронирования',
                    'guest_name': guest_name
                    if guest_name is not None
                    else None,
                    'guest_name_indicator': True if not guest_name else False,
                    'guest_name_message': 'Вы не ввели имя гостя',
                    'guest_phone': guest_phone
                    if guest_phone is not None
                    else None,
                    'guest_phone_indicator': True
                    if not guest_phone
                    else False,
                    'guest_phone_message': 'Вы не ввели номер телефона',
                    'is_edit': True,
                    'order_id': order_id,
                    'selected_cafe_id': cafe.id,
                    'cafe_id': cafe.id,
                    'sets_indicator': True,
                    'sets_message': 'Добавьте хотя бы один сет',
                },
            )
        buyer = User.objects.get_or_create(
            name=guest_name, phone_number=guest_phone
        )[0]
        order.description = request.POST.get('description')
        order.buyer = buyer
        order.admin_booking = True
        if hasattr(order, 'job'):
            order.job
            order.job.scheduled_time = order.from_date
            order.job.save()
        order.save()
        url = reverse('azucafe:cafe_detail', kwargs={'cafe_id': order.cafe.id})
        url_date = quote(order.from_date)

        return redirect(f'{url}?date={url_date}')
