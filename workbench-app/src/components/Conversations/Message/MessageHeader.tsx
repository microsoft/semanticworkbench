import { Timestamp } from '@fluentui-copilot/react-copilot';
import { Persona, Text } from '@fluentui/react-components';
import React from 'react';
import { useParticipantUtility } from '../../../libs/useParticipantUtility';
import { ConversationParticipant } from '../../../models/ConversationParticipant';

interface HeaderProps {
    participant: ConversationParticipant;
    time: string;
    attribution?: string;
    className?: string;
}

export const MessageHeader: React.FC<HeaderProps> = (props) => {
    const { participant, time, attribution, className } = props;
    const { getAvatarData } = useParticipantUtility();

    return (
        <div className={className}>
            <Persona size="extra-small" name={participant.name} avatar={getAvatarData(participant)} />
            {attribution && <Text size={300}>[{attribution}]</Text>}
            <div>
                <Timestamp>{time}</Timestamp>
            </div>
        </div>
    );
};
