import {
    Button,
    Drawer,
    DrawerBody,
    Link,
    makeStyles,
    mergeClasses,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { ChatAddRegular, PanelLeftContractRegular, PanelLeftExpandRegular } from '@fluentui/react-icons';
import React from 'react';
import { useDispatch } from 'react-redux';
import { useNavigate, useParams } from 'react-router-dom';
import { Loading } from '../components/App/Loading';
import { SiteMenuButton } from '../components/FrontDoor/Controls/SiteMenuButton';
import { GlobalContent } from '../components/FrontDoor/GlobalContent';
import { MainContent } from '../components/FrontDoor/MainContent';
import { Constants } from '../Constants';
import { EventSubscriptionManager } from '../libs/EventSubscriptionManager';
import { useWorkbenchConversationEventSource, useWorkbenchUserEventSource } from '../libs/useWorkbenchEventSource';
import { useAppSelector } from '../redux/app/hooks';
import { setActiveConversationId, setGlobalContentOpen } from '../redux/features/app/appSlice';

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
        minWidth: Constants.app.conversationListMinWidth,
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

export const workbenchUserEvents = new EventSubscriptionManager();
export const workbenchConversationEvents = new EventSubscriptionManager();

export const FrontDoor: React.FC = () => {
    const classes = useClasses();
    const { conversationId } = useParams();
    const activeConversationId = useAppSelector((state) => state.app.activeConversationId);
    const globalContentOpen = useAppSelector((state) => state.app.globalContentOpen);
    const dispatch = useDispatch();
    const [isInitialized, setIsInitialized] = React.useState(false);
    const navigate = useNavigate();

    // set up the workbench event sources and connect to the conversation and user event streams
    // any child components can subscribe to these events using the subscription managers
    // these should only reset when the conversation ID changes
    useWorkbenchUserEventSource(workbenchUserEvents);
    useWorkbenchConversationEventSource(workbenchConversationEvents, activeConversationId);

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

    const sideRailLeftButton = React.useMemo(
        () => (
            <Button
                icon={globalContentOpen ? <PanelLeftContractRegular /> : <PanelLeftExpandRegular />}
                onClick={(event) => {
                    event.stopPropagation();
                    dispatch(setGlobalContentOpen(!globalContentOpen));
                }}
            />
        ),
        [dispatch, globalContentOpen],
    );

    const handleNewConversation = React.useCallback(() => {
        navigate('/');
    }, [navigate]);

    const newConversationButton = React.useMemo(
        () => (
            <Link href="/" onClick={(event) => event.preventDefault()}>
                <Button title="New Conversation" icon={<ChatAddRegular />} onClick={handleNewConversation} />
            </Link>
        ),
        [handleNewConversation],
    );

    const globalContent = React.useMemo(
        () => <GlobalContent headerBefore={sideRailLeftButton} headerAfter={newConversationButton} />,
        [sideRailLeftButton, newConversationButton],
    );

    return (
        <div className={classes.root}>
            <div className={classes.body}>
                <Drawer
                    className={classes.sideRailLeft}
                    open={globalContentOpen}
                    modalType="non-modal"
                    type="inline"
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
                                        !globalContentOpen ? 'in' : undefined,
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
