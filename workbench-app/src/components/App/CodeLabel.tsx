import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';

const useClasses = makeStyles({
    root: {
        ...shorthands.border(tokens.strokeWidthThin, 'solid', tokens.colorNeutralStroke2),
        borderRadius: tokens.borderRadiusMedium,
        backgroundColor: tokens.colorNeutralBackground3,
        ...shorthands.padding(tokens.spacingVerticalXXS, tokens.spacingHorizontalS),
    },
});

interface CodeLabelProps {
    children?: React.ReactNode;
}

export const CodeLabel: React.FC<CodeLabelProps> = (props) => {
    const { children } = props;
    const classes = useClasses();

    return <span className={classes.root}>{children}</span>;
};
