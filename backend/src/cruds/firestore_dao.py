from firebase import db
from datetime import datetime
import hashlib
import warnings

# Suppress Firestore warning about positional arguments in 'where'
warnings.filterwarnings("ignore", message="Detected filter using positional arguments")


def upsert_reservation(doc_id: str, data: dict):
    """Creates or updates a reservation document in Firestore.

    Args:
        doc_id: The unique Firestore document ID.
        data: A dictionary containing reservation data.

    Returns:
        None
    """
    db.collection("reservations").document(doc_id).set(data)


def add_popup_details(reservation_id: str, details: dict):
    """Stores popup details as a subcollection under the reservation.

    Args:
        reservation_id: Firestore document ID of the parent reservation.
        details: A dictionary where keys are field names and values are the detail values.

    Returns:
        None
    """
    ref = db.collection("reservations").document(reservation_id).collection("popup_details")
    for k, v in details.items():
        ref.document(k).set({"key": k, "value": v})


def find_reservation(facility_name: str, date: str, place: str, event: str):
    """Finds a reservation document by its identifying fields.

    Args:
        facility_name: Name of the facility.
        date: Reservation date in 'YYYY-MM-DD' format.
        place: Location or room name.
        event: Event name.

    Returns:
        A tuple of (doc_id, doc_data) if found; otherwise, (None, None).
    """
    query = db.collection("reservations") \
        .where(field_path="facility_name", op_string="==", value=facility_name) \
        .where(field_path="date", op_string="==", value=date) \
        .where(field_path="place", op_string="==", value=place) \
        .where(field_path="event", op_string="==", value=event) \
        .limit(1) \
        .stream()

    for doc in query:
        return doc.id, doc.to_dict()
    return None, None


def get_all_reservations():
    """Retrieves all reservation documents.

    Returns:
        A list of dictionaries, each with reservation data and its document ID.
    """
    reservations = []
    docs = db.collection("reservations").stream()
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        reservations.append(data)
    return reservations


def get_reservations_by_filter(facility_name=None, date=None):
    """Queries reservation documents using a single Firestore filter and applies other filters in Python.

    Args:
        facility_name: Optional; name of the facility to filter by.
        date: Optional; reservation date in 'YYYY-MM-DD' format to filter by.

    Returns:
        A list of filtered reservation documents, each as a dictionary with an 'id' field.
    """
    query = db.collection("reservations")

    # Apply only one Firestore-level filter to avoid index requirement
    if facility_name:
        query = query.where("facility_name", "==", facility_name)
    elif date:
        query = query.where("date", "==", date)

    results = []
    for doc in query.stream():
        data = doc.to_dict()
        # Python-side filtering
        if facility_name and data.get("facility_name") != facility_name:
            continue
        if date and data.get("date") != date:
            continue
        data["id"] = doc.id
        results.append(data)

    return results



def get_popup_details_by_reservation_id(reservation_id: str):
    """Fetches popup detail documents for a given reservation.

    Args:
        reservation_id: Firestore document ID of the reservation.

    Returns:
        A list of dictionaries containing popup detail data.
    """
    collection_ref = db.collection("reservations") \
                       .document(reservation_id) \
                       .collection("popup_details")

    return [{"key": doc.id, **doc.to_dict()} for doc in collection_ref.stream()]


def delete_reservation(doc_id: str):
    """Deletes a reservation document.

    Args:
        doc_id: The Firestore document ID.

    Returns:
        None
    """
    db.collection("reservations").document(doc_id).delete()


def get_reservations_by_facility(facility_name: str):
    """Retrieves all reservations for a specific facility.

    Args:
        facility_name: Name of the facility.

    Returns:
        A list of dictionaries, each with reservation data and document ID.
    """
    return [
        {"id": doc.id, **doc.to_dict()}
        for doc in db.collection("reservations")
                     .where(field_path="facility_name", op_string="==", value=facility_name)
                     .stream()
    ]


def hash_reservation(resv: dict) -> str:
    """Generates a hash to uniquely identify a reservation.

    Args:
        resv: Reservation dictionary.

    Returns:
        A SHA-256 hash string based on key fields.
    """
    key_fields = [resv.get("date", ""), resv.get("place", ""), resv.get("event", "")]
    return hashlib.sha256("|".join(key_fields).encode()).hexdigest()


def sync_reservations(facility_name: str, date: str, crawled_ids: set[str]) -> int:
    """Deletes outdated reservations from Firestore that are no longer in the current crawl.

    This version avoids composite Firestore indexes by using only one filter and performing
    remaining filtering in Python.

    Args:
        facility_name: Name of the facility being crawled.
        date: The current date of interest (YYYY-MM-DD).
        crawled_ids: Set of document IDs that were crawled and considered valid.

    Returns:
        The number of documents deleted from Firestore.
    """
    query = db.collection("reservations").where("facility_name", "==", facility_name)

    delete_count = 0
    for doc in query.stream():
        data = doc.to_dict()
        # Apply remaining filters in Python to avoid Firestore index errors
        if data.get("date") != date:
            continue
        if doc.id not in crawled_ids:
            doc.reference.delete()
            delete_count += 1

    return delete_count

