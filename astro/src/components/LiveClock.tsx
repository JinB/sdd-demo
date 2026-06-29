import { useState, useEffect } from "react";

function formatTime(date: Date): string {
  return date.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

export default function LiveClock() {
  const [time, setTime] = useState<string>("");
  const [timezone, setTimezone] = useState<string>("");

  useEffect(() => {
    setTimezone(new Intl.DateTimeFormat().resolvedOptions().timeZone);
    setTime(formatTime(new Date()));

    const interval = setInterval(() => {
      setTime(formatTime(new Date()));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  if (!time) return null;

  return (
    <span role="status" aria-live="polite" aria-label={`Current time: ${time} ${timezone}`}>
      {time} · {timezone}
    </span>
  );
}
