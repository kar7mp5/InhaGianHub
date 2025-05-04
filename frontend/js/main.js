document.addEventListener("DOMContentLoaded", () => {
    generateTimeLabels();
    generateHourLines();

    const datePicker = document.getElementById("datePicker");
    datePicker.valueAsDate = new Date();
    loadSchedule();

    datePicker.addEventListener("change", loadSchedule);
});

/**
 * Generates vertical time labels from 9:00 to 22:00.
 */
function generateTimeLabels() {
    const timeLabels = document.querySelector(".time-labels");
    for (let hour = 9; hour <= 22; hour++) {
        const label = document.createElement("div");
        label.className = "time-label";
        label.innerText = `${hour}:00`;
        timeLabels.appendChild(label);
    }
}

/**
 * Generates horizontal hour lines inside each facility column.
 */
function generateHourLines() {
    const facilities = document.querySelectorAll(".facility");
    facilities.forEach(facility => {
        for (let i = 0; i < 13; i++) {
            const line = document.createElement("div");
            line.className = "hour-line";
            facility.appendChild(line);
        }
    });
}

/**
 * Loads reservations for the selected date and renders them on the UI.
 */
async function loadSchedule() {
    const date = document.getElementById("datePicker").value;
    if (!date) return;

    clearFacilities();
    document.getElementById("loading").style.display = "block";

    try {
        // Load reservations only (no live crawling)
        const response = await fetch(`${API_BASE}/reservations?date=${date}`);
        const data = await response.json();

        if (!data.success) {
            console.error("Failed to fetch reservations:", data.error);
            return;
        }

        const reservations = data.data;

        for (const reservation of reservations) {
            let { start_time, end_time } = reservation;

            // Fallback to popup detail if time is missing
            if (!start_time || !end_time) {
                const detailsRes = await fetch(`${API_BASE}/reservations/${reservation.id}/details`);
                const detailsJson = await detailsRes.json();
                const times = extractTimeDetails(detailsJson.data);
                start_time = times.start_time;
                end_time = times.end_time;
            }

            if (!start_time || !end_time) {
                console.warn(`Missing time info for reservation ID ${reservation.id}`);
                continue;
            }

            renderEventBlock({
                ...reservation,
                start_time: start_time.trim(),
                end_time: end_time.trim()
            });
        }

    } catch (err) {
        console.error("Error loading schedule:", err);
    } finally {
        document.getElementById("loading").style.display = "none";
    }
}

/**
 * Removes all event blocks from the screen.
 */
function clearFacilities() {
    document.querySelectorAll(".facility .event-block").forEach(e => e.remove());
    document.getElementById("popup-detail").style.display = "none";
}

/**
 * Extracts start_time and end_time from popup details (already in English keys).
 * 
 * @param {Array} dataArray - Array of {key, value} pairs
 * @returns {{ start_time: string | null, end_time: string | null }}
 */
function extractTimeDetails(dataArray) {
    let start_time = null;
    let end_time = null;

    for (const item of dataArray) {
        if (item.key === "start_time") {
            start_time = item.value;
        } else if (item.key === "end_time") {
            end_time = item.value;
        }
    }

    return { start_time, end_time };
}

/**
 * Renders a reservation block at the correct time position on the UI.
 *
 * @param {Object} event - Reservation object with time and metadata.
 */
function renderEventBlock(event) {
    const facilityDiv = document.querySelector(`.facility[data-name='${event.facility_name}']`);
    if (!facilityDiv) return;

    const block = document.createElement("div");
    block.className = "event-block";
    block.textContent = event.event;

    const [startH, startM] = event.start_time.split(":").map(Number);
    const [endH, endM] = event.end_time.split(":").map(Number);

    const top = ((startH - 9) * 60) + startM;
    const height = ((endH - startH) * 60) + (endM - startM);

    block.style.top = `${top}px`;
    block.style.height = `${height}px`;

    block.addEventListener("click", async (e) => {
        e.preventDefault();
        const res = await fetch(`${API_BASE}/reservations/${event.id}/details`);
        const json = await res.json();
        showPopupDetail(json.data);
    });

    facilityDiv.appendChild(block);
}
