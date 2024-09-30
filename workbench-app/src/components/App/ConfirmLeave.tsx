// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { unstable_usePrompt } from 'react-router-dom';

interface ConfirmLeaveProps {
    isDirty: boolean;
    onConfirm?: () => void;
}

export const ConfirmLeave: React.FC<ConfirmLeaveProps> = (props) => {
    const { isDirty } = props;

    const alertUser = (event: BeforeUnloadEvent) => {
        event.preventDefault();
        event.returnValue = '';
    };

    unstable_usePrompt({
        when: isDirty,
        message: 'Changes you made may not be saved.',
    });

    React.useEffect(() => {
        if (isDirty) {
            window.addEventListener('beforeunload', alertUser);
        } else {
            window.removeEventListener('beforeunload', alertUser);
        }
        return () => {
            window.removeEventListener('beforeunload', alertUser);
        };
    }, [isDirty]);

    return null;
};
