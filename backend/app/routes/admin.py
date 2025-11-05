from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlmodel import Session, select, func
from ..database import get_session
from ..models import DriverDocument, Ride, User, Payment
from ..utils.audit import log_action, AUDIT_FILE
from ..utils.jwt_handler import get_current_admin_user
import csv, os
from typing import List

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin_user)])

@router.get("/pending_drivers", response_model=List[dict])
def list_pending_drivers(session: Session = Depends(get_session)):
    query = select(DriverDocument, User).join(User, User.id == DriverDocument.user_id) \
            .where(DriverDocument.approved == False)
    results = session.exec(query).all()
    
    pending = []
    for doc, user in results:
        pending.append({
            "doc_id": doc.id,
            "user_id": user.id,
            "driver_name": user.name,
            "driver_email": user.email,
            "doc_type": doc.doc_type,
            "file_path": doc.file_path,
            "uploaded_at": doc.uploaded_at
        })
    return pending

@router.post("/approve_driver/{doc_id}")
def approve_driver(doc_id: int, session: Session = Depends(get_session)):
    doc = session.get(DriverDocument, doc_id)
    if not doc:
        raise HTTPException(404, "Doc not found")
    doc.approved = True
    session.add(doc)
    
    # Check if all docs for this driver are approved
    all_docs = session.exec(select(DriverDocument).where(DriverDocument.user_id == doc.user_id)).all()
    all_approved = all(d.approved for d in all_docs)
    
    user = session.get(User, doc.user_id)
    if user and all_approved:
        user.is_active = True
        session.add(user)
        log_action("admin", "APPROVE_DRIVER", f"doc_id={doc_id}, driver_id={user.id}")
    
    session.commit()
    return {"status": "approved", "driver_id": doc.user_id, "driver_activated": all_approved}

@router.get("/document/{doc_id}")
def get_document(doc_id: int, session: Session = Depends(get_session)):
    doc = session.get(DriverDocument, doc_id)
    if not doc:
        raise HTTPException(404, "Doc not found")
    
    if not os.path.exists(doc.file_path):
        raise HTTPException(404, "File not found on server")
        
    return FileResponse(doc.file_path, media_type="application/pdf", filename=os.path.basename(doc.file_path))

@router.get("/reports")
def system_reports(session: Session = Depends(get_session)):
    total_rides = session.exec(select(func.count(Ride.id))).one()
    completed_rides = session.exec(select(func.count(Ride.id)).where(Ride.status == "completed")).one()
    revenue = session.exec(select(func.sum(Ride.fare))).one() or 0
    total_drivers = session.exec(select(func.count(User.id)).where(User.role == "driver")).one()
    active_drivers = session.exec(select(func.count(User.id)).where(User.role == "driver", User.is_active == True)).one()
    total_passengers = session.exec(select(func.count(User.id)).where(User.role == "passenger")).one()
    
    return {
        "total_rides": total_rides,
        "completed_rides": completed_rides,
        "total_revenue": revenue,
        "total_drivers": total_drivers,
        "active_drivers": active_drivers,
        "total_passengers": total_passengers
    }

@router.get("/reports/peak_hours")
def peak_hours_report(session: Session = Depends(get_session)):
    query = select(func.strftime('%H', Ride.created_at).label('hour'), func.count(Ride.id).label('ride_count')) \
            .group_by('hour') \
            .order_by('hour')
            
    results = session.exec(query).all()
    report = {f"{int(r.hour):02d}:00": r.ride_count for r in results}
    return report

@router.get("/audit_logs")
def get_audit_logs():
    try:
        logs = []
        with open(AUDIT_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                logs.append(row)
        return logs
    except FileNotFoundError:
        return {"message": "Audit log file not found."}
    except Exception as e:
        raise HTTPException(500, f"Error reading log: {e}")

@router.post("/block_user/{user_id}")
def block_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    user.is_active = False
    session.add(user); session.commit()
    log_action("admin", "BLOCK_USER", f"user_id={user_id}, email={user.email}")
    return {"status": "blocked", "user_email": user.email}