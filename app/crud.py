from app import database

def create_reservation(db, reservation_data):
    """
    Insert a reservation record into the database.

    Args:
        db: Database session.
        reservation_data: Reservation ORM object.

    Returns:
        Inserted reservation object.
    """
    db.add(reservation_data)
    db.commit()
    db.refresh(reservation_data)
    return reservation_data

def create_popup_detail(db, popup_data):
    """
    Insert popup detail data into the database.

    Args:
        db: Database session.
        popup_data: PopupDetail ORM object.
    """
    db.add(popup_data)
    db.commit()
