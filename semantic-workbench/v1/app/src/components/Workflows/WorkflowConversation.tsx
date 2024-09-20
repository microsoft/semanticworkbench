// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    MessageBar,
    MessageBarBody,
    MessageBarTitle,
    makeStyles,
    mergeClasses,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { BookInformation24Regular } from '@fluentui/react-icons';
import { EventSourceMessage } from '@microsoft/fetch-event-source';
import React from 'react';
import { Constants } from '../../Constants';
import { InteractHistory } from '../../components/Conversations/InteractHistory';
import { InteractInput } from '../../components/Conversations/InteractInput';
import { WorkbenchEventSource } from '../../libs/WorkbenchEventSource';
import { useEnvironment } from '../../libs/useEnvironment';
import { useSiteUtility } from '../../libs/useSiteUtility';
import { WorkflowDefinition } from '../../models/WorkflowDefinition';
import { WorkflowRun } from '../../models/WorkflowRun';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { setCanvasState, setChatWidthPercent } from '../../redux/features/app/appSlice';
import {
    useGetConversationParticipantsQuery,
    useGetConversationQuery,
    useGetWorkflowRunAssistantsQuery,
} from '../../services/workbench';
import { Loading } from '../App/Loading';
import { ConversationCanvas } from '../Conversations/Canvas/ConversationCanvas';
import { WorkflowControl } from './WorkflowControl';

const useClasses = makeStyles({
    root: {
        display: 'grid',
        gridTemplateColumns: '1fr auto',
        gridTemplateRows: '1fr',
        height: '100%',
    },
    main: {
        position: 'relative',
        display: 'grid',
        gridTemplateColumns: '1fr',
        gridTemplateRows: '1fr auto',
        height: '100%',
    },
    history: {
        position: 'relative',
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'center',
        gap: tokens.spacingVerticalM,
    },
    controls: {
        position: 'absolute',
        top: 0,
        left: 0,
        bottom: 0,
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'stretch',
        zIndex: 1000,
    },
    body: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
    drawerButton: {
        position: 'absolute',
        ...shorthands.padding(tokens.spacingVerticalS),
    },
    resizer: {
        ...shorthands.borderLeft(tokens.strokeWidthThin, 'solid', tokens.colorNeutralBackground5),
        width: '8px',
        position: 'absolute',
        top: 0,
        bottom: 0,
        left: 0,
        cursor: 'col-resize',
        resize: 'horizontal',
        ':hover': {
            borderLeftWidth: '4px',
        },
    },
    resizerActive: {
        borderLeftWidth: '4px',
        borderLeftColor: tokens.colorNeutralBackground5Pressed,
    },
    inspectorButton: {
        position: 'absolute',
        top: 0,
        right: 0,
        ...shorthands.padding(tokens.spacingVerticalS),
        zIndex: 1000,
    },
    inspectors: {
        position: 'relative',
        backgroundColor: tokens.colorNeutralBackgroundAlpha,
        height: '100%',
        overflowY: 'auto',
    },
    input: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'center',
        backgroundColor: tokens.colorNeutralBackgroundAlpha,
    },
    historyContent: {
        // do not use flexbox here, it breaks the virtuoso
        width: '100%',
        maxWidth: `${Constants.app.maxContentWidth}px`,
        ...shorthands.padding(0, tokens.spacingHorizontalXXXL),
    },
    historyContentWithInspector: {
        paddingRight: tokens.spacingHorizontalNone,
    },
});

interface WorkflowConversationProps {
    workflowDefinition: WorkflowDefinition;
    workflowRun: WorkflowRun;
    conversationId: string;
}

export const WorkflowConversation: React.FC<WorkflowConversationProps> = (props) => {
    const { conversationId, workflowRun } = props;

    const classes = useClasses();
    const { chatWidthPercent, canvasState } = useAppSelector((state) => state.app);
    const dispatch = useAppDispatch();
    const animationFrame = React.useRef<number>(0);
    const resizeHandleRef = React.useRef<HTMLDivElement>(null);

    const {
        data: workflowRunAssistants,
        isLoading: isLoadingWorkflowRunAssistants,
        error: workflowRunAssistantsError,
    } = useGetWorkflowRunAssistantsQuery(workflowRun.id);
    const {
        currentData: conversation,
        isLoading: isLoadingConversation,
        error: conversationError,
    } = useGetConversationQuery(conversationId);
    const {
        currentData: participants,
        isLoading: isLoadingParticipants,
        error: participantsError,
    } = useGetConversationParticipantsQuery(conversationId, { refetchOnMountOrArgChange: true });

    const [isResizing, setIsResizing] = React.useState(false);
    const siteUtility = useSiteUtility();
    const environment = useEnvironment();

    if (conversationError) {
        const errorMessage = JSON.stringify(conversationError);
        throw new Error(`Error loading conversation: ${errorMessage}`);
    }

    if (participantsError) {
        const errorMessage = JSON.stringify(participantsError);
        throw new Error(`Error loading participants: ${errorMessage}`);
    }

    if (workflowRunAssistantsError) {
        const errorMessage = JSON.stringify(workflowRunAssistantsError);
        throw new Error(`Error loading workflow run assistants: ${errorMessage}`);
    }

    React.useEffect(() => {
        if (conversation) {
            siteUtility.setDocumentTitle(conversation.title);
        }
    }, [conversation, siteUtility]);

    const startResizing = React.useCallback(() => setIsResizing(true), []);
    const stopResizing = React.useCallback(() => setIsResizing(false), []);

    const resize = React.useCallback(
        (event: { clientX: number }) => {
            animationFrame.current = requestAnimationFrame(() => {
                if (isResizing && resizeHandleRef.current) {
                    const desiredWidth =
                        resizeHandleRef.current.getBoundingClientRect().left +
                        (event.clientX - resizeHandleRef.current.getBoundingClientRect().left);
                    const desiredWidthPercent = (desiredWidth / window.innerWidth) * 100;
                    const minChatWidthPercent = Constants.app.minChatWidthPercent;
                    dispatch(
                        setChatWidthPercent(
                            Math.max(minChatWidthPercent, Math.min(desiredWidthPercent, 100 - minChatWidthPercent)),
                        ),
                    );
                }
            });
        },
        [dispatch, isResizing],
    );

    React.useEffect(() => {
        window.addEventListener('mousemove', resize);
        window.addEventListener('mouseup', stopResizing);

        return () => {
            cancelAnimationFrame(animationFrame.current);
            window.removeEventListener('mousemove', resize);
            window.removeEventListener('mouseup', stopResizing);
        };
    }, [resize, stopResizing]);

    React.useEffect(() => {
        var workbenchEventSource: WorkbenchEventSource | undefined;

        const handleFocusEvent = (event: EventSourceMessage) => {
            const { data } = JSON.parse(event.data);
            dispatch(
                setCanvasState({ open: true, assistantId: data['assistant_id'], assistantStateId: data['state_id'] }),
            );
        };

        (async () => {
            workbenchEventSource = await WorkbenchEventSource.createOrUpdate(environment.url, conversationId);
            workbenchEventSource.addEventListener('assistant.state.focus', handleFocusEvent);
        })();

        return () => {
            workbenchEventSource?.removeEventListener('assistant.state.focus', handleFocusEvent);
        };
    }, [environment, conversationId, dispatch]);

    if (
        isLoadingWorkflowRunAssistants ||
        isLoadingConversation ||
        isLoadingParticipants ||
        !conversation ||
        !participants ||
        !workflowRunAssistants
    ) {
        return <Loading />;
    }

    const conversationAssistants =
        workflowRunAssistants?.filter((assistant) =>
            participants.some((participant) => participant.active && participant.id === assistant.id),
        ) ?? [];

    return (
        <div
            className={classes.root}
            style={{
                gridTemplateColumns: canvasState?.open
                    ? `min(${chatWidthPercent}%, ${Constants.app.maxContentWidth}px) auto`
                    : '1fr auto',
            }}
        >
            <div className={classes.main}>
                <div className={classes.history}>
                    <div
                        className={
                            canvasState?.open
                                ? mergeClasses(classes.historyContent, classes.historyContentWithInspector)
                                : classes.historyContent
                        }
                    >
                        <InteractHistory conversation={conversation} participants={participants} />
                    </div>
                </div>
                <div className={classes.input}>
                    <InteractInput
                        conversationId={conversation.id}
                        additionalContent={
                            <>
                                <MessageBar intent="warning" layout="multiline">
                                    <MessageBarBody>
                                        <MessageBarTitle>Workflow Run Support Under Construction:</MessageBarTitle>
                                        All features are early versions that need further testing. UX will be refined
                                        further.
                                    </MessageBarBody>
                                </MessageBar>
                                <WorkflowControl workflowRun={workflowRun} readOnly />
                            </>
                        }
                    />
                </div>
                {!canvasState?.open && (
                    <div className={classes.inspectorButton}>
                        <Button
                            appearance={canvasState?.open ? 'subtle' : 'secondary'}
                            icon={<BookInformation24Regular />}
                            onClick={() => dispatch(setCanvasState({ open: true }))}
                        />
                    </div>
                )}
            </div>
            <div className={classes.inspectors} onMouseDown={(event) => event.preventDefault()}>
                <div
                    className={mergeClasses(classes.resizer, isResizing && classes.resizerActive)}
                    ref={resizeHandleRef}
                    onMouseDown={startResizing}
                />
                {canvasState?.open && (
                    <ConversationCanvas
                        conversationAssistants={conversationAssistants}
                        conversation={conversation}
                        conversationFiles={[]}
                        conversationParticipants={participants}
                        preventAssistantModifyOnParticipantIds={workflowRunAssistants?.map((assistant) => assistant.id)}
                    />
                )}
            </div>
        </div>
    );
};
