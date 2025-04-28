const FACILITIES = ["대강당", "중강당", "소강당", "5남소강당"];

document.addEventListener("DOMContentLoaded", () => {
    generateTimeLabels();     
    generateHourLines();      

    const datePicker = document.getElementById("datePicker");
    datePicker.valueAsDate = new Date();  
    loadSchedule();  
    datePicker.addEventListener("change", loadSchedule);
});

/**
 * Generate time labels for the left side.
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
 * Generate 13 hour lines inside each facility column.
 */
function generateHourLines() {
    const facilities = document.querySelectorAll('.facility');
    facilities.forEach(facility => {
        for (let i = 0; i < 13; i++) {
            const line = document.createElement('div');
            line.className = 'hour-line';
            facility.appendChild(line);
        }
    });
}

/**
 * Main function to load schedule data.
 */
async function loadSchedule() {
    const date = document.getElementById("datePicker").value;
    if (!date) return;

    clearFacilities();  
    document.getElementById("loading").style.display = "block";

    try {
        for (const facility of FACILITIES) {
            await fetch(`${API_BASE}/crawl/${encodeURIComponent(facility)}`, { method: 'POST' });
        }

        const data = await fetchReservations(date);

        if (!data.success) {
            console.error("Failed to fetch reservations:", data.error);
            return;
        }

        const reservations = data.data;

        for (const reservation of reservations) {
            const detailsResponse = await fetch(`${API_BASE}/reservations/${reservation.id}/details`);
            const detailsJson = await detailsResponse.json();

            const { start_time, end_time } = extractTimeDetails(detailsJson.data);

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

    } catch (error) {
        console.error("Error during crawling or fetching schedule:", error);
    } finally {
        document.getElementById("loading").style.display = "none";
    }
}

/**
 * Remove only event blocks, keep hour lines.
 */
function clearFacilities() {
    document.querySelectorAll(".facility .event-block").forEach(e => e.remove());
    document.getElementById("popup-detail").style.display = "none";
}

/**
 * Extract start_time and end_time from details array.
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
 * Render reservation block with centered text and safe click.
 */
function renderEventBlock(event) {
    const facilityDiv = document.querySelector(`.facility[data-name='${event.facility_name}']`);
    if (!facilityDiv) return;

    const block = document.createElement("div");
    block.className = "event-block";
    block.textContent = event.event;

    const startTime = event.start_time.split(':').map(Number);
    const endTime = event.end_time.split(':').map(Number);

    const topPosition = ((startTime[0] - 9) * 60) + startTime[1];
    const height = ((endTime[0] - startTime[0]) * 60) + (endTime[1] - startTime[1]);

    block.style.top = `${topPosition}px`;
    block.style.height = `${height}px`;

    block.addEventListener("click", async (e) => {
        e.preventDefault();   // Prevent any default behavior
        const detailsResponse = await fetch(`${API_BASE}/reservations/${event.id}/details`);
        const detailsJson = await detailsResponse.json();
        showPopupDetail(detailsJson.data);
    });

    facilityDiv.appendChild(block);
}
