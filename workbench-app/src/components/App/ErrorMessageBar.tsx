// Copyright (c) Microsoft. All rights reserved.

import { Button, MessageBar, MessageBarActions, MessageBarBody, MessageBarTitle } from '@fluentui/react-components';
import { DismissRegular } from '@fluentui/react-icons';
import React from 'react';
import { Utility } from '../../libs/Utility';

interface ErrorMessageBarProps {
    title?: string;
    error?: Record<string, any> | string;
    onDismiss?: () => void;
}

export const ErrorMessageBar: React.FC<ErrorMessageBarProps> = (props) => {
    const { title, error, onDismiss } = props;

    let message = Utility.errorToMessageString(error);
    if (!title && !message) {
        message = 'An unknown error occurred';
    }

    return (
        <MessageBar intent="error" layout="multiline">
            <MessageBarBody>
                <MessageBarTitle>{title ?? 'Error'}:</MessageBarTitle>
                {message}
            </MessageBarBody>
            {onDismiss && (
                <MessageBarActions
                    containerAction={<Button appearance="transparent" icon={<DismissRegular />} onClick={onDismiss} />}
                />
            )}
        </MessageBar>
    );
};
