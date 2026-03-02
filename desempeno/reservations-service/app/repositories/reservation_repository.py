import uuid
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.reservation import Reservation, ReservationStatus
from app.repositories.base import AbstractReservationRepository
from app.schemas.reservation import ReservationCreate, ReservationUpdate

ENCRYPTED_FIELDS = frozenset(
    {"traveler_name", "traveler_email", "traveler_phone", "traveler_document"}
)

SELECT_COLUMNS = """
    id,
    pgp_sym_decrypt(traveler_name, :key) AS traveler_name,
    pgp_sym_decrypt(traveler_email, :key) AS traveler_email,
    pgp_sym_decrypt(traveler_phone, :key) AS traveler_phone,
    pgp_sym_decrypt(traveler_document, :key) AS traveler_document,
    destination, origin, departure_date, return_date,
    status, num_passengers, created_at, updated_at
"""


class ReservationRepository(AbstractReservationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._key = get_settings().encryption_key

    async def create(self, data: ReservationCreate) -> Reservation:
        query = text(f"""
            INSERT INTO reservations (
                id, traveler_name, traveler_email, traveler_phone,
                traveler_document, destination, origin,
                departure_date, return_date, status, num_passengers
            ) VALUES (
                gen_random_uuid(),
                pgp_sym_encrypt(:name, :key),
                pgp_sym_encrypt(:email, :key),
                pgp_sym_encrypt(:phone, :key),
                pgp_sym_encrypt(:document, :key),
                :destination, :origin,
                :departure_date, :return_date, :status, :num_passengers
            )
            RETURNING {SELECT_COLUMNS}
        """)

        result = await self._session.execute(
            query,
            {
                "name": data.traveler_name,
                "email": data.traveler_email,
                "phone": data.traveler_phone,
                "document": data.traveler_document,
                "destination": data.destination,
                "origin": data.origin,
                "departure_date": data.departure_date,
                "return_date": data.return_date,
                "status": ReservationStatus.PENDING.value,
                "num_passengers": data.num_passengers,
                "key": self._key,
            },
        )
        return self._row_to_entity(result.fetchone())

    async def get_by_id(self, reservation_id: uuid.UUID) -> Optional[Reservation]:
        query = text(f"""
            SELECT {SELECT_COLUMNS}
            FROM reservations
            WHERE id = :id
        """)
        result = await self._session.execute(
            query, {"id": reservation_id, "key": self._key}
        )
        row = result.fetchone()
        return self._row_to_entity(row) if row else None

    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[Reservation], int]:
        count_result = await self._session.execute(
            text("SELECT COUNT(*) FROM reservations")
        )
        total = count_result.scalar()

        query = text(f"""
            SELECT {SELECT_COLUMNS}
            FROM reservations
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :skip
        """)
        result = await self._session.execute(
            query, {"key": self._key, "limit": limit, "skip": skip}
        )
        rows = result.fetchall()
        return [self._row_to_entity(row) for row in rows], total

    async def update(
        self, reservation_id: uuid.UUID, data: ReservationUpdate
    ) -> Optional[Reservation]:
        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_by_id(reservation_id)

        set_clauses: list[str] = []
        params: dict = {"id": reservation_id, "key": self._key}

        for field_name, value in update_data.items():
            if field_name in ENCRYPTED_FIELDS:
                set_clauses.append(
                    f"{field_name} = pgp_sym_encrypt(:{field_name}, :key)"
                )
            else:
                set_clauses.append(f"{field_name} = :{field_name}")

            if isinstance(value, ReservationStatus):
                params[field_name] = value.value
            else:
                params[field_name] = value

        set_clauses.append("updated_at = NOW()")
        set_sql = ", ".join(set_clauses)

        query = text(f"""
            UPDATE reservations
            SET {set_sql}
            WHERE id = :id
            RETURNING {SELECT_COLUMNS}
        """)

        result = await self._session.execute(query, params)
        row = result.fetchone()
        return self._row_to_entity(row) if row else None

    @staticmethod
    def _row_to_entity(row) -> Reservation:
        return Reservation(
            id=row.id,
            traveler_name=row.traveler_name,
            traveler_email=row.traveler_email,
            traveler_phone=row.traveler_phone,
            traveler_document=row.traveler_document,
            destination=row.destination,
            origin=row.origin,
            departure_date=row.departure_date,
            return_date=row.return_date,
            status=ReservationStatus(row.status),
            num_passengers=row.num_passengers,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
