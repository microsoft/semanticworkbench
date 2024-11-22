type Listener = (event: any) => void;

export class EventSubscriptionManager {
    private listeners: Map<string, Set<Listener>>;

    constructor() {
        this.listeners = new Map();
    }

    addEventListener(eventName: string, listener: Listener) {
        if (!this.listeners.has(eventName)) {
            this.listeners.set(eventName, new Set());
        }
        this.listeners.get(eventName)!.add(listener);
    }

    removeEventListener(eventName: string, listener: Listener) {
        if (!this.listeners.has(eventName)) return;

        const listeners = this.listeners.get(eventName)!;
        listeners.delete(listener);

        if (listeners.size === 0) {
            this.listeners.delete(eventName);
        }
    }

    emit(eventName: string, event: any) {
        if (!this.listeners.has(eventName)) return;

        this.listeners.get(eventName)!.forEach((listener) => listener(event));
    }
}
