async function fetchReservations(date) {
    try {
        const response = await fetch(`${API_BASE}/reservations?date=${date}`);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        console.log("Fetched reservations:", data);
        return data;
    } catch (error) {
        console.error("Error fetching reservations:", error);
        return [];
    }
}

async function fetchPopupDetails(reservationId) {
    try {
        const response = await fetch(`${API_BASE}/popup-details/${reservationId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Error fetching popup details:", error);
        return {};
    }
}
