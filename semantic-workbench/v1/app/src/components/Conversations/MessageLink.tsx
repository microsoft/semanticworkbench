// Copyright (c) Microsoft. All rights reserved.
import { makeStyles } from '@fluentui/react-components';
import { LinkRegular } from '@fluentui/react-icons';
import React from 'react';
import { useLocation } from 'react-router-dom';
import { CopyButton } from '../App/CopyButton';

const useClasses = makeStyles({
    root: {
        display: 'inline-block',
    },
});

interface MessageLinkProps {
    messageId: string;
}

export const MessageLink: React.FC<MessageLinkProps> = ({ messageId }) => {
    const classes = useClasses();
    const location = useLocation();
    const path = location.pathname + `#${messageId}`;
    const link = `${window.location.origin}${path}`;
    return (
        <div className={classes.root}>
            <CopyButton
                icon={<LinkRegular />}
                appearance="subtle"
                data={link}
                tooltip="Copy message link"
                size="small"
            />
        </div>
    );
};
