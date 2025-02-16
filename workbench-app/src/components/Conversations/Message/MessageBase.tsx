import { makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
    },
    actions: {
        display: 'flex',
        flexDirection: 'row',
        gap: '8px',
        ...shorthands.margin(0, tokens.spacingHorizontalS),
    },
    body: {
        marginTop: tokens.spacingVerticalXS,
    },
});

interface MessageBaseProps {
    className?: string;
    header: React.ReactNode;
    body: React.ReactNode;
    actions?: React.ReactNode;
    footer?: React.ReactNode;
}

export const MessageBase: React.FC<MessageBaseProps> = (props) => {
    const { className, header, body, actions, footer } = props;
    const classes = useClasses();

    return (
        <div className={mergeClasses(classes.root, className)}>
            {header}
            <div className={classes.body}>{body}</div>
            {actions && <div className={classes.actions}>{actions}</div>}
            {footer}
        </div>
    );
};
