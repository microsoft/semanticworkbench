// Copyright (c) Microsoft. All rights reserved.

import { ProgressBar } from '@fluentui/react-components';
import React from 'react';
import { Conversation } from '../../models/Conversation';

interface FileListProps {
    conversation: Conversation;
}

export const ContextWindow: React.FC<FileListProps> = (props) => {
    const { conversation } = props;

    const tokenCountToDisplay = (count: number | undefined, includeLabel: boolean = true) => {
        const label = includeLabel ? ' token' + (count !== 1 ? 's' : '') : '';
        if (!count) {
            return `0${label}`;
        }
        if (count < 1_000) {
            return `${count}${label}`;
        } else if (count < 1_000_000) {
            return `${(count / 1_000).toFixed(1).toString().replaceAll('.0', '')}k${label}`;
        } else {
            return `${(count / 1_000_000).toFixed(1).toString().replaceAll('.0', '')}m${label}`;
        }
    };

    if (conversation.metadata?.token_counts === undefined) {
        return 'Token count not available';
    }

    const { total: totalTokenCount, max: maxTokenCount } = conversation.metadata?.token_counts;

    return (
        <>
            {tokenCountToDisplay(totalTokenCount, false)} of {tokenCountToDisplay(maxTokenCount)} (
            {Math.floor((totalTokenCount / maxTokenCount) * 100)}%)
            <ProgressBar thickness="large" value={totalTokenCount / maxTokenCount}></ProgressBar>
        </>
    );
};
