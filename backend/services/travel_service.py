from sqlalchemy.orm import Session
from models.travel_history import TravelHistory

def create_mock_travel_history(db: Session):
    """Create mock travel history if it doesn't exist"""
    # Check if travel history already exists
    if db.query(TravelHistory).count() > 0:
        return
    
    # Travel history for User 1 (haile)
    travel1_1 = TravelHistory(
        user_id=1,
        country="Kenya",
        city="Nairobi",
        travel_date="2024-01-15"
    )
    
    travel1_2 = TravelHistory(
        user_id=1,
        country="Tanzania",
        city="Dar es Salaam",
        travel_date="2023-11-20"
    )
    
    travel1_3 = TravelHistory(
        user_id=1,
        country="Uganda",
        city="Kampala",
        travel_date="2023-08-10"
    )
    
    # Travel history for User 2 (traveler1)
    travel2_1 = TravelHistory(
        user_id=2,
        country="Canada",
        city="Toronto",
        travel_date="2024-02-01"
    )
    
    travel2_2 = TravelHistory(
        user_id=2,
        country="United Kingdom",
        city="London",
        travel_date="2023-12-15"
    )
    
    travel2_3 = TravelHistory(
        user_id=2,
        country="France",
        city="Paris",
        travel_date="2023-09-05"
    )
    
    db.add(travel1_1)
    db.add(travel1_2)
    db.add(travel1_3)
    db.add(travel2_1)
    db.add(travel2_2)
    db.add(travel2_3)
    db.commit()
