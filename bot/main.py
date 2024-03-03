import logging

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    PicklePersistence,
    PreCheckoutQueryHandler,
    filters,
)

from core.config import settings
from core.constants import ButtonCallbackData, UserFlowState
from crud.worker import Worker
from modules import (
    booking_detail_back,
    booking_detail_show,
    booking_menu_cancel,
    booking_menu_show,
    bookings_switching,
    build_menu_start,
    cafe_select_booking,
    cafe_select_cancel,
    cafe_select_change_cafe,
    cafe_select_start,
    contact_phone_request,
    date_select_button,
    date_select_show,
    help_message,
    menu_add_to_basket,
    menu_booking,
    menu_cancel,
    menu_clear_basket,
    menu_remove_from_basket,
    menu_switching_sets,
    payment_cancel,
    payment_precheckout,
    payment_show_dialog,
    payment_successful,
    spam_message,
    start_bot,
    timers_for_start_bot
)

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


async def test_func(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    worker: Worker = context.user_data['worker']
    cafe_list = ''
    for cafe_id, cafe in worker.cafes.items():
        cafe_list += f'**{cafe.name}**\n'
        cafe_list += f'\tAddress: {cafe.address}\n'
        cafe_list += f'\tPhone: {cafe.phone}\n'
        seats_count = 0
        for table in cafe.tables:
            seats_count += table.seats_count if table.available else 0
        cafe_list += f'\tSeats: {seats_count}\n'

    await query.edit_message_text(text=f'Cafes\n{cafe_list}\n')

    return UserFlowState.START


def main():
    config_loggig()
    persistence = PicklePersistence(filepath="azucafebot")
    azucafe_bot = (
        Application.builder()
        .token(settings.bot_token)
        .persistence(persistence)
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
                MessageHandler(
                    filters.CONTACT, contact_phone_request
                ),
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
        ],
        name="azubot_conversation",
        persistent=True,
    )

    azucafe_bot.add_handler(conv_handler)
    azucafe_bot.add_handler(CommandHandler(
        "restarttimers", timers_for_start_bot))
    azucafe_bot.add_handler(PreCheckoutQueryHandler(payment_precheckout))
    azucafe_bot.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
