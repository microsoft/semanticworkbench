// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogOpenChangeData, DialogOpenChangeEvent, Field, Input } from '@fluentui/react-components';
import { Copy24Regular, Share24Regular } from '@fluentui/react-icons';
import React from 'react';
import { CommandButton } from '../App/CommandButton';

interface ConversationShareProps {
    conversationId: string;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ConversationShare: React.FC<ConversationShareProps> = (props) => {
    const { conversationId, iconOnly, asToolbarButton } = props;
    const linkRef = React.useRef<HTMLInputElement>(null);
    const [copiedTimeout, setCopiedTimeout] = React.useState<NodeJS.Timeout>();

    if (!conversationId) {
        throw new Error('ConversationId is required');
    }

    const link = `${window.location.origin}/conversation/${conversationId}`;

    const handleOpenChange = React.useCallback(
        (_event: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
            if (!data.open) {
                return;
            }

            // clear the copied timeout when the dialog is opened
            if (copiedTimeout) {
                clearTimeout(copiedTimeout);
                setCopiedTimeout(undefined);
            }

            // wait for the dialog to open before selecting the link
            setTimeout(() => {
                linkRef.current?.select();
            }, 0);
        },
        [copiedTimeout],
    );

    const handleCopy = React.useCallback(async () => {
        if (copiedTimeout) {
            clearTimeout(copiedTimeout);
            setCopiedTimeout(undefined);
        }

        await navigator.clipboard.writeText(link);

        // set a timeout to clear the copied message
        const timeout = setTimeout(() => {
            setCopiedTimeout(undefined);
        }, 2000);
        setCopiedTimeout(timeout);
    }, [link, copiedTimeout]);

    return (
        <CommandButton
            icon={<Share24Regular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            label="Share"
            description="Share conversation link"
            dialogContent={{
                title: 'Share Conversation',
                content: (
                    <>
                        <Field
                            label={`Send this link to others to share this conversation ${
                                copiedTimeout ? ' (Copied to clipboard!)' : ''
                            }`}
                        >
                            <Input
                                ref={linkRef}
                                value={link}
                                readOnly
                                contentAfter={
                                    <Button appearance="transparent" icon={<Copy24Regular />} onClick={handleCopy} />
                                }
                            />
                        </Field>
                    </>
                ),
                onOpenChange: handleOpenChange,
            }}
        />
    );
};
