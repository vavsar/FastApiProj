from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_seller
from app.db_depends import get_async_db
from app.models import ProductModel, UserModel, ReviewModel
from app.models.categories import CategoryModel
from app.schemas import ProductSchema, ProductCreateSchema, ReviewSchema

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.get("/", response_model=List[ProductSchema])
async def get_all_products(db: AsyncSession = Depends(get_async_db)):
    """Возвращает список всех товаров."""

    products = await db.scalars(
        select(ProductModel).where(ProductModel.is_active == True).order_by(desc(ProductModel.id))
    )
    products = products.all()

    return products


@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller)
):
    """Создаёт новый товар, привязанный к текущему продавцу (только для 'seller')."""

    category_result = await db.scalars(
        select(CategoryModel).where(CategoryModel.id == product.category_id, CategoryModel.is_active == True)
    )
    if not category_result.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found or inactive")

    db_product = ProductModel(**product.model_dump(), seller_id=current_user.id)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)

    return db_product


@router.get("/category/{category_id}", response_model=List[ProductSchema], status_code=status.HTTP_200_OK)
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    """Возвращает список товаров в указанной категории по её ID."""

    category = await db.scalars(
        select(CategoryModel).where(
            CategoryModel.id == category_id,
            CategoryModel.is_active == True,
        )
    )
    category = category.first()

    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    products = await db.scalars(
        select(ProductModel).where(CategoryModel.id == category_id)
    )
    products = products.all()

    return products


@router.get("/products/{product_id}/reviews/", response_model=List[ReviewSchema], status_code=status.HTTP_200_OK)
async def get_product_reviews(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """Возвращает все отзывы по конкретному товару."""

    product = await db.scalars(
        select(ProductModel).where(ProductModel.id == product_id)
    )
    product = product.first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    reviews = await db.scalars(
        select(ReviewModel).where(
            ReviewModel.product_id == product_id,
            ReviewModel.is_active == True,
        ).order_by(desc(ReviewModel.id))
    )
    reviews = reviews.all()

    return reviews


@router.get("/{product_id}", response_model=ProductSchema, status_code=status.HTTP_200_OK)
async def get_product(product_id: int, category_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает детальную информацию о товаре по его ID.
    """
    product = await db.scalars(
        select(ProductModel).where(ProductModel.id == product_id)
    )
    product = product.first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    category = await db.scalars(
        select(CategoryModel).where(CategoryModel.id == category_id)
    )
    category = category.first()

    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    return product


@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(
    product_id: int,
    product: ProductCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller)
):
    """
    Обновляет товар, если он принадлежит текущему продавцу (только для 'seller').
    """
    result = await db.scalars(select(ProductModel).where(ProductModel.id == product_id))
    db_product = result.first()
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if db_product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own products")
    category_result = await db.scalars(
        select(CategoryModel).where(CategoryModel.id == product.category_id, CategoryModel.is_active == True)
    )
    if not category_result.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found or inactive")
    await db.execute(
        update(ProductModel).where(ProductModel.id == product_id).values(**product.model_dump())
    )
    await db.commit()
    await db.refresh(db_product)  # Для консистентности данных
    return db_product

@router.delete("/{product_id}", response_model=ProductSchema)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_seller)
):
    """
    Выполняет мягкое удаление товара, если он принадлежит текущему продавцу (только для 'seller').
    """
    result = await db.scalars(
        select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    )
    product = result.first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or inactive")
    if product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own products")
    await db.execute(
        update(ProductModel).where(ProductModel.id == product_id).values(is_active=False)
    )
    await db.commit()
    await db.refresh(product)  # Для возврата is_active = False
    return product
