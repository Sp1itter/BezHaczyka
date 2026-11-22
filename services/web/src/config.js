// Marka i nawigacja w jednym miejscu.
// Zalogowany analityk (placeholder do czasu logowania). Decyzje zapisywane sa na jego konto.
export const DEFAULT_USER = "Anna";

export const BRAND = {
  name: "BezHaczyka",
  subtitle: "nadzór reklam",
  identity: "InvestWatch / UKNF",
};

const ICON = {
  grid: ["M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z"],
  shield: ["M12 3 4.5 6v5.2c0 4.7 3.2 8.5 7.5 9.8 4.3-1.3 7.5-5.1 7.5-9.8V6L12 3Z", "M12 8v4M12 16h.01"],
  clipboard: ["M9 4h6M9 4a2 2 0 0 0-2 2H5v15h14V6h-2a2 2 0 0 0-2-2M8 13l2.5 2.5L16 10"],
  inbox: ["M4 5h16v14H4zM4 14h4l2 2h4l2-2h4"],
  network: ["M7 7a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM17 13a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM7 23a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM9.5 8.5l5 2M9.5 17.5l5-2"],
  flask: ["M9 3h6M10 3v5l-5 9a2 2 0 0 0 1.8 3h10.4a2 2 0 0 0 1.8-3l-5-9V3M8 14h8"],
  server: ["M4 4h16v6H4zM4 14h16v6H4zM8 7h.01M8 17h.01"],
};

export const NAV_GROUPS = [
  {
    id: "operations",
    label: "Praca",
    items: [
      { id: "overview", label: "Przegląd", href: "#/", icon: ICON.grid },
      { id: "alerts", label: "Alerty", href: "#/alerts", icon: ICON.shield },
      { id: "findings", label: "Wyniki", href: "#/findings", icon: ICON.inbox },
    ],
  },
  {
    id: "reports",
    label: "Raporty",
    items: [
      { id: "module1", label: "Moduł 1: podmioty", href: "#/module1", icon: ICON.network },
      { id: "module3", label: "Moduł 3: doradztwo", href: "#/module3", icon: ICON.clipboard },
    ],
  },
  {
    id: "system",
    label: "System",
    items: [
      { id: "calibration", label: "Kalibracja", href: "#/calibration", icon: ICON.flask },
      { id: "operator", label: "Operator", href: "#/operator", icon: ICON.server },
    ],
  },
];
