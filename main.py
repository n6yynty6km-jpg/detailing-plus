import os
import secrets

from typing import Literal
from fastapi import Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from database.database import SessionLocal
from database.models import Appointment, Client, Service
from pathlib import Path
from datetime import date, time

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.booking import get_available_slots, TIMEZONE
from backend.appointments import create_appointment

app = FastAPI(
    title="Detailing+ API",
    description="API для сайта детейлинг-центра Detailing+",
    version="1.0.0"
)


load_dotenv()

security = HTTPBasic()

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


def verify_admin(
    credentials: HTTPBasicCredentials = Depends(security)
):
    correct_username = (
        ADMIN_USERNAME is not None
        and secrets.compare_digest(
            credentials.username,
            ADMIN_USERNAME
        )
    )

    correct_password = (
        ADMIN_PASSWORD is not None
        and secrets.compare_digest(
            credentials.password,
            ADMIN_PASSWORD
        )
    )

    if not (correct_username and correct_password):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=401,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Basic"}
        )

    return credentials.username


class AppointmentStatusUpdate(BaseModel):
    status: Literal[
        "new",
        "confirmed",
        "completed",
        "cancelled"
    ]

from decimal import Decimal


class ServiceUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(max_length=1000)

    price_small: Decimal = Field(ge=0)
    price_medium: Decimal = Field(ge=0)
    price_large: Decimal = Field(ge=0)

    duration_minutes: int = Field(gt=0, le=1440)
    is_active: bool


@app.get("/api/admin/services")
def admin_services(
    admin: str = Depends(verify_admin)
):
    session = SessionLocal()

    try:
        services = session.query(Service).order_by(Service.id).all()

        return [
            {
                "id": service.id,
                "code": service.code,
                "name": service.name,
                "description": service.description or "",
                "price_small": str(service.price_small),
                "price_medium": str(service.price_medium),
                "price_large": str(service.price_large),
                "duration_minutes": service.duration_minutes,
                "is_active": service.is_active
            }
            for service in services
        ]

    finally:
        session.close()


@app.put("/api/admin/services/{service_id}")
def update_service(
    service_id: int,
    data: ServiceUpdate,
    admin: str = Depends(verify_admin)
):
    session = SessionLocal()

    try:
        service = session.query(Service).filter_by(
            id=service_id
        ).first()

        if service is None:
            raise HTTPException(
                status_code=404,
                detail="Услуга не найдена"
            )

        service.name = data.name
        service.description = data.description

        service.price_small = data.price_small
        service.price_medium = data.price_medium
        service.price_large = data.price_large

        service.duration_minutes = data.duration_minutes
        service.is_active = data.is_active

        session.commit()

        return {
            "success": True,
            "message": "Услуга обновлена",
            "service_id": service.id
        }

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


@app.get("/api/services")
def public_services():
    session = SessionLocal()

    try:
        services = session.query(Service).filter_by(
            is_active=True
        ).order_by(Service.id).all()

        return [
            {
                "code": service.code,
                "name": service.name,
                "description": service.description or "",
                "price_small": str(service.price_small),
                "price_medium": str(service.price_medium),
                "price_large": str(service.price_large)
            }
            for service in services
        ]

    finally:
        session.close()


class AppointmentRequest(BaseModel):
    client_name: str = Field(min_length=2, max_length=100)
    client_phone: str = Field(min_length=5, max_length=30)

    service_code: str
    car_brand: str = Field(min_length=1, max_length=100)
    car_model: str = Field(min_length=1, max_length=100)
    car_size: str

    appointment_date: date
    start_time: time

    comment: str | None = None

@app.get("/api/slots")
def available_slots(
    service_code: str,
    car_size: str,
    target_date: date
):
    try:
        slots = get_available_slots(
            service_code=service_code,
            car_size=car_size,
            target_date=target_date
        )

        return {
            "date": target_date.isoformat(),
            "slots": slots
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

@app.post("/api/appointments")
def add_appointment(data: AppointmentRequest):
    try:
        result = create_appointment(
            client_name=data.client_name,
            client_phone=data.client_phone,
            service_code=data.service_code,
            car_brand=data.car_brand,
            car_model=data.car_model,
            car_size=data.car_size,
            appointment_date=data.appointment_date,
            start_time=data.start_time,
            comment=data.comment
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )


@app.get("/api/admin/appointments")
def admin_appointments(
    admin: str = Depends(verify_admin)
):
    session = SessionLocal()

    try:
        records = (
            session.query(Appointment, Client, Service)
            .join(Client, Appointment.client_id == Client.id)
            .join(Service, Appointment.service_id == Service.id)
            .order_by(Appointment.start_at.desc())
            .all()
        )

        result = []

        for appointment, client, service in records:
            local_start = appointment.start_at.astimezone(TIMEZONE)
            local_end = appointment.end_at.astimezone(TIMEZONE)
            result.append({
                "id": appointment.id,
                "client_name": client.name,
                "client_phone": client.phone,
                "car": (
                    f"{appointment.car_brand} "
                    f"{appointment.car_model}"
                ),
                "car_size": appointment.car_size,
                "service": service.name,
                "date": local_start.strftime("%d.%m.%Y"),
                "start": local_start.strftime("%H:%M"),
                "end": local_end.strftime("%H:%M"),
                "price": str(appointment.estimated_price),
                "status": appointment.status,
                "comment": appointment.comment
            })

        return result

    finally:
        session.close()


@app.put("/api/admin/appointments/{appointment_id}/status")
def update_appointment_status(
    appointment_id: int,
    data: AppointmentStatusUpdate,
    admin: str = Depends(verify_admin)
):
    session = SessionLocal()

    try:
        appointment = session.query(Appointment).filter_by(
            id=appointment_id
        ).first()

        if appointment is None:
            raise HTTPException(
                status_code=404,
                detail="Заявка не найдена"
            )

        appointment.status = data.status
        session.commit()

        return {
            "success": True,
            "appointment_id": appointment.id,
            "status": appointment.status
        }

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


@app.get("/admin", include_in_schema=False)
def admin_page():
    return FileResponse(
        frontend_path / "admin.html"
    )


frontend_path = Path(__file__).resolve().parent / "frontend"

app.mount(
    "/",
    StaticFiles(directory=frontend_path, html=True),
    name="frontend"
)