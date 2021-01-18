from telegram.ext import ConversationHandler

END = ConversationHandler.END

# main_menu
MENU_ACTION = chr(0)
ADD_PERSON = chr(1)
MARK_PERSON = chr(2)
STOPPING = chr(3)
PERSONS_LIST = chr(4)
USER_DATA = chr(5)
INSERT = chr(6)

# status
PERSON_SELECTION = chr(7)

# user_menu
UPDATE_PERSON_NAME = chr(8)
PERSONAL_MENU = chr(9)
INSERT_NEW_MARK = chr(10)
PREPARE_UPDATE_PERSON_NAME = chr(11)
PREPARE_INSERT_NEW_MARK = chr(12)
EDITING_PERSON_ID = chr(13)
