from telegram import InlineKeyboardButton, InlineKeyboardMarkup

import menu_addresses as ma

main_menu_buttons = [
    [
        InlineKeyboardButton(text="Add Person", callback_data=ma.ADD_PERSON),
        InlineKeyboardButton(
            text="Persons list", callback_data=ma.PERSONS_LIST
        ),
    ],
    [
        InlineKeyboardButton(text="Done", callback_data=ma.END),
    ],
]

edit_person_buttons = [
    [
        InlineKeyboardButton(
            text="Rename",
            callback_data=ma.PREPARE_UPDATE_PERSON_NAME,
        )
    ],
    [
        InlineKeyboardButton(
            text="Mark person",
            callback_data=ma.PREPARE_INSERT_NEW_MARK,
        )
    ],
]
edit_person_keyboard = InlineKeyboardMarkup(edit_person_buttons)
main_menu_keyboard = InlineKeyboardMarkup(main_menu_buttons)
