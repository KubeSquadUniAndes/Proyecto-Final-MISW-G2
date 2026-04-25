"""Unit tests for rate and discount use cases and domain entities."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from src.application.dtos.rate_dto import (
    CreateDiscountDTO,
    CreateRateDTO,
    UpdateDiscountDTO,
    UpdateRateDTO,
)
from src.application.use_cases.create_discount import CreateDiscountUseCase
from src.application.use_cases.create_rate import CreateRateUseCase
from src.application.use_cases.delete_discount import DeleteDiscountUseCase
from src.application.use_cases.delete_rate import DeleteRateUseCase
from src.application.use_cases.get_effective_price import GetEffectivePriceUseCase
from src.application.use_cases.get_rate import GetRateUseCase
from src.application.use_cases.list_discounts import ListDiscountsUseCase
from src.application.use_cases.list_rates import ListRatesUseCase
from src.application.use_cases.update_discount import UpdateDiscountUseCase
from src.application.use_cases.update_rate import UpdateRateUseCase
from src.domain.entities.rate import Discount, DiscountType, Rate, SeasonType
from src.domain.entities.room import Room, RoomStatus, RoomType


# ── Mock repositories ──────────────────────────────────────────────────────────

class MockRateRepository:
    def __init__(self):
        self.rates: dict[UUID, Rate] = {}

    async def save(self, rate: Rate) -> Rate:
        self.rates[rate.id] = rate
        return rate

    async def get_by_id(self, rate_id: UUID) -> Rate | None:
        return self.rates.get(rate_id)

    async def list_by_hotel(self, hotel_id: UUID, room_type: RoomType | None = None) -> list[Rate]:
        rates = [r for r in self.rates.values() if r.hotel_id == hotel_id]
        if room_type is not None:
            rates = [r for r in rates if r.room_type == room_type]
        return rates

    async def get_by_hotel_room_type_season(
        self, hotel_id: UUID, room_type: RoomType, season: SeasonType
    ) -> Rate | None:
        return next(
            (
                r for r in self.rates.values()
                if r.hotel_id == hotel_id
                and r.room_type == room_type
                and r.season == season
            ),
            None,
        )

    async def update(self, rate: Rate) -> Rate:
        self.rates[rate.id] = rate
        return rate

    async def delete(self, rate_id: UUID) -> bool:
        if rate_id in self.rates:
            del self.rates[rate_id]
            return True
        return False


class MockDiscountRepository:
    def __init__(self):
        self.discounts: dict[UUID, Discount] = {}

    async def save(self, discount: Discount) -> Discount:
        self.discounts[discount.id] = discount
        return discount

    async def get_by_id(self, discount_id: UUID) -> Discount | None:
        return self.discounts.get(discount_id)

    async def list_by_rate(self, rate_id: UUID) -> list[Discount]:
        return [d for d in self.discounts.values() if d.rate_id == rate_id]

    async def update(self, discount: Discount) -> Discount:
        self.discounts[discount.id] = discount
        return discount

    async def delete(self, discount_id: UUID) -> bool:
        if discount_id in self.discounts:
            del self.discounts[discount_id]
            return True
        return False


class MockRoomRepository:
    def __init__(self, rooms: list[Room] | None = None):
        self._rooms = rooms or []

    async def list_all(self, hotel_id: UUID | None = None) -> list[Room]:
        if hotel_id is not None:
            return [r for r in self._rooms if r.hotel_id == hotel_id]
        return list(self._rooms)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_rate(
    hotel_id: UUID | None = None,
    room_type: RoomType = RoomType.DOBLE,
    season: SeasonType = SeasonType.BASE,
    base_price: Decimal = Decimal("150.00"),
) -> Rate:
    return Rate(
        id=uuid4(),
        hotel_id=hotel_id or uuid4(),
        room_type=room_type,
        season=season,
        base_price=base_price,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _make_discount(
    rate_id: UUID,
    discount_type: DiscountType = DiscountType.PORCENTAJE,
    value: Decimal = Decimal("20.00"),
    active: bool = True,
) -> Discount:
    today = date.today()
    if active:
        start = today - timedelta(days=1)
        end = today + timedelta(days=1)
    else:
        start = today - timedelta(days=10)
        end = today - timedelta(days=5)
    return Discount(
        id=uuid4(),
        rate_id=rate_id,
        name="Test Discount",
        discount_type=discount_type,
        value=value,
        start_date=start,
        end_date=end,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ── Domain entity tests ────────────────────────────────────────────────────────

def test_discount_is_active_when_today_in_range():
    d = _make_discount(rate_id=uuid4(), active=True)
    assert d.is_active() is True


def test_discount_is_inactive_when_expired():
    d = _make_discount(rate_id=uuid4(), active=False)
    assert d.is_active() is False


def test_discount_apply_porcentaje():
    d = _make_discount(rate_id=uuid4(), discount_type=DiscountType.PORCENTAJE, value=Decimal("20"))
    result = d.apply(Decimal("100.00"))
    assert result == Decimal("80.00")


def test_discount_apply_fijo():
    d = _make_discount(rate_id=uuid4(), discount_type=DiscountType.FIJO, value=Decimal("30"))
    result = d.apply(Decimal("100.00"))
    assert result == Decimal("70.00")


def test_rate_effective_price_with_active_discount():
    rate = _make_rate(base_price=Decimal("100.00"))
    discount = _make_discount(rate.id, active=True, value=Decimal("10"))
    price, active = rate.effective_price([discount])
    assert price == Decimal("90.00")
    assert active == discount


def test_rate_effective_price_without_active_discount():
    rate = _make_rate(base_price=Decimal("100.00"))
    inactive = _make_discount(rate.id, active=False)
    price, active = rate.effective_price([inactive])
    assert price == Decimal("100.00")
    assert active is None


def test_rate_effective_price_no_discounts():
    rate = _make_rate(base_price=Decimal("200.00"))
    price, active = rate.effective_price([])
    assert price == Decimal("200.00")
    assert active is None


# ── CreateRateUseCase ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_rate_success():
    repo = MockRateRepository()
    use_case = CreateRateUseCase(repo)
    hotel_id = uuid4()

    result = await use_case.execute(
        CreateRateDTO(hotel_id=hotel_id, room_type=RoomType.DOBLE, season=SeasonType.BASE, base_price=Decimal("150.00"))
    )

    assert result.hotel_id == hotel_id
    assert result.room_type == RoomType.DOBLE
    assert result.base_price == Decimal("150.00")
    assert result.final_price == Decimal("150.00")
    assert result.active_discount is None


@pytest.mark.asyncio
async def test_create_rate_zero_price_raises():
    repo = MockRateRepository()
    use_case = CreateRateUseCase(repo)

    with pytest.raises(ValueError, match="positive"):
        await use_case.execute(
            CreateRateDTO(hotel_id=uuid4(), room_type=RoomType.DOBLE, season=SeasonType.BASE, base_price=Decimal("0"))
        )


@pytest.mark.asyncio
async def test_create_rate_negative_price_raises():
    repo = MockRateRepository()
    use_case = CreateRateUseCase(repo)

    with pytest.raises(ValueError, match="positive"):
        await use_case.execute(
            CreateRateDTO(hotel_id=uuid4(), room_type=RoomType.SUITE, season=SeasonType.ALTA, base_price=Decimal("-50"))
        )


@pytest.mark.asyncio
async def test_create_rate_duplicate_raises():
    hotel_id = uuid4()
    repo = MockRateRepository()
    existing = _make_rate(hotel_id=hotel_id, room_type=RoomType.DOBLE, season=SeasonType.BASE)
    repo.rates[existing.id] = existing
    use_case = CreateRateUseCase(repo)

    with pytest.raises(ValueError, match="already exists"):
        await use_case.execute(
            CreateRateDTO(hotel_id=hotel_id, room_type=RoomType.DOBLE, season=SeasonType.BASE, base_price=Decimal("200"))
        )


# ── GetRateUseCase ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_rate_success_no_discount():
    rate_repo = MockRateRepository()
    discount_repo = MockDiscountRepository()
    rate = _make_rate()
    rate_repo.rates[rate.id] = rate

    result = await GetRateUseCase(rate_repo, discount_repo).execute(rate.id)

    assert result.id == rate.id
    assert result.final_price == rate.base_price
    assert result.active_discount is None


@pytest.mark.asyncio
async def test_get_rate_success_with_active_discount():
    rate_repo = MockRateRepository()
    discount_repo = MockDiscountRepository()
    rate = _make_rate(base_price=Decimal("100.00"))
    discount = _make_discount(rate.id, active=True, value=Decimal("25"))
    rate_repo.rates[rate.id] = rate
    discount_repo.discounts[discount.id] = discount

    result = await GetRateUseCase(rate_repo, discount_repo).execute(rate.id)

    assert result.final_price == Decimal("75.00")
    assert result.active_discount is not None
    assert result.active_discount.is_active is True


@pytest.mark.asyncio
async def test_get_rate_not_found():
    with pytest.raises(ValueError, match="not found"):
        await GetRateUseCase(MockRateRepository(), MockDiscountRepository()).execute(uuid4())


# ── ListRatesUseCase ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_rates_returns_all_for_hotel():
    hotel_id = uuid4()
    rate_repo = MockRateRepository()
    discount_repo = MockDiscountRepository()
    rate1 = _make_rate(hotel_id=hotel_id, room_type=RoomType.DOBLE)
    rate2 = _make_rate(hotel_id=hotel_id, room_type=RoomType.SUITE)
    other = _make_rate(room_type=RoomType.INDIVIDUAL)  # otro hotel
    rate_repo.rates.update({rate1.id: rate1, rate2.id: rate2, other.id: other})

    results = await ListRatesUseCase(rate_repo, discount_repo).execute(hotel_id=hotel_id)

    assert len(results) == 2


@pytest.mark.asyncio
async def test_list_rates_filter_by_room_type():
    hotel_id = uuid4()
    rate_repo = MockRateRepository()
    discount_repo = MockDiscountRepository()
    rate1 = _make_rate(hotel_id=hotel_id, room_type=RoomType.DOBLE)
    rate2 = _make_rate(hotel_id=hotel_id, room_type=RoomType.SUITE)
    rate_repo.rates.update({rate1.id: rate1, rate2.id: rate2})

    results = await ListRatesUseCase(rate_repo, discount_repo).execute(hotel_id=hotel_id, room_type=RoomType.DOBLE)

    assert len(results) == 1
    assert results[0].room_type == RoomType.DOBLE


@pytest.mark.asyncio
async def test_list_rates_shows_active_discount():
    hotel_id = uuid4()
    rate_repo = MockRateRepository()
    discount_repo = MockDiscountRepository()
    rate = _make_rate(hotel_id=hotel_id, base_price=Decimal("100.00"))
    discount = _make_discount(rate.id, active=True, value=Decimal("10"))
    rate_repo.rates[rate.id] = rate
    discount_repo.discounts[discount.id] = discount

    results = await ListRatesUseCase(rate_repo, discount_repo).execute(hotel_id=hotel_id)

    assert results[0].final_price == Decimal("90.00")
    assert results[0].active_discount is not None


# ── UpdateRateUseCase ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_rate_success():
    rate_repo = MockRateRepository()
    rate = _make_rate(base_price=Decimal("100.00"))
    rate_repo.rates[rate.id] = rate

    result = await UpdateRateUseCase(rate_repo).execute(rate.id, UpdateRateDTO(base_price=Decimal("200.00")))

    assert result.base_price == Decimal("200.00")


@pytest.mark.asyncio
async def test_update_rate_not_found():
    with pytest.raises(ValueError, match="not found"):
        await UpdateRateUseCase(MockRateRepository()).execute(uuid4(), UpdateRateDTO(base_price=Decimal("100")))


@pytest.mark.asyncio
async def test_update_rate_zero_price_raises():
    rate_repo = MockRateRepository()
    rate = _make_rate()
    rate_repo.rates[rate.id] = rate

    with pytest.raises(ValueError, match="positive"):
        await UpdateRateUseCase(rate_repo).execute(rate.id, UpdateRateDTO(base_price=Decimal("0")))


# ── DeleteRateUseCase ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_rate_success():
    rate_repo = MockRateRepository()
    rate = _make_rate()
    rate_repo.rates[rate.id] = rate

    await DeleteRateUseCase(rate_repo).execute(rate.id)

    assert rate.id not in rate_repo.rates


@pytest.mark.asyncio
async def test_delete_rate_not_found():
    with pytest.raises(ValueError, match="not found"):
        await DeleteRateUseCase(MockRateRepository()).execute(uuid4())


# ── CreateDiscountUseCase ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_discount_porcentaje_success():
    rate_repo = MockRateRepository()
    discount_repo = MockDiscountRepository()
    rate = _make_rate(base_price=Decimal("100.00"))
    rate_repo.rates[rate.id] = rate
    today = date.today()

    result = await CreateDiscountUseCase(rate_repo, discount_repo).execute(
        CreateDiscountDTO(
            rate_id=rate.id,
            name="Promo",
            discount_type=DiscountType.PORCENTAJE,
            value=Decimal("20"),
            start_date=today,
            end_date=today + timedelta(days=5),
        )
    )

    assert result.rate_id == rate.id
    assert result.value == Decimal("20")


@pytest.mark.asyncio
async def test_create_discount_fijo_success():
    rate_repo = MockRateRepository()
    discount_repo = MockDiscountRepository()
    rate = _make_rate(base_price=Decimal("100.00"))
    rate_repo.rates[rate.id] = rate
    today = date.today()

    result = await CreateDiscountUseCase(rate_repo, discount_repo).execute(
        CreateDiscountDTO(
            rate_id=rate.id,
            name="Promo Fija",
            discount_type=DiscountType.FIJO,
            value=Decimal("30"),
            start_date=today,
            end_date=today + timedelta(days=3),
        )
    )

    assert result.discount_type == DiscountType.FIJO


@pytest.mark.asyncio
async def test_create_discount_rate_not_found():
    with pytest.raises(ValueError, match="not found"):
        await CreateDiscountUseCase(MockRateRepository(), MockDiscountRepository()).execute(
            CreateDiscountDTO(
                rate_id=uuid4(),
                name="X",
                discount_type=DiscountType.PORCENTAJE,
                value=Decimal("10"),
                start_date=date.today(),
                end_date=date.today() + timedelta(days=1),
            )
        )


@pytest.mark.asyncio
async def test_create_discount_invalid_dates():
    rate_repo = MockRateRepository()
    rate = _make_rate()
    rate_repo.rates[rate.id] = rate
    today = date.today()

    with pytest.raises(ValueError, match="start_date"):
        await CreateDiscountUseCase(rate_repo, MockDiscountRepository()).execute(
            CreateDiscountDTO(
                rate_id=rate.id,
                name="X",
                discount_type=DiscountType.PORCENTAJE,
                value=Decimal("10"),
                start_date=today + timedelta(days=2),
                end_date=today,
            )
        )


@pytest.mark.asyncio
async def test_create_discount_zero_value_raises():
    rate_repo = MockRateRepository()
    rate = _make_rate()
    rate_repo.rates[rate.id] = rate

    with pytest.raises(ValueError, match="positive"):
        await CreateDiscountUseCase(rate_repo, MockDiscountRepository()).execute(
            CreateDiscountDTO(
                rate_id=rate.id,
                name="X",
                discount_type=DiscountType.PORCENTAJE,
                value=Decimal("0"),
                start_date=date.today(),
                end_date=date.today() + timedelta(days=1),
            )
        )


@pytest.mark.asyncio
async def test_create_discount_price_becomes_zero_raises():
    """Escenario 3: descuento >= precio base debe rechazarse."""
    rate_repo = MockRateRepository()
    rate = _make_rate(base_price=Decimal("50.00"))
    rate_repo.rates[rate.id] = rate

    with pytest.raises(ValueError, match="zero or less"):
        await CreateDiscountUseCase(rate_repo, MockDiscountRepository()).execute(
            CreateDiscountDTO(
                rate_id=rate.id,
                name="X",
                discount_type=DiscountType.FIJO,
                value=Decimal("50"),  # precio final = 0
                start_date=date.today(),
                end_date=date.today() + timedelta(days=1),
            )
        )


@pytest.mark.asyncio
async def test_create_discount_price_goes_negative_raises():
    rate_repo = MockRateRepository()
    rate = _make_rate(base_price=Decimal("50.00"))
    rate_repo.rates[rate.id] = rate

    with pytest.raises(ValueError, match="zero or less"):
        await CreateDiscountUseCase(rate_repo, MockDiscountRepository()).execute(
            CreateDiscountDTO(
                rate_id=rate.id,
                name="X",
                discount_type=DiscountType.FIJO,
                value=Decimal("60"),  # precio final = -10
                start_date=date.today(),
                end_date=date.today() + timedelta(days=1),
            )
        )


# ── ListDiscountsUseCase ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_discounts_for_rate():
    discount_repo = MockDiscountRepository()
    rate_id = uuid4()
    d1 = _make_discount(rate_id, active=True)
    d2 = _make_discount(rate_id, active=False)
    other = _make_discount(uuid4(), active=True)
    discount_repo.discounts.update({d1.id: d1, d2.id: d2, other.id: other})

    results = await ListDiscountsUseCase(discount_repo).execute(rate_id)

    assert len(results) == 2
    ids = {r.id for r in results}
    assert d1.id in ids and d2.id in ids


@pytest.mark.asyncio
async def test_list_discounts_reflects_is_active():
    discount_repo = MockDiscountRepository()
    rate_id = uuid4()
    active = _make_discount(rate_id, active=True)
    inactive = _make_discount(rate_id, active=False)
    discount_repo.discounts.update({active.id: active, inactive.id: inactive})

    results = await ListDiscountsUseCase(discount_repo).execute(rate_id)

    by_id = {r.id: r for r in results}
    assert by_id[active.id].is_active is True
    assert by_id[inactive.id].is_active is False


# ── UpdateDiscountUseCase ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_discount_success():
    rate_repo = MockRateRepository()
    discount_repo = MockDiscountRepository()
    rate = _make_rate(base_price=Decimal("200.00"))
    discount = _make_discount(rate.id, value=Decimal("10"))
    rate_repo.rates[rate.id] = rate
    discount_repo.discounts[discount.id] = discount

    result = await UpdateDiscountUseCase(rate_repo, discount_repo).execute(
        discount.id, UpdateDiscountDTO(name="Updated Name", value=Decimal("20"))
    )

    assert result.name == "Updated Name"
    assert result.value == Decimal("20")


@pytest.mark.asyncio
async def test_update_discount_not_found():
    with pytest.raises(ValueError, match="not found"):
        await UpdateDiscountUseCase(MockRateRepository(), MockDiscountRepository()).execute(
            uuid4(), UpdateDiscountDTO(name="X")
        )


@pytest.mark.asyncio
async def test_update_discount_invalid_dates_raises():
    rate_repo = MockRateRepository()
    discount_repo = MockDiscountRepository()
    rate = _make_rate()
    today = date.today()
    discount = _make_discount(rate.id)
    rate_repo.rates[rate.id] = rate
    discount_repo.discounts[discount.id] = discount

    with pytest.raises(ValueError, match="start_date"):
        await UpdateDiscountUseCase(rate_repo, discount_repo).execute(
            discount.id,
            UpdateDiscountDTO(start_date=today + timedelta(days=5), end_date=today),
        )


@pytest.mark.asyncio
async def test_update_discount_price_becomes_zero_raises():
    rate_repo = MockRateRepository()
    discount_repo = MockDiscountRepository()
    rate = _make_rate(base_price=Decimal("50.00"))
    discount = _make_discount(rate.id, discount_type=DiscountType.FIJO, value=Decimal("10"))
    rate_repo.rates[rate.id] = rate
    discount_repo.discounts[discount.id] = discount

    with pytest.raises(ValueError, match="zero or less"):
        await UpdateDiscountUseCase(rate_repo, discount_repo).execute(
            discount.id, UpdateDiscountDTO(value=Decimal("50"))  # precio final = 0
        )


@pytest.mark.asyncio
async def test_update_discount_zero_value_raises():
    rate_repo = MockRateRepository()
    discount_repo = MockDiscountRepository()
    rate = _make_rate()
    discount = _make_discount(rate.id)
    rate_repo.rates[rate.id] = rate
    discount_repo.discounts[discount.id] = discount

    with pytest.raises(ValueError, match="positive"):
        await UpdateDiscountUseCase(rate_repo, discount_repo).execute(
            discount.id, UpdateDiscountDTO(value=Decimal("0"))
        )


# ── DeleteDiscountUseCase ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_discount_success():
    discount_repo = MockDiscountRepository()
    discount = _make_discount(uuid4())
    discount_repo.discounts[discount.id] = discount

    await DeleteDiscountUseCase(discount_repo).execute(discount.id)

    assert discount.id not in discount_repo.discounts


@pytest.mark.asyncio
async def test_delete_discount_not_found():
    with pytest.raises(ValueError, match="not found"):
        await DeleteDiscountUseCase(MockDiscountRepository()).execute(uuid4())


# ── GetEffectivePriceUseCase ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_effective_price_with_rate_and_active_discount():
    hotel_id = uuid4()
    rate_repo = MockRateRepository()
    discount_repo = MockDiscountRepository()
    rate = _make_rate(hotel_id=hotel_id, room_type=RoomType.DOBLE, base_price=Decimal("100.00"))
    discount = _make_discount(rate.id, active=True, value=Decimal("10"))
    rate_repo.rates[rate.id] = rate
    discount_repo.discounts[discount.id] = discount

    result = await GetEffectivePriceUseCase(rate_repo, discount_repo, MockRoomRepository()).execute(
        hotel_id=hotel_id, room_type=RoomType.DOBLE, season=SeasonType.BASE
    )

    assert result.base_price == Decimal("100.00")
    assert result.final_price == Decimal("90.00")
    assert result.has_discount is True
    assert result.discount_name == discount.name


@pytest.mark.asyncio
async def test_effective_price_with_rate_no_discount():
    hotel_id = uuid4()
    rate_repo = MockRateRepository()
    rate = _make_rate(hotel_id=hotel_id, room_type=RoomType.SUITE, base_price=Decimal("300.00"))
    rate_repo.rates[rate.id] = rate

    result = await GetEffectivePriceUseCase(rate_repo, MockDiscountRepository(), MockRoomRepository()).execute(
        hotel_id=hotel_id, room_type=RoomType.SUITE, season=SeasonType.BASE
    )

    assert result.final_price == Decimal("300.00")
    assert result.has_discount is False
    assert result.discount_name is None


@pytest.mark.asyncio
async def test_effective_price_fallback_to_room_price():
    hotel_id = uuid4()
    room = Room(
        id=uuid4(),
        hotel_id=hotel_id,
        name="Doble 101",
        room_type=RoomType.DOBLE,
        price=Decimal("80.00"),
        capacity=2,
        beds="2 Single",
        size=25.0,
        status=RoomStatus.DISPONIBLE,
        amenities="WiFi",
    )

    result = await GetEffectivePriceUseCase(
        MockRateRepository(), MockDiscountRepository(), MockRoomRepository(rooms=[room])
    ).execute(hotel_id=hotel_id, room_type=RoomType.DOBLE, season=SeasonType.BASE)

    assert result.season is None
    assert result.base_price == Decimal("80.00")
    assert result.final_price == Decimal("80.00")
    assert result.has_discount is False


@pytest.mark.asyncio
async def test_effective_price_fallback_no_room_returns_zero():
    result = await GetEffectivePriceUseCase(
        MockRateRepository(), MockDiscountRepository(), MockRoomRepository()
    ).execute(hotel_id=uuid4(), room_type=RoomType.INDIVIDUAL, season=SeasonType.BASE)

    assert result.final_price == Decimal("0")
    assert result.has_discount is False


@pytest.mark.asyncio
async def test_effective_price_with_inactive_discount():
    hotel_id = uuid4()
    rate_repo = MockRateRepository()
    discount_repo = MockDiscountRepository()
    rate = _make_rate(hotel_id=hotel_id, base_price=Decimal("100.00"))
    discount = _make_discount(rate.id, active=False, value=Decimal("20"))
    rate_repo.rates[rate.id] = rate
    discount_repo.discounts[discount.id] = discount

    result = await GetEffectivePriceUseCase(rate_repo, discount_repo, MockRoomRepository()).execute(
        hotel_id=hotel_id, room_type=rate.room_type, season=rate.season
    )

    assert result.final_price == Decimal("100.00")
    assert result.has_discount is False
