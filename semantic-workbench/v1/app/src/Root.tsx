import React from 'react';
import { Outlet } from 'react-router-dom';
import { useKeySequence } from './libs/useKeySequence';
import { useAppDispatch } from './redux/app/hooks';
import { toggleDevMode } from './redux/features/app/appSlice';

export const Root: React.FC = () => {
    const dispatch = useAppDispatch();
    useKeySequence(
        [
            'ArrowUp',
            'ArrowUp',
            'ArrowDown',
            'ArrowDown',
            'ArrowLeft',
            'ArrowRight',
            'ArrowLeft',
            'ArrowRight',
            'b',
            'a',
            'Enter',
        ],
        () => dispatch(toggleDevMode()),
    );

    return <Outlet />;
};
