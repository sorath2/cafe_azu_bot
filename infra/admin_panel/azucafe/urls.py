from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .views import cafe_detail, cafe_list, cafe_seats, cancel_reservation
from .views_booking import booking_create, booking_update
from .views_payments import payment_fail, payment_result, payment_success

app_name = 'azucafe'

urlpatterns = [
    path(
        'azucafe/cancel_reservation/<int:reservation_id>/',
        cancel_reservation,
        name='cancel_reservation',
    ),
    path('azucafe/profile/', cafe_list, name='cafe_list'),
    path(
        'azucafe/cafe_detail/<int:cafe_id>/', cafe_detail, name='cafe_detail'
    ),
    path('azucafe/cafe_seats/<int:cafe_id>/', cafe_seats, name='cafe_seats'),
    path(
        '',
        LoginView.as_view(template_name='azucafe/index.html'),
        name='index',
    ),
    path(
        'azucafe/logout/',
        LogoutView.as_view(template_name='azucafe/logged_out.html'),
        name='logout',
    ),
    path(
        'azucafe/login/',
        LoginView.as_view(template_name='azucafe/index.html'),
        name='login',
    ),
    path('azucafe/booking/', booking_create, name='booking_create'),
    path(
        'azucafe/booking/<order_id>/edit/',
        booking_update,
        name='booking_update',
    ),
    path(
        'azucafe/payresult/',
        payment_result,
        name='payment_result',
    ),
    path(
        'azucafe/paysuccess/',
        payment_success,
        name='payment_success',
    ),
    path(
        'azucafe/payfail/',
        payment_fail,
        name='payment_fail',
    ),
]
