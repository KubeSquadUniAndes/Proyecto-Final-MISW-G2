# Test Instructions

## Base Configuration

```
BASE_URL=https://k8s-workload-travelhu-f26ddf980b-5888409b6dd7c4c7.elb.us-east-1.amazonaws.com
```

## User Registration

**Endpoint:** `POST {{base_url}}/users/api/v1/users/register`

**Description:** Register a new user account.

**Request Body:**

```json
{
  "first_name": "Newman",
  "last_name": "Test",
  "email": "{{test_email}}",
  "phone": "+57 300 000 0000",
  "country": "Colombia",
  "city": "Bogotá",
  "birth_date": "1995-01-01",
  "password": "{{test_password}}",
  "user_type": "traveler",
  "identification_type": "CC",
  "identification_number": "1111111111"
}
```

**Notes:** `user_type` can be either `traveler` or `hotel`.



## Create Booking

**Endpoint:** `POST {{base_url}}/reservas/api/v1/bookings/`

**Description:** Create a new booking for a hotel room.

**Request Body:**

**Notes:** only use the following ids for testing
```json
{
  "hotel_id": "80eeb63a-ad68-41d0-be1a-3d57f2ec4a67",
  "room_id": "2aa4f911-337e-46ed-b3af-ec1b8a434e8d",
  "start_time": "2026-05-01T15:00:00Z",
  "end_time": "2026-05-05T11:00:00Z",
  "room_type": "suite",
  "num_guests": 2,
  "price_per_night": 300000.00,
  "traveler_name": "Test User Moreno",
  "traveler_email": "test-moreno@example.com",
  "traveler_phone": "+573001234567",
  "traveler_document": "1234567890",
  "notes": "Test booking 1",
  "special_requests": "Late check-in"
}
```

## Get Room Details

**Endpoint:** `GET {{base_url}}/hospedajes/api/v1/rooms/{{room_id}}`

**Description:** Retrieve room information by room ID.