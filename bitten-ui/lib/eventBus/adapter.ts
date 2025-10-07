"use client";

import { useEffect, useState } from "react";
import type { BusTopics, TopicName } from "./contracts";

// TODO: Wire to actual backend SSE/WebSocket endpoint
const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8888";

type TopicHandler<T extends TopicName> = (data: BusTopics[T]) => void;
type Unsubscribe = () => void;

/**
 * Event bus adapter - thin layer over backend event stream
 * Provides subscribe(topic, handler) and useTopic<T>(topic) hook
 *
 * NOTE: This is a stub. In production:
 * 1. Connect to SSE endpoint at ${BACKEND_URL}/events or WebSocket
 * 2. Parse incoming messages and route by topic
 * 3. Handle reconnection logic
 */

type GenericHandler = (data: unknown) => void;

class EventBusAdapter {
  private handlers: Map<string, Set<GenericHandler>> = new Map();
  private connected = false;
  private eventSource?: EventSource;

  constructor() {
    if (
      typeof window !== "undefined" &&
      process.env.NEXT_PUBLIC_USE_MOCKS !== "1"
    ) {
      this.connect();
    }
  }

  private connect() {
    // TODO: Connect to real backend SSE/WebSocket
    // Example SSE connection:
    // this.eventSource = new EventSource(`${BACKEND_URL}/events`);
    // this.eventSource.onmessage = (event) => {
    //   const { topic, data } = JSON.parse(event.data);
    //   this.emit(topic, data);
    // };
    console.log("[EventBus] Stub - would connect to", BACKEND_URL);
    this.connected = true;
  }

  subscribe<T extends TopicName>(
    topic: T,
    handler: TopicHandler<T>,
  ): Unsubscribe {
    if (!this.handlers.has(topic)) {
      this.handlers.set(topic, new Set());
    }

    this.handlers.get(topic)!.add(handler as GenericHandler);

    // Return unsubscribe function
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

  disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = undefined;
    }
    this.connected = false;
  }

  isConnected(): boolean {
    return this.connected;
  }
}

// Singleton instance
const adapter = new EventBusAdapter();

export const eventBus = {
  subscribe: adapter.subscribe.bind(adapter),
  emit: adapter.emit.bind(adapter),
  isConnected: adapter.isConnected.bind(adapter),
};

/**
 * React hook to subscribe to a topic
 * Returns { data, loading, error }
 *
 * Usage:
 *   const { data: profile, loading } = useTopic('user.profile');
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

    // Simulate loading delay in dev mode
    if (process.env.NEXT_PUBLIC_USE_MOCKS === "1") {
      setTimeout(() => setLoading(false), 100);
    }

    return unsubscribe;
  }, [topic]);

  return { data, loading, error };
}
