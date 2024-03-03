import decimal
import os
from http import HTTPStatus

from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import HttpResponse, render

from . import robokassa
from .models import Order


def payment_result(request: WSGIRequest):
    data = {}
    if request.method == 'GET':
        data['cost'] = decimal.Decimal(request.GET.get('OutSum', '-1'))
        data['order_id'] = int(request.GET.get('InvId', '-1'))
        data['signature_value'] = request.GET.get('SignatureValue', '')
    else:
        return HttpResponse(status=HTTPStatus.METHOD_NOT_ALLOWED)

    if not robokassa.check_signature_result(
        order_number=data['order_id'],
        received_sum=data['cost'],
        received_signature=data['signature_value'],
        password=os.getenv('MERCHANT_PASSWORD2', ' '),
    ):
        return HttpResponse(status=HTTPStatus.BAD_REQUEST)

    try:
        order = Order.objects.get(id=data['order_id'])
    except:
        return HttpResponse(status=HTTPStatus.BAD_REQUEST)

    order.is_paid = True
    order.save()

    return HttpResponse(status=HTTPStatus.NO_CONTENT)


def payment_success(request: WSGIRequest):
    data = {}
    if request.method == 'GET':
        data['cost'] = decimal.Decimal(request.GET.get('OutSum', '-1'))
        data['order_id'] = int(request.GET.get('InvId', '-1'))
        data['signature_value'] = request.GET.get('SignatureValue', '')
    else:
        return HttpResponse(status=HTTPStatus.METHOD_NOT_ALLOWED)

    if not robokassa.check_signature_result(
        order_number=data['order_id'],
        received_sum=data['cost'],
        received_signature=data['signature_value'],
        password=os.getenv('MERCHANT_PASSWORD1', ' '),
    ):
        return HttpResponse(status=HTTPStatus.BAD_REQUEST)

    try:
        order = Order.objects.get(id=data['order_id'])
    except:
        return HttpResponse(status=HTTPStatus.BAD_REQUEST)

    return render(
        request,
        'payments/payment_success.html',
        context={'order': order, 'bot_address': os.getenv('BOT_ADDRESS', '#')},
    )


def payment_fail(request: WSGIRequest):
    data = {}
    if request.method == 'GET':
        data['cost'] = decimal.Decimal(request.GET.get('OutSum', '-1'))
        data['order_id'] = int(request.GET.get('InvId', '-1'))
        data['signature_value'] = request.GET.get('SignatureValue', '')
    else:
        return HttpResponse(status=HTTPStatus.METHOD_NOT_ALLOWED)

    try:
        order = Order.objects.get(id=data['order_id'])
    except:
        order = None

    return render(
        request,
        'payments/payment_fail.html',
        context={'order': order, 'bot_address': os.getenv('BOT_ADDRESS', '#')},
    )
