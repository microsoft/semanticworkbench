import { Button, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import { PanelLeftContractRegular, PanelLeftExpandRegular } from '@fluentui/react-icons';
import React from 'react';
import { useDispatch } from 'react-redux';
import { useParams } from 'react-router-dom';
import { Loading } from '../components/App/Loading';
import { NewConversationButton } from '../components/FrontDoor/Controls/NewConversationButton';
import { SiteMenuButton } from '../components/FrontDoor/Controls/SiteMenuButton';
import { GlobalContent } from '../components/FrontDoor/GlobalContent';
import { MainContent } from '../components/FrontDoor/MainContent';
import { useAppSelector } from '../redux/app/hooks';
import { setActiveConversationId } from '../redux/features/app/appSlice';

const useClasses = makeStyles({
    root: {
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
    },
    body: {
        flex: '1 1 auto',
        display: 'flex',
        flexDirection: 'row',
        height: '100%',
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

        '&.overlay': {
            position: 'absolute',
            zIndex: tokens.zIndexFloating,
            height: '100%',
            ...shorthands.borderRight(tokens.strokeWidthThick, 'solid', tokens.colorNeutralStroke3),
            boxShadow: tokens.shadow8Brand,
        },
    },
    transitionFade: {
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
    mainContent: {
        flex: '1 1 auto',
        display: 'flex',
        flexDirection: 'column',
    },
    controls: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalS,
    },
});

export const FrontDoor: React.FC = () => {
    const classes = useClasses();
    const { conversationId } = useParams();
    const { activeConversationId, interactCanvasState } = useAppSelector((state) => state.app);
    const dispatch = useDispatch();
    const [sideRailLeftOpen, setSideRailLeftOpen] = React.useState(!activeConversationId && !conversationId);
    const [sideRailLeftOverlay, setSideRailLeftOverlay] = React.useState(false);
    const [isInitialized, setIsInitialized] = React.useState(false);
    const sideRailLeftRef = React.useRef<HTMLDivElement>(null);

    React.useEffect(() => {
        if (conversationId && conversationId !== activeConversationId) {
            dispatch(setActiveConversationId(conversationId));
        }
        setIsInitialized(true);
    }, [conversationId, activeConversationId, dispatch]);

    React.useEffect(() => {
        if (!interactCanvasState) return;

        if (interactCanvasState.open) {
            setSideRailLeftOpen(false);
        }
        setSideRailLeftOverlay(interactCanvasState.open ?? false);
    }, [interactCanvasState, interactCanvasState?.open]);

    React.useEffect(() => {
        if (!sideRailLeftRef.current) return;

        const handleOutsideClick = (event: MouseEvent) => {
            if (sideRailLeftOpen && sideRailLeftOverlay && !sideRailLeftRef.current?.contains(event.target as Node)) {
                setSideRailLeftOpen(false);
            }
        };

        document.addEventListener('mousedown', handleOutsideClick);
        return () => {
            document.removeEventListener('mousedown', handleOutsideClick);
        };
    }, [sideRailLeftOpen, sideRailLeftOverlay]);

    const sideRailLeftButton = (
        <Button
            icon={sideRailLeftOpen ? <PanelLeftContractRegular /> : <PanelLeftExpandRegular />}
            onClick={() => setSideRailLeftOpen((prev) => !prev)}
        />
    );

    return (
        <div className={classes.root}>
            <div className={classes.body}>
                <div
                    className={mergeClasses(
                        classes.sideRailLeft,
                        sideRailLeftOpen ? 'open' : undefined,
                        sideRailLeftOverlay ? 'overlay' : undefined,
                    )}
                    ref={sideRailLeftRef}
                >
                    <div className={mergeClasses(classes.transitionFade, sideRailLeftOpen ? 'in' : undefined)}>
                        <GlobalContent headerBefore={sideRailLeftButton} headerAfter={<NewConversationButton />} />
                    </div>
                </div>
                <div className={classes.mainContent}>
                    {!isInitialized ? (
                        <Loading />
                    ) : (
                        <MainContent
                            headerBefore={
                                <div
                                    className={mergeClasses(
                                        classes.controls,
                                        classes.transitionFade,
                                        !sideRailLeftOpen ? 'in' : undefined,
                                    )}
                                >
                                    {sideRailLeftButton}
                                    <NewConversationButton />
                                </div>
                            }
                            headerAfter={<SiteMenuButton />}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};
