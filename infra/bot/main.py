import logging

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    PicklePersistence,
    PreCheckoutQueryHandler,
    filters,
)

from core.config import settings
from core.constants import ButtonCallbackData, UserFlowState
from modules import *

logger = None


def config_loggig():
    # Enable logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    # set higher logging level for httpx to avoid all GET and POST
    # requests being logged
    logging.getLogger("httpx").setLevel(logging.WARNING)

    global logger
    logger = logging.getLogger(__name__)


def main():
    config_loggig()
    # persistence = PicklePersistence(filepath="azucafebot")
    azucafe_bot = (
        Application.builder()
        .token(settings.bot_token)
        # .persistence(persistence)
        .build()
    )

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_bot)],
        states={
            UserFlowState.START: [
                CallbackQueryHandler(
                    booking_menu_show,
                    pattern=f'^{ButtonCallbackData.MAIN_MENU_BOOKING}$',
                ),
                CallbackQueryHandler(
                    booking_detail_show,
                    pattern=f'^{ButtonCallbackData.MAIN_MENU_BOOKING_DETAIL}$',
                ),
                CallbackQueryHandler(
                    payment_show_dialog,
                    pattern=f'^{ButtonCallbackData.BOOKING_OK}$',
                ),
            ],
            UserFlowState.PHONE_REQUEST: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, contact_phone_request
                ),
                MessageHandler(filters.CONTACT, contact_phone_request),
            ],
            UserFlowState.SELECT_CAFE: [
                CallbackQueryHandler(
                    cafe_select_booking,
                    pattern=f'^{ButtonCallbackData.CAFE_BOOK}$',
                ),
                CallbackQueryHandler(
                    cafe_select_cancel,
                    pattern=f'^{ButtonCallbackData.CAFE_CANCEL}$',
                ),
                CallbackQueryHandler(
                    cafe_select_change_cafe,
                    pattern=f'^{ButtonCallbackData.CAFE_DETAIL_PREFIX}',
                ),
            ],
            UserFlowState.BOOKING: [
                CallbackQueryHandler(
                    payment_show_dialog,
                    pattern=f'^{ButtonCallbackData.BOOKING_OK}$',
                ),
                CallbackQueryHandler(
                    booking_menu_cancel,
                    pattern=f'^{ButtonCallbackData.BOOKING_CANCEL}$',
                ),
                CallbackQueryHandler(
                    cafe_select_start,
                    pattern=f'^{ButtonCallbackData.BOOKING_SELECT_CAFE}$',
                ),
                CallbackQueryHandler(
                    date_select_show,
                    pattern=f'^{ButtonCallbackData.BOOKING_SELECT_DATE}$',
                ),
                CallbackQueryHandler(
                    build_menu_start,
                    pattern=f'^{ButtonCallbackData.BOOKING_SELECT_SETS}$',
                ),
                CallbackQueryHandler(
                    payment_cancel,
                    pattern=f'^{ButtonCallbackData.BOOKING_PAYMENT_CANCEL}$',
                ),
            ],
            UserFlowState.SELECT_DATA: [
                # CallbackQueryHandler(
                #     test_func, pattern=f'^{ButtonCallbackData.DATE_CANCEL}$'
                # ),
                CallbackQueryHandler(
                    date_select_button,
                    pattern=f'^{ButtonCallbackData.DATE_SELECT_PREFIX}',
                ),
            ],
            UserFlowState.BUILD_MENU: [
                CallbackQueryHandler(
                    menu_switching_sets,
                    pattern=f'^{ButtonCallbackData.SET_NEXT}$',
                ),
                CallbackQueryHandler(
                    menu_switching_sets,
                    pattern=f'^{ButtonCallbackData.SET_PREV}$',
                ),
                CallbackQueryHandler(
                    menu_booking, pattern=f'^{ButtonCallbackData.SET_ORDER}$'
                ),
                CallbackQueryHandler(
                    menu_cancel, pattern=f'^{ButtonCallbackData.SET_CANCEL}$'
                ),
                CallbackQueryHandler(
                    menu_clear_basket,
                    pattern=f'^{ButtonCallbackData.SET_CLEAR_CART}$',
                ),
                CallbackQueryHandler(
                    menu_add_to_basket,
                    pattern=f'^{ButtonCallbackData.SET_ADD_TO_CART}$',
                ),
                CallbackQueryHandler(
                    menu_remove_from_basket,
                    pattern=f'^{ButtonCallbackData.SET_REMOVE_FROM_CART}$',
                ),
            ],
            UserFlowState.PAYMENT_CHOOSE: [
                CallbackQueryHandler(
                    payment_cancel,
                    pattern=f'^{ButtonCallbackData.PAYMENT_CANCEL}$',
                ),
                # MessageHandler(filters.SUCCESSFUL_PAYMENT, payment_successful),
                CallbackQueryHandler(
                    payment_successful,
                    pattern=f'^{ButtonCallbackData.PAYMENT_OK}$',
                ),
            ],
            UserFlowState.BOOKING_DETAIL: [
                CallbackQueryHandler(
                    booking_detail_back,
                    pattern=f'^{ButtonCallbackData.BOOKING_DETAIL_BACK}$',
                ),
                CallbackQueryHandler(
                    bookings_switching,
                    pattern=f'^{ButtonCallbackData.BOOKING_DETAIL_NEXT}$',
                ),
                CallbackQueryHandler(
                    bookings_switching,
                    pattern=f'^{ButtonCallbackData.BOOKING_DETAIL_PREV}$',
                ),
            ],
        },
        fallbacks=[
            CommandHandler("help", help_message),
            CommandHandler("start", start_bot),
            CommandHandler("restarttimers", timers_for_start_bot),
            MessageHandler(
                filters.ALL & (~filters.COMMAND | filters.SUCCESSFUL_PAYMENT),
                spam_message,
            ),
            CallbackQueryHandler(unknow_query_handler),
        ],
        name="azubot_conversation",
        # persistent=True,
    )

    azucafe_bot.add_handler(conv_handler)
    azucafe_bot.add_handler(
        CommandHandler("restarttimers", timers_for_start_bot)
    )
    azucafe_bot.add_handler(CommandHandler("help", help_message))
    azucafe_bot.add_handler(PreCheckoutQueryHandler(payment_precheckout))

    azucafe_bot.add_handler(CallbackQueryHandler(unknow_query_handler))
    azucafe_bot.add_handler(
        MessageHandler(
            filters.ALL & (~filters.COMMAND | filters.SUCCESSFUL_PAYMENT),
            spam_message,
        )
    )

    azucafe_bot.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
