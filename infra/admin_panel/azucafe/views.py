from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .constants import RAMADAN_END, RAMADAN_START
from .models import Cafe, Menu, Order, Table


def get_selected_date_and_orders(request, cafe_id):
    """Получение даты и заказов."""
    selected_date_str = request.GET.get('date')
    today = date.today()
    if selected_date_str:
        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d").date()
    else:
        if today <= RAMADAN_START:
            selected_date = RAMADAN_START
        elif today <= RAMADAN_END:
            selected_date = today
        else:
            selected_date = RAMADAN_END
    cafe = Cafe.objects.get(id=cafe_id)
    orders_for_date = Order.objects.filter(
        cafe=cafe,
        from_date__lte=selected_date,
        to_date__gte=selected_date,
        is_cancelled=False,
    )
    return selected_date, orders_for_date


def cancel_reservation(request, reservation_id):
    """Отмена бронирования."""
    reservation = get_object_or_404(Order, id=reservation_id)
    reservation.is_cancelled = True
    if hasattr(reservation, 'job'):
        reservation.job.delete()
    reservation.save()
    return redirect('azucafe:cafe_detail', cafe_id=reservation.cafe.id)


@login_required
def cafe_list(request):
    """Вывод списка кафе."""
    cafes = Cafe.objects.all()
    context = {'cafes': cafes}
    return render(request, 'azucafe/profile.html', context)


@login_required
def cafe_detail(request, cafe_id):
    """Вывод списка кафе и даты в деталях."""
    default_date = get_selected_date_and_orders(request, cafe_id)[0]
    cafes = Cafe.objects.all()
    context = {
        'cafes': cafes,
        'cafe_id': cafe_id,
        'default_date': default_date.strftime("%Y-%m-%d"),
    }
    return render(request, 'azucafe/cafe_detail.html', context)


def cafe_seats(request, cafe_id):
    """Вывод свободных мест и бронирований."""
    selected_date, orders_for_date = get_selected_date_and_orders(
        request, cafe_id
    )
    cafe = Cafe.objects.get(id=cafe_id)
    tables = Table.objects.filter(cafe=cafe, available=True)
    total_seats = tables.aggregate(total_seats=Sum('seats_count'))[
        'total_seats'
    ]
    booked_seats = (
        orders_for_date.aggregate(booked_seats=Sum('guests'))['booked_seats']
        or 0
    )
    available_seats = max(total_seats - booked_seats, 0)
    ordered_sets = Menu.objects.filter(
        order__cafe=cafe,
        order__from_date__lte=selected_date,
        order__to_date__gte=selected_date,
    ).exclude(order__is_cancelled=True)
    sets_data = ordered_sets.values('set__name').annotate(
        quantity=Sum('quantity')
    )
    reservations = Order.objects.filter(
        cafe=cafe,
        from_date__lte=selected_date,
        to_date__gte=selected_date,
        is_cancelled=False,
    ).values(
        'id',
        'buyer__name',
        'buyer__phone_number',
        'guests',
        'is_paid',
        'admin_booking',
    )
    data = {
        'total_seats': total_seats,
        'available_seats': available_seats,
        'ordered_sets': list(sets_data),
        'reservations': [],
    }
    for reservation in reservations:
        reservation_id = reservation['id']
        reservation['sets'] = list(
            ordered_sets.filter(order__id=reservation_id).values(
                'set__name', 'quantity'
            )
        )
        data['reservations'].append(reservation)
    return JsonResponse(data)
