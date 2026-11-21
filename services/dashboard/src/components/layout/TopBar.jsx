// Pasek wyszukiwania + wybor zakresu czasu (jak w Kibanie).
export const RANGES = [
  { id: "24h", label: "Ostatnie 24 h", days: 1 },
  { id: "7d", label: "Ostatnie 7 dni", days: 7 },
  { id: "30d", label: "Ostatnie 30 dni", days: 30 },
  { id: "90d", label: "Ostatnie 90 dni", days: 90 },
  { id: "custom", label: "Własny zakres" },
];

export default function TopBar({ title, query, onQuery, range, onRange, custom, onCustom, onRefresh, live }) {
  return (
    <header className="topbar">
      <h1>{title}</h1>
      <input
        className="search"
        placeholder="Szukaj: tytuł, publikujący, podmiot, uzasadnienie…"
        value={query}
        onChange={(e) => onQuery(e.target.value)}
      />
      <select className="range" value={range} onChange={(e) => onRange(e.target.value)}>
        {RANGES.map((r) => (
          <option key={r.id} value={r.id}>{r.label}</option>
        ))}
      </select>
      {range === "custom" && (
        <>
          <input type="date" value={custom.from} onChange={(e) => onCustom({ ...custom, from: e.target.value })} />
          <input type="date" value={custom.to} onChange={(e) => onCustom({ ...custom, to: e.target.value })} />
        </>
      )}
      <button className="btn primary" onClick={onRefresh}>Odśwież</button>
      <span className={`live ${live ? "on" : ""}`} title="Połączenie WebSocket /ws/alerts">{live ? "● na żywo" : "○ offline"}</span>
    </header>
  );
}
