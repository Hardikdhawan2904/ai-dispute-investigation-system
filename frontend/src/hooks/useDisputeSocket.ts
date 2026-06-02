"use client";
import { useEffect, useRef, useCallback, useState } from "react";

export type DisputeSocketEventType =
  | "DISPUTE_QUEUED"
  | "ANALYSIS_COMPLETE"
  | "ANALYSIS_FAILED";

export interface DisputeQueuedEvent {
  type: "DISPUTE_QUEUED";
  case_id: string;
  customer_id: string;
  customer_name: string;
  merchant: string;
  amount: number;
  currency: string;
  timestamp: string;
}

export interface AnalysisCompleteEvent {
  type: "ANALYSIS_COMPLETE";
  case_id: string;
  case: Record<string, unknown>;
}

export interface AnalysisFailedEvent {
  type: "ANALYSIS_FAILED";
  case_id: string;
  errors: string[];
}

export type DisputeSocketEvent =
  | DisputeQueuedEvent
  | AnalysisCompleteEvent
  | AnalysisFailedEvent;

const WS_URL =
  (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000")
    .replace(/^http/, "ws") + "/ws/disputes";

const BACKOFF_BASE = 2_000;
const BACKOFF_MAX  = 30_000;

export function useDisputeSocket(
  onEvent: (event: DisputeSocketEvent) => void
): { isConnected: boolean } {
  const [isConnected, setIsConnected]  = useState(false);
  // Always holds the latest callback without causing the effect to re-run.
  const onEventRef    = useRef(onEvent);
  onEventRef.current  = onEvent;

  const isMounted     = useRef(true);
  const wsRef         = useRef<WebSocket | null>(null);
  const retryCount    = useRef(0);
  const retryTimeout  = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    if (!isMounted.current) return;

    const ws        = new WebSocket(WS_URL);
    wsRef.current   = ws;          // set immediately so old sockets detect they're superseded

    ws.onopen = () => {
      // If cleanup ran and a newer socket was created, discard this one silently.
      if (wsRef.current !== ws) { ws.close(); return; }
      retryCount.current = 0;
      setIsConnected(true);
      const ping = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send("ping");
        else clearInterval(ping);
      }, 20_000);
    };

    ws.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data) as DisputeSocketEvent;
        onEventRef.current(event);
      } catch {
        // ignore malformed frames
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      // Only the current socket should schedule a reconnect.
      if (!isMounted.current || wsRef.current !== ws) return;

      retryCount.current += 1;
      const delay = Math.min(BACKOFF_BASE * 2 ** (retryCount.current - 1), BACKOFF_MAX);
      retryTimeout.current = setTimeout(connect, delay);
    };

    ws.onerror = () => {
      // No-op: the browser automatically closes the socket on error and fires onclose.
      // Calling ws.close() here while readyState is still CONNECTING produces a
      // spurious "WebSocket is closed before the connection is established" warning.
    };
  }, []);

  useEffect(() => {
    isMounted.current  = true;
    retryCount.current = 0;
    connect();

    return () => {
      isMounted.current = false;
      if (retryTimeout.current) clearTimeout(retryTimeout.current);
      const ws = wsRef.current;
      if (!ws) return;
      // Only close sockets that are already open/closing.
      // A CONNECTING socket will detect it has been superseded via wsRef identity
      // check in onopen, and close itself then — avoids the browser console warning
      // "WebSocket is closed before the connection is established."
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CLOSING) {
        ws.close();
      }
    };
  }, [connect]);

  return { isConnected };
}
