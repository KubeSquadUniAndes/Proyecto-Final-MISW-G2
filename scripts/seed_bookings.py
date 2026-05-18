#!/usr/bin/env python3
"""
Creates 100 bookings against a single room.

Usage:
    python scripts/seed_bookings.py --token <JWT_TOKEN>
"""

import argparse
import json
import ssl
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

BASE_URL = "https://k8s-workload-travelhu-f26ddf980b-5888409b6dd7c4c7.elb.us-east-1.amazonaws.com"
ROOM_ID  = "xxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
HOTEL_ID = "xxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"


def create_booking(token: str, payload: dict) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/reservas/api/v1/bookings/",
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, context=_SSL_CTX) as resp:
        return json.loads(resp.read())


def main():
    parser = argparse.ArgumentParser(description="Seed 100 bookings against one room")
    parser.add_argument("--token", required=True, help="JWT bearer token (traveler role)")
    parser.add_argument("--count", type=int, default=100, help="Number of bookings to create")
    args = parser.parse_args()

    # Each booking: check-in 15:00, check-out 11:00 four days later (3 nights).
    # Bookings are spaced 5 days apart so dates never overlap.
    base_start = datetime(2028, 1, 1, 15, 0, 0, tzinfo=timezone.utc)
    window = 5  # days between booking starts

    success, failed = 0, 0

    for i in range(args.count):
        start = base_start + timedelta(days=i * window)
        end   = start + timedelta(days=4, hours=-4)  # check-out at 11:00

        payload = {
            "hotel_id":         HOTEL_ID,
            "room_id":          ROOM_ID,
            "start_time":       start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_time":         end.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "room_type":        "Deluxe",
            "num_guests":       2,
            "price_per_night":  250000.00,
            "traveler_name":    f"Test User {i + 1}",
            "traveler_email":   f"test{i + 1}@example.com",
            "traveler_phone":   "+57 300 000 0000",
            "traveler_document":"1111111111",
            "notes":            "Prueba flujo completo",
            "special_requests": "Late check-in",
        }

        try:
            result = create_booking(args.token, payload)
            code = result.get("booking_code", result.get("id", "?"))
            print(f"[{i + 1}/{args.count}] OK  {code}  ({payload['start_time']} → {payload['end_time']})")
            success += 1
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            print(f"[{i + 1}/{args.count}] ERR {e.code}  {body[:200]}", file=sys.stderr)
            failed += 1
        except Exception as e:
            print(f"[{i + 1}/{args.count}] ERR {e}", file=sys.stderr)
            failed += 1

    print(f"\nDone: {success} created, {failed} failed.")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
