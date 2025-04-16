from aiogram import types


def get_one_button_keyboard(text: str, callback_data: str):
    buttons = [
        [types.InlineKeyboardButton(text=text, callback_data=callback_data)]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


def get_two_buttons_keyboard(text1: str, callback_data1: str, text2: str, callback_data2: str):
    buttons = [
        [types.InlineKeyboardButton(text=text1, callback_data=callback_data1),
         types.InlineKeyboardButton(text=text2, callback_data=callback_data2)]
    ]
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)