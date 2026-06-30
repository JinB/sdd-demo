import React, { useState, useEffect } from "react";

function formatTime(date: Date): string {
  return date.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

export default function LiveClock(): React.JSX.Element | null {
  const [time, setTime] = useState<string>("");
  const [timezone, setTimezone] = useState<string>("");

  useEffect(() => {
    setTimezone(Intl.DateTimeFormat().resolvedOptions().timeZone);
    setTime(formatTime(new Date()));
    const interval = setInterval(() => {
      setTime(formatTime(new Date()));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  if (!time) return null;

  return (
    <span
      role="status"
      aria-live="polite"
      style={{ fontSize: "0.85rem", opacity: 0.8, whiteSpace: "nowrap" }}
    >
      {time} · {timezone}
    </span>
  );
}
