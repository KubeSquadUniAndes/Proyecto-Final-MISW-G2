from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.booking import Booking, BookingStatus
from src.domain.repositories.booking_repository_port import BookingRepositoryPort
from src.infrastructure.config.settings import settings
from src.infrastructure.database.models.booking_model import BookingModel


class SQLAlchemyBookingRepository(BookingRepositoryPort):
    """Output adapter: concrete repository implementation using SQLAlchemy + pgcrypto."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._key = settings.AES_ENCRYPTION_KEY

    # -------------------------------------------------------------------------
    # Mappers
    # -------------------------------------------------------------------------

    @staticmethod
    def _parse_status(raw) -> BookingStatus:
        """Convert whatever asyncpg returns for the enum column to a BookingStatus.

        asyncpg may return the Python enum member (when a codec is cached from a
        previous Enum(BookingStatus,...) column definition), the lowercase value string
        ("confirmed"), or the uppercase name string ("CONFIRMED").  Handle all cases.
        """
        if isinstance(raw, BookingStatus):
            return raw
        if hasattr(raw, "value"):
            return BookingStatus(raw.value)
        try:
            return BookingStatus(raw)  # value lookup: "confirmed" → CONFIRMED
        except ValueError:
            return BookingStatus[raw]  # name lookup:  "CONFIRMED" → CONFIRMED

    def _to_domain(self, model: BookingModel, decrypted: dict | None = None) -> Booking:
        d = decrypted or {}
        return Booking(
            id=model.id,
            user_id=model.user_id,
            hotel_id=model.hotel_id,
            room_id=model.room_id,
            start_time=model.start_time,
            end_time=model.end_time,
            status=self._parse_status(model.status),
            notes=model.notes,
            booking_code=model.booking_code,
            room_type=model.room_type,
            num_guests=model.num_guests,
            additional_guests=model.additional_guests,
            special_requests=model.special_requests,
            price_per_night=Decimal(str(model.price_per_night))
            if model.price_per_night
            else None,
            total_nights=model.total_nights,
            total_price=Decimal(str(model.total_price)) if model.total_price else None,
            taxes=Decimal(str(model.taxes)) if model.taxes else None,
            final_price=Decimal(str(model.final_price)) if model.final_price else None,
            payment_id=model.payment_id,
            payment_status=model.payment_status,
            traveler_name=d.get("traveler_name"),
            traveler_email=d.get("traveler_email"),
            traveler_phone=d.get("traveler_phone"),
            traveler_document=d.get("traveler_document"),
            qr_code=model.qr_code,
            qr_generated_at=model.qr_generated_at,
            qr_is_valid=model.qr_is_valid if model.qr_is_valid is not None else True,
            checked_in_at=model.checked_in_at,
            checkin_staff_id=model.checkin_staff_id,
            checkin_device=model.checkin_device,
            checkin_ip=model.checkin_ip,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    # -------------------------------------------------------------------------
    # Encryption helpers
    # -------------------------------------------------------------------------

    async def _decrypt_row(self, model: BookingModel) -> dict:
        """Decrypts sensitive fields for a single BookingModel row."""
        if not model.traveler_name:
            return {}
        result = await self._session.execute(
            text(
                "SELECT "
                "pgp_sym_decrypt(:name, :key) AS traveler_name, "
                "pgp_sym_decrypt(:email, :key) AS traveler_email, "
                "pgp_sym_decrypt(:phone, :key) AS traveler_phone, "
                "pgp_sym_decrypt(:doc, :key) AS traveler_document"
            ),
            {
                "name": model.traveler_name,
                "email": model.traveler_email,
                "phone": model.traveler_phone,
                "doc": model.traveler_document,
                "key": self._key,
            },
        )
        row = result.mappings().one()
        return dict(row)

    async def _encrypt_sensitive(self, booking: Booking) -> dict:
        """Returns a dict with encrypted bytea values for sensitive fields."""
        if not booking.traveler_name:
            return {}
        result = await self._session.execute(
            text(
                "SELECT "
                "pgp_sym_encrypt(:name, :key) AS traveler_name, "
                "pgp_sym_encrypt(:email, :key) AS traveler_email, "
                "pgp_sym_encrypt(:phone, :key) AS traveler_phone, "
                "pgp_sym_encrypt(:doc, :key) AS traveler_document"
            ),
            {
                "name": booking.traveler_name,
                "email": booking.traveler_email,
                "phone": booking.traveler_phone,
                "doc": booking.traveler_document,
                "key": self._key,
            },
        )
        row = result.mappings().one()
        return dict(row)

    # -------------------------------------------------------------------------
    # Port implementation
    # -------------------------------------------------------------------------

    async def save(self, booking: Booking) -> Booking:
        encrypted = await self._encrypt_sensitive(booking)
        # Omit status from INSERT so PostgreSQL uses server_default ('pending'
        # literal → booking_status_enum).  The real status is written right after
        # flush via _update_status_raw() which uses an explicit CAST.
        model = BookingModel(
            id=booking.id,
            user_id=booking.user_id,
            hotel_id=booking.hotel_id,
            room_id=booking.room_id,
            start_time=booking.start_time,
            end_time=booking.end_time,
            notes=booking.notes,
            booking_code=booking.booking_code,
            room_type=booking.room_type,
            num_guests=booking.num_guests,
            additional_guests=booking.additional_guests,
            special_requests=booking.special_requests,
            price_per_night=booking.price_per_night,
            total_nights=booking.total_nights,
            total_price=booking.total_price,
            taxes=booking.taxes,
            final_price=booking.final_price,
            payment_id=booking.payment_id,
            payment_status=booking.payment_status,
            traveler_name=encrypted.get("traveler_name"),
            traveler_email=encrypted.get("traveler_email"),
            traveler_phone=encrypted.get("traveler_phone"),
            traveler_document=encrypted.get("traveler_document"),
            qr_code=booking.qr_code,
            qr_generated_at=booking.qr_generated_at,
            qr_is_valid=booking.qr_is_valid,
            created_at=booking.created_at,
            updated_at=booking.updated_at,
        )
        self._session.add(model)
        await self._session.flush()
        await self._update_status_raw(model.id, booking.status.value)
        await self._session.refresh(model)
        decrypted = await self._decrypt_row(model)
        return self._to_domain(model, decrypted)

    async def get_by_id(self, booking_id: UUID) -> Booking | None:
        result = await self._session.execute(
            select(BookingModel).where(BookingModel.id == booking_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return None
        print(f"DEBUG get_by_id: model.payment_id = {model.payment_id}")
        decrypted = await self._decrypt_row(model)
        booking = self._to_domain(model, decrypted)
        print(f"DEBUG get_by_id: booking.payment_id = {booking.payment_id}")
        return booking

    async def list_by_user(self, user_id: UUID) -> list[Booking]:
        result = await self._session.execute(
            select(BookingModel).where(BookingModel.user_id == user_id)
        )
        models = result.scalars().all()
        bookings = []
        for m in models:
            decrypted = await self._decrypt_row(m)
            bookings.append(self._to_domain(m, decrypted))
        return bookings

    async def get_active_by_user(self, user_id: UUID) -> list[Booking]:
        # Use SQL literal for enum filter — bound parameters are sent as ::VARCHAR
        # which PostgreSQL rejects when comparing against booking_status_enum.
        result = await self._session.execute(
            select(BookingModel).where(
                BookingModel.user_id == user_id,
                text("status IN ('pending', 'confirmed')"),
            )
        )
        models = result.scalars().all()
        bookings = []
        for m in models:
            decrypted = await self._decrypt_row(m)
            bookings.append(self._to_domain(m, decrypted))
        return bookings

    async def _update_status_raw(self, booking_id: UUID, status_value: str) -> None:
        """Write status with explicit ::booking_status_enum cast.

        String(50) generates ::VARCHAR which PostgreSQL rejects for enum columns.
        Raw SQL with a named cast is the only reliable workaround for the
        Python 3.12 + asyncpg + SQLAlchemy Enum C-extension incompatibility.
        """
        await self._session.execute(
            text(
                "UPDATE bookings SET status = CAST(:s AS booking_status_enum)"
                " WHERE id = CAST(:id AS uuid)"
            ),
            {"s": status_value, "id": str(booking_id)},
        )

    async def update(self, booking: Booking) -> Booking:
        result = await self._session.execute(
            select(BookingModel).where(BookingModel.id == booking.id)
        )
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"Booking with id={booking.id} not found")

        await self._update_status_raw(booking.id, booking.status.value)
        model.notes = booking.notes
        model.start_time = booking.start_time
        model.end_time = booking.end_time
        model.updated_at = booking.updated_at
        model.special_requests = booking.special_requests
        model.payment_id = booking.payment_id
        model.payment_status = booking.payment_status
        model.qr_code = booking.qr_code
        model.qr_generated_at = booking.qr_generated_at
        model.qr_is_valid = booking.qr_is_valid
        model.checked_in_at = booking.checked_in_at
        model.checkin_staff_id = booking.checkin_staff_id
        model.checkin_device = booking.checkin_device
        model.checkin_ip = booking.checkin_ip

        if booking.traveler_name:
            encrypted = await self._encrypt_sensitive(booking)
            model.traveler_name = encrypted.get("traveler_name")
            model.traveler_email = encrypted.get("traveler_email")
            model.traveler_phone = encrypted.get("traveler_phone")
            model.traveler_document = encrypted.get("traveler_document")

        await self._session.flush()
        await self._session.refresh(model)
        decrypted = await self._decrypt_row(model)
        return self._to_domain(model, decrypted)

    async def delete(self, booking_id: UUID) -> bool:
        result = await self._session.execute(
            select(BookingModel).where(BookingModel.id == booking_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True

    async def get_by_room_and_date_range(
        self, room_id: UUID, start_time, end_time
    ) -> list[Booking]:
        """Get all bookings for a room that overlap with the date range."""
        result = await self._session.execute(
            select(BookingModel).where(
                BookingModel.room_id == room_id,
                BookingModel.start_time < end_time,
                BookingModel.end_time > start_time,
            )
        )
        models = result.scalars().all()
        bookings = []
        for m in models:
            decrypted = await self._decrypt_row(m)
            bookings.append(self._to_domain(m, decrypted))
        return bookings

    async def list_by_hotel(self, hotel_id: UUID) -> list[Booking]:
        """Get all bookings for a hotel."""
        result = await self._session.execute(
            select(BookingModel).where(BookingModel.hotel_id == hotel_id)
        )
        models = result.scalars().all()
        bookings = []
        for m in models:
            decrypted = await self._decrypt_row(m)
            bookings.append(self._to_domain(m, decrypted))
        return bookings

    async def get_dates_by_ids(
        self,
        booking_ids: list[UUID],
        checkin: datetime | None = None,
        checkout: datetime | None = None,
    ) -> list:
        """Get date info for multiple booking IDs (pending/confirmed only).

        If checkin/checkout are provided, only bookings that overlap with the
        given date range are returned (SQL-level filtering).
        """
        from src.domain.repositories.booking_repository_port import BookingDateInfo

        if not booking_ids:
            return []
        filters = [
            BookingModel.id.in_(booking_ids),
            text("status = ANY(ARRAY['pending', 'confirmed']::booking_status_enum[])"),
        ]
        if checkin is not None and checkout is not None:
            filters += [
                BookingModel.start_time < checkout,
                BookingModel.end_time > checkin,
            ]
        result = await self._session.execute(
            select(
                BookingModel.id,
                BookingModel.status,
                BookingModel.start_time,
                BookingModel.end_time,
            ).where(*filters)
        )
        return [
            BookingDateInfo(
                id=row.id,
                status=row.status,
                start_time=row.start_time,
                end_time=row.end_time,
            )
            for row in result.all()
        ]
