// Filtry wielokrotnego wyboru jako "pigułki". groups: [{ key, label, options: {value: label} }]
export default function FilterBar({ groups, value, onChange, onClear }) {
  const toggle = (key, v) => {
    const cur = value[key] || [];
    onChange({ ...value, [key]: cur.includes(v) ? cur.filter((x) => x !== v) : [...cur, v] });
  };
  const active = groups.some((g) => (value[g.key] || []).length);
  return (
    <div className="filterbar">
      {groups.map((g) => (
        <div key={g.key} className="filter-group">
          <span className="filter-label">{g.label}</span>
          {Object.entries(g.options).map(([v, label]) => (
            <button
              key={v}
              className={`pill ${(value[g.key] || []).includes(v) ? "on" : ""}`}
              onClick={() => toggle(g.key, v)}
            >
              {label}
            </button>
          ))}
        </div>
      ))}
      {active && <button className="btn link" onClick={onClear}>Wyczyść filtry</button>}
    </div>
  );
}
