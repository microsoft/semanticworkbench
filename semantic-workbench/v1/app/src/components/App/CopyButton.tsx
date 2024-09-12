// Copyright (c) Microsoft. All rights reserved.

import { Button, Slot, Tooltip, makeStyles, tokens } from '@fluentui/react-components';
import { CopyRegular } from '@fluentui/react-icons';
import React from 'react';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        alignItems: 'center',
        gap: tokens.spacingHorizontalS,
    },
});

interface CopyButtonProps {
    data: string;
    icon?: Slot<'span'>;
    appearance?: 'secondary' | 'primary' | 'outline' | 'subtle' | 'transparent';
    tooltip?: string;
    size?: 'small' | 'medium' | 'large';
    noticeOn?: 'left' | 'right';
}

export const CopyButton: React.FC<CopyButtonProps> = (props) => {
    const { data, icon, appearance, tooltip, size, noticeOn = 'right' } = props;
    const classes = useClasses();
    const [copied, setCopied] = React.useState(false);

    const handleCopy = React.useCallback(async () => {
        await navigator.clipboard.writeText(data);
        setCopied(true);
        setTimeout(() => {
            setCopied(false);
        }, 2000);
    }, [data]);

    const button = (
        <Button as="a" appearance={appearance} size={size} icon={icon ?? <CopyRegular />} onClick={handleCopy} />
    );

    const content = tooltip ? (
        <Tooltip content={tooltip} relationship="label">
            {button}
        </Tooltip>
    ) : (
        button
    );

    return (
        <div className={classes.root}>
            {noticeOn === 'left' && copied && <span>Copied!</span>}
            {content}
            {noticeOn === 'right' && copied && <span>Copied!</span>}
        </div>
    );
};
