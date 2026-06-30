"use client";
import { useEffect, useState } from "react";

function formatTime(d: Date): string {
  return d.toLocaleTimeString("en-GB", { hour12: false });
}

export default function LiveClock() {
  const [time, setTime] = useState("");
  const [tz, setTz] = useState("");

  useEffect(() => {
    setTz(Intl.DateTimeFormat().resolvedOptions().timeZone);
    setTime(formatTime(new Date()));
    const id = setInterval(() => setTime(formatTime(new Date())), 1000);
    return () => clearInterval(id);
  }, []);

  if (!time) return null;
  return (
    <span role="status" aria-live="polite" className="live-clock">
      {time} · {tz}
    </span>
  );
}
