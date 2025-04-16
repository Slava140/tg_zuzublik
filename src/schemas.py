from typing import Annotated

from pydantic import BaseModel, Field, HttpUrl, BeforeValidator, NonNegativeInt


def non_empty_str_validator(value: str) -> str:
    if isinstance(value, str):
        return value.strip()


NonEmptyStr255 = Annotated[str, Field(min_length=1, max_length=255), BeforeValidator(non_empty_str_validator)]
UrlStr = Annotated[HttpUrl, Field(min_length=1, max_length=255), BeforeValidator(non_empty_str_validator)]


class ItemS(BaseModel):
    title: NonEmptyStr255
    url: UrlStr
    xpath: NonEmptyStr255
    price: NonNegativeInt | None = None


class FullItemS(ItemS):
    id: int
