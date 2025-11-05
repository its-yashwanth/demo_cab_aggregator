from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..database import get_session
from ..models import Ride, User
from ..utils.audit import log_action
from ..utils.jwt_handler import get_current_user
from ..crud import find_available_driver, get_user_by_email, haversine_distance
from pydantic import BaseModel
from datetime import datetime
import os

router = APIRouter(prefix="/rides", tags=["rides"])

class FareEstReq(BaseModel):
    pickup_lat: float
    pickup_lon: float
    drop_lat: float
    drop_lon: float

class BookReq(FareEstReq):
    email: str
    pickup: str
    drop: str

class ScheduleReq(BookReq):
    scheduled_time: str  # ISO Format

class RateReq(BaseModel):
    ride_id: int
    rating: int

BASE_FARE = float(os.environ.get("BASE_FARE", 50.0))
PER_KM_RATE = float(os.environ.get("PER_KM_RATE", 12.5))

@router.post("/estimate_fare", response_model=dict)
def estimate_fare(payload: FareEstReq):
    distance = haversine_distance(
        payload.pickup_lon, payload.pickup_lat,
        payload.drop_lon, payload.drop_lat
    )
    estimated_fare = BASE_FARE + (distance * PER_KM_RATE)
    
    return {
        "estimated_fare": round(estimated_fare, 2),
        "distance_km": round(distance, 2)
    }

@router.post("/book")
def book_ride(
    payload: BookReq, 
    session: Session = Depends(get_session),
    user_payload: dict = Depends(get_current_user)):
    
    if user_payload.get("sub") != payload.email:
        raise HTTPException(403, "You can only book rides for your own account")
        
    passenger = get_user_by_email(session, payload.email)
    if not passenger or not passenger.is_active:
        raise HTTPException(404, "Active passenger not found")
    
    driver = find_available_driver(session, payload.pickup_lat, payload.pickup_lon)
    
    ride = Ride(
        passenger_id=passenger.id, 
        driver_id=(driver.id if driver else None),
        pickup=payload.pickup, 
        drop=payload.drop,
        pickup_latitude=payload.pickup_lat,
        pickup_longitude=payload.pickup_lon,
        drop_latitude=payload.drop_lat,
        drop_longitude=payload.drop_lon,
        status="assigned" if driver else "requested"
    )
    session.add(ride); session.commit(); session.refresh(ride)
    log_action(payload.email, "BOOK_RIDE", f"ride_id={ride.id}, driver_id={ride.driver_id}")
    return {"ride_id": ride.id, "driver_assigned": bool(driver)}

@router.post("/schedule")
def schedule_ride(
    payload: ScheduleReq, 
    session: Session = Depends(get_session),
    user_payload: dict = Depends(get_current_user)):
    
    if user_payload.get("sub") != payload.email:
        raise HTTPException(403, "You can only schedule rides for your own account")
        
    passenger = get_user_by_email(session, payload.email)
    if not passenger:
        raise HTTPException(404, "Passenger not found")
        
    sched = datetime.fromisoformat(payload.scheduled_time)
    ride = Ride(
        passenger_id=passenger.id, 
        pickup=payload.pickup, 
        drop=payload.drop,
        pickup_latitude=payload.pickup_lat,
        pickup_longitude=payload.pickup_lon,
        drop_latitude=payload.drop_lat,
        drop_longitude=payload.drop_lon,
        scheduled_time=sched, 
        status="scheduled"
    )
    session.add(ride); session.commit(); session.refresh(ride)
    log_action(payload.email, "SCHEDULE_RIDE", f"ride_id={ride.id}")
    return {"ride_id": ride.id, "status": ride.status}

@router.get("/history/{email}")
def trip_history(
    email: str, 
    session: Session = Depends(get_session),
    user_payload: dict = Depends(get_current_user)):
    
    if user_payload.get("sub") != email:
        raise HTTPException(403, "You can only view your own history")
        
    user = get_user_by_email(session, email)
    if not user:
        raise HTTPException(404, "User not found")
        
    rides = session.exec(select(Ride).where(Ride.passenger_id == user.id)).all()
    return rides

@router.post("/rate")
def rate_driver(
    payload: RateReq, 
    session: Session = Depends(get_session),
    user_payload: dict = Depends(get_current_user)):
    
    ride = session.get(Ride, payload.ride_id)
    if not ride:
        raise HTTPException(404, "Ride not found")
    
    if ride.passenger_id != user_payload.get("id"):
        raise HTTPException(403, "You can only rate rides you took")
        
    if not ride.driver_id:
        raise HTTPException(400, "This ride had no driver to rate")
        
    driver = session.get(User, ride.driver_id)
    if not driver:
        raise HTTPException(404, "Driver not found")
        
    driver.rating_total += payload.rating
    driver.rating_count += 1
    session.add(driver); session.commit()
    
    avg = driver.rating_total / max(1, driver.rating_count)
    log_action(user_payload.get("sub"), "RATE_DRIVER", f"driver_id={driver.id},avg={avg}")
    return {"driver_id": driver.id, "avg_rating": round(avg, 2)}