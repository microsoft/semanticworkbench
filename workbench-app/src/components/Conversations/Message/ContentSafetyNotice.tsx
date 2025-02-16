import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';

const useClasses = makeStyles({
    root: {
        width: 'fit-content',
        fontSize: tokens.fontSizeBase200,
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
        alignItems: 'center',
        color: tokens.colorPaletteRedForeground1,
        ...shorthands.padding(tokens.spacingVerticalXS, tokens.spacingHorizontalS),
    },
});

interface ContentSafetyNoticeProps {
    contentSafety?: { result: string; note?: string };
}

export const ContentSafetyNotice: React.FC<ContentSafetyNoticeProps> = (props) => {
    const { contentSafety } = props;
    const classes = useClasses();

    if (!contentSafety || !contentSafety.result || contentSafety.result === 'pass') return null;

    const messageNote = `[Content Safety: ${contentSafety.result}] ${
        contentSafety.note || 'this message has been flagged as potentially unsafe'
    }`;

    return <div className={classes.root}>{messageNote}</div>;
};
