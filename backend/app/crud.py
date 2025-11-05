from sqlmodel import Session, select
from .models import User, Ride
from math import radians, cos, sin, asin, sqrt

def get_user_by_email(session: Session, email: str):
    return session.exec(select(User).where(User.email == email)).first()

def create_user(session: Session, user: User):
    session.add(user); session.commit(); session.refresh(user); return user

def get_ride(session: Session, ride_id: int):
    return session.get(Ride, ride_id)

def haversine_distance(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers.
    return c * r

def find_available_driver(session: Session, passenger_lat: float, passenger_lon: float):
    """
    Finds the nearest, active, approved driver.
    """
    drivers = session.exec(
        select(User).where(User.role == "driver", User.is_active == True)
    ).all()
    
    if not drivers:
        return None

    min_distance = float('inf')
    nearest_driver = None
    
    for driver in drivers:
        if driver.latitude is None or driver.longitude is None:
            continue
            
        distance = haversine_distance(
            passenger_lon, passenger_lat, 
            driver.longitude, driver.latitude
        )
        
        if distance < min_distance:
            min_distance = distance
            nearest_driver = driver
            
    return nearest_driver