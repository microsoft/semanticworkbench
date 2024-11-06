// Copyright (c) Microsoft. All rights reserved.

import {
    $createTextNode,
    $getRoot,
    ChatInput,
    ChatInputEntityNode,
    ChatInputSubmitEvents,
    ChatInputTokenNode,
    EditorInputValueData,
    EditorState,
    LexicalEditor,
    LexicalEditorRefPlugin,
    TextNode,
} from '@fluentui-copilot/react-copilot';
import { Button, makeStyles, mergeClasses, shorthands, Title3, tokens } from '@fluentui/react-components';
import { Attach20Regular } from '@fluentui/react-icons';
import debug from 'debug';
import { getEncoding } from 'js-tiktoken';
import {
    $createLineBreakNode,
    CLEAR_EDITOR_COMMAND,
    COMMAND_PRIORITY_LOW,
    LineBreakNode,
    PASTE_COMMAND,
    SerializedTextNode,
} from 'lexical';
import React from 'react';
import { Constants } from '../../Constants';
import useDragAndDrop from '../../libs/useDragAndDrop';
import { useNotify } from '../../libs/useNotify';
import { AssistantCapability } from '../../models/AssistantCapability';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import {
    updateGetConversationMessagesQueryData,
    useCreateConversationMessageMutation,
    useGetConversationMessagesQuery,
    useGetConversationParticipantsQuery,
    useUploadConversationFilesMutation,
} from '../../services/workbench';
import { ClearEditorPlugin } from './ChatInputPlugins/ClearEditorPlugin';
import { ParticipantMentionsPlugin } from './ChatInputPlugins/ParticipantMentionsPlugin';
import { InputAttachmentList } from './InputAttachmentList';
import { InputOptionsControl } from './InputOptionsControl';
import { SpeechButton } from './SpeechButton';

const log = debug(Constants.debug.root).extend('InteractInput');

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        width: '100%',
        gap: tokens.spacingVerticalS,
        ...shorthands.padding(tokens.spacingVerticalM),
    },
    readOnly: {
        pointerEvents: 'none',
        opacity: 0.5,
    },
    content: {
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'stretch',
        width: '100%',
        maxWidth: `${Constants.app.maxContentWidth}px`,
        gap: tokens.spacingVerticalS,

        // ...shorthands.padding(0, tokens.spacingHorizontalXXL, 0, tokens.spacingHorizontalM),
        boxSizing: 'border-box',
    },
    row: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        width: '100%',
        gap: tokens.spacingHorizontalS,
    },
    rowEnd: {
        justifyContent: 'end',
    },
    fullWidth: {
        width: '100%',
        maxWidth: '100%',
    },
    commandTextbox: {
        '& [role=textbox]': {
            fontFamily: 'monospace',
        },
    },
    dragTarget: {
        transition: 'border 0.3s',
        border: `2px dashed transparent`,
    },
    dragOverBody: {
        border: `2px dashed ${tokens.colorPaletteBlueBorderActive}`,
        borderRadius: tokens.borderRadiusLarge,
    },
    dragOverTarget: {
        cursor: 'copy',
        border: `2px dashed ${tokens.colorPaletteGreenBorderActive}`,
        borderRadius: tokens.borderRadiusLarge,
    },
});

interface InteractInputProps {
    conversationId: string;
    additionalContent?: React.ReactNode;
    readOnly: boolean;
    assistantCapabilities: Set<AssistantCapability>;
}

interface SerializedTemporaryTextNode extends SerializedTextNode {}

class TemporaryTextNode extends TextNode {
    static getType() {
        return 'temporary';
    }

    static clone(node: TemporaryTextNode) {
        return new TemporaryTextNode(node.__text, node.__key);
    }

    static importJSON(serializedNode: SerializedTextNode): TextNode {
        return super.importJSON(serializedNode) as TemporaryTextNode;
    }

    exportJSON(): SerializedTextNode {
        return super.exportJSON() as SerializedTemporaryTextNode;
    }
}

export const InteractInput: React.FC<InteractInputProps> = (props) => {
    const { conversationId, additionalContent, readOnly, assistantCapabilities } = props;
    const classes = useClasses();
    const dropTargetRef = React.useRef<HTMLDivElement>(null);
    const localUserId = useAppSelector((state) => state.localUser.id);
    const isDraggingOverBody = useAppSelector((state) => state.app.isDraggingOverBody);
    const isDraggingOverTarget = useDragAndDrop(dropTargetRef.current, log);
    const [createMessage] = useCreateConversationMessageMutation();
    const [uploadConversationFiles] = useUploadConversationFilesMutation();
    const [messageTypeValue, setMessageTypeValue] = React.useState<'Chat' | 'Command'>('Chat');
    const [tokenCount, setTokenCount] = React.useState(0);
    const [directedAtId, setDirectedAtId] = React.useState<string>();
    const [attachmentFiles, setAttachmentFiles] = React.useState<Map<string, File>>(new Map());
    const [isSubmitting, setIsSubmitting] = React.useState(false);
    const [isListening, setIsListening] = React.useState(false);
    const [editorIsInitialized, setEditorIsInitialized] = React.useState(false);
    const editorRef = React.useRef<LexicalEditor | null>();
    const attachmentInputRef = React.useRef<HTMLInputElement>(null);
    const { notifyWarning } = useNotify();
    const dispatch = useAppDispatch();

    const {
        data: conversationMessages,
        isLoading: isConversationMessagesLoading,
        error: conversationMessagesError,
    } = useGetConversationMessagesQuery({ conversationId });

    const {
        data: participants,
        isLoading: isParticipantsLoading,
        error: participantsError,
    } = useGetConversationParticipantsQuery(conversationId);

    if (conversationMessagesError) {
        const errorMessage = JSON.stringify(conversationMessagesError);
        console.error(`Failed to load conversation messages: ${errorMessage}`);
    }

    if (participantsError) {
        const errorMessage = JSON.stringify(participantsError);
        console.error(`Failed to load conversation participants: ${errorMessage}`);
    }

    const editorRefCallback = React.useCallback((editor: LexicalEditor) => {
        editorRef.current = editor;

        // set the editor as initialized
        setEditorIsInitialized(true);
    }, []);

    // add a set of attachments to the list of attachments
    const addAttachments = React.useCallback(
        (files: Iterable<File>) => {
            setAttachmentFiles((prevFiles) => {
                const updatedFiles = new Map(prevFiles);
                const duplicates = new Map<string, number>();

                for (const file of files) {
                    // limit the number of attachments to the maximum allowed
                    if (updatedFiles.size >= Constants.app.maxFileAttachmentsPerMessage) {
                        notifyWarning({
                            id: 'attachment-limit-reached',
                            title: 'Attachment limit reached',
                            message: `Only ${Constants.app.maxFileAttachmentsPerMessage} files can be attached per message`,
                        });
                        return updatedFiles;
                    }

                    if (updatedFiles.has(file.name)) {
                        duplicates.set(file.name, (duplicates.get(file.name) || 0) + 1);
                        continue;
                    }

                    updatedFiles.set(file.name, file);
                }

                for (const [filename, count] of duplicates.entries()) {
                    notifyWarning({
                        id: `duplicate-attachment-${filename}`,
                        title: `Attachment with duplicate filename`,
                        message: `Attachment with filename '${filename}' ${count !== 1 ? 'was' : 'were'} ignored`,
                    });
                }
                return updatedFiles;
            });
        },
        [notifyWarning],
    );

    React.useEffect(() => {
        if (!editorIsInitialized) return;

        if (!editorRef.current) {
            console.error('Failed to get editor reference after initialization');
            return;
        }
        const editor = editorRef.current;

        const removePasteListener = editor.registerCommand(
            PASTE_COMMAND,
            (event: ClipboardEvent) => {
                log('paste event', event);

                const clipboardItems = event.clipboardData?.items;
                if (!clipboardItems) return false;

                for (const item of clipboardItems) {
                    if (item.kind !== 'file') continue;
                    const file = item.getAsFile();
                    if (!file) continue;
                    // ensure the filename is unique by appending a timestamp before the extension
                    const timestamp = new Date().getTime();
                    const filename = `${file.name.replace(/\.[^/.]+$/, '')}_${timestamp}${file.name.match(
                        /\.[^/.]+$/,
                    )}`;

                    // file.name is read-only, so create a new file object with the new name
                    // make sure to use the same file contents, content type, etc.
                    const updatedFile = filename !== file.name ? new File([file], filename, { type: file.type }) : file;

                    // add the file to the list of attachments
                    log('calling add attachment from paste', file);
                    addAttachments([updatedFile]);

                    // Prevent default paste for file items
                    event.preventDefault();
                    event.stopPropagation();

                    // Indicate command was handled
                    return true;
                }

                // Allow default handling for non-file paste
                return false;
            },
            COMMAND_PRIORITY_LOW,
        );

        return () => {
            // Clean up listeners on unmount
            removePasteListener();
        };
    }, [editorIsInitialized, addAttachments]);

    const tokenizer = React.useMemo(() => getEncoding('cl100k_base'), []);

    const onAttachmentChanged = React.useCallback(() => {
        if (!attachmentInputRef.current) {
            return;
        }
        addAttachments(attachmentInputRef.current.files ?? []);
        attachmentInputRef.current.value = '';
    }, [addAttachments]);

    const handleDrop = React.useCallback(
        (event: React.DragEvent) => {
            addAttachments(event.dataTransfer.files);
        },
        [addAttachments],
    );

    if (isConversationMessagesLoading || isParticipantsLoading) {
        return null;
    }

    const handleSend = (_event: ChatInputSubmitEvents, data: EditorInputValueData) => {
        if (data.value.trim() === '' || isSubmitting) {
            return;
        }

        (async () => {
            if (!localUserId) {
                throw new Error('Local user ID is not set');
            }

            setIsSubmitting(true);
            const content = data.value.trim();
            let metadata: Record<string, any> | undefined = directedAtId ? undefined : { directed_at: directedAtId };

            const messageType = messageTypeValue.toLowerCase() as 'chat' | 'command';

            const mentions: string[] = [];
            const nodes = editorRef.current?.getEditorState()._nodeMap;
            if (nodes) {
                for (const node of nodes.values()) {
                    if (node.__type !== 'entity') continue;
                    try {
                        const nodeData = (node as any).__data as { type: string; participant: ConversationParticipant };
                        if (nodeData.type === 'mention') {
                            mentions.push(nodeData.participant.id);
                        }
                    } catch (error) {
                        // ignore, not a mention
                    }
                }
            }

            if (mentions.length > 0) {
                if (!metadata) {
                    metadata = {};
                }
                metadata.mentions = mentions;
            }

            // optimistically update the UI
            // this will be replaced by the actual message when the mutation completes
            // need to define the extra fields for the message such as sender, timestamp, etc.
            // so that the message can be rendered correctly
            dispatch(
                updateGetConversationMessagesQueryData(conversationId, [
                    ...(conversationMessages ?? []),
                    {
                        id: 'optimistic',
                        sender: {
                            participantId: localUserId,
                            participantRole: 'user',
                        },
                        timestamp: new Date().toISOString(),
                        messageType,
                        content,
                        contentType: 'text/plain',
                        filenames: [],
                        metadata,
                        hasDebugData: false,
                    },
                ]),
            );

            editorRef.current?.dispatchCommand(CLEAR_EDITOR_COMMAND, undefined);

            // upload attachments
            const filenames = attachmentFiles.size > 0 ? [...attachmentFiles.keys()] : undefined;
            const files = attachmentFiles.size > 0 ? [...attachmentFiles.values()] : undefined;
            // reset the attachment files so that the same files are not uploaded again
            setAttachmentFiles(new Map());
            // reset the files form input
            if (attachmentInputRef.current) {
                attachmentInputRef.current.value = '';
            }
            if (files) {
                await uploadConversationFiles({ conversationId, files });
            }

            // create the message
            await createMessage({
                conversationId,
                content,
                messageType,
                filenames,
                metadata,
            });

            // reset for the next message
            setMessageTypeValue('Chat');

            setIsSubmitting(false);
        })();
    };

    const updateInput = (newInput: string) => {
        const newMessageType = newInput.startsWith('/') ? 'Command' : 'Chat';
        if (newMessageType !== messageTypeValue) {
            setMessageTypeValue(newMessageType);
        }

        const tokens = tokenizer.encode(newInput);
        setTokenCount(tokens.length);
    };

    const onAttachment = () => {
        attachmentInputRef.current?.click();
    };

    // update the listening state when the speech recognizer starts or stops
    // so that we can disable the input send while listening
    const handleListeningChange = (listening: boolean) => {
        setIsListening(listening);
    };

    // update the editor with the in-progress recognized text while the speech recognizer is recognizing,
    // which is not the final text yet, but it will give the user an idea of what is being recognized
    const handleSpeechRecognizing = (text: string) => {
        const editor = editorRef.current;
        if (!editor) {
            console.error('Failed to get editor reference');
            return;
        }

        editor.update(() => {
            // get the editor state
            const editorState: EditorState = editor.getEditorState();

            // check if there is a temporary text node in the editor
            // if found, update the text content of the temporary text node
            let foundTemporaryNode = false;
            editorState._nodeMap.forEach((node) => {
                if (node instanceof TemporaryTextNode) {
                    node.setTextContent(text);
                    foundTemporaryNode = true;
                }
            });

            // get the root node of the editor
            const root = $getRoot();

            // if no temporary text node was found, insert a new temporary text node at the end of the editor
            if (!foundTemporaryNode) {
                const selection = root.selectEnd();
                if (!selection) {
                    console.error('Failed to get selection');
                    return;
                }

                // insert a line break before the temporary text node if the editor is not empty
                if (root.getTextContentSize() > 0) {
                    selection.insertNodes([$createLineBreakNode()]);
                }

                // insert the temporary text node at the end of the editor
                selection.insertNodes([new TemporaryTextNode(text)]);
            }

            // select the end of the editor to ensure the temporary text node is visible
            root.selectEnd();
        });
    };

    // update the editor with the final recognized text when the speech recognizer has recognized the speech
    // this will replace the in-progress recognized text in the editor
    const handleSpeechRecognized = (text: string) => {
        const editor = editorRef.current;
        if (!editor) {
            console.error('Failed to get editor reference');
            return;
        }

        editor.update(() => {
            // get the editor state
            const editorState: EditorState = editor.getEditorState();

            // remove any temporary text nodes from the editor
            editorState._nodeMap.forEach((node) => {
                if (node instanceof TemporaryTextNode) {
                    node.remove();
                }
            });

            // get the root node of the editor
            const root = $getRoot();

            // insert the recognized text as a text node at the end of the editor
            const selection = root.selectEnd();
            if (!selection) {
                console.error('Failed to get selection');
                return;
            }
            selection.insertNodes([$createTextNode(text)]);

            // select the end of the editor to ensure the text node is visible
            root.selectEnd();
        });
    };

    const disableSend = readOnly || isSubmitting || tokenCount === 0;
    const disableInputs = readOnly || isSubmitting || isListening;
    const disableAttachments =
        readOnly || isSubmitting || !assistantCapabilities.has(AssistantCapability.SupportsConversationFiles);

    const tokenCounts = `${tokenCount} token${tokenCount !== 1 ? 's' : ''}`;
    const attachmentCount = disableAttachments
        ? ''
        : `${attachmentFiles.size} attachments (max ${Constants.app.maxFileAttachmentsPerMessage})`;
    const inputCounts = [tokenCounts, attachmentCount].filter((count) => count !== '').join(' | ');
    const attachFilesButtonTitle = disableAttachments
        ? 'Attachments are not supported by the assistants in this conversation'
        : 'Attach files';

    return (
        <div className={classes.root}>
            {readOnly ? (
                <div className={classes.readOnly}>
                    <Title3>You are currently observing this conversation.</Title3>
                </div>
            ) : (
                <div className={classes.content}>
                    {/* // this is for injecting controls for supporting features like workflow */}
                    {additionalContent}
                    <InputOptionsControl
                        disabled={readOnly}
                        messageTypeValue={messageTypeValue}
                        participants={participants}
                        onDirectedAtChange={setDirectedAtId}
                    />
                    <div
                        ref={dropTargetRef}
                        onDrop={handleDrop}
                        className={mergeClasses(
                            classes.row,
                            classes.dragTarget,
                            isDraggingOverTarget
                                ? classes.dragOverTarget
                                : isDraggingOverBody
                                ? classes.dragOverBody
                                : '',
                        )}
                    >
                        <ChatInput
                            className={mergeClasses(
                                classes.fullWidth,
                                messageTypeValue === 'Command' ? classes.commandTextbox : '',
                            )}
                            onChange={(_event, data) => updateInput(data.value)}
                            maxLength={Constants.app.maxInputLength}
                            characterCount={tokenCount}
                            charactersRemainingMessage={(charactersRemaining) =>
                                `${charactersRemaining} characters remaining`
                            }
                            count={<span>{inputCounts}</span>}
                            disabled={readOnly}
                            placeholderValue="Ask a question or request assistance or type / to enter a command."
                            customNodes={[ChatInputTokenNode, ChatInputEntityNode, LineBreakNode, TemporaryTextNode]}
                            disableSend={disableSend}
                            onSubmit={handleSend}
                            trimWhiteSpace
                            showCount
                            actions={
                                <span style={{ display: 'flex', alignItems: 'center' }}>
                                    <span>
                                        <input
                                            hidden
                                            ref={attachmentInputRef}
                                            type="file"
                                            onChange={onAttachmentChanged}
                                            multiple
                                        />
                                        <Button
                                            appearance="transparent"
                                            title={attachFilesButtonTitle}
                                            disabled={disableAttachments}
                                            icon={<Attach20Regular />}
                                            onClick={onAttachment}
                                        />
                                        <SpeechButton
                                            disabled={disableInputs}
                                            onListeningChange={handleListeningChange}
                                            onSpeechRecognizing={handleSpeechRecognizing}
                                            onSpeechRecognized={handleSpeechRecognized}
                                        />
                                    </span>
                                </span>
                            }
                            attachments={
                                <InputAttachmentList
                                    attachments={[...attachmentFiles.values()]}
                                    onDismissAttachment={(dismissedFile) =>
                                        setAttachmentFiles((prevFiles) => {
                                            const updatedFiles = new Map(prevFiles);
                                            updatedFiles.delete(dismissedFile.name);
                                            return updatedFiles;
                                        })
                                    }
                                />
                            }
                        >
                            <ClearEditorPlugin />
                            {participants && (
                                <ParticipantMentionsPlugin
                                    participants={participants.filter((participant) => participant.id !== localUserId)}
                                    parent={document.getElementById('app')}
                                />
                            )}
                            <LexicalEditorRefPlugin editorRef={editorRefCallback} />
                        </ChatInput>
                    </div>
                </div>
            )}
        </div>
    );
};
