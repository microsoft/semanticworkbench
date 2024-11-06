import { Button, Drawer, DrawerBody, makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
import { PanelLeftContractRegular, PanelLeftExpandRegular } from '@fluentui/react-icons';
import React from 'react';
import { useDispatch } from 'react-redux';
import { useParams } from 'react-router-dom';
import { Loading } from '../components/App/Loading';
import { NewConversationButton } from '../components/FrontDoor/Controls/NewConversationButton';
import { SiteMenuButton } from '../components/FrontDoor/Controls/SiteMenuButton';
import { GlobalContent } from '../components/FrontDoor/GlobalContent';
import { MainContent } from '../components/FrontDoor/MainContent';
import { useMediaQuery } from '../libs/useMediaQuery';
import { useAppSelector } from '../redux/app/hooks';
import { setActiveConversationId } from '../redux/features/app/appSlice';

const useClasses = makeStyles({
    documentBody: {
        backgroundColor: `rgba(0, 0, 0, 0.1)`,
    },
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
        backgroundColor: tokens.colorNeutralBackground2,
        ...shorthands.borderRight(tokens.strokeWidthThick, 'solid', tokens.colorNeutralStroke3),
        boxSizing: 'border-box',
    },
    sideRailLeftBody: {
        // override Fluent UI DrawerBody padding
        padding: 0,
        '&:first-child': {
            paddingTop: 0,
        },
        '&:last-child': {
            paddingBottom: 0,
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
    const activeConversationId = useAppSelector((state) => state.app.activeConversationId);
    const chatCanvasState = useAppSelector((state) => state.chatCanvas);
    const dispatch = useDispatch();
    const sideRailLeftRef = React.useRef<HTMLDivElement | null>(null);
    const [sideRailLeftOpen, setSideRailLeftOpen] = React.useState(!activeConversationId && !conversationId);
    const [isInitialized, setIsInitialized] = React.useState(false);
    const isSmall = useMediaQuery({ maxWidth: 720 });
    const [sideRailLeftType, setSideRailLeftType] = React.useState<'inline' | 'overlay'>('inline');

    React.useEffect(() => {
        document.body.className = classes.documentBody;
        return () => {
            document.body.className = '';
        };
    }, [classes.documentBody]);

    React.useEffect(() => {
        if (conversationId !== activeConversationId) {
            dispatch(setActiveConversationId(conversationId));
        }
        setIsInitialized(true);
    }, [conversationId, activeConversationId, dispatch]);

    const handleClickOutside = React.useCallback(
        (event: MouseEvent) => {
            if (!sideRailLeftRef.current) return;

            if (!sideRailLeftRef.current.contains(event.target as HTMLElement)) {
                setSideRailLeftOpen(false);
            }
        },
        [sideRailLeftRef],
    );

    React.useEffect(() => {
        if (sideRailLeftOpen && sideRailLeftType === 'overlay') {
            document.addEventListener('click', handleClickOutside);
        } else {
            document.removeEventListener('click', handleClickOutside);
        }
        return () => document.removeEventListener('click', handleClickOutside);
    }, [handleClickOutside, sideRailLeftOpen, sideRailLeftRef, sideRailLeftType]);

    const sideRailLeftButton = React.useMemo(
        () => (
            <Button
                icon={sideRailLeftOpen ? <PanelLeftContractRegular /> : <PanelLeftExpandRegular />}
                onClick={(event) => {
                    event.stopPropagation();
                    setSideRailLeftOpen((prev) => !prev);
                }}
            />
        ),
        [sideRailLeftOpen],
    );

    React.useEffect(() => {
        if (sideRailLeftType === 'overlay') {
            if (isSmall || chatCanvasState.open) return;
            setSideRailLeftType('inline');
        } else {
            if (!isSmall && !chatCanvasState.open) return;
            setSideRailLeftType('overlay');
        }
    }, [sideRailLeftType, isSmall, chatCanvasState.open]);

    const globalContent = React.useMemo(
        () => <GlobalContent headerBefore={sideRailLeftButton} headerAfter={<NewConversationButton />} />,
        [sideRailLeftButton],
    );

    const newConversationButton = React.useMemo(() => <NewConversationButton />, []);

    return (
        <div className={classes.root}>
            <div className={classes.body}>
                <Drawer
                    ref={sideRailLeftRef}
                    className={classes.sideRailLeft}
                    open={sideRailLeftOpen}
                    modalType="non-modal"
                    type={sideRailLeftType}
                    size="small"
                >
                    <DrawerBody className={classes.sideRailLeftBody}>{globalContent}</DrawerBody>
                </Drawer>
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
                                    {newConversationButton}
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
