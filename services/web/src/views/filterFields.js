// Pola filtrow (kolejnosc i typy kontrolek jak w szufladzie filtrow wzorca).
import { MODULE, RISK, SOURCE, STATUS } from "../lib/labels.js";

const search = { name: "q", label: "Szukaj", type: "search", placeholder: "Tytuł, publikujący lub treść" };
const risk = { name: "risk", label: "Poziom ryzyka", type: "select", options: RISK };
const module = { name: "module", label: "Moduł", type: "select", options: MODULE };
const status = { name: "status", label: "Status", type: "select", options: STATUS };
const source = { name: "source", label: "Źródło", type: "select", options: SOURCE };
const from = { name: "from", label: "Od", type: "date" };
const to = { name: "to", label: "Do", type: "date" };

export const FILTER_FIELDS = [search, from, to, source, risk, module, status];
export const ALERT_FIELDS = [search, module, status, source];
