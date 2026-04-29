from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.delete_room_image import DeleteRoomImageUseCase
from src.application.use_cases.list_room_images import ListRoomImagesUseCase
from src.application.use_cases.upload_room_image import UploadRoomImageUseCase
from src.infrastructure.database.base import get_db
from src.infrastructure.database.repositories.sqlalchemy_room_image_repository import (
    SQLAlchemyRoomImageRepository,
)
from src.infrastructure.database.repositories.sqlalchemy_room_repository import (
    SQLAlchemyRoomRepository,
)
from src.infrastructure.http.dependencies import (
    TokenClaims,
    require_hotel_or_traveler_role,
    require_hotel_role,
)
from src.infrastructure.http.schemas.room_image_schema import RoomImageResponse
from src.infrastructure.http.schemas.room_schema import ErrorResponse, MessageResponse
from src.infrastructure.storage.s3_image_storage import S3ImageStorage

router = APIRouter(prefix="/rooms", tags=["Room Images"])


@router.post(
    "/{room_id}/images",
    response_model=RoomImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image for a room",
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def upload_room_image(
    room_id: UUID,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    claims: TokenClaims = Depends(require_hotel_role),
):
    data = await file.read()
    try:
        result = await UploadRoomImageUseCase(
            room_repo=SQLAlchemyRoomRepository(db),
            image_repo=SQLAlchemyRoomImageRepository(db),
            storage=S3ImageStorage(),
        ).execute(
            room_id=room_id,
            hotel_id=claims.user_id,
            data=data,
            content_type=file.content_type or "application/octet-stream",
            filename=file.filename or "upload",
        )
        return RoomImageResponse(**result.__dict__)
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.get(
    "/{room_id}/images",
    response_model=list[RoomImageResponse],
    summary="List all images for a room",
)
async def list_room_images(
    room_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: TokenClaims = Depends(require_hotel_or_traveler_role),
):
    results = await ListRoomImagesUseCase(
        repo=SQLAlchemyRoomImageRepository(db),
    ).execute(room_id)
    return [RoomImageResponse(**r.__dict__) for r in results]


@router.delete(
    "/images/{image_id}",
    response_model=MessageResponse,
    summary="Delete a room image",
    responses={404: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def delete_room_image(
    image_id: UUID,
    db: AsyncSession = Depends(get_db),
    claims: TokenClaims = Depends(require_hotel_role),
):
    try:
        await DeleteRoomImageUseCase(
            room_repo=SQLAlchemyRoomRepository(db),
            image_repo=SQLAlchemyRoomImageRepository(db),
            storage=S3ImageStorage(),
        ).execute(image_id=image_id, hotel_id=claims.user_id)
        return MessageResponse(message="Image deleted successfully")
    except ValueError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc))
