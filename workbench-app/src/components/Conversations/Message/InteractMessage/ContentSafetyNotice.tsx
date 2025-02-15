import { mergeClasses } from '@fluentui/react-components';
import React from 'react';

type ContentSafetyNoticeProps = {
    contentSafety: { result: string; note?: string } | null;
    noticeClass: string;
    safetyClass: string;
};

export const ContentSafetyNotice: React.FC<ContentSafetyNoticeProps> = ({
    contentSafety,
    noticeClass,
    safetyClass,
}) => {
    if (!contentSafety || !contentSafety.result || contentSafety.result === 'pass') return null;

    const messageNote = `[Content Safety: ${contentSafety.result}] ${
        contentSafety.note || 'this message has been flagged as potentially unsafe'
    }`;

    return <div className={mergeClasses(noticeClass, safetyClass)}>{messageNote}</div>;
};
