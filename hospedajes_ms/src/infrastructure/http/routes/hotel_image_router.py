from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.delete_hotel_image import DeleteHotelImageUseCase
from src.application.use_cases.list_hotel_images import ListHotelImagesUseCase
from src.application.use_cases.upload_hotel_image import UploadHotelImageUseCase
from src.infrastructure.database.base import get_db
from src.infrastructure.database.repositories.sqlalchemy_hotel_image_repository import (
    SQLAlchemyHotelImageRepository,
)
from src.infrastructure.http.dependencies import (
    TokenClaims,
    require_hotel_or_traveler_role,
    require_hotel_role,
)
from src.infrastructure.http.schemas.hotel_image_schema import HotelImageResponse
from src.infrastructure.http.schemas.room_schema import ErrorResponse, MessageResponse
from src.infrastructure.storage.s3_image_storage import S3ImageStorage

router = APIRouter(prefix="/hotels", tags=["Hotel Images"])


@router.post(
    "/images",
    response_model=HotelImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image for the authenticated hotel",
    responses={422: {"model": ErrorResponse}},
)
async def upload_hotel_image(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    claims: TokenClaims = Depends(require_hotel_role),
):
    data = await file.read()
    try:
        result = await UploadHotelImageUseCase(
            repo=SQLAlchemyHotelImageRepository(db),
            storage=S3ImageStorage(),
        ).execute(
            hotel_id=claims.user_id,
            data=data,
            content_type=file.content_type or "application/octet-stream",
            filename=file.filename or "upload",
        )
        return HotelImageResponse(**result.__dict__)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get(
    "/{hotel_id}/images",
    response_model=list[HotelImageResponse],
    summary="List all images for a hotel",
)
async def list_hotel_images(
    hotel_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: TokenClaims = Depends(require_hotel_or_traveler_role),
):
    results = await ListHotelImagesUseCase(
        repo=SQLAlchemyHotelImageRepository(db),
    ).execute(hotel_id)
    return [HotelImageResponse(**r.__dict__) for r in results]


@router.delete(
    "/images/{image_id}",
    response_model=MessageResponse,
    summary="Delete a hotel image",
    responses={404: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def delete_hotel_image(
    image_id: UUID,
    db: AsyncSession = Depends(get_db),
    claims: TokenClaims = Depends(require_hotel_role),
):
    try:
        await DeleteHotelImageUseCase(
            repo=SQLAlchemyHotelImageRepository(db),
            storage=S3ImageStorage(),
        ).execute(image_id=image_id, hotel_id=claims.user_id)
        return MessageResponse(message="Image deleted successfully")
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc))
