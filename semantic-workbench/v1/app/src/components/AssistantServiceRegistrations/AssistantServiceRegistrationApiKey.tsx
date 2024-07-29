// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogSurface,
    DialogTitle,
    Field,
    Input,
    Text,
    makeStyles,
} from '@fluentui/react-components';
import { Copy24Regular } from '@fluentui/react-icons';
import React from 'react';

const useClasses = makeStyles({
    row: {
        display: 'flex',
        alignItems: 'center',
    },
});

interface AssistantServiceRegistrationApiKeyProps {
    apiKey: string;
    onClose: () => void;
}

export const AssistantServiceRegistrationApiKey: React.FC<AssistantServiceRegistrationApiKeyProps> = (props) => {
    const { apiKey, onClose } = props;
    const classes = useClasses();
    const inputRef = React.useRef<HTMLInputElement>(null);
    const [copiedTimeout, setCopiedTimeout] = React.useState<NodeJS.Timeout>();

    React.useEffect(() => {
        // wait for the dialog to open before selecting the link
        setTimeout(() => {
            inputRef.current?.select();
        }, 0);
    }, []);

    const handleCopy = React.useCallback(async () => {
        if (copiedTimeout) {
            clearTimeout(copiedTimeout);
            setCopiedTimeout(undefined);
        }

        await navigator.clipboard.writeText(apiKey);

        // set a timeout to clear the copied message
        const timeout = setTimeout(() => {
            setCopiedTimeout(undefined);
        }, 2000);
        setCopiedTimeout(timeout);
    }, [apiKey, copiedTimeout]);

    return (
        <Dialog open={true} onOpenChange={onClose}>
            <DialogSurface>
                <DialogBody>
                    <DialogTitle>Assistant Service Registration API Key</DialogTitle>
                    <DialogContent>
                        <Field>
                            <Input
                                ref={inputRef}
                                value={apiKey}
                                readOnly
                                contentAfter={
                                    <div className={classes.row}>
                                        {copiedTimeout && <Text>Copied to clipboard!</Text>}
                                        <Button
                                            appearance="transparent"
                                            icon={<Copy24Regular />}
                                            onClick={handleCopy}
                                        />
                                    </div>
                                }
                            />
                        </Field>
                        <p>
                            <Text>
                                Make sure to copy the API key before closing this dialog, as it will not be displayed
                                again.
                            </Text>
                        </p>
                    </DialogContent>
                    <DialogActions>
                        <Button appearance="primary" onClick={onClose}>
                            Close
                        </Button>
                    </DialogActions>
                </DialogBody>
            </DialogSurface>
        </Dialog>
    );
};
