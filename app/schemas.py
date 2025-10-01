from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional

from sqlalchemy import DateTime


class CategoryCreateSchema(BaseModel):
    """
    Модель для создания и обновления категории.
    Используется в POST и PUT запросах.
    """
    name: str = Field(min_length=3, max_length=50, description="Название категории (3-50 символов)")
    parent_id: Optional[int] = Field(None, description="ID родительской категории, если есть")


class CategorySchema(BaseModel):
    """
    Модель для ответа с данными категории.
    Используется в GET-запросах.
    """
    id: int = Field(description="Уникальный идентификатор категории")
    name: str = Field(description="Название категории")
    parent_id: Optional[int] = Field(None, description="ID родительской категории, если есть")
    is_active: bool = Field(description="Активность категории")

    model_config = ConfigDict(from_attributes=True)


class ProductCreateSchema(BaseModel):
    """
    Модель для создания и обновления товара.
    Используется в POST и PUT запросах.
    """
    name: str = Field(min_length=3, max_length=100, description="Название товара (3-100 символов)")
    description: Optional[str] = Field(None, max_length=500, description="Описание товара (до 500 символов)")
    price: float = Field(gt=0, description="Цена товара (больше 0)")
    image_url: Optional[str] = Field(None, max_length=200, description="URL изображения товара")
    stock: int = Field(ge=0, description="Количество товара на складе (0 или больше)")
    category_id: int = Field(description="ID категории, к которой относится товар")


class ProductSchema(BaseModel):
    """
    Модель для ответа с данными товара.
    Используется в GET-запросах.
    """
    id: int = Field(description="Уникальный идентификатор товара")
    name: str = Field(description="Название товара")
    description: Optional[str] = Field(None, description="Описание товара")
    price: float = Field(description="Цена товара")
    image_url: Optional[str] = Field(None, description="URL изображения товара")
    stock: int = Field(description="Количество товара на складе")
    rating: float = Field(description="Средняя оценка по отзывам")
    category_id: int = Field(description="ID категории")
    is_active: bool = Field(description="Активность товара")

    model_config = ConfigDict(from_attributes=True)


class UserCreateSchema(BaseModel):
    email: EmailStr = Field(description="Email пользователя")
    password: str = Field(min_length=8, description="Пароль (минимум 8 символов)")
    role: str = Field(default="buyer", pattern="^(buyer|seller)$", description="Роль: 'buyer' или 'seller'")


class UserSchema(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    role: str
    model_config = ConfigDict(from_attributes=True)


class ReviewSchema(BaseModel):
    """
    Модель для ответа с данными отзывы.
    Используется в GET-запросах.
    """

    id: int = Field(description="Уникальный идентификатор товара")
    user_id: int = Field(description="ID пользователя")
    product_id: int = Field(description="ID товара")
    comment: Optional[str] = Field(None, description="Текст отзыва")
    comment_date: datetime = Field(DateTime, description="Дата отзыва")
    grade: int = Field(description="Оценка")
    is_active: bool = Field(description="Активность товара")

    model_config = ConfigDict(from_attributes=True)


class ReviewCreateSchema(BaseModel):
    """
    Модель для создания и обновления отзыва.
    Используется в POST и PUT запросах.
    """
    product_id: int = Field(description="ID товара")
    comment: Optional[str] = Field(None, description="Текст отзыва")
    grade: int = Field(ge=1, le=5, description="Оценка")
