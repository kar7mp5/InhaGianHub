import React, { useState } from 'react';
import '@/App.css';

/**
 * List of facility names to render columns for.
 */
const FACILITIES = ['대강당', '중강당', '소강당', '5남소강당'];

/**
 * Type definition for a single reservation entry.
 */
interface Reservation {
  facility: string;
  name: string;
  start_time?: string; // Optional: undefined means unknown reservation time
  end_time?: string;
  status?: string;
}

const App: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<string>(''); // Currently selected date
  const [loading, setLoading] = useState<boolean>(false); // Whether data is loading
  const [reservations, setReservations] = useState<Reservation[]>([]); // All reservations for the date

  /**
   * Handles the date change from the date picker.
   * @param e The change event from the input element.
   */
  const handleDateChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const date = e.target.value;
    setSelectedDate(date);
    await fetchReservations(date);
  };

  /**
   * Fetches reservation data from the backend API for a given date.
   * @param date Date in YYYY-MM-DD format.
   */
  const fetchReservations = async (date: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/reservations?date=${date}`);
      const data: Reservation[] = await response.json();
      setReservations(data);
    } catch (error) {
      console.error('Failed to fetch reservations', error);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Returns the list of reservations for a specific facility that have valid times.
   * @param facilityName The name of the facility.
   */
  const getReservationsForFacility = (facilityName: string) => {
    return reservations.filter(
      r => r.facility === facilityName && r.start_time && r.end_time
    );
  };

  /**
   * Filters reservations that have unknown start or end times.
   */
  const unknownTimeReservations = reservations.filter(
    r => !r.start_time || !r.end_time
  );

  /**
   * Calculates the vertical position (in pixels) from the start time.
   * Used for top offset in absolute positioning.
   * @param start ISO timestamp string of the start time.
   */
  const calculateTop = (start: string): number => {
    const date = new Date(start);
    return date.getHours() * 60 + date.getMinutes(); // Top in pixels (1 min = 1 px)
  };

  /**
   * Calculates the height of a reservation block (in pixels).
   * @param start Start time string.
   * @param end End time string.
   */
  const calculateHeight = (start: string, end: string): number => {
    const diffMs = new Date(end).getTime() - new Date(start).getTime();
    return diffMs / 60000; // Height in minutes
  };

  return (
    <div id="main">
      <h2 id="service-title">인하대학교 학생지원팀 시설물 사용 조회 (강당전용)</h2>

      <input type="date" id="datePicker" value={selectedDate} onChange={handleDateChange} />

      {loading && (
        <div id="loading" className="loading-spinner">
          Loading<span className="dots"></span>
        </div>
      )}

      {/* Unknown time reservations list */}
      <div id="unknown-reservations">
        <h2>🕓 시간 미상 예약</h2>
        <div id="unknown-list">
          {unknownTimeReservations.length === 0 && <p>없음</p>}
          {unknownTimeReservations.map((r, i) => (
            <div key={i}>{r.name} ({r.facility})</div>
          ))}
        </div>
      </div>

      {/* Main calendar grid view */}
      <div id="calendar-box">
        <div id="calendar-container">
          <div className="facility-header">
            <div className="time-label-header"></div>
            {FACILITIES.map(name => (
              <div key={name} className="facility-title">{name}</div>
            ))}
          </div>

          <div className="calendar-body">
            {/* Time labels on the left (00:00 ~ 23:00) */}
            <div className="time-labels">
              {Array.from({ length: 24 }).map((_, i) => (
                <div key={i} className="time-label">{`${i}:00`}</div>
              ))}
            </div>

            {/* Facility columns with reservations */}
            <div className="facility-columns">
              {FACILITIES.map(facility => (
                <div key={facility} className="facility" data-name={facility}>
                  {getReservationsForFacility(facility).map((res, i) => {
                    const top = calculateTop(res.start_time!);
                    const height = calculateHeight(res.start_time!, res.end_time!);
                    return (
                      <div
                        key={i}
                        className={`reservation-block ${res.status === '대기중' ? 'pending' : ''}`}
                        style={{ top: `${top}px`, height: `${height}px` }}
                        title={res.name}
                      >
                        {res.name}
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
