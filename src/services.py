from datetime import datetime, timezone
from io import BytesIO
from itertools import groupby
from pathlib import Path
from pprint import pp
from typing import TYPE_CHECKING, Sequence

import aiofiles
from aiohttp import ClientSession
import numpy as np
import pandas as pd
from fake_useragent import UserAgent
from lxml import html
from lxml.etree import XPathEvalError
from pydantic import ValidationError
from sqlalchemy import insert, select, func, update, case

from src.config import settings
from src.database import async_db_session, Item
from src.errors import SuffixNotAllowedError, InvalidDocumentSchemaError, UnableToReadError
from src.schemas import ItemS, FullItemS

if TYPE_CHECKING:
    from aiogram.types import Document


def clear_price(price: str) -> int:
    # Склеивает цифры из цены
    return int(''.join(filter(str.isdigit, price)))


def get_datetime_prefix(format_: str = '%Y%m%d_%H%M%S') -> str:
    return datetime.now(timezone.utc).strftime(format_)


def get_user_agent() -> str:
    return UserAgent().random


def validate_suffix(filename: str | Path) -> str:
    file_suffix = Path(filename).suffix
    if file_suffix not in settings.UPLOAD_ALLOWED_SUFFIXES:
        raise SuffixNotAllowedError
    return file_suffix


async def save_document(document: "Document", destination_dir: str | Path | None = None) -> Path:
    if destination_dir:
        destination_dir = Path(destination_dir)
        if not destination_dir.is_dir():
            destination_dir = destination_dir.parent
    else:
        destination_dir = settings.uploads_dir


    file_suffix = validate_suffix(document.file_name)
    document_bytes = BytesIO()
    bot = document.bot
    await bot.download(document.file_id, document_bytes)

    try:
        if file_suffix == '.csv':
            dataframe = pd.read_csv(document_bytes)
        else:
            dataframe = pd.read_excel(document_bytes)
    except UnicodeDecodeError:
        raise UnableToReadError

    if set(dataframe) != settings.DOCUMENT_COLUMN_NAMES:
        raise InvalidDocumentSchemaError

    unique_filename = f'{get_datetime_prefix()}_{document.file_id}'
    destination_filename = destination_dir / f'{unique_filename}{file_suffix}'

    async with aiofiles.open(destination_filename, 'wb') as file:
        await file.write(document_bytes.getbuffer())

    return destination_filename


def validate_document(file_path: str | Path) -> tuple[ list[int], list[ItemS] ]:
    file_path = Path(file_path)
    file_suffix = file_path.suffix

    try:
        if file_suffix == '.csv':
            df = pd.read_csv(file_path, na_values=' ')
        else:
            df = pd.read_excel(file_path)
    except UnicodeDecodeError:
        raise UnableToReadError

    df.replace(r'^\s*$', np.nan, regex=True, inplace=True)

    # +1 потому что индексация с нуля и +1 из-за заголовка
    invalid_rows_nums = list(df[df['url'].isnull() | df['xpath'].isnull()].index + 2)
    clean_df = df.dropna(subset=['url', 'xpath']).fillna('Untitled')

    items = []
    for index, record in clean_df.to_dict('index').items():
        try:
            items.append(ItemS.model_validate(record))
        except ValidationError:
            invalid_rows_nums.append(index + 2)

    return sorted(invalid_rows_nums), items

async def parse_prices(items: Sequence[FullItemS]) -> list[FullItemS]:
    key_func = lambda s: s.url
    sorted_items = sorted(items, key=key_func)
    grouped_items_by_url = {
        str(url): list(items_group)
        for url, items_group in groupby(sorted_items, key=key_func)
    }

    items_with_price = []
    async with ClientSession() as client:
        for url, items in grouped_items_by_url.items():
            async with client.get(url, headers={'User-Agent': get_user_agent()}) as response:
                text = await response.text()

            for item in items:
                root = html.fromstring(text)
                try:
                    found_elements = root.xpath(item.xpath)
                    price = clear_price(found_elements[0].text) if found_elements else None
                except XPathEvalError:
                    price = None

                items_with_price.append(
                    FullItemS(id=item.id, title=item.title, url=url, xpath=item.xpath, price=price)
                )

    return items_with_price


async def insert_items(schemas: Sequence[ItemS]) -> list[FullItemS]:
    stmt = insert(
        Item
    ).values(
        [item.model_dump(mode='json') for item in schemas]
    ).returning('*')

    async with async_db_session() as session:
        result = await session.execute(stmt)
        inserted_items = result.mappings().all()
        await session.commit()

    return [FullItemS(**item_dict) for item_dict in inserted_items]


async def get_average_by_url(url: str) -> float | None:
    query = select(
        func.sum(Item.price) / func.count(Item.price)
    ).where(
        Item.url == url.strip(),
        Item.price.is_not(None)
    )

    async with async_db_session() as session:
        result = await session.execute(query)

    avg = result.scalar_one_or_none()
    return float(avg) if avg else None


async def update_item_prices(id_price_dict: dict[int, int]):
    def get_update_stmt(_id: int, _price: int):
        return update(Item).where(Item.id == _id).values({'price': _price})

    async with async_db_session() as session:
        for id, price in id_price_dict.items():
            await session.execute(get_update_stmt(id, price))
        await session.commit()
