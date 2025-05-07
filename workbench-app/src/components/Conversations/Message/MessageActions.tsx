import { makeStyles } from '@fluentui/react-components';
import React from 'react';
import { Conversation } from '../../../models/Conversation';
import { ConversationMessage } from '../../../models/ConversationMessage';
import { useGetConversationMessageDebugDataQuery } from '../../../services/workbench';
import { CopyButton } from '../../App/CopyButton';
import { DebugInspector } from '../DebugInspector';
import { MessageDelete } from '../MessageDelete';
import { MessageLink } from '../MessageLink';
import { RewindConversation } from '../RewindConversation';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'row',
        flexShrink: 1,
    },
});

interface MessageActionsProps {
    readOnly: boolean;
    message: ConversationMessage;
    conversation: Conversation;
    onRewind?: (message: ConversationMessage, redo: boolean) => void;
}

export const MessageActions: React.FC<MessageActionsProps> = (props) => {
    const { readOnly, message, conversation, onRewind } = props;

    const [skipDebugLoad, setSkipDebugLoad] = React.useState(true);
    const {
        data: debugData,
        isLoading: isLoadingDebugData,
        isUninitialized: isUninitializedDebugData,
    } = useGetConversationMessageDebugDataQuery(
        { conversationId: conversation.id, messageId: message.id },
        { skip: skipDebugLoad },
    );

    const classes = useClasses();

    return (
        <div className={classes.root}>
            {!readOnly && <MessageLink conversation={conversation} messageId={message.id} />}
            <DebugInspector
                debug={{
                    debug: message.hasDebugData ? debugData?.debugData || { loading: true } : null,
                    message: message,
                }}
                loading={isLoadingDebugData || isUninitializedDebugData}
                onOpen={() => {
                    setSkipDebugLoad(false);
                }}
            />
            <CopyButton data={message.content} tooltip="Copy message" size="small" appearance="transparent" />
            {!readOnly && (
                <>
                    <MessageDelete conversationId={conversation.id} message={message} />
                    {onRewind && <RewindConversation onRewind={(redo) => onRewind?.(message, redo)} />}
                </>
            )}
        </div>
    );
};
