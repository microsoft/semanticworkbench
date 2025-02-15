import { Timestamp } from '@fluentui-copilot/react-copilot';
import { Persona } from '@fluentui/react-components';
import React from 'react';
import { useParticipantUtility } from '../../../libs/useParticipantUtility';

interface HeaderProps {
    participant: any; // update with the correct type if available
    time: string;
    attribution: JSX.Element | null;
    headerClassName: string;
}

export const MessageHeader: React.FC<HeaderProps> = ({ participant, time, attribution, headerClassName }) => {
    const { getAvatarData } = useParticipantUtility();

    return (
        <div className={headerClassName}>
            <Persona size="extra-small" name={participant.name} avatar={getAvatarData(participant)} />
            {attribution}
            <div>
                <Timestamp>{time}</Timestamp>
            </div>
        </div>
    );
};
