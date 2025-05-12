from firebase import db
import hashlib
import warnings

# Suppress Firestore warning about positional arguments
warnings.filterwarnings("ignore", message="Detected filter using positional arguments")


def upsert_reservation(room_id: str, reservation_id: str, data: dict):
    """
    Inserts or updates a reservation document under a specific room.

    Args:
        room_id (str): The Firestore document ID of the room.
        reservation_id (str): The Firestore document ID of the reservation.
        data (dict): Reservation data to be written.

    Returns:
        None
    """
    db.collection("rooms").document(room_id).collection("reservations").document(reservation_id).set(data)


def add_popup_details(room_id: str, reservation_id: str, details: dict):
    """
    Adds detailed popup information as a subcollection under a reservation.

    Args:
        room_id (str): Parent room document ID.
        reservation_id (str): Parent reservation document ID.
        details (dict): Dictionary of key-value pairs to be stored.

    Returns:
        None
    """
    ref = db.collection("rooms").document(room_id).collection("reservations").document(reservation_id).collection("popup_details")
    for k, v in details.items():
        ref.document(k).set({"key": k, "value": v})


def find_reservation(room_id: str, date: str, event: str):
    """
    Searches for a reservation based on room, date, and event.

    Args:
        room_id (str): Room identifier.
        date (str): Reservation date in YYYY-MM-DD format.
        event (str): Name of the event.

    Returns:
        Tuple[str, dict]: (Document ID, Reservation data) if found, otherwise (None, None).
    """
    query = db.collection("rooms").document(room_id).collection("reservations") \
        .where("date", "==", date).where("event", "==", event).limit(1).stream()
    for doc in query:
        return doc.id, doc.to_dict()
    return None, None


def get_all_reservations():
    """
    Retrieves all reservations across all rooms.

    Returns:
        List[dict]: List of all reservations including room ID and reservation ID.
    """
    reservations = []
    rooms = db.collection("rooms").stream()
    for room in rooms:
        room_id = room.id
        sub = db.collection("rooms").document(room_id).collection("reservations").stream()
        for resv in sub:
            data = resv.to_dict()
            data["id"] = resv.id
            data["room_id"] = room_id
            reservations.append(data)
    return reservations


def get_reservations_by_filter(room_id=None, date=None):
    """
    Retrieves filtered reservations. If room_id is provided, queries Firestore.
    Otherwise, filters all reservations in memory.

    Args:
        room_id (str, optional): Room identifier to filter by.
        date (str, optional): Date to filter reservations by.

    Returns:
        List[dict]: List of filtered reservation dictionaries.
    """
    results = []
    if room_id:
        query = db.collection("rooms").document(room_id).collection("reservations")
        if date:
            query = query.where("date", "==", date)
        docs = query.stream()
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            data["room_id"] = room_id
            results.append(data)
    else:
        results = get_all_reservations()
        if date:
            results = [r for r in results if r.get("date") == date]
    return results


def get_popup_details_by_reservation_id(room_id: str, reservation_id: str):
    """
    Fetches popup details for a specific reservation.

    Args:
        room_id (str): Room identifier.
        reservation_id (str): Reservation identifier.

    Returns:
        List[dict]: List of detail entries as dictionaries with key/value.
    """
    ref = db.collection("rooms").document(room_id).collection("reservations").document(reservation_id).collection("popup_details")
    return [{"key": doc.id, **doc.to_dict()} for doc in ref.stream()]


def delete_reservation(room_id: str, reservation_id: str):
    """
    Deletes a reservation document.

    Args:
        room_id (str): Room identifier.
        reservation_id (str): Reservation identifier.

    Returns:
        None
    """
    db.collection("rooms").document(room_id).collection("reservations").document(reservation_id).delete()


def hash_reservation(resv: dict) -> str:
    """
    Generates a SHA-256 hash based on reservation content.

    Args:
        resv (dict): Reservation dictionary.

    Returns:
        str: SHA-256 hash string.
    """
    key_fields = [resv.get("date", ""), resv.get("event", "")]
    return hashlib.sha256("|".join(key_fields).encode()).hexdigest()


def sync_reservations(room_id: str, date: str, crawled_ids: set[str]) -> int:
    """
    Removes outdated reservations that are no longer valid.

    Args:
        room_id (str): Room identifier.
        date (str): Date to match against.
        crawled_ids (set[str]): Set of valid IDs that should be kept.

    Returns:
        int: Count of deleted reservations.
    """
    query = db.collection("rooms").document(room_id).collection("reservations").where("date", "==", date)
    delete_count = 0
    for doc in query.stream():
        if doc.id not in crawled_ids:
            doc.reference.delete()
            delete_count += 1
    return delete_count
