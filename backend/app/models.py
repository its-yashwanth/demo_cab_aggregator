from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timedelta

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = None
    email: str = Field(index=True, unique=True)
    password: str
    role: str = Field(default="passenger")
    
    is_active: bool = Field(default=False) # Must verify with OTP
    failed_attempts: int = Field(default=0)
    
    rating_total: int = Field(default=0)
    rating_count: int = Field(default=0)
    
    # OTP Fields
    otp: Optional[str] = None
    otp_expires: Optional[datetime] = None
    
    # Geolocation for Drivers
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class DriverDocument(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    doc_type: str
    file_path: str
    approved: bool = Field(default=False)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

class Ride(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    passenger_id: int = Field(foreign_key="user.id")
    driver_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    pickup: str
    drop: str
    pickup_latitude: float
    pickup_longitude: float
    drop_latitude: float
    drop_longitude: float
    
    fare: Optional[float] = Field(default=0.0)
    status: str = Field(default="requested") # requested, assigned, completed, cancelled
    scheduled_time: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Payment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ride_id: int = Field(foreign_key="ride.id")
    user_email: str
    amount: float
    method: str
    status: str = Field(default="completed")
    timestamp: datetime = Field(default_factory=datetime.utcnow)