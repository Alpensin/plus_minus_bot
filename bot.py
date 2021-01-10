import logging
import sys
from typing import Dict, List, Text, Union

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
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

from settings import tables, telegram_token
from sqlite_handler import insert_data, select_persons, update_data

END = ConversationHandler.END
MENU_ACTION, ADD_PERSON, PERSONS_LIST, MARK_PERSON, STOPPING = map(
    chr, range(5)
)
CURRENT_OPERATION, INSERT = map(chr, range(5, 7))
RENAMING_PERSON = map(chr, range(7, 9))
EDITING_PERSON_ID = chr(9)
USER_DATA = chr(100)
updater = Updater(token=telegram_token, use_context=True)
dispatcher = updater.dispatcher

logging.basicConfig(
    format="%(asctime)s, %(levelname)s, %(name)s, %(message)s",
    level=logging.DEBUG,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

main_menu_buttons = [
    [
        InlineKeyboardButton(
            text="Add mark to existing person",
            callback_data=str(MARK_PERSON),
        )
    ],
    [
        InlineKeyboardButton(text="Add Person", callback_data=str(ADD_PERSON)),
        InlineKeyboardButton(
            text="Persons list", callback_data=str(PERSONS_LIST)
        ),
    ],
    [
        InlineKeyboardButton(
            text="User data",
            callback_data=str(USER_DATA),
        )
    ],
]
main_menu_keyboard = InlineKeyboardMarkup(main_menu_buttons)


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
    insert_data("persons", **insert_query)  # Потом доставать это из settings
    text = f"{user_data[CURRENT_OPERATION]}:\n{name}"
    user_data[CURRENT_OPERATION] = None
    update.message.reply_text(text=text, reply_markup=main_menu_keyboard)
    return MENU_ACTION


def input_new_name(update: Update, context: CallbackContext) -> int:
    name = update.message.text
    user_data = context.user_data
    person_id = user_data[EDITING_PERSON_ID]
    update_data(person_id, name)
    text = f"{user_data[CURRENT_OPERATION]}:\n{name}"
    user_data[CURRENT_OPERATION] = None
    update.message.reply_text(text=text, reply_markup=main_menu_keyboard)
    return END


def stop(update: Update, context: CallbackContext) -> None:
    """End Conversation by command."""
    update.message.reply_text("Okay, bye.")

    return END


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
    return MENU_ACTION


def persons_list(update: Update, context: CallbackContext) -> str:
    tg_user = update.effective_user.id
    persons = select_persons(tg_user)
    keyboard = create_persons_selection_inline_menu(persons)
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text="Choose Person", reply_markup=keyboard
    )
    return RENAMING_PERSON


def user_data(update: Update, context: CallbackContext) -> str:
    user_data = context.user_data
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text=user_data, reply_markup=main_menu_keyboard
    )
    return MENU_ACTION


def add_person(update: Update, context: CallbackContext) -> str:
    user_data = context.user_data
    user_data[CURRENT_OPERATION] = "New Person"
    text = "Please send me name of Person"

    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)
    return INSERT


def rename_person(update: Update, context: CallbackContext) -> str:
    user_data = context.user_data
    user_data[CURRENT_OPERATION] = "Rename Person"
    try:
        user_data[EDITING_PERSON_ID] = int(update.callback_query.data[1:])
        text = "Please send me new name of Person"
    except ValueError as e:
        logger.exception(e)
        text = f"Wrong selection. data={update.callback_query.data}"
    except Exception as e:
        logger.exception(e)
        text = "Something gone wrong"
    update.callback_query.answer()
    update.callback_query.edit_message_text(text=text)

    return INSERT


def mark_person(update: Update, context: CallbackContext) -> str:
    text = "marking person"
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text=text, reply_markup=main_menu_keyboard
    )

    return MENU_ACTION


def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        "Bye! I hope we can talk again some day.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return ConversationHandler.END


def unknown(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


def main() -> None:

    # unknown_handler = MessageHandler(Filters.command, unknown)
    # dispatcher.add_handler(unknown_handler)
    persons_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(rename_person, pattern="^p\d+$")],
        states={
            INSERT: [
                MessageHandler(Filters.text & ~Filters.command, input_new_name)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    adding_mark = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                rename_person, pattern="^" + str(ADDING_MARK) + "$"
            )
        ],
        states={
            INSERT: [
                MessageHandler(Filters.text & ~Filters.command, input_new_name)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU_ACTION: [
                CallbackQueryHandler(
                    mark_person, pattern="^" + str(MARK_PERSON) + "$"
                ),
                CallbackQueryHandler(
                    add_person, pattern="^" + str(ADD_PERSON) + "$"
                ),
                CallbackQueryHandler(
                    persons_list, pattern="^" + str(PERSONS_LIST) + "$"
                ),
                CallbackQueryHandler(
                    user_data, pattern="^" + str(USER_DATA) + "$"
                ),
            ],
            RENAMING_PERSON: [persons_conv],
            INSERT: [
                MessageHandler(Filters.text & ~Filters.command, new_person)
            ],
            STOPPING: [CommandHandler("start", start)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
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
