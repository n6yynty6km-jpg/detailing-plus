
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Numeric,
    DateTime,
    CheckConstraint,
    ForeignKey,
)
from sqlalchemy.sql import func

from database.database import Base


# Таблица услуг
class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text)

    # Демонстрационные цены для разных размеров автомобиля
    price_small = Column(Numeric(10, 2), nullable=False)
    price_medium = Column(Numeric(10, 2), nullable=False)
    price_large = Column(Numeric(10, 2), nullable=False)

    duration_minutes = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint(
            "price_small >= 0 AND price_medium >= 0 AND price_large >= 0",
            name="check_service_prices"
        ),
        CheckConstraint(
            "duration_minutes > 0",
            name="check_service_duration"
        ),
    )


# Таблица клиентов
class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(30), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Таблица заявок на обслуживание
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)

    # Связь с клиентом и выбранной услугой
    client_id = Column(
        Integer,
        ForeignKey("clients.id"),
        nullable=False
    )

    service_id = Column(
        Integer,
        ForeignKey("services.id"),
        nullable=False
    )

    # Информация об автомобиле
    car_brand = Column(String(100), nullable=False)
    car_model = Column(String(100), nullable=False)
    car_size = Column(String(20), nullable=False)

    # Дата и время обслуживания
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=False)

    # Стоимость на момент оформления заявки
    estimated_price = Column(Numeric(10, 2), nullable=False)

    # Статус заявки
    status = Column(String(20), default="new", nullable=False)

    comment = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "car_size IN ('small', 'medium', 'large')",
            name="check_appointment_car_size"
        ),
        CheckConstraint(
            "status IN ('new', 'confirmed', 'completed', 'cancelled')",
            name="check_appointment_status"
        ),
        CheckConstraint(
            "end_at > start_at",
            name="check_appointment_time"
        ),
        CheckConstraint(
            "estimated_price >= 0",
            name="check_appointment_price"
        ),
    )

