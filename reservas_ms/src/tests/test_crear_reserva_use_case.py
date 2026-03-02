"""Tests del caso de uso CrearReserva con mocks."""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.dtos.reserva_dto import CrearReservaDTO
from src.application.use_cases.crear_reserva import CrearReservaUseCase
from src.domain.entities.reserva import Reserva, ReservaEstado
from src.domain.services.reserva_domain_service import ReservaDomainService


@pytest.fixture
def usuario_id():
    return uuid4()


@pytest.fixture
def recurso_id():
    return uuid4()


@pytest.fixture
def fechas_validas():
    ahora = datetime.utcnow()
    return ahora + timedelta(hours=1), ahora + timedelta(hours=3)


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.listar_por_usuario.return_value = []
    return repo


@pytest.fixture
def use_case(mock_repo):
    domain_service = ReservaDomainService(mock_repo)
    return CrearReservaUseCase(mock_repo, domain_service)


@pytest.mark.asyncio
async def test_crear_reserva_exitosa(use_case, mock_repo, usuario_id, recurso_id, fechas_validas):
    fecha_inicio, fecha_fin = fechas_validas

    # Arrange
    reserva_esperada = Reserva(
        usuario_id=usuario_id,
        recurso_id=recurso_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )
    mock_repo.guardar.return_value = reserva_esperada

    dto = CrearReservaDTO(
        usuario_id=usuario_id,
        recurso_id=recurso_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )

    # Act
    result = await use_case.ejecutar(dto)

    # Assert
    assert result.usuario_id == usuario_id
    assert result.recurso_id == recurso_id
    assert result.estado == ReservaEstado.PENDIENTE
    mock_repo.guardar.assert_called_once()


@pytest.mark.asyncio
async def test_crear_reserva_con_conflicto_de_horario(
    use_case, mock_repo, usuario_id, recurso_id, fechas_validas
):
    fecha_inicio, fecha_fin = fechas_validas

    # Arrange: ya existe una reserva en el mismo horario
    reserva_existente = Reserva(
        usuario_id=usuario_id,
        recurso_id=recurso_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )
    mock_repo.listar_por_usuario.return_value = [reserva_existente]

    dto = CrearReservaDTO(
        usuario_id=usuario_id,
        recurso_id=recurso_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )

    # Act & Assert
    with pytest.raises(ValueError, match="conflicto de horario"):
        await use_case.ejecutar(dto)

    mock_repo.guardar.assert_not_called()
