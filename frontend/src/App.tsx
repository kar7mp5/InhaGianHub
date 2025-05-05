import React, { useState, useEffect } from 'react';
import '@/App.css';

const FACILITIES = ['대강당', '중강당', '소강당', '5남소강당'];

/**
 * Type definition for a single reservation entry.
 */
interface Reservation {
  id: string;
  facility_name: string;
  event: string;
  start_time?: string;
  end_time?: string;
  approval?: string;
}

/**
 * Main App component.
 */
const App: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<string>(''); // Currently selected date
  const [loading, setLoading] = useState<boolean>(false); // Whether data is loading
  const [reservations, setReservations] = useState<Reservation[]>([]); // All reservations for the date

  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    setSelectedDate(today);
    loadSchedule(today);
  }, []);

  /**
   * Fetches reservation data for the selected date from backend API.
   */
  const loadSchedule = async (date: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/reservations?date=${date}`);
      const data = await response.json();

      if (!data.success) {
        console.error("Failed to fetch reservations:", data.error);
        return;
      }

      const fetchedReservations = data.data;

      for (const reservation of fetchedReservations) {
        let { start_time, end_time } = reservation;

        // Fallback to popup details if time is missing
        if (!start_time || !end_time) {
          const detailsRes = await fetch(`/api/reservations/${reservation.id}/details`);
          const detailsJson = await detailsRes.json();
          const times = extractTimeDetails(detailsJson.data);
          start_time = times.start_time;
          end_time = times.end_time;
        }

        if (start_time && end_time) {
          reservation.start_time = start_time.trim();
          reservation.end_time = end_time.trim();
        }
      }

      setReservations(fetchedReservations);
    } catch (error) {
      console.error("Error loading schedule:", error);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Extracts start_time and end_time from popup details.
   */
  const extractTimeDetails = (dataArray: any[]) => {
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
  };

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const date = e.target.value;
    setSelectedDate(date);
    loadSchedule(date);
  };

  /**
   * Returns reservations for a specific facility that have valid start and end times.
   */
  const getReservationsForFacility = (facilityName: string) => {
    return reservations.filter(
      (r) => r.facility_name === facilityName && r.start_time && r.end_time
    );
  };

  const unknownTimeReservations = reservations.filter(
    (r) => !r.start_time || !r.end_time
  );

  // Define baseHour outside both functions
  const baseHour = 9; // Starting from 9:00 AM
  const slotHeightInRem = 2; // Each time slot has a height of 3rem (adjust this based on your actual CSS)

  /**
   * Calculates the top offset for the reservation block based on absolute values, starting at 9:00 AM.
   * @param start_time The start time of the event in HH:MM format.
   * @returns The calculated top position in rem units.
   */
  const calculateTop = (start_time: string): number => {
    const [startH, startM] = start_time.split(":").map(Number);

    // Convert the start time to minutes from 9:00 AM (base time)
    const startTimeInMinutes = (startH - baseHour) * 60 + startM;

    // Calculate the top position in rem units based on time
    const topPositionInRem = (startTimeInMinutes / 60) * slotHeightInRem;

    return topPositionInRem;
  };

  /**
   * Calculates the height of the reservation block based on its start and end time.
   * This function calculates the height based on absolute time values.
   * @param start_time The start time of the event in HH:MM format.
   * @param end_time The end time of the event in HH:MM format.
   * @returns The calculated height of the reservation block in rem units.
   */
  const calculateHeight = (start_time: string, end_time: string): number => {
    const [startH, startM] = start_time.split(":").map(Number);
    const [endH, endM] = end_time.split(":").map(Number);

    // Move baseHour, slotHeightInRem, and totalMinutesInDay inside the function
    const totalMinutesInDay = 13 * 60; // Total minutes from 9 AM to 10 PM (780 minutes)

    // Calculate the duration of the event in minutes
    const durationMinutes = ((endH - startH) * 60 + (endM - startM));

    // Calculate the height based on the duration, scaled to the total day height
    const heightInRem = (durationMinutes / totalMinutesInDay) * 13 * slotHeightInRem;

    return heightInRem;
  };

  return (
    <div id="main">
      <h2 id="service-title">인하대학교 학생지원팀 시설물 조회 (강당전용)</h2>

      <input
        type="date"
        id="datePicker"
        value={selectedDate}
        onChange={handleDateChange}
      />

      {loading && (
        <div id="loading" className="loading-spinner">
          Loading<span className="dots"></span>
        </div>
      )}

      <div id="unknown-reservations">
        <h2>🕓 시간 미상 예약</h2>
        <div id="unknown-list">
          {unknownTimeReservations.length === 0 && <p>없음</p>}
          {unknownTimeReservations.map((r, i) => (
            <div key={i} className="unknown-item">
              [{r.facility_name}] {r.event}
            </div>
          ))}
        </div>
      </div>

      <div id="calendar-box">
        <div id="calendar-container">
          <div className="facility-header">
            <div className="time-label-header"></div>
            {FACILITIES.map((name) => (
              <div key={name} className="facility-title">
                {name}
              </div>
            ))}
          </div>

          <div className="calendar-body">
            <div className="time-labels">
              {Array.from({ length: 14 }, (_, i) => 9 + i).map((hour) => (
                <div key={hour} className="time-label">{`${hour}:00`}</div>
              ))}
            </div>

            <div className="facility-columns">
              {FACILITIES.map((facility) => (
                <div key={facility} className="facility" data-name={facility}>
                  {getReservationsForFacility(facility).map((res, i) => {
                    if (!res.start_time || !res.end_time) {
                      console.warn(
                        `Skipping reservation with missing time data: ${
                          res?.id || 'unknown'
                        }`
                      );
                      return null;
                    }

                    // Handling facility class
                    const facilityClass =
                      {
                        '대강당': 'dg',
                        '중강당': 'jg',
                        '소강당': 'sg',
                        '5남소강당': 'n5',
                      }[res.facility_name] || 'default';

                    return (
                      <div
                        key={res.id || i}
                        className={`reservation-block ${
                          res.approval !== '승인' ? 'pending' : ''
                        } ${facilityClass}`}
                        style={{
                          top: `${calculateTop(res.start_time!)}rem`,
                          height: `${calculateHeight(res.start_time!, res.end_time!)}rem`,
                        }}
                        title={res.event}
                      >
                        {res.event}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
