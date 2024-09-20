export interface InteractCanvasState {
    open?: boolean;
    mode?: 'conversation' | 'assistant';
    assistantId?: string | null;
    assistantStateId?: string | null;
}
