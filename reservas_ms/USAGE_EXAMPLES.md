# Ejemplos de Uso - Approve/Reject Endpoints

## Variables de Entorno

```bash
export BASE_URL="http://localhost:8000"
export JWT_TOKEN="your-jwt-token-here"
export BOOKING_ID="550e8400-e29b-41d4-a716-446655440000"
```

## 1. Crear una Reserva (Prerequisito)

```bash
curl -X POST "${BASE_URL}/bookings/" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_id": "123e4567-e89b-12d3-a456-426614174000",
    "start_time": "2024-06-15T14:00:00Z",
    "end_time": "2024-06-18T12:00:00Z",
    "room_type": "Deluxe",
    "num_guests": 2,
    "price_per_night": "150.00",
    "traveler_name": "Juan Pérez",
    "traveler_email": "juan@example.com",
    "traveler_phone": "+57 300 123 4567",
    "traveler_document": "CC 1234567890",
    "notes": "Llegada tarde, después de las 10pm"
  }'
```

**Respuesta esperada:** Status `201 Created` con booking en estado `pending`

---

## 2. Listar Reservas Pendientes

```bash
curl -X GET "${BASE_URL}/bookings/" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

**Filtrar solo pendientes (en frontend):**
```javascript
const pendingBookings = bookings.filter(b => b.status === 'pending');
```

---

## 3. Aprobar una Reserva

### Curl
```bash
curl -X PATCH "${BASE_URL}/bookings/${BOOKING_ID}/approve" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -v
```

### HTTPie
```bash
http PATCH "${BASE_URL}/bookings/${BOOKING_ID}/approve" \
  "Authorization: Bearer ${JWT_TOKEN}"
```

### Python (requests)
```python
import requests

response = requests.patch(
    f"{BASE_URL}/bookings/{BOOKING_ID}/approve",
    headers={"Authorization": f"Bearer {JWT_TOKEN}"}
)

if response.status_code == 200:
    booking = response.json()
    print(f"Booking approved: {booking['status']}")
else:
    print(f"Error: {response.json()['detail']}")
```

### JavaScript (fetch)
```javascript
const response = await fetch(
  `${BASE_URL}/bookings/${BOOKING_ID}/approve`,
  {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${JWT_TOKEN}`
    }
  }
);

if (response.ok) {
  const booking = await response.json();
  console.log('Booking approved:', booking.status);
} else {
  const error = await response.json();
  console.error('Error:', error.detail);
}
```

**Respuesta exitosa (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "resource_id": "123e4567-e89b-12d3-a456-426614174000",
  "start_time": "2024-06-15T14:00:00Z",
  "end_time": "2024-06-18T12:00:00Z",
  "status": "confirmed",
  "status_display": "Confirmada",
  "booking_code": "BK789012",
  "room_type": "Deluxe",
  "num_guests": 2,
  "price_per_night": "150.00",
  "total_nights": 3,
  "total_price": "450.00",
  "taxes": "67.50",
  "final_price": "517.50",
  "traveler_name": "Juan Pérez",
  "traveler_email": "juan@example.com",
  "traveler_phone": "+57 300 123 4567",
  "cancellable": true,
  "created_at": "2024-06-10T10:00:00Z",
  "updated_at": "2024-06-10T15:30:45Z"
}
```

**Errores posibles:**

```bash
# 404 - Booking no encontrado
{
  "detail": "Booking 550e8400-e29b-41d4-a716-446655440000 not found"
}

# 409 - Booking no está en pending
{
  "detail": "Cannot approve booking with status 'confirmed'. Only pending bookings can be approved."
}

# 401 - Token inválido o expirado
{
  "detail": "Could not validate credentials"
}
```

---

## 4. Rechazar una Reserva

### Curl
```bash
curl -X PATCH "${BASE_URL}/bookings/${BOOKING_ID}/reject" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "rejection_reason": "Habitación no disponible por mantenimiento programado"
  }' \
  -v
```

### HTTPie
```bash
http PATCH "${BASE_URL}/bookings/${BOOKING_ID}/reject" \
  "Authorization: Bearer ${JWT_TOKEN}" \
  rejection_reason="Habitación no disponible por mantenimiento programado"
```

### Python (requests)
```python
import requests

response = requests.patch(
    f"{BASE_URL}/bookings/{BOOKING_ID}/reject",
    headers={
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    },
    json={
        "rejection_reason": "Habitación no disponible por mantenimiento programado"
    }
)

if response.status_code == 200:
    booking = response.json()
    print(f"Booking rejected: {booking['status']}")
    print(f"Reason: {booking['notes']}")
else:
    print(f"Error: {response.json()['detail']}")
```

### JavaScript (fetch)
```javascript
const response = await fetch(
  `${BASE_URL}/bookings/${BOOKING_ID}/reject`,
  {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${JWT_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      rejection_reason: 'Habitación no disponible por mantenimiento programado'
    })
  }
);

if (response.ok) {
  const booking = await response.json();
  console.log('Booking rejected:', booking.status);
  console.log('Reason:', booking.notes);
} else {
  const error = await response.json();
  console.error('Error:', error.detail);
}
```

**Respuesta exitosa (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "resource_id": "123e4567-e89b-12d3-a456-426614174000",
  "start_time": "2024-06-15T14:00:00Z",
  "end_time": "2024-06-18T12:00:00Z",
  "status": "cancelled",
  "status_display": "Cancelada",
  "notes": "Llegada tarde, después de las 10pm\n[REJECTED by admin] Habitación no disponible por mantenimiento programado",
  "booking_code": "BK789012",
  "room_type": "Deluxe",
  "num_guests": 2,
  "price_per_night": "150.00",
  "cancellable": false,
  "created_at": "2024-06-10T10:00:00Z",
  "updated_at": "2024-06-10T15:35:22Z"
}
```

**Errores posibles:**

```bash
# 422 - Falta rejection_reason
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "rejection_reason"],
      "msg": "Field required"
    }
  ]
}

# 404 - Booking no encontrado
{
  "detail": "Booking 550e8400-e29b-41d4-a716-446655440000 not found"
}

# 409 - Booking no está en pending
{
  "detail": "Cannot reject booking with status 'confirmed'. Only pending bookings can be rejected."
}
```

---

## 5. Verificar el Cambio de Estado

```bash
curl -X GET "${BASE_URL}/bookings/${BOOKING_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

---

## 6. Casos de Prueba Completos

### Caso 1: Flujo Exitoso de Aprobación
```bash
# 1. Crear booking
BOOKING_ID=$(curl -s -X POST "${BASE_URL}/bookings/" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_id": "123e4567-e89b-12d3-a456-426614174000",
    "start_time": "2024-06-15T14:00:00Z",
    "end_time": "2024-06-18T12:00:00Z",
    "room_type": "Deluxe",
    "num_guests": 2,
    "price_per_night": "150.00",
    "traveler_name": "Test User",
    "traveler_email": "test@example.com"
  }' | jq -r '.id')

echo "Created booking: ${BOOKING_ID}"

# 2. Verificar estado pending
curl -s -X GET "${BASE_URL}/bookings/${BOOKING_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  | jq '.status'

# 3. Aprobar
curl -X PATCH "${BASE_URL}/bookings/${BOOKING_ID}/approve" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# 4. Verificar estado confirmed
curl -s -X GET "${BASE_URL}/bookings/${BOOKING_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  | jq '.status'
```

### Caso 2: Flujo Exitoso de Rechazo
```bash
# 1. Crear booking
BOOKING_ID=$(curl -s -X POST "${BASE_URL}/bookings/" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "resource_id": "123e4567-e89b-12d3-a456-426614174000",
    "start_time": "2024-06-20T14:00:00Z",
    "end_time": "2024-06-23T12:00:00Z",
    "room_type": "Standard",
    "num_guests": 1,
    "price_per_night": "100.00",
    "traveler_name": "Test User 2",
    "traveler_email": "test2@example.com"
  }' | jq -r '.id')

echo "Created booking: ${BOOKING_ID}"

# 2. Rechazar
curl -X PATCH "${BASE_URL}/bookings/${BOOKING_ID}/reject" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "rejection_reason": "Overbooking - no hay disponibilidad"
  }'

# 3. Verificar estado cancelled y notas
curl -s -X GET "${BASE_URL}/bookings/${BOOKING_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  | jq '{status: .status, notes: .notes}'
```

### Caso 3: Error - Aprobar booking ya confirmado
```bash
# Intentar aprobar dos veces
curl -X PATCH "${BASE_URL}/bookings/${BOOKING_ID}/approve" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# Segunda vez debería fallar con 409
curl -X PATCH "${BASE_URL}/bookings/${BOOKING_ID}/approve" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

---

## 7. Postman Collection

### Approve Booking Request
```json
{
  "name": "Approve Booking",
  "request": {
    "method": "PATCH",
    "header": [
      {
        "key": "Authorization",
        "value": "Bearer {{jwt_token}}",
        "type": "text"
      }
    ],
    "url": {
      "raw": "{{base_url}}/bookings/{{booking_id}}/approve",
      "host": ["{{base_url}}"],
      "path": ["bookings", "{{booking_id}}", "approve"]
    }
  },
  "response": []
}
```

### Reject Booking Request
```json
{
  "name": "Reject Booking",
  "request": {
    "method": "PATCH",
    "header": [
      {
        "key": "Authorization",
        "value": "Bearer {{jwt_token}}",
        "type": "text"
      },
      {
        "key": "Content-Type",
        "value": "application/json",
        "type": "text"
      }
    ],
    "body": {
      "mode": "raw",
      "raw": "{\n  \"rejection_reason\": \"Habitación no disponible\"\n}"
    },
    "url": {
      "raw": "{{base_url}}/bookings/{{booking_id}}/reject",
      "host": ["{{base_url}}"],
      "path": ["bookings", "{{booking_id}}", "reject"]
    }
  },
  "response": []
}
```

### Environment Variables
```json
{
  "name": "TravelHub Local",
  "values": [
    {
      "key": "base_url",
      "value": "http://localhost:8000",
      "enabled": true
    },
    {
      "key": "jwt_token",
      "value": "",
      "enabled": true
    },
    {
      "key": "booking_id",
      "value": "",
      "enabled": true
    }
  ]
}
```

---

## 8. Tests Automatizados con Newman

```bash
# Instalar newman
npm install -g newman

# Ejecutar colección
newman run postman/approve-reject-collection.json \
  -e postman/local-environment.json \
  --reporters cli,json \
  --reporter-json-export results.json
```

---

## Notas

- Todos los endpoints requieren autenticación JWT
- Los UUIDs deben ser válidos (formato UUID v4)
- El campo `rejection_reason` es obligatorio para reject
- Los timestamps deben estar en formato ISO 8601
- Las respuestas incluyen el booking completo actualizado
