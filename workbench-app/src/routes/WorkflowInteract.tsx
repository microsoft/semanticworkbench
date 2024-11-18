// Copyright (c) Microsoft. All rights reserved.

import {
    Divider,
    Overflow,
    OverflowItem,
    Tab,
    TabList,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { EventSourceMessage } from '@microsoft/fetch-event-source';
import React from 'react';
import { useParams } from 'react-router-dom';
import { Constants } from '../Constants';
import { AppView } from '../components/App/AppView';
import { Loading } from '../components/App/Loading';
import { OverflowMenu, OverflowMenuItemData } from '../components/App/OverflowMenu';
import { WorkflowConversation } from '../components/Workflows/WorkflowConversation';
import { WorkflowEdit } from '../components/Workflows/WorkflowEdit';
import { WorkbenchEventSource, WorkbenchEventSourceType } from '../libs/WorkbenchEventSource';
import { useEnvironment } from '../libs/useEnvironment';
import { useSiteUtility } from '../libs/useSiteUtility';
import { conversationMessageFromJSON } from '../models/ConversationMessage';
import { useAppDispatch } from '../redux/app/hooks';
import { setChatWidthPercent } from '../redux/features/app/appSlice';
import { useGetWorkflowDefinitionQuery, useGetWorkflowRunQuery, workflowApi } from '../services/workbench';

const useClasses = makeStyles({
    root: {
        position: 'relative',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        ...shorthands.gap(0),
    },
    tabs: {
        backgroundColor: tokens.colorNeutralBackground1,
    },
    tab: {
        color: tokens.colorPaletteLightGreenForeground1,
        paddingRight: tokens.spacingHorizontalS,
    },
    menu: {
        backgroundColor: tokens.colorNeutralBackground1,
    },
    menuButton: {
        alignSelf: 'center',
    },
});

export const WorkflowInteract: React.FC = () => {
    const { workflowDefinitionId, workflowRunId } = useParams();
    if (!workflowDefinitionId) {
        throw new Error('Workflow Definition ID is required');
    }
    if (!workflowRunId) {
        throw new Error('Workflow Run ID is required');
    }
    const classes = useClasses();
    const environment = useEnvironment();
    const dispatch = useAppDispatch();
    const animationFrame = React.useRef<number>(0);
    const resizeHandleRef = React.useRef<HTMLDivElement>(null);

    const {
        data: workflowRun,
        error: workflowRunError,
        isLoading: workflowRunIsLoading,
        refetch: refetchWorkflowRun,
    } = useGetWorkflowRunQuery(workflowRunId);

    if (workflowRunError) {
        const errorMessage = JSON.stringify(workflowRunError);
        throw new Error(`Error loading workflow run: ${errorMessage}`);
    }

    const {
        data: workflowDefinition,
        error: workflowDefinitionError,
        isLoading: workflowDefinitionIsLoading,
    } = useGetWorkflowDefinitionQuery(workflowDefinitionId);

    if (workflowDefinitionError) {
        const errorMessage = JSON.stringify(workflowDefinitionError);
        throw new Error(`Error loading workflow definition: ${errorMessage}`);
    }

    if (!workflowRunIsLoading && !workflowRun) {
        throw new Error('Workflow run not found');
    }

    if (!workflowDefinitionIsLoading && !workflowDefinition) {
        throw new Error('Workflow definition not found');
    }

    // verify the workflow and get the conversation ID
    const [conversationId, setConversationId] = React.useState<string>();
    React.useEffect(() => {
        if (workflowDefinitionIsLoading || workflowRunIsLoading) return;
        if (!workflowDefinition) {
            throw new Error('No workflow definition loaded');
        }
        if (!workflowRun) {
            throw new Error('No workflow run loaded');
        }

        const conversationDefinitionId = workflowDefinition.states.find(
            (state) => state.id === workflowRun.currentStateId,
        )?.conversationDefinitionId;
        if (!conversationDefinitionId) {
            throw new Error('No conversation definition ID found');
        }

        const conversationMapping = workflowRun.conversationMappings.find(
            (mapping) => mapping.conversationDefinitionId === conversationDefinitionId,
        );
        if (!conversationMapping) {
            throw new Error('No conversation mapping found');
        }
        setConversationId(conversationMapping.conversationId);
    }, [workflowDefinition, workflowDefinitionIsLoading, workflowRun, workflowRunIsLoading]);

    const [isResizing, setIsResizing] = React.useState(false);
    const siteUtility = useSiteUtility();

    React.useEffect(() => {
        if (workflowDefinition && workflowRun) {
            siteUtility.setDocumentTitle(`${workflowRun.title} - ${workflowDefinition.label}`);
        }
    }, [siteUtility, workflowDefinition, workflowRun]);

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

    // handle workflow level events
    React.useEffect(() => {
        if (!environment || !conversationId || workflowRunIsLoading || !workflowRun) {
            return;
        }

        const messageHandler = async (event: EventSourceMessage) => {
            const { data } = JSON.parse(event.data);
            const parsedEventData = {
                timestamp: data.timestamp,
                data: {
                    message: conversationMessageFromJSON(data.message),
                },
            };

            if (parsedEventData.data.message.metadata === undefined) {
                // ignore messages without metadata
                return;
            }

            const { metadata } = parsedEventData.data.message;

            for (const key in metadata) {
                if (key === 'workflow_run_updated') {
                    if (metadata[key] === workflowRunId) {
                        // update the workflow run
                        // this will trigger a re-render of the component
                        // and the conversation will be updated
                        // with the new message
                        dispatch(workflowApi.endpoints.getWorkflowRun.initiate(workflowRunId, { forceRefetch: true }));
                    }
                }
            }
        };

        (async () => {
            // get the event source
            const workbenchEventSource = await WorkbenchEventSource.createOrUpdate(
                environment.url,
                WorkbenchEventSourceType.Conversation,
                conversationId,
            );
            workbenchEventSource.addEventListener('message.created', messageHandler);
        })();

        return () => {
            (async () => {
                const workbenchEventSource = await WorkbenchEventSource.getInstance(
                    WorkbenchEventSourceType.Conversation,
                );
                workbenchEventSource.removeEventListener('message.created', messageHandler);
            })();
        };
    }, [workflowRunId, refetchWorkflowRun, environment, conversationId, workflowRunIsLoading, workflowRun, dispatch]);

    const tabItems = React.useMemo(
        () =>
            workflowRun?.conversationMappings.map((mapping): OverflowMenuItemData => {
                const conversationDefinition = workflowDefinition?.definitions.conversations.find(
                    (definition) => definition.id === mapping.conversationDefinitionId,
                );

                if (!conversationDefinition) {
                    throw new Error('No conversation definition found');
                }

                return {
                    id: mapping.conversationId,
                    name: conversationDefinition.title,
                };
            }),
        [workflowDefinition, workflowRun],
    );

    const handleTabSelect = React.useCallback((tabId: string) => {
        setConversationId(tabId);
    }, []);

    const workflowCurrentConversationId = React.useMemo(
        () =>
            workflowRun?.conversationMappings.find(
                (mapping) =>
                    mapping.conversationDefinitionId ===
                    workflowDefinition?.states.find((state) => state.id === workflowRun.currentStateId)
                        ?.conversationDefinitionId,
            )?.conversationId,
        [workflowRun, workflowDefinition],
    );

    if (!tabItems || !workflowDefinition || !workflowRun || !conversationId) {
        return (
            <AppView title="Interact">
                <Loading />
            </AppView>
        );
    }

    const actions = {
        items: [<WorkflowEdit key="edit" iconOnly workflowDefinition={workflowDefinition} />],
    };

    return (
        <AppView title={`${workflowRun.title} - ${workflowDefinition.label}`} actions={actions} fullSizeContent>
            <div className={classes.root}>
                <Overflow minimumVisible={1}>
                    <TabList
                        className={classes.tabs}
                        selectedValue={conversationId}
                        onTabSelect={(_, data) => handleTabSelect(data.value as string)}
                    >
                        {tabItems?.map((tabItem) => (
                            <OverflowItem
                                key={tabItem.id}
                                id={tabItem.id}
                                priority={tabItem.id === workflowCurrentConversationId ? 2 : 1}
                            >
                                <Tab value={tabItem.id}>{tabItem.name}</Tab>
                            </OverflowItem>
                        ))}
                        <OverflowMenu items={tabItems} onItemSelect={handleTabSelect} />
                    </TabList>
                </Overflow>
                <Divider />
                <WorkflowConversation
                    conversationId={conversationId}
                    workflowDefinition={workflowDefinition}
                    workflowRun={workflowRun}
                />
            </div>
        </AppView>
    );
};
