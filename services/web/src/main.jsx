import React from "react";
import { createRoot } from "react-dom/client";
import { MantineProvider } from "@mantine/core";
import { DatesProvider } from "@mantine/dates";
import { Notifications } from "@mantine/notifications";
import dayjs from "dayjs";
import "dayjs/locale/pl";
import "@mantine/core/styles.css";
import "@mantine/dates/styles.css";
import "@mantine/notifications/styles.css";
import "mantine-react-table/styles.css";
import "./app.css";
import App from "./App.jsx";
import { theme } from "./theme.js";

dayjs.locale("pl");

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <MantineProvider theme={theme} forceColorScheme="light">
      <DatesProvider settings={{ locale: "pl", firstDayOfWeek: 1 }}>
        <Notifications position="bottom-right" autoClose={8000} limit={3} />
        <App />
      </DatesProvider>
    </MantineProvider>
  </React.StrictMode>,
);
