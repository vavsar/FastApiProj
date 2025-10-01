from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_seller, get_current_buyer, get_admin
from app.db_depends import get_async_db
from app.models import ProductModel, UserModel
from app.models.reviews import ReviewModel
from app.schemas import ProductSchema, ProductCreateSchema, ReviewSchema, ReviewCreateSchema

router = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
)


async def update_product_rating(db: AsyncSession, product_id: int):
    result = await db.execute(
        select(func.avg(ReviewModel.grade)).where(
            ReviewModel.product_id == product_id,
            ReviewModel.is_active == True
        )
    )
    avg_rating = result.scalar() or 0.0
    product = await db.get(ProductModel, product_id)
    product.rating = avg_rating
    await db.commit()


@router.get("/", response_model=List[ReviewSchema])
async def get_all_reviews(db: AsyncSession = Depends(get_async_db)):
    """Возвращает список всех отзывов."""

    reviews = await db.scalars(
        select(ReviewModel).where(ReviewModel.is_active == True).order_by(desc(ReviewModel.id))
    )
    reviews = reviews.all()

    return reviews


@router.post("/", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def create_review(
    review: ReviewCreateSchema,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_buyer)
):
    """Создаёт новый отзыв, привязанный к текущему продавцу (только для 'seller')."""

    product_result = await db.scalars(
        select(ProductModel).where(
            ProductModel.id == review.product_id,
            ProductModel.is_active == True,
        )
    )
    product = product_result.first()
    if not product:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product not found or inactive")

    await update_product_rating(db=db, product_id=product.id)

    db_review = ReviewModel(**review.model_dump(), user_id=current_user.id)
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)

    return db_review


@router.delete("/{review_id}")
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_admin)
):
    """Выполняет мягкое удаление отзыв по ID, устанавливая is_active = False."""

    result = await db.scalars(
        select(ReviewModel).where(
            ReviewModel.id == review_id,
            ReviewModel.is_active == True,
        )
    )
    db_review = result.first()
    # product_id = select(ProductModel.id).where(ProductModel.id == db_review.product_id).scalar()

    if not db_review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    await db.execute(
        update(ReviewModel)
        .where(ReviewModel.id == review_id)
        .values(is_active=False)
    )
    await update_product_rating(db=db, product_id=db_review.product_id)
    await db.commit()

    return {"message": "Review deleted"}
