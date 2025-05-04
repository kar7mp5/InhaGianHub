import React, { useState, useEffect } from 'react';
import '@/App.css';

const FACILITIES = ['대강당', '중강당', '소강당', '5남소강당'];

interface Reservation {
  id: string;
  facility: string;
  name: string;
  start_time?: string;
  end_time?: string;
  status?: string;
}

const App: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  /**
   * Fetch reservations for selected date from backend API.
   */
  const fetchReservations = async (date: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/reservations?date=${date}`);
      if (!response.ok) {
        const text = await response.text();
        throw new Error(`HTTP ${response.status}: ${text}`);
      }

      const json = await response.json();

      if (!json.success || !Array.isArray(json.data)) {
        console.error('Unexpected response structure:', json);
        setReservations([]);
      } else {
        // ✅ Map backend fields to frontend format
        const mapped = json.data.map((item: any) => ({
          id: item.id,
          facility: item.facility_name,
          name: item.event,
          start_time: item.start_time,
          end_time: item.end_time,
          status: item.approval,
        }));
        setReservations(mapped);
      }
    } catch (error) {
      console.error('Failed to fetch reservations', error);
      setReservations([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDateChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const date = e.target.value;
    setSelectedDate(date);
    await fetchReservations(date);
  };

  const getReservationsForFacility = (facilityName: string) => {
    return reservations.filter(
      r => r.facility === facilityName && r.start_time && r.end_time
    );
  };

  const unknownTimeReservations = reservations.filter(
    r => !r.start_time || !r.end_time
  );

  /**
   * Returns pixels per minute based on .time-label height (60min block).
   */
  const getMinuteToPixelRatio = (): number => {
    const el = document.querySelector('.time-label');
    if (!el) return 1; // fallback
    const height = el.getBoundingClientRect().height;
    return height / 60;
  };

  /**
   * Calculates top offset based on time and .time-label height.
   */
  const calculateTop = (time: string): number => {
    const [hour, minute] = time.split(':').map(Number);
    const minutesFromStart = (hour - 9) * 60 + minute;
    return minutesFromStart * getMinuteToPixelRatio();
  };

  /**
   * Calculates height based on duration between start and end time.
   */
  const calculateHeight = (start: string, end: string): number => {
    const [sh, sm] = start.split(':').map(Number);
    const [eh, em] = end.split(':').map(Number);
    const durationMinutes = (eh * 60 + em) - (sh * 60 + sm);
    return durationMinutes * getMinuteToPixelRatio();
  };

  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    setSelectedDate(today);
    fetchReservations(today);
  }, []);

  return (
    <div id="main">
      <h2 id="service-title">인하대학교 학생지원팀 시설물 사용 조회 (강당전용)</h2>

      <input type="date" id="datePicker" value={selectedDate} onChange={handleDateChange} />

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
            <div key={i} className="unknown-item">[{r.facility}] {r.name}</div>
          ))}
        </div>
      </div>

      <div id="calendar-box">
        <div id="calendar-container">
          <div className="facility-header">
            <div className="time-label-header"></div>
            {FACILITIES.map(name => (
              <div key={name} className="facility-title">{name}</div>
            ))}
          </div>

          <div className="calendar-body">
            {/* ✅ Show only 9:00 ~ 22:00 time labels */}
            <div className="time-labels">
              {Array.from({ length: 14 }, (_, i) => 9 + i).map(hour => (
                <div key={hour} className="time-label">{`${hour}:00`}</div>
              ))}
            </div>

            <div className="facility-columns">
              {FACILITIES.map(facility => (
                <div key={facility} className="facility" data-name={facility}>
                  {getReservationsForFacility(facility).map((res, i) => {
                    if (!res || !res.start_time || !res.end_time) {
                      console.warn(`Skipping reservation with missing time data: ${res?.id || 'unknown'}`);
                      return null;
                    }

                    // Handling facility class
                    const facilityClass = {
                      '대강당': 'dg',
                      '중강당': 'jg',
                      '소강당': 'sg',
                      '5남소강당': 'n5',
                    }[res.facility] || 'default';  // 'default' is the fallback if facility doesn't match

                    return (
                      <div
                        key={res.id || i}
                        className={`reservation-block ${res.status === '대기중' ? 'pending' : ''} ${facilityClass}`}
                        style={{
                          top: `${calculateTop(res.start_time!)}px`,
                          height: `${calculateHeight(res.start_time!, res.end_time!)}px`,
                        }}
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
