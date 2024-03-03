from telegram import Update
from telegram.ext import ContextTypes

from core.constants import UserFlowState


async def help_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выводит справочное сообщение, если пользователь ввел что-то не то."""
    await update.message.reply_text(
        'Это просто справка',
        disable_web_page_preview=True,
    )
    return UserFlowState.START


async def spam_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выводит справочное сообщение, если пользователь ввел что-то не то."""
    message_text = (
        'Извените, не известная команда.\n'
        'Найдите последнее сообщение с кнопками или '
        'выберите `/start`'
    )
    if update.message:
        await update.message.reply_text(
            message_text,
            disable_web_page_preview=True,
        )
    else:
        await context.bot.send_message(
            update.effective_chat.id,
            message_text,
            disable_web_page_preview=True,
        )


async def unknow_query_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()
    await query.delete_message()

    message_text = (
        'Извените, видимо что-то пошло не так.\n'
        'Начните, пожалуйста, с начала `/start`'
    )
    if update.message:
        await update.message.reply_text(
            message_text,
            disable_web_page_preview=True,
        )
    else:
        await context.bot.send_message(
            update.effective_chat.id,
            message_text,
            disable_web_page_preview=True,
        )
