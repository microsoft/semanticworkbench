import { Timestamp } from '@fluentui-copilot/react-copilot';
import { Text } from '@fluentui/react-components';
import React from 'react';
import { Utility } from '../../../libs/Utility';
import { ConversationMessage } from '../../../models/ConversationMessage';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import { ParticipantAvatar } from '../ParticipantAvatar';

interface HeaderProps {
    message: ConversationMessage;
    participant: ConversationParticipant;
    className?: string;
}

export const MessageHeader: React.FC<HeaderProps> = (props) => {
    const { message, participant, className } = props;

    const time = Utility.toFormattedDateString(message.timestamp, 'h:mm A');
    const attribution = message.metadata?.['attribution'];

    return (
        <div className={className}>
            <ParticipantAvatar participant={participant} />
            {attribution && <Text size={300}>[{attribution}]</Text>}
            <div>
                <Timestamp>{time}</Timestamp>
            </div>
        </div>
    );
};
