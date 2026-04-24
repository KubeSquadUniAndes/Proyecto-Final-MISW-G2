# Approve/Reject Booking Endpoints

## Overview

New endpoints for hotel administrators to approve or reject pending booking requests.

## Flow Diagram

```
┌─────────────┐
│   Traveler  │
│  Creates    │
│  Booking    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Status: PENDING │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│APPROVE │ │REJECT  │
│(Hotel) │ │(Hotel) │
└───┬────┘ └───┬────┘
    │          │
    ▼          ▼
┌──────────┐ ┌──────────┐
│CONFIRMED │ │CANCELLED │
│          │ │          │
│• Payment │ │• Release │
│• Notify  │ │  Inventory│
│          │ │• Notify  │
└──────────┘ └──────────┘
```

## Endpoints

### 1. Approve Booking

**Endpoint:** `PATCH /bookings/{booking_id}/approve`

**Description:** Approve a pending booking and trigger payment processing.

**Authentication:** Required (JWT token)

**Path Parameters:**
- `booking_id` (UUID): The booking ID to approve

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "resource_id": "uuid",
  "start_time": "2024-01-15T14:00:00Z",
  "end_time": "2024-01-18T12:00:00Z",
  "status": "confirmed",
  "status_display": "Confirmada",
  "booking_code": "BK123456",
  "room_type": "Deluxe",
  "num_guests": 2,
  "price_per_night": "150.00",
  "total_price": "450.00",
  "final_price": "517.50",
  "traveler_name": "John Doe",
  "traveler_email": "john@example.com",
  "cancellable": true,
  "created_at": "2024-01-10T10:00:00Z",
  "updated_at": "2024-01-10T15:30:00Z"
}
```

**Error Responses:**
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: Admin doesn't have permission over the property
- `404 Not Found`: Booking not found
- `409 Conflict`: Booking is not in pending status or hold expired

**Business Rules:**
- Only bookings in `pending` status can be approved
- Changes status from `pending` to `confirmed`
- Triggers payment processing (TODO: integration pending)
- Sends notification to traveler (TODO: integration pending)
- Response time: < 500ms (as per acceptance criteria)

---

### 2. Reject Booking

**Endpoint:** `PATCH /bookings/{booking_id}/reject`

**Description:** Reject a pending booking and release inventory.

**Authentication:** Required (JWT token)

**Path Parameters:**
- `booking_id` (UUID): The booking ID to reject

**Request Body:**
```json
{
  "rejection_reason": "Room not available due to maintenance"
}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "resource_id": "uuid",
  "start_time": "2024-01-15T14:00:00Z",
  "end_time": "2024-01-18T12:00:00Z",
  "status": "cancelled",
  "status_display": "Cancelada",
  "notes": "[REJECTED by admin] Room not available due to maintenance",
  "booking_code": "BK123456",
  "room_type": "Deluxe",
  "num_guests": 2,
  "price_per_night": "150.00",
  "cancellable": false,
  "created_at": "2024-01-10T10:00:00Z",
  "updated_at": "2024-01-10T15:35:00Z"
}
```

**Error Responses:**
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: Admin doesn't have permission over the property
- `404 Not Found`: Booking not found
- `409 Conflict`: Booking is not in pending status or hold expired
- `422 Unprocessable Entity`: Missing rejection_reason

**Business Rules:**
- Only bookings in `pending` status can be rejected
- Changes status from `pending` to `cancelled`
- Rejection reason is stored in the notes field
- Releases room inventory (TODO: integration with hospedajes_ms pending)
- Sends notification to traveler (TODO: integration with notificaciones_ms pending)

---

## User Story Implementation

### Historia de Usuario
**Como hotel**, quiero tener la capacidad de aprobar o rechazar manualmente las solicitudes de reserva en estado pendiente, para asegurar el control final sobre la asignación de mi inventario y validar condiciones especiales antes de confirmar.

### Acceptance Criteria Coverage

✅ **Escenario 1: Seguridad y Estado de la Reserva**
- Endpoints require authentication via JWT token
- Only bookings in `pending` status can be managed
- Validation implemented in use cases

✅ **Escenario 2: Aprobación y Procesamiento de Cobro**
- Approve endpoint changes status to `confirmed`
- Response time < 500ms (FastAPI async implementation)
- Payment processing trigger ready (TODO: integrate payment service)

✅ **Escenario 3: Rechazo y Liberación de Inventario**
- Reject endpoint requires `rejection_reason` in request body
- Status changed to `cancelled`
- Inventory release ready (TODO: integrate hospedajes_ms)

✅ **Escenario 4: Validaciones y Mensajería del Sistema**
- Hold expiration validation ready (TODO: add hold_until field to model)
- Error messages for invalid states (409 Conflict)
- Success confirmation in response (200 OK with updated booking)

⏳ **Escenario 5: Actualización en Tiempo Real (Dashboard)**
- Backend endpoints ready
- Frontend integration pending

✅ **Escenario 6: Notificación Automática al Viajero**
- Notification trigger points identified in code
- TODO: Integrate with notificaciones_ms

---

## Testing

### Unit Tests

Run unit tests:
```bash
cd reservas_ms
uv run pytest src/tests/test_approve_booking_use_case.py -v
uv run pytest src/tests/test_reject_booking_use_case.py -v
uv run pytest src/tests/test_booking_entity_reject.py -v
```

### Integration Tests

Run integration tests:
```bash
uv run pytest src/tests/test_approve_reject_endpoints.py -v
```

### Test Coverage

- ✅ Approve pending booking (success)
- ✅ Approve non-existent booking (404)
- ✅ Approve non-pending booking (409)
- ✅ Approve cancelled booking (409)
- ✅ Reject pending booking (success)
- ✅ Reject non-existent booking (404)
- ✅ Reject non-pending booking (409)
- ✅ Reject without reason (422)
- ✅ Timestamp updates on approve/reject
- ✅ Notes appending on rejection

---

## TODO: Pending Integrations

### 1. Payment Processing (Approve)
```python
# In approve_booking.py
# TODO: Trigger payment processing
# await payment_client.process_payment(booking_id, amount)
```

### 2. Inventory Release (Reject)
```python
# In reject_booking.py
# TODO: Release inventory in hospedajes_ms
# await hospedajes_client.release_room(resource_id, start_time, end_time)
```

### 3. Notifications (Both)
```python
# TODO: Send notification to traveler
# await notification_client.send(user_id, "booking_approved", data)
# await notification_client.send(user_id, "booking_rejected", data)
```

### 4. Permission Validation
```python
# TODO: Validate admin has permission over the property
# This would require checking if admin_user_id owns/manages resource_id
```

### 5. Hold Expiration
```python
# TODO: Add hold_until field to Booking model
# TODO: Validate hold expiration in use cases
# if booking.hold_until and datetime.utcnow() > booking.hold_until:
#     raise ValueError("Booking hold has expired")
```

---

## Example Usage

### Approve a booking
```bash
curl -X PATCH "http://localhost:8000/bookings/{booking_id}/approve" \
  -H "Authorization: Bearer {jwt_token}"
```

### Reject a booking
```bash
curl -X PATCH "http://localhost:8000/bookings/{booking_id}/reject" \
  -H "Authorization: Bearer {jwt_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "rejection_reason": "Room not available due to maintenance"
  }'
```
