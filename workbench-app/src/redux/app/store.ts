import { Action, ThunkAction, configureStore } from '@reduxjs/toolkit';
import { workbenchApi } from '../../services/workbench';
import appReducer from '../features/app/appSlice';
import chatCanvasReducer from '../features/chatCanvas/chatCanvasSlice';
import settingsReducer from '../features/settings/settingsSlice';
import { rtkQueryErrorLogger } from './rtkQueryErrorLogger';

export const store = configureStore({
    reducer: {
        app: appReducer,
        chatCanvas: chatCanvasReducer,
        settings: settingsReducer,
        [workbenchApi.reducerPath]: workbenchApi.reducer,
    },
    middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(workbenchApi.middleware, rtkQueryErrorLogger),
});

export type AppDispatch = typeof store.dispatch;
export type RootState = ReturnType<typeof store.getState>;
export type AppThunk<ReturnType = void> = ThunkAction<ReturnType, RootState, unknown, Action<string>>;
