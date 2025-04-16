from urllib.parse import urlparse

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from config import settings
from errors import SuffixNotAllowedError, InvalidDocumentSchemaError, UnableToReadError
from keyboards import get_one_button_keyboard, get_two_buttons_keyboard
from schemas import FullItemS
from services import (save_document, validate_document, parse_prices,
                      insert_items, get_average_by_url, update_item_prices)


class Upload(StatesGroup):
    sending = State()
    getting_average = State()


router = Router()


@router.message(Command('menu', 'start'))
async def command_menu_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text='Что нужно?',
        reply_markup=get_two_buttons_keyboard('Загрузить зюзюбликов!', 'send',
                                              'Вычислить среднюю цену', 'get_avg')
    )


@router.callback_query(F.data == 'menu')
async def callback_menu_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.answer(
        text='Что нужно?',
        reply_markup=get_two_buttons_keyboard('Загрузить зюзюбликов!', 'send',
                                              'Вычислить среднюю цену', 'get_avg')
    )


@router.callback_query(F.data == 'send')
async def callback_send_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Upload.sending)
    await callback.message.edit_text(
        text=f'Отправь файл.\nРазрешенные расширения: <code>{settings.allowed_suffixes}</code>'
    )
    await callback.message.edit_reply_markup(
        reply_markup=get_one_button_keyboard('Главное меню', 'menu')
    )

@router.message(F.document, Upload.sending)
async def message_sending_document_handler(message: Message, state: FSMContext):
    try:
        saved_document_path = await save_document(message.document)

    except SuffixNotAllowedError:
        await message.answer(
            text=f'Я не умею обрабатывать такие файлы.\nА такие могу: {settings.allowed_suffixes}',
            reply_markup=get_one_button_keyboard('Ааа, понятно! Отправить другой файл', 'send')
        )
        return

    except (InvalidDocumentSchemaError, UnableToReadError):
        await message.answer(
            text=f'Файл должен содержать столбцы {settings.document_column_names}',
            reply_markup=get_one_button_keyboard('Отправить другой файл', 'send')
        )
        return

    msg = await message.answer(text='Загрузил файл. Начинаю обрабатывать...')
    invalid_rows, valid_items = validate_document(saved_document_path)

    answer = ''
    if invalid_rows:
        invalid_rows_str = ', '.join(map(str, invalid_rows))
        if len(invalid_rows) == 1:
            answer += f'Строка {invalid_rows_str} проигнорирована\n\n'
        else:
            answer += f'Строки ({invalid_rows_str}) проигнорированы\n\n'

    if valid_items:
        template = ('<b>Название</b>: <i>{title}</i>\n'
                    '<b>url</b>: <i>{url}</i>\n'
                    '<b>xpath</b>: <code>{xpath}</code>\n')
        answer += '\n'.join(template.format(**item.model_dump()) for item in valid_items)
        markup = get_two_buttons_keyboard('Собрать данные', 'collect_data',
                                          'Загрузить другой файл', 'send')
        inserted_items = await insert_items(valid_items)
        await state.set_data({'items': inserted_items})
    else:
        answer += 'Ничего нет'
        markup = get_one_button_keyboard('Загрузить другой файл', 'send')

    await msg.edit_text(answer.strip())
    await msg.edit_reply_markup(reply_markup=markup)


@router.callback_query(F.data == 'collect_data', Upload.sending)
async def callback_collect_data_handler(callback: CallbackQuery, state: FSMContext):
    items: list[FullItemS] = await state.get_value('items')
    items_with_price = await parse_prices(items)

    items_with_not_null_price = filter(lambda s: s.price, items_with_price)
    dict_to_update = {schema.id: schema.price for schema in items_with_not_null_price}

    await update_item_prices(dict_to_update)

    template = ('<b>Название</b>: <i>{title}</i>\n'
                '<b>url</b>: <i>{url}</i>\n'
                '<b>xpath</b>: <code>{xpath}</code>\n'
                '<b>Цена</b>: <i>{price}</i>\n')
    answer = '\n'.join(template.format(**item.model_dump()) for item in items_with_price)
    await callback.message.edit_text(answer)
    markup = get_two_buttons_keyboard('Вычислить среднюю цену', 'get_avg',
                                      'Загрузить другой файл', 'send')
    await callback.message.edit_reply_markup(reply_markup=markup)


@router.callback_query(F.data == 'get_avg')
async def callback_get_avg_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Upload.getting_average)
    await callback.answer()
    await callback.message.answer('Введи ссылку, по которой нужно вычислить среднюю цену')


@router.message(F.text, Upload.getting_average)
async def message_getting_average_handler(message: Message, state: FSMContext):
    user_url = message.text
    urlparse_result = urlparse(user_url)
    is_url_valid = all([urlparse_result.scheme, urlparse_result.netloc])
    if is_url_valid:
        average_price = await get_average_by_url(user_url)
        if average_price:
            answer = (f'Средняя цена зюзюблика на этой странице: <i>{int(average_price)}</i>.\n'
                      f'Ты можешь ввести еще одну ссылку')
        else:
            answer = (f'Не могу вычислить среднюю цену на этой странице.\n'
                      f'Попробуй отправить другую ссылку')
    else:
        answer = 'Не могу разобрать ссылку, попробуй еще раз'
    await message.reply(
        text=answer,
        reply_markup=get_one_button_keyboard('Главное меню', 'menu')
    )