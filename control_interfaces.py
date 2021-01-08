from telegram import InlineKeyboardButton, InlineKeyboardMarkup

buttons = [
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
keyboard = InlineKeyboardMarkup(buttons)
