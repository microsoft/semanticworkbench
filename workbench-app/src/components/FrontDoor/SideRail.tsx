import { Button, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import {
    PanelLeftContractRegular,
    PanelLeftExpandRegular,
    PanelRightContractRegular,
    PanelRightExpandRegular,
} from '@fluentui/react-icons';
import React from 'react';

const useClasses = makeStyles({
    rail: {
        flex: '0 0 auto',
        backgroundColor: tokens.colorNeutralBackground2,
        ...shorthands.transition('width', tokens.durationSlow, tokens.curveAccelerateMax),
        overflow: 'hidden',
        ...shorthands.padding(
            tokens.spacingVerticalXXXL,
            tokens.spacingHorizontalM,
            tokens.spacingVerticalM,
            tokens.spacingHorizontalM,
        ),
        boxSizing: 'border-box',
    },
    collapsed: {
        width: '40px',
    },
    sideRailLeft: {
        borderRight: `1px solid ${tokens.colorNeutralBackground2}`,
        width: '300px',
    },
    sideRailRight: {
        borderLeft: `1px solid ${tokens.colorNeutralBackground2}`,
        width: '300px',
    },
    pinButton: {
        position: 'absolute',
        top: tokens.spacingVerticalXS,
        zIndex: tokens.zIndexFloating,
    },
    pinButtonLeft: {
        left: tokens.spacingHorizontalXS,
    },
    pinButtonRight: {
        right: tokens.spacingHorizontalXS,
    },
    content: {
        opacity: 0,
        position: 'relative',
        height: '100%',
        width: '100%',
        ...shorthands.transition('opacity', tokens.durationFast, '0', tokens.curveEasyEase),
    },
    contentOpen: {
        opacity: 1,
        ...shorthands.transition('opacity', tokens.durationNormal, tokens.durationNormal, tokens.curveEasyEase),
    },
});

interface SideRailBaseProps {
    className?: string;
    openClassName?: string;
    children: React.ReactNode;
}

interface SideRailProps extends SideRailBaseProps {
    position: 'left' | 'right';
    open: boolean;
    onToggleOpen: () => void;
    hideControls?: boolean;
}

export const SideRail: React.FC<SideRailProps> = (props) => {
    const { className, openClassName, children, position, open, onToggleOpen, hideControls } = props;
    const classes = useClasses();

    const pinIcon = open ? (
        position === 'left' ? (
            <PanelLeftContractRegular />
        ) : (
            <PanelRightContractRegular />
        )
    ) : position === 'left' ? (
        <PanelLeftExpandRegular />
    ) : (
        <PanelRightExpandRegular />
    );

    return (
        <div
            className={mergeClasses(
                className,
                classes.rail,
                position === 'left' ? classes.sideRailLeft : classes.sideRailRight,
                open ? openClassName : classes.collapsed,
            )}
        >
            {!hideControls && (
                <Button
                    className={mergeClasses(
                        classes.pinButton,
                        position === 'left' ? classes.pinButtonLeft : classes.pinButtonRight,
                    )}
                    icon={pinIcon}
                    onClick={onToggleOpen}
                />
            )}
            <div className={mergeClasses(classes.content, open ? classes.contentOpen : undefined)}>{children}</div>
        </div>
    );
};

export const useSideRail = () => {
    const [sideRailLeftOpen, setSideRailLeftOpen] = React.useState(false);
    const [sideRailRightOpen, setSideRailRightOpen] = React.useState(false);

    const SideRailLeftController = () => {
        return (
            <Button
                icon={sideRailLeftOpen ? <PanelLeftContractRegular /> : <PanelLeftExpandRegular />}
                onClick={() => setSideRailLeftOpen((prev) => !prev)}
            />
        );
    };

    const SideRailLeft: React.FC<SideRailBaseProps> = (props) => {
        const { children, className, openClassName } = props;
        return (
            <SideRail
                className={className}
                openClassName={openClassName}
                position="left"
                open={sideRailLeftOpen}
                onToggleOpen={() => setSideRailLeftOpen((prev) => !prev)}
                hideControls
            >
                {children}
            </SideRail>
        );
    };

    const SideRailRightController = () => {
        return (
            <Button
                icon={sideRailRightOpen ? <PanelRightContractRegular /> : <PanelRightExpandRegular />}
                onClick={() => setSideRailRightOpen((prev) => !prev)}
            />
        );
    };

    const SideRailRight: React.FC<SideRailBaseProps> = (props) => {
        const { children, className, openClassName } = props;
        return (
            <SideRail
                className={className}
                openClassName={openClassName}
                position="right"
                open={sideRailRightOpen}
                onToggleOpen={() => setSideRailRightOpen((prev) => !prev)}
                hideControls
            >
                {children}
            </SideRail>
        );
    };

    return {
        SideRail,
        SideRailLeftController,
        SideRailLeft,
        SideRailRightController,
        SideRailRight,
    };
};
