import datetime
from urllib.parse import quote

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect

from .models import Order, Menu, User, Set, Cafe


@csrf_protect
def booking_create(request):
    start_date = datetime.datetime(2024, 3, 10).strftime("%Y-%m-%d")
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
        description = request.POST.get('description')
        sets = Set.objects.all()
        sets_data = []
        guests = 0
        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                set_id = int(key.split('quantity_')[1])
                request_set_quantities = request.POST.get(
                    f'quantity_{set_id}',
                    ''
                )
                if (
                    request_set_quantities.isdecimal()
                    and int(request_set_quantities) > 0
                ):
                    set_quantities = (request.POST.get(f'quantity_{set_id}'))
                    sets_data.append((set_id, set_quantities))
                    guests += int(set_quantities)
        buyer = User.objects.get_or_create(
            name=guest_name,
            phone_number=guest_phone
        )[0]
        order = Order.objects.create(
            buyer=buyer,
            from_date=from_date,
            to_date=to_date,
            guests=guests,
            cafe=cafe,
            description=description
        )
        for set_id, set_quantities in sets_data:
            Menu.objects.create(
                order=order,
                set=Set.objects.get(id=set_id),
                quantity=set_quantities
            )
        url = reverse(
            'azucafe:cafe_detail',
            kwargs={
                'cafe_id': cafe.id
            }
        )
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
            'menus': menus
        })

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
                'selected_cafe_id': cafe.id
            })
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        order.cafe = Cafe.objects.get(id=request.POST.get('selected_cafe'))
        order.from_date = order.to_date = request.POST.get('date')
        guest_name = request.POST.get('guest_name')
        guest_phone = request.POST.get('guest_phone')
        buyer = User.objects.get_or_create(
            name=guest_name,
            phone_number=guest_phone
        )[0]
        order.description = request.POST.get('description')
        order.buyer = buyer
        order_menus = order.menu_set.all()
        order_menus.delete()
        sets_data = []
        guests = 0
        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                set_id = int(key.split('quantity_')[1])
                request_set_quantities = request.POST.get(
                    f'quantity_{set_id}',
                    ''
                )
                if (
                    request_set_quantities.isdecimal()
                    and int(request_set_quantities) > 0
                ):
                    set_quantities = (request.POST.get(f'quantity_{set_id}'))
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
                quantity=set_quantities
            )
        job = order.job
        job.scheduled_time = order.from_date
        job.save()
        order.save()
        url = reverse(
            'azucafe:cafe_detail',
            kwargs={
                'cafe_id': order.cafe.id
            }
        )
        url_date = quote(order.from_date)

        return redirect(f'{url}?date={url_date}')