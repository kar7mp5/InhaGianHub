import React, { useState, useEffect } from 'react';
import '@/App.css';

const api = import.meta.env.VITE_API_BASE_URL;

// Mapping of Korean facility names to backend room_id
const FACILITY_MAP: Record<string, string> = {
  '대강당': 'daegangdang',
  '중강당': 'junggangdang',
  '소강당': 'sogangdang',
  '5남소강당': '5nam_sogangdang',
};

const FACILITIES = Object.keys(FACILITY_MAP);

/** Type for a single reservation */
interface Reservation {
  id: string;
  room_id: string;
  event: string;
  start_time?: string;
  end_time?: string;
  approval?: string;
}

const App: React.FC = () => {
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [reservations, setReservations] = useState<Reservation[]>([]);

  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    setSelectedDate(today);
    loadSchedule(today);
  }, []);

  /**
   * Load all reservations from all rooms for a given date.
   */
  const loadSchedule = async (date: string) => {
    setLoading(true);
    try {
      const allReservations: Reservation[] = [];

      for (const facilityName of FACILITIES) {
        const room_id = FACILITY_MAP[facilityName];
        const res = await fetch(`${api}/api/reservations?room_id=${room_id}&date=${date}`);
        const json = await res.json();

        if (!json.success) {
          console.error(`❌ ${room_id} fetch failed:`, json.error);
          continue;
        }

        const fetched: Reservation[] = json.data;
        for (const r of fetched) {
          if (!r.start_time || !r.end_time) {
            const detailRes = await fetch(`${api}/api/reservations/${r.room_id}/${r.id}/details`);
            const detailJson = await detailRes.json();
            const times = extractTimeDetails(detailJson.data);
            r.start_time = times.start_time?.trim();
            r.end_time = times.end_time?.trim();
          }
          allReservations.push(r);
        }
      }

      setReservations(allReservations);
    } catch (e) {
      console.error("🚨 Error loading schedule:", e);
    } finally {
      setLoading(false);
    }
  };

  /** Extracts time from popup detail array */
  const extractTimeDetails = (data: any[]) => {
    let start_time = null;
    let end_time = null;
    for (const item of data) {
      if (item.key === 'start_time') start_time = item.value;
      if (item.key === 'end_time') end_time = item.value;
    }
    return { start_time, end_time };
  };

  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const date = e.target.value;
    setSelectedDate(date);
    loadSchedule(date);
  };

  const getReservationsForFacility = (facilityName: string) => {
    const room_id = FACILITY_MAP[facilityName];
    return reservations.filter(
      (r) => r.room_id === room_id && r.start_time && r.end_time
    );
  };

  const unknownTimeReservations = reservations.filter(
    (r) => !r.start_time || !r.end_time
  );

  const baseHour = 9;
  const slotHeightInRem = 2;

  const calculateTop = (start_time: string): number => {
    const [h, m] = start_time.split(':').map(Number);
    return ((h - baseHour) * 60 + m) / 60 * slotHeightInRem;
  };

  const calculateHeight = (start_time: string, end_time: string): number => {
    const [h1, m1] = start_time.split(':').map(Number);
    const [h2, m2] = end_time.split(':').map(Number);
    const total = 13 * 60;
    const duration = (h2 - h1) * 60 + (m2 - m1);
    return (duration / total) * 13 * slotHeightInRem;
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
        <h2>🕓 시간 미정 예약</h2>
        <div id="unknown-list">
          {unknownTimeReservations.length === 0 && <p>없음</p>}
          {unknownTimeReservations.map((r, i) => (
            <div key={i} className="unknown-item">
              [{r.room_id}] {r.event}
            </div>
          ))}
        </div>
      </div>

      <div id="calendar-box">
        <div id="calendar-container">
          <div className="facility-header">
            <div className="time-label-header"></div>
            {FACILITIES.map((name) => (
              <div key={name} className="facility-title">{name}</div>
            ))}
          </div>

          <div className="calendar-body">
            <div className="time-labels">
              {Array.from({ length: 14 }, (_, i) => 9 + i).map((hour) => (
                <div key={hour} className="time-label">{`${hour}:00`}</div>
              ))}
            </div>

            <div className="facility-columns">
              {FACILITIES.map((facility) => {
                const list = getReservationsForFacility(facility);
                const room_id = FACILITY_MAP[facility];
                return (
                  <div key={facility} className="facility" data-name={facility}>
                    {list.map((res, i) => {
                      if (!res.start_time || !res.end_time) return null;
                      const cls = {
                        '대강당': 'dg',
                        '중강당': 'jg',
                        '소강당': 'sg',
                        '5남소강당': 'n5',
                      }[facility] || 'default';
                      return (
                        <div
                          key={res.id}
                          className={`reservation-block ${
                            res.approval !== '승인' ? 'pending' : ''
                          } ${cls}`}
                          style={{
                            top: `${calculateTop(res.start_time)}rem`,
                            height: `${calculateHeight(res.start_time, res.end_time)}rem`,
                          }}
                          title={res.event}
                        >
                          {res.event}
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
