// Copyright (c) Microsoft. All rights reserved.

import { generateUuid } from '@azure/ms-rest-js';
import {
    Button,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
    makeStyles,
} from '@fluentui/react-components';
import React from 'react';
import ReactFlow, {
    Background,
    Connection,
    Controls,
    Edge,
    EdgeChange,
    MiniMap,
    Node,
    NodeChange,
    OnConnect,
    OnConnectEnd,
    OnConnectStart,
    OnConnectStartParams,
    OnSelectionChangeParams,
    addEdge,
    applyEdgeChanges,
    applyNodeChanges,
    useReactFlow,
} from 'reactflow';
import { Utility } from '../../../libs/Utility';
import {
    ConversationDefinition,
    OutletData,
    WorkflowDefinition,
    WorkflowState,
} from '../../../models/WorkflowDefinition';
import { WorkflowStateNode, WorkflowStateNodeData } from './WorkflowStateNode';

const useClasses = makeStyles({
    canvas: {
        height: '100%',
    },
});

const nodeTypes = {
    workflowState: WorkflowStateNode,
};

interface WorkflowForReactFlow {
    id: string;
    nodes: Node<WorkflowStateNodeData>[];
    edges: Edge[];
}

interface WorkflowCanvasProps {
    workflowDefinition: WorkflowDefinition;
    onChange: (newWorkflowDefinition: WorkflowDefinition) => void;
    onSelectWorkflowStateToEdit: (workflowStateId: string) => void;
}

const defaultExitOutletData: OutletData = {
    id: generateUuid(),
    label: 'Exit',
    prompts: {
        evaluateTransition: 'User has indicated they want abort the current task.',
        contextTransfer:
            'Capture a summary of the recent conversation including any details about why and what the user chose to abort.',
    },
};

export const WorkflowCanvas: React.FC<WorkflowCanvasProps> = (props) => {
    const { workflowDefinition, onChange, onSelectWorkflowStateToEdit } = props;
    const classes = useClasses();
    const reactFlowWrapper = React.useRef(null);
    const connectingNodeId = React.useRef<string | null>(null);
    const connectingHandleId = React.useRef<string | null>(null);
    const [selectedNodes, setSelectedNodes] = React.useState<Node[]>([]);
    const [selectedEdges, setSelectedEdges] = React.useState<Edge[]>([]);
    const [showConfirmDelete, setShowConfigDelete] = React.useState(false);
    const { screenToFlowPosition } = useReactFlow();
    const [conversationDefinitions, setConversationDefinitions] = React.useState<ConversationDefinition[]>(
        workflowDefinition.definitions.conversations,
    );

    const workflowDefinitionToReactFlow = React.useCallback(
        (value: WorkflowDefinition, onEdit: (stateId: string) => void): WorkflowForReactFlow => {
            if (conversationDefinitions !== value.definitions.conversations) {
                setConversationDefinitions(value.definitions.conversations);
            }

            return {
                id: value.id,
                nodes: value.states.map((state) => {
                    const node: Node<WorkflowStateNodeData> = {
                        id: state.id,
                        type: 'workflowState',
                        position: state.editorData.position,
                        data: {
                            ...state,
                            isStart: state.id === value.startStateId,
                            onEdit: () => onEdit(state.id),
                        },
                    };
                    return node;
                }),
                edges: value.transitions.map((transition) => {
                    const source = value.states.find((state) =>
                        state.outlets.some((outlet) => outlet.id === transition.sourceOutletId),
                    );
                    if (!source) {
                        throw new Error(`Source state not found: ${transition.sourceOutletId}`);
                    }
                    return {
                        id: transition.id,
                        source: source.id,
                        sourceHandle: transition.sourceOutletId,
                        target: transition.targetStateId,
                    };
                }),
            };
        },
        [conversationDefinitions],
    );

    // transform the data to the format expected by react-flow
    const workflowForReactFlow = React.useMemo(
        () => workflowDefinitionToReactFlow(workflowDefinition, onSelectWorkflowStateToEdit),
        [workflowDefinitionToReactFlow, workflowDefinition, onSelectWorkflowStateToEdit],
    );

    const reactFlowToWorkflowDefinition = React.useCallback(
        (nodes: Node<WorkflowStateNodeData>[], edges: Edge[]): WorkflowDefinition => {
            return {
                ...workflowDefinition,
                definitions: {
                    ...workflowDefinition.definitions,
                    conversations: conversationDefinitions,
                },
                states: nodes.map((node) => {
                    const { id, position, data } = node;
                    return {
                        id,
                        label: data.label,
                        conversationDefinitionId: data.conversationDefinitionId,
                        forceNewConversationInstance: data.forceNewConversationInstance,
                        assistantDataList: data.assistantDataList,
                        editorData: {
                            position,
                        },
                        outlets: data.outlets,
                    };
                }),
                transitions: edges.map((edge) => {
                    const sourceNode = nodes.find((node) => node.id === edge.source);
                    if (!sourceNode) {
                        throw new Error(`Source node not found: ${edge.source}`);
                    }
                    const sourceOutlet = sourceNode.data.outlets.find((outlet) => outlet.id === edge.sourceHandle);
                    if (!sourceOutlet) {
                        throw new Error(`Source outlet not found: ${edge.sourceHandle}`);
                    }
                    return {
                        id: edge.id,
                        sourceOutletId: sourceOutlet.id,
                        targetStateId: edge.target,
                    };
                }),
            };
        },
        [conversationDefinitions, workflowDefinition],
    );

    const updateWorkflow = (nodes: Node<WorkflowStateNodeData>[], edges: Edge[]) => {
        const validEdges = edges.filter((edge) => {
            const sourceNodeId = edge.source;
            const node = nodes.find((n) => n.id === sourceNodeId);
            if (!node) {
                return false;
            }

            const sourceHandleId = edge.sourceHandle;
            if (sourceHandleId) {
                const handle = node.data.outlets.find((outlet) => outlet.id === sourceHandleId);
                if (!handle) {
                    return false;
                }
            }

            const targetNodeId = edge.target;
            const targetNode = nodes.find((n) => n.id === targetNodeId);
            if (!targetNode) {
                return false;
            }

            const targetHandleId = edge.targetHandle;
            if (targetHandleId) {
                const handle = targetNode.data.outlets.find((outlet) => outlet.id === targetHandleId);
                if (!handle) {
                    return false;
                }
            }

            return true;
        });

        const updatedWorkflowDefinition = reactFlowToWorkflowDefinition(nodes, validEdges);

        const differences = Utility.deepDiff(updatedWorkflowDefinition, workflowDefinition);
        if (Object.entries(differences).length > 0) {
            onChange(updatedWorkflowDefinition);
        }
    };

    const createNewNode = (
        sourceNodeId: string,
        sourceNodeHandleId: string | null,
        screenPosition: { x: number; y: number },
    ) => {
        // allowing for re-use of the same node configuration as a starting point
        const sourceNode = workflowForReactFlow.nodes.find((node) => node.id === sourceNodeId);
        if (!sourceNode) {
            throw new Error(`Source node not found: ${sourceNodeId}`);
        }

        // find the source outlet, to get the label for a starting label for the new node
        const sourceOutlet = sourceNode.data.outlets.find((outlet) => outlet.id === sourceNodeHandleId);
        if (!sourceOutlet) {
            throw new Error(`Source outlet not found: ${sourceNodeHandleId}`);
        }

        // create a new conversation for the new node
        const newConversationDefinition: ConversationDefinition = {
            id: generateUuid(),
            title: sourceOutlet.label,
        };
        setConversationDefinitions((value) => [...value, newConversationDefinition]);

        // copy the data from the source node as the defaults for the new node
        const newNodeId = generateUuid();
        const data: WorkflowState = {
            ...sourceNode.data,
            label: sourceOutlet.label,
            conversationDefinitionId: newConversationDefinition.id,
            outlets: sourceNode.data.outlets.map((outlet) => ({
                ...outlet,
                id: generateUuid(),
            })),
        };

        // add a default exit outlet if one does not already exist
        if (data.outlets.every((outlet) => outlet.label !== defaultExitOutletData.label)) {
            const exitOutlet = {
                ...defaultExitOutletData,
                id: generateUuid(),
            };
            data.outlets.push(exitOutlet);
        }

        // set the new node's position to the click location
        const position = screenToFlowPosition({
            x: screenPosition.x,
            y: screenPosition.y,
        });

        // create the new node
        const newNode: Node = {
            id: newNodeId,
            position,
            type: 'workflowState',
            data,
        };

        const nodes = applyNodeChanges(
            [
                {
                    item: newNode,
                    type: 'add',
                },
            ],
            workflowForReactFlow.nodes,
        );

        const edges = applyEdgeChanges(
            [
                {
                    item: {
                        id: generateUuid(),
                        source: sourceNodeId,
                        sourceHandle: sourceNodeHandleId,
                        target: newNodeId,
                    },
                    type: 'add',
                },
            ],
            workflowForReactFlow.edges,
        );

        updateWorkflow(nodes, edges);
    };

    const handleConnect: OnConnect = (params) => {
        connectingNodeId.current = null;
        connectingHandleId.current = null;

        const nodes = workflowForReactFlow.nodes;
        const edges = addEdge(params, workflowForReactFlow.edges);

        updateWorkflow(nodes, edges);
    };

    const handleConnectStart: OnConnectStart = (_event, params: OnConnectStartParams) => {
        const { nodeId, handleId } = params;

        connectingNodeId.current = nodeId;
        connectingHandleId.current = handleId;
    };

    const isValidConnection = (connection: Connection) => {
        const sourceNode = workflowForReactFlow.nodes.find((node) => node.id === connection.source);
        const sourceOutlet = sourceNode?.data.outlets.find((outlet) => outlet.id === connection.sourceHandle);

        const targetNode = workflowForReactFlow.nodes.find((node) => node.id === connection.target);
        const targetOutlet = targetNode?.data.outlets.find((outlet) => outlet.id === connection.targetHandle);

        // prevent connecting to an outlet that already has a connection
        if (
            workflowForReactFlow.edges.some(
                (edge) =>
                    (sourceOutlet &&
                        (edge.sourceHandle === sourceOutlet.id || edge.targetHandle === sourceOutlet.id)) ||
                    (targetOutlet && (edge.sourceHandle === targetOutlet.id || edge.targetHandle === targetOutlet.id)),
            )
        ) {
            return false;
        }

        return true;
    };

    const handleConnectEnd: OnConnectEnd = (event) => {
        const sourceNodeId = connectingNodeId.current;
        const sourceNodeHandleId = connectingHandleId.current;
        if (!sourceNodeId) return;
        if (!(event instanceof MouseEvent)) return;

        let targetIsPane = false;
        try {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            const target = event.target as any;
            // eslint-disable-next-line no-empty
            targetIsPane = target.className?.includes?.('react-flow__pane');
        } catch (e) {
            // eslint-disable-next-line no-empty
        }

        if (targetIsPane) {
            // exit early if the source outlet already has a connection
            if (
                workflowForReactFlow.edges.some(
                    (edge) => edge.sourceHandle === sourceNodeHandleId || edge.targetHandle === sourceNodeHandleId,
                )
            ) {
                return;
            }

            // create a new node at the position of the click
            createNewNode(sourceNodeId, sourceNodeHandleId, { x: event.clientX, y: event.clientY });
        }
    };

    const handleNodesChange = (changedNodes: NodeChange[]) => {
        const nodes = applyNodeChanges(
            changedNodes.filter((node) => node.type !== 'remove'),
            workflowForReactFlow.nodes,
        );

        const edges = workflowForReactFlow.edges;

        updateWorkflow(nodes, edges);
    };

    const handleEdgesChange = (changedEdges: EdgeChange[]) => {
        const nodes = workflowForReactFlow.nodes;

        const edges = applyEdgeChanges(
            changedEdges.filter((edge) => edge.type !== 'remove'),
            workflowForReactFlow.edges,
        );

        updateWorkflow(nodes, edges);
    };

    const handleEdgesDelete = (edges: Edge[]) => {
        if (edges.length > 0) {
            setShowConfigDelete(true);
        }
    };

    const handleNodesDelete = (nodes: Node[]) => {
        // do not allow deleting the start node
        if (nodes.some((node) => node.data.isStart)) {
            return;
        }

        if (nodes.length > 0) {
            setShowConfigDelete(true);
        }
    };

    const handleSelectionChange = (selection: OnSelectionChangeParams) => {
        const { nodes, edges } = selection;
        setSelectedNodes(nodes);
        setSelectedEdges(edges);
    };

    const onDelete = () => {
        const nodeChanges: NodeChange[] = selectedNodes
            .filter((node) => !node.data.isRoot)
            .map((node) => {
                return {
                    id: node.id,
                    item: node,
                    type: 'remove',
                };
            });

        const edgeChanges: EdgeChange[] = selectedEdges.map((edge) => {
            return {
                id: edge.id,
                item: edge,
                type: 'remove',
            };
        });

        const nodes = applyNodeChanges(nodeChanges, workflowForReactFlow.nodes);
        const edges = applyEdgeChanges(edgeChanges, workflowForReactFlow.edges);

        updateWorkflow(nodes, edges);
        setShowConfigDelete(false);
    };

    return (
        <div className={classes.canvas} ref={reactFlowWrapper}>
            <Dialog open={showConfirmDelete} onOpenChange={() => setShowConfigDelete(false)}>
                <DialogSurface>
                    <DialogBody>
                        <DialogTitle>Confirm Delete</DialogTitle>
                        <DialogContent>
                            <p>Are you sure you want to delete these items?</p>
                        </DialogContent>
                        <DialogActions>
                            <DialogTrigger>
                                <Button>Cancel</Button>
                            </DialogTrigger>
                            <DialogTrigger>
                                <Button onClick={onDelete}>Delete</Button>
                            </DialogTrigger>
                        </DialogActions>
                    </DialogBody>
                </DialogSurface>
            </Dialog>
            <ReactFlow
                onSelectionChange={handleSelectionChange}
                nodeTypes={nodeTypes}
                nodes={workflowForReactFlow.nodes}
                onNodesChange={handleNodesChange}
                onNodesDelete={handleNodesDelete}
                edges={workflowForReactFlow.edges}
                onEdgesChange={handleEdgesChange}
                onEdgesDelete={handleEdgesDelete}
                onConnect={handleConnect}
                onConnectStart={handleConnectStart}
                onConnectEnd={handleConnectEnd}
                isValidConnection={isValidConnection}
                fitView
                fitViewOptions={{ maxZoom: 1 }}
                maxZoom={1}
                nodeOrigin={[0.5, 0.5]}
                deleteKeyCode={['Backspace', 'Delete']}
            >
                <Background />
                <Controls />
                <MiniMap />
            </ReactFlow>
        </div>
    );
};
