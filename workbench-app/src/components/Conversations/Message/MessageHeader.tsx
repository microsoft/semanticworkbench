import { Timestamp } from '@fluentui-copilot/react-copilot';
import { Persona } from '@fluentui/react-components';
import React from 'react';
import { useParticipantUtility } from '../../../libs/useParticipantUtility';

interface HeaderProps {
    participant: any; // TODO: Replace 'any' with the correct type (e.g., ParticipantModel) once available.
    time: string;
    attribution: JSX.Element | null;
    headerClassName: string;
}

export const MessageHeader: React.FC<HeaderProps> = ({ participant, time, attribution, headerClassName }) => {
        // Retrieve avatar data for the participant using a utility hook.
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
