from enum import Enum


class UserFlowState(Enum):
    """Определяет этап (состояние) юзер флоу."""

    START = 1
    SELECT_CAFE = 2
    BOOKING = 3
    BOOKING_DETAIL = 4
    BUILD_MENU = 5
    SELECT_DATA = 6
    GUEST_COUNT = 7
    PAYMENT_CHOOSE = 8
    PAYMENT_WAITING = 9
    PAYMENT_ERROR = 10
    PHONE_REQUEST = 11


class ButtonCallbackData(str, Enum):
    # Главное меню
    MAIN_MENU_SELECT_CAFE = 'cafe_select'
    MAIN_MENU_BOOKING = 'booking'
    MAIN_MENU_SELECT_SET = 'sets_select'
    MAIN_MENU_BOOKING_DETAIL = 'booking_detail'

    # Меню выбора кафе
    CAFE_BOOK = 'cafe_book'
    CAFE_DETAIL_PREFIX = 'cafe_detail_'
    CAFE_ADMIN_CONTACT = 'admin_contact'
    CAFE_CANCEL = 'cafe_cancel'

    # Меню выбора сетов
    SET_ORDER = 'set_order'
    SET_NEXT = 'set_next'
    SET_PREV = 'set_prev'
    SET_ADD_TO_CART = 'set_add_to_cart'
    SET_REMOVE_FROM_CART = 'set_remove_from_cart'
    SET_CLEAR_CART = 'set_clear_cart'
    SET_CANCEL = 'set_cancel'

    # Меню бронирования
    BOOKING_SELECT_CAFE = 'select_cafe'
    BOOKING_SELECT_DATE = 'select_date'
    BOOKING_SELECT_GUEST_COUNT = 'select_guest_count'
    BOOKING_SELECT_SETS = 'select_menu'
    BOOKING_CANCEL = 'booking_cancel'
    BOOKING_OK = 'booking_ok'
    BOOKING_PAYMENT_CANCEL = 'booking_payment_cancel'

    # Меню деталей брони
    BOOKING_DETAIL_PREV = 'booking_detail_next'
    BOOKING_DETAIL_NEXT = 'booking_detail_prev'
    BOOKING_DETAIL_ADMIN_CONTACT = 'admin_contact'
    BOOKING_DETAIL_BACK = 'booking_detail_back'

    # Меню ввода количества гостей
    GUEST_COUNT_CANCEL = 'guest_count_cancel'

    # Меню выбора даты
    DATE_SELECT_PREFIX = 'cbcal_'
    DATE_CANCEL = 'date_cancel'

    # Меню выбора способа оплаты
    PAYMENT_METHOD_PREFIX = 'payment_method_'
    PAYMENT_CANCEL = 'payment_cancel'
    PAYMENT_OK = 'payment_ok'

    # Меню блока ошибки при оплате
    PAYMENT_CHOOSE_OTHER_METHOD = 'payment_choose_other_method'
    PAYMENT_REPEAT = 'payment_repeat'
    PAYMENT_ADMIN_CONTACT = 'admin_contact'
    PAYMENT_CANCEL_BOOKING = 'booking_cancel'
