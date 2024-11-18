import {
    Slot,
    Toast,
    ToastBody,
    ToastFooter,
    ToastIntent,
    ToastTitle,
    ToastTrigger,
    useToastController,
} from '@fluentui/react-components';
import React from 'react';
import { Constants } from '../Constants';

interface NotifyOptions {
    id: string;
    title?: string;
    message: string;
    subtitle?: string;
    action?: Slot<'div'> | string;
    additionalActions?: React.ReactElement[];
    timeout?: number;
    intent: ToastIntent;
}

export const useNotify = (toasterId: string = Constants.app.globalToasterId) => {
    const { dispatchToast } = useToastController(toasterId);

    const notify = React.useCallback(
        (options: NotifyOptions) => {
            const { id, title, message, subtitle, action, additionalActions, timeout, intent } = options;

            const getAction = () => {
                if (typeof action === 'string') {
                    return (
                        <ToastTrigger>
                            <span>{action}</span>
                        </ToastTrigger>
                    );
                }
                return action;
            };

            dispatchToast(
                <Toast>
                    <ToastTitle action={getAction()}>{title}</ToastTitle>
                    <ToastBody subtitle={subtitle}>{message}</ToastBody>
                    {additionalActions && <ToastFooter>{additionalActions}</ToastFooter>}
                </Toast>,
                {
                    toastId: id,
                    timeout,
                    intent,
                },
            );
        },
        [dispatchToast],
    );

    const notifySuccess = React.useCallback(
        (options: Omit<NotifyOptions, 'intent'>) =>
            notify({
                ...options,
                intent: 'success',
            }),
        [notify],
    );

    const notifyInfo = React.useCallback(
        (options: Omit<NotifyOptions, 'intent'>) =>
            notify({
                ...options,
                intent: 'info',
            }),
        [notify],
    );

    const notifyWarning = React.useCallback(
        (options: Omit<NotifyOptions, 'intent'>) =>
            notify({
                ...options,
                intent: 'warning',
            }),
        [notify],
    );

    const notifyError = React.useCallback(
        (options: Omit<NotifyOptions, 'intent'>) =>
            notify({
                action: 'Dismiss',
                timeout: -1,
                ...options,
                intent: 'error',
            }),
        [notify],
    );

    return { notify, notifySuccess, notifyInfo, notifyError, notifyWarning };
};
