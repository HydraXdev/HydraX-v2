"use client";

import { useEffect, useState } from "react";
import type { BusTopics, TopicName } from "./contracts";

type TopicHandler<T extends TopicName> = (data: BusTopics[T]) => void;
type Unsubscribe = () => void;

const SOCKET_URL =
  process.env.NEXT_PUBLIC_BUS_URL || "ws://localhost:8888/socket.io";

type GenericHandler = (data: unknown) => void;

/**
 * Real Event Bus Adapter - Production WebSocket Implementation
 *
 * Features:
 * - WebSocket connection with auto-reconnect
 * - Exponential backoff on failures
 * - Heartbeat monitoring
 * - Topic-based message routing
 * - Auth via JWT or cookie
 */
class RealEventBusAdapter {
  private handlers: Map<string, Set<GenericHandler>> = new Map();
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000;
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private lastHeartbeat = Date.now();

  constructor() {
    if (typeof window !== "undefined") {
      this.connect();
    }
  }

  private connect(token?: string) {
    try {
      const url = token
        ? `${SOCKET_URL}?token=${encodeURIComponent(token)}`
        : SOCKET_URL;

      console.log("[EventBus] Connecting to", url);
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log("[EventBus] Connected");
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        this.startHeartbeat();
        this.emit("system.status", {
          secure: true,
          latencyMs: 0,
          hydraNode: "OK",
        });
      };

      this.ws.onmessage = (event) => {
        this.lastHeartbeat = Date.now();
        try {
          const message = JSON.parse(event.data);
          this.route(message);
        } catch (error) {
          console.error("[EventBus] Failed to parse message:", error);
        }
      };

      this.ws.onclose = () => {
        console.log("[EventBus] Disconnected");
        this.stopHeartbeat();
        this.emit("system.status", {
          secure: false,
          latencyMs: -1,
          hydraNode: "DOWN",
        });
        this.scheduleReconnect();
      };

      this.ws.onerror = (error) => {
        console.error("[EventBus] Error:", error);
        this.scheduleReconnect();
      };
    } catch (error) {
      console.error("[EventBus] Failed to create WebSocket:", error);
      this.scheduleReconnect();
    }
  }

  private route(message: { topic?: string; data?: unknown }) {
    // Route message to appropriate topic handlers
    // Expected message format: { topic: string, data: unknown }
    const { topic, data } = message;

    if (!topic) {
      console.warn("[EventBus] Message missing topic:", message);
      return;
    }

    this.emit(topic, data);
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("[EventBus] Max reconnect attempts reached");
      return;
    }

    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
      30000, // Max 30 seconds
    );

    console.log(
      `[EventBus] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`,
    );

    setTimeout(() => {
      this.reconnectAttempts++;
      this.connect();
    }, delay);
  }

  private startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        const latency = Date.now() - this.lastHeartbeat;
        this.ws.send(JSON.stringify({ type: "ping", timestamp: Date.now() }));

        this.emit("system.status", {
          secure: true,
          latencyMs: latency,
          hydraNode: latency < 1000 ? "OK" : "WARN",
        });
      }
    }, 5000); // Every 5 seconds
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  subscribe<T extends TopicName>(
    topic: T,
    handler: TopicHandler<T>,
  ): Unsubscribe {
    if (!this.handlers.has(topic)) {
      this.handlers.set(topic, new Set());
    }

    this.handlers.get(topic)!.add(handler as GenericHandler);

    return () => {
      const handlers = this.handlers.get(topic);
      if (handlers) {
        handlers.delete(handler as GenericHandler);
        if (handlers.size === 0) {
          this.handlers.delete(topic);
        }
      }
    };
  }

  emit<T extends TopicName>(topic: T, data: BusTopics[T]) {
    const handlers = this.handlers.get(topic);
    if (handlers) {
      handlers.forEach((handler) => {
        try {
          (handler as TopicHandler<T>)(data);
        } catch (error) {
          console.error(`[EventBus] Error in handler for ${topic}:`, error);
        }
      });
    }
  }

  send(message: Record<string, unknown>) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn("[EventBus] Cannot send, not connected");
    }
  }

  disconnect() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
const adapter = new RealEventBusAdapter();

export const eventBus = {
  subscribe: adapter.subscribe.bind(adapter),
  emit: adapter.emit.bind(adapter),
  send: adapter.send.bind(adapter),
  disconnect: adapter.disconnect.bind(adapter),
  isConnected: adapter.isConnected.bind(adapter),
};

/**
 * React hook to subscribe to a topic
 */
export function useTopic<T extends TopicName>(
  topic: T,
): { data: BusTopics[T] | null; loading: boolean; error: Error | null } {
  const [data, setData] = useState<BusTopics[T] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const unsubscribe = eventBus.subscribe(topic, (newData) => {
      setData(newData);
      setLoading(false);
      setError(null);
    });

    // Set loading false after short delay if no data
    const timeout = setTimeout(() => setLoading(false), 1000);

    return () => {
      unsubscribe();
      clearTimeout(timeout);
    };
  }, [topic]);

  return { data, loading, error };
}
