import React from 'react';

interface ContentSafetyNoticeProps {
    contentSafety?: { result: string; note?: string };
    className?: string;
}

export const ContentSafetyNotice: React.FC<ContentSafetyNoticeProps> = (props) => {
    const { contentSafety, className } = props;

    if (!contentSafety || !contentSafety.result || contentSafety.result === 'pass') return null;

    const messageNote = `[Content Safety: ${contentSafety.result}] ${
        contentSafety.note || 'this message has been flagged as potentially unsafe'
    }`;

    return <div className={className}>{messageNote}</div>;
};
