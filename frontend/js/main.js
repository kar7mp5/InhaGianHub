const generateTimeLabels = () => {
    const timeLabels = document.querySelector(".time-labels");
    timeLabels.innerHTML = "";
    for (let hour = 9; hour <= 22; hour++) {
        const label = document.createElement("div");
        label.className = "time-label";
        label.innerText = `${hour}:00`;
        timeLabels.appendChild(label);
    }
};

const generateHourLines = () => {
    const facilities = document.querySelectorAll(".facility");
    facilities.forEach(facility => {
        facility.innerHTML = "";
        for (let i = 0; i < 14; i++) {
            const line = document.createElement("div");
            line.className = "hour-line";
            facility.appendChild(line);
        }
    });
};

const adjustCalendarHeight = () => {
    requestAnimationFrame(() => {
        const container = document.getElementById("calendar-container");
        const calendarBody = document.querySelector(".calendar-body");
        const topOffset = container.getBoundingClientRect().top;
        const availableHeight = window.innerHeight - topOffset;

        const hourCount = 14;
        const rowHeight = availableHeight / hourCount;
        const fullHeight = rowHeight * (hourCount + 0.3);

        container.style.height = `${fullHeight}px`;
        calendarBody.style.height = `${fullHeight}px`;
        document.querySelectorAll(".facility").forEach(fac => {
            fac.style.height = `${fullHeight}px`;
        });

        document.querySelectorAll(".time-label").forEach(label => {
            label.style.height = `${rowHeight}px`;
            label.style.minHeight = `${rowHeight}px`;
        });

        document.querySelectorAll(".hour-line").forEach(line => {
            line.style.height = `${rowHeight}px`;
            line.style.minHeight = `${rowHeight}px`;
        });

        updateAllEventBlockPositions(rowHeight);
    });
};

const updateAllEventBlockPositions = (rowHeight) => {
    const eventBlocks = document.querySelectorAll(".event-block");
    eventBlocks.forEach(block => {
        const start = block.dataset.start;
        const end = block.dataset.end;
        if (!start || !end) return;

        const [startH, startM] = start.split(":").map(Number);
        const [endH, endM] = end.split(":").map(Number);

        const top = ((startH - 9) * 60 + startM) * (rowHeight / 60);
        const height = ((endH - startH) * 60 + (endM - startM)) * (rowHeight / 60);

        block.style.top = `${top}px`;
        block.style.height = `${height}px`;
    });
};

const loadSchedule = async () => {
    const date = document.getElementById("datePicker").value;
    if (!date) return;

    generateTimeLabels();
    generateHourLines();
    clearEventBlocks();

    document.getElementById("loading").style.display = "block";
    document.getElementById("unknown-list").innerHTML = "";

    try {
        const response = await fetch(`${API_BASE}/reservations?date=${date}`);
        const data = await response.json();

        if (!data.success) {
            console.error("Failed to fetch reservations:", data.error);
            return;
        }

        const reservations = data.data;
        let hasEvent = false;

        for (const reservation of reservations) {
            let { start_time, end_time } = reservation;

            if (!start_time || !end_time) {
                const detailsRes = await fetch(`${API_BASE}/reservations/${reservation.id}/details`);
                const detailsJson = await detailsRes.json();
                const times = extractTimeDetails(detailsJson.data);
                start_time = times.start_time;
                end_time = times.end_time;
            }

            const hasValidTime = start_time && end_time &&
                /^\d{2}:\d{2}$/.test(start_time) &&
                /^\d{2}:\d{2}$/.test(end_time);

            const enhancedReservation = {
                ...reservation,
                start_time: start_time ? start_time.trim() : null,
                end_time: end_time ? end_time.trim() : null
            };

            if (hasValidTime) {
                renderEventBlock(enhancedReservation);
                hasEvent = true;
            } else {
                renderUnknownReservation(enhancedReservation);
            }
        }

        if (!hasEvent) removeEmptyMessage();

        adjustCalendarHeight();
    } catch (err) {
        console.error("Error loading schedule:", err);
    } finally {
        document.getElementById("loading").style.display = "none";
    }
};

const clearEventBlocks = () => {
    document.querySelectorAll(".facility .event-block").forEach(e => e.remove());
    removeEmptyMessage();
};

const removeEmptyMessage = () => {
    const existingMsg = document.querySelector(".empty-message");
    if (existingMsg) existingMsg.remove();
};

const extractTimeDetails = (dataArray) => {
    let start_time = null;
    let end_time = null;

    for (const item of dataArray) {
        if (item.key === "start_time") start_time = item.value;
        if (item.key === "end_time") end_time = item.value;
    }

    return { start_time, end_time };
};

const renderEventBlock = (event) => {
    const facilityDiv = document.querySelector(`.facility[data-name='${event.facility_name}']`);
    if (!facilityDiv) return;

    const block = document.createElement("div");
    block.className = "event-block";
    block.dataset.start = event.start_time;
    block.dataset.end = event.end_time;

    const rowHeight = parseFloat(getComputedStyle(document.querySelector(".hour-line")).height);
    const [startH, startM] = event.start_time.split(":").map(Number);
    const [endH, endM] = event.end_time.split(":").map(Number);

    const top = ((startH - 9) * 60 + startM) * (rowHeight / 60);
    const height = ((endH - startH) * 60 + (endM - startM)) * (rowHeight / 60);

    block.style.top = `${top}px`;
    block.style.height = `${height}px`;

    const status = event.approval || "Unknown";
    block.textContent = `${event.event} (${status})`;

    block.addEventListener("click", async (e) => {
        e.preventDefault();
        const res = await fetch(`${API_BASE}/reservations/${event.id}/details`);
        const json = await res.json();
        showPopupDetail(json.data);
    });

    facilityDiv.appendChild(block);
};

const renderUnknownReservation = (event) => {
    const container = document.getElementById("unknown-list");
    const div = document.createElement("div");
    div.className = "unknown-item";

    const status = event.approval || "Unknown";
    div.textContent = `[${event.facility_name}] ${event.event} (${status})`;

    container.appendChild(div);
};

document.addEventListener("DOMContentLoaded", () => {
    generateTimeLabels();
    generateHourLines();
    adjustCalendarHeight();

    const datePicker = document.getElementById("datePicker");
    datePicker.valueAsDate = new Date();
    loadSchedule();

    datePicker.addEventListener("change", loadSchedule);
});

window.addEventListener("resize", adjustCalendarHeight);
