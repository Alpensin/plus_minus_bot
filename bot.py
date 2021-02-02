import logging
import re
import sys
from typing import Dict, List, Text, Union

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    Updater,
)

import global_variables
import menu_addresses as ma
from control_interfaces import edit_person_keyboard, main_menu_keyboard
from settings import tables, telegram_token
from sqlite_handler import (
    insert_new_mark,
    insert_new_person,
    select_persons,
    update_data,
)

MARK_PATTERN = r"([+|-])\s(.*)"
MARK_MAPPING = {"+": 1, "-": -1}
updater = Updater(token=telegram_token, use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(
    format="%(asctime)s, %(levelname)s, %(name)s, %(message)s",
    level=logging.WARNING,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def stop(update: Update, context: CallbackContext) -> None:
    """End Conversation by command."""
    text = "Bye! Want to /start again?"
    if update.message:
        update.message.reply_text(text)
    else:
        update.callback_query.answer()
        update.callback_query.edit_message_text(text=text)

    return ma.END


def create_persons_selection_inline_menu(persons):
    person_buttons = list()
    for person in persons:
        person_id, person_name = person
        person_buttons.append(
            [
                InlineKeyboardButton(
                    text=person_name,
                    callback_data=f"p{person_id}",
                )
            ]
        )
    return InlineKeyboardMarkup(person_buttons)


def new_person(update: Update, context: CallbackContext) -> str:
    """Save input for feature and return to feature selection."""
    name = update.message.text
    tg_user = update.effective_user.id
    user_data = context.user_data
    insert_query = {"name": name, "tg_user": tg_user}
    insert_new_person(
        "persons", **insert_query
    )  # Потом доставать это из settings
    text = f"{user_data[global_variables.CURRENT_OPERATION]}:\n{name}"
    user_data[global_variables.CURRENT_OPERATION] = None
    update.message.reply_text(text=text, reply_markup=main_menu_keyboard)
    return ma.MENU_ACTION


def input_new_name(update: Update, context: CallbackContext):
    name = update.message.text
    user_data = context.user_data
    person_id = user_data[ma.EDITING_PERSON_ID]
    update_data(person_id, name)
    text = f"{user_data[global_variables.CURRENT_OPERATION]}:\n{name}"
    user_data[global_variables.CURRENT_OPERATION] = None
    update.message.reply_text(text=text)
    return stop(update, context)


def input_new_mark(update: Update, context: CallbackContext):
    user_data = context.user_data
    user_data[global_variables.CURRENT_OPERATION] = "Adding mark"
    mark_text = update.message.text.strip()
    mark, comment = re.search(MARK_PATTERN, mark_text, re.S).groups()
    try:
        mark = MARK_MAPPING[mark]
    except KeyError as e:
        logger.exception(e)
        raise
    person_id = user_data[ma.EDITING_PERSON_ID]
    insert_new_mark(person_id, mark, comment)
    text = f"{user_data[global_variables.CURRENT_OPERATION]}:\nDone"
    update.message.reply_text(text=text)
    user_data[global_variables.CURRENT_OPERATION] = None
    return stop(update, context)


def bot_help(update: Update, context: CallbackContext):
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="Type /start for beginning"
    )


def start(update: Update, context: CallbackContext):

    update.message.reply_text(
        f"Hi, i'm {context.bot.name}! I'm here to help you mark persons you want"
        "Send /cancel to stop talking to me.\n\n"
        "Please choose action",
        reply_markup=main_menu_keyboard,
    )
    return ma.MENU_ACTION


def person_selection(update: Update, context: CallbackContext) -> str:
    tg_user = update.effective_user.id
    persons = select_persons(tg_user)
    keyboard = create_persons_selection_inline_menu(persons)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="Choose Person", reply_markup=keyboard
    )
    return ma.PERSON_SELECTION


def user_data(update: Update, context: CallbackContext) -> str:
    user_data = context.user_data
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text=user_data, reply_markup=main_menu_keyboard
    )
    return ma.MENU_ACTION


def add_person(update: Update, context: CallbackContext) -> str:
    user_data = context.user_data
    user_data[global_variables.CURRENT_OPERATION] = "New Person"
    text = "Please send me name of Person"

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)
    return ma.INSERT


def prepare_insert_new_mark(update: Update, context: CallbackContext) -> str:
    user_data = context.user_data
    user_data[global_variables.CURRENT_OPERATION] = "Insert new Mark"
    text = (
        "<b>Please send me mark</b>\n<pre>Type + or - and Comment</pre>\n"
        "<i>Example:</i>\n<code>+ Nice Job!</code>"
    )

    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text=text, parse_mode=ParseMode.HTML
    )
    return ma.INSERT_NEW_MARK


def prepare_update_person_name(
    update: Update, context: CallbackContext
) -> str:
    user_data = context.user_data
    user_data[global_variables.CURRENT_OPERATION] = "Rename Person"
    text = "Please send me new name of Person"
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)

    return ma.UPDATE_PERSON_NAME


def personal_menu(update: Update, context: CallbackContext) -> str:
    user_data = context.user_data
    try:
        user_data[ma.EDITING_PERSON_ID] = int(update.callback_query.data[1:])
        text = "Please choose action"
    except ValueError as e:
        logger.exception(e)
        text = f"Wrong selection. data={update.callback_query.data}"
    except Exception as e:
        logger.exception(e)
        text = "Something gone wrong"
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text=text, reply_markup=edit_person_keyboard
    )

    return ma.PERSONAL_MENU


def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        "Bye! I hope we can talk again some day.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ma.END


def unknown(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


def main() -> None:

    # unknown_handler = MessageHandler(Filters.command, unknown)
    # dispatcher.add_handler(unknown_handler)
    persons_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(personal_menu, pattern="^p\d+$")],
        states={
            ma.PERSONAL_MENU: [
                CallbackQueryHandler(
                    prepare_update_person_name,
                    pattern="^" + ma.PREPARE_UPDATE_PERSON_NAME + "$",
                ),
                CallbackQueryHandler(
                    prepare_insert_new_mark,
                    pattern="^" + ma.PREPARE_INSERT_NEW_MARK + "$",
                ),
            ],
            ma.INSERT_NEW_MARK: [
                MessageHandler(Filters.text & ~Filters.command, input_new_mark)
            ],
            ma.UPDATE_PERSON_NAME: [
                MessageHandler(Filters.text & ~Filters.command, input_new_name)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        map_to_parent={
            ma.END: ma.END,
        },
    )
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ma.MENU_ACTION: [
                CallbackQueryHandler(
                    add_person, pattern="^" + ma.ADD_PERSON + "$"
                ),
                CallbackQueryHandler(
                    person_selection,
                    pattern="^" + ma.PERSONS_LIST + "$",
                ),
                CallbackQueryHandler(
                    stop,
                    pattern="^" + str(ma.END) + "$",
                ),
            ],
            ma.PERSON_SELECTION: [persons_conv],
            ma.INSERT: [
                MessageHandler(Filters.text & ~Filters.command, new_person)
            ],
            ma.STOPPING: [CommandHandler("start", start)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("stop", stop),
        ],
    )
    dispatcher.add_handler(conv_handler)
    help_handler = CommandHandler("help", bot_help)
    dispatcher.add_handler(help_handler)
    # start_handler = CommandHandler("start", start)

    # dispatcher.add_handler(start_handler)
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(e)
