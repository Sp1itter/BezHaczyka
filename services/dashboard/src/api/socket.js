// Alerty na zywo przez Socket.io. [DB-7]
// Mock emituje: "finding.high", "finding.new", "finding.updated".
// Przy integracji: albo socket.io w services/api (python-socketio), albo adapter na natywny WS /ws/alerts.
import { io } from "socket.io-client";

export function connectAlerts({ onHigh, onNew, onUpdated, onState }) {
  const socket = io(import.meta.env.VITE_SOCKET_URL || "/", { path: "/socket.io", transports: ["websocket", "polling"] });
  socket.on("connect", () => onState?.(true));
  socket.on("disconnect", () => onState?.(false));
  socket.on("finding.high", (a) => onHigh?.(a));
  socket.on("finding.new", (a) => onNew?.(a));
  socket.on("finding.updated", (a) => onUpdated?.(a));
  return () => socket.close();
}
