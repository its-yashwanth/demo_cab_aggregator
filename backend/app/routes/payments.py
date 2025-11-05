from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session, select
from ..database import get_session
from ..models import Payment, Ride, User
from ..utils.audit import log_action
from ..utils.jwt_handler import get_current_user

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/")
def process_payment(
    payment_data: dict = Body(...), 
    session: Session = Depends(get_session),
    user_payload: dict = Depends(get_current_user)):
    
    ride_id = int(payment_data.get("ride_id", 0))
    ride = session.get(Ride, ride_id)
    if not ride:
        raise HTTPException(404, "Ride not found")
    
    if ride.passenger_id != user_payload.get("id"):
        raise HTTPException(403, "You can only pay for your own rides")

    payment = Payment(
        ride_id=ride_id,
        user_email=user_payload.get("sub"),
        amount=float(payment_data.get("amount", 0.0)),
        method=payment_data.get("method", "UPI"),
        status="completed"
    )
    session.add(payment); session.commit(); session.refresh(payment)
    
    ride.fare = payment.amount
    ride.status = "completed"
    session.add(ride); session.commit()
    
    log_action(payment.user_email, "PAYMENT", f"ride={ride_id},amount={payment.amount}")
    return {"status": "paid", "payment_id": payment.id}

@router.get("/receipt/{ride_id}")
def get_receipt(
    ride_id: int, 
    session: Session = Depends(get_session),
    user_payload: dict = Depends(get_current_user)):
    
    ride = session.get(Ride, ride_id)
    if not ride:
        raise HTTPException(404, "Ride not found")
        
    if ride.passenger_id != user_payload.get("id") and user_payload.get("role") != "admin":
        raise HTTPException(403, "Access denied")

    payment = session.exec(select(Payment).where(Payment.ride_id == ride.id)).first()
    passenger = session.get(User, ride.passenger_id)
    driver = session.get(User, ride.driver_id) if ride.driver_id else None
    
    if not payment:
        raise HTTPException(404, "Payment for this ride not found")

    return {
        "receipt_id": f"RCPT-{payment.id}",
        "ride_id": ride.id,
        "passenger_name": passenger.name if passenger else "N/A",
        "passenger_email": passenger.email if passenger else "N/A",
        "driver_name": driver.name if driver else "N/A",
        "driver_email": driver.email if driver else "N/A",
        "pickup": ride.pickup,
        "drop": ride.drop,
        "fare": ride.fare,
        "payment_method": payment.method,
        "paid_at": payment.timestamp,
        "status": ride.status,
        "ride_start_time": ride.created_at
    }