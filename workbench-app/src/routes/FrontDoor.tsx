import { Button, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import { PanelLeftContractRegular, PanelLeftExpandRegular } from '@fluentui/react-icons';
import React from 'react';
import { NewConversationButton } from '../components/FrontDoor/Controls/NewConversationButton';
import { SiteMenuButton } from '../components/FrontDoor/Controls/SiteMenuButton';
import { Conversations } from '../components/FrontDoor/Conversations';

const useClasses = makeStyles({
    root: {
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
    },
    header: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
    },
    body: {
        display: 'flex',
        flex: '1 1 auto',
    },
    sideRailLeft: {
        width: '0px',
        flex: '0 0 auto',
        overflow: 'hidden',
        backgroundColor: tokens.colorNeutralBackground2,
        ...shorthands.transition('width', tokens.durationSlow, '0', tokens.curveEasyEase),

        '&.open': {
            width: '300px',
        },
    },
    sideRailLeftContent: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
        ...shorthands.padding(
            tokens.spacingVerticalM,
            tokens.spacingHorizontalM,
            tokens.spacingVerticalM,
            tokens.spacingHorizontalM,
        ),
    },
    fade: {
        opacity: 0,
        transitionProperty: 'opacity',
        transitionDuration: tokens.durationFast,
        transitionDelay: '0',
        transitionTimingFunction: tokens.curveEasyEase,

        '&.in': {
            opacity: 1,
            transitionProperty: 'opacity',
            transitionDuration: tokens.durationNormal,
            transitionDelay: tokens.durationNormal,
            transitionTimingFunction: tokens.curveEasyEase,
        },
    },
    main: {
        position: 'relative',
        flex: '1 1 auto',
        overflow: 'auto',
        backgroundColor: tokens.colorNeutralBackground1,
        padding: tokens.spacingHorizontalM,
    },
    controls: {
        display: 'inline-flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalS,
    },
    sideRailRightOpen: {
        width: '50vw',
    },
});

export const FrontDoor: React.FC = () => {
    const classes = useClasses();
    const [sideRailLeftOpen, setSideRailLeftOpen] = React.useState(false);

    const sideRailLeftButton = (
        <Button
            icon={sideRailLeftOpen ? <PanelLeftContractRegular /> : <PanelLeftExpandRegular />}
            onClick={() => setSideRailLeftOpen((prev) => !prev)}
        />
    );

    return (
        <div className={classes.root}>
            <div className={classes.body}>
                <div className={mergeClasses(classes.sideRailLeft, sideRailLeftOpen ? 'open' : undefined)}>
                    <div
                        className={mergeClasses(
                            classes.sideRailLeftContent,
                            classes.fade,
                            sideRailLeftOpen ? 'in' : undefined,
                        )}
                    >
                        <div className={classes.header}>
                            {sideRailLeftButton}
                            <NewConversationButton />
                        </div>
                        <Conversations />
                    </div>
                </div>
                <div className={classes.main}>
                    <div className={classes.header}>
                        <div
                            className={mergeClasses(
                                classes.controls,
                                classes.fade,
                                !sideRailLeftOpen ? 'in' : undefined,
                            )}
                        >
                            {sideRailLeftButton}
                            <NewConversationButton />
                        </div>
                        <div className={classes.controls}>
                            <SiteMenuButton />
                        </div>
                    </div>
                    <h1>Main Content Area</h1>
                </div>
            </div>
        </div>
    );
};
