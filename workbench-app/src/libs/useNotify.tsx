import {
    Slot,
    Toast,
    ToastBody,
    Toaster,
    ToastFooter,
    ToastIntent,
    ToastTitle,
    useId,
    useToastController,
} from '@fluentui/react-components';
import React from 'react';
import { Constants } from '../Constants';

interface NotifyOptions {
    title?: string;
    message: string;
    details?: string;
    action?: Slot<'div'>;
    additionalActions?: React.ReactElement[];
    intent: ToastIntent;
}

export const useGlobalNotify = () => {
    const { dispatchToast } = useToastController(Constants.app.globalToasterId);

    const notify = React.useCallback(
        (options: NotifyOptions) => {
            const { title, message, details, action, additionalActions, intent } = options;
            dispatchToast(
                <Toast>
                    <ToastTitle action={action}>{title}</ToastTitle>
                    <ToastBody subtitle={details}>{message}</ToastBody>
                    {additionalActions && <ToastFooter>{additionalActions}</ToastFooter>}
                </Toast>,
                { intent },
            );
        },
        [dispatchToast],
    );

    const notifyWarning = React.useCallback(
        (options: Omit<NotifyOptions, 'intent'>) => notify({ ...options, intent: 'warning' }),
        [notify],
    );

    const notifyError = React.useCallback(
        (options: Omit<NotifyOptions, 'intent'>) => notify({ ...options, intent: 'error' }),
        [notify],
    );

    return { notify, notifyError, notifyWarning };
};

export const useInlineNotify = () => {
    const toasterId = useId();
    const { dispatchToast } = useToastController(toasterId);

    const notify = React.useCallback(
        (options: NotifyOptions) => {
            const { title, message, details, action, additionalActions, intent } = options;
            dispatchToast(
                <Toast>
                    <ToastTitle action={action}>{title}</ToastTitle>
                    <ToastBody subtitle={details}>{message}</ToastBody>
                    {additionalActions && <ToastFooter>{additionalActions}</ToastFooter>}
                </Toast>,
                { intent },
            );
        },
        [dispatchToast],
    );

    const notifyWarning = React.useCallback(
        (options: Omit<NotifyOptions, 'intent'>) => notify({ ...options, intent: 'warning' }),
        [notify],
    );

    const notifyError = React.useCallback(
        (options: Omit<NotifyOptions, 'intent'>) => notify({ ...options, intent: 'error' }),
        [notify],
    );

    const NotifyElement = <Toaster toasterId={toasterId} />;

    return { notify, notifyError, notifyWarning, NotifyElement };
};
