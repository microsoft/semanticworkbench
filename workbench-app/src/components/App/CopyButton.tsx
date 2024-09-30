// Copyright (c) Microsoft. All rights reserved.

import { Button, Slot, Tooltip, makeStyles, tokens } from '@fluentui/react-components';
import { Checkmark24Regular, CopyRegular } from '@fluentui/react-icons';
import React from 'react';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        alignItems: 'center',
        gap: tokens.spacingHorizontalS,
    },
});

interface CopyButtonProps {
    data: string | (() => Promise<string>);
    icon?: Slot<'span'>;
    appearance?: 'secondary' | 'primary' | 'outline' | 'subtle' | 'transparent';
    tooltip?: string;
    size?: 'small' | 'medium' | 'large';
}

export const CopyButton: React.FC<CopyButtonProps> = (props) => {
    const { data, icon, appearance, tooltip, size } = props;
    const classes = useClasses();
    const [copying, setCopying] = React.useState(false);
    const [copied, setCopied] = React.useState(false);

    const handleCopy = React.useCallback(async () => {
        setCopying(true);
        try {
            const text = typeof data === 'function' ? await data() : data;
            await navigator.clipboard.writeText(text);
        } finally {
            setCopying(false);
        }
        setCopied(true);
        setTimeout(() => {
            setCopied(false);
        }, 2000);
    }, [data, setCopying]);

    const copyIcon = React.useCallback(() => {
        return copied ? <Checkmark24Regular /> : icon ?? <CopyRegular />;
    }, [copied, icon]);

    const button = (
        <Button as="a" appearance={appearance} size={size} disabled={copying} icon={copyIcon()} onClick={handleCopy} />
    );

    const content = tooltip ? (
        <Tooltip content={tooltip} relationship="label">
            {button}
        </Tooltip>
    ) : (
        button
    );

    return <div className={classes.root}>{content}</div>;
};
