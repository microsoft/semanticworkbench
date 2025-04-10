// Re-export everything from the individual modules
export { listBreakpoints, listBreakpointsSchema, setBreakpoint, setBreakpointSchema } from './breakpoints';
export { activeSessions, getCallStack } from './common';
export type { BreakpointHitInfo } from './common';
export {
    breakpointEventEmitter,
    onBreakpointHit,
    subscribeToBreakpointEvents,
    subscribeToBreakpointEventsSchema,
    waitForBreakpointHit,
    waitForBreakpointHitSchema,
} from './events';
export { getCallStackSchema, getStackFrameVariables, getStackFrameVariablesSchema } from './inspection';
export {
    listDebugSessions,
    listDebugSessionsSchema,
    resumeDebugSession,
    resumeDebugSessionSchema,
    startDebugSession,
    startDebugSessionSchema,
    stopDebugSession,
    stopDebugSessionSchema,
} from './session';
