// Copyright (c) Microsoft. All rights reserved.

import { Dropdown, makeStyles, mergeClasses, Option, tokens } from '@fluentui/react-components';
import React from 'react';
import { ConversationParticipant } from '../../models/ConversationParticipant';

const useClasses = makeStyles({
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
});

interface InputOptionsControlProps {
    disabled?: boolean;
    messageTypeValue: string;
    participants?: ConversationParticipant[];
    onDirectedAtChange: (participantId?: string) => void;
}

const directedAtDefaultKey = 'all';
const directedAtDefaultValue = 'All assistants';

export const InputOptionsControl: React.FC<InputOptionsControlProps> = (props) => {
    const { messageTypeValue, participants, onDirectedAtChange, disabled } = props;
    const classes = useClasses();
    const [directedAtId, setDirectedAtId] = React.useState<string>(directedAtDefaultKey);
    const [directedAtName, setDirectedAtName] = React.useState<string>(directedAtDefaultValue);

    const handleDirectedToChange = (participantId?: string, participantName?: string) => {
        setDirectedAtId(participantId ?? directedAtDefaultKey);
        setDirectedAtName(participantName ?? directedAtDefaultValue);

        onDirectedAtChange(participantId);
    };

    return (
        <div className={classes.row}>
            <div className={classes.row}>Message type: {messageTypeValue}</div>
            <div className={mergeClasses(classes.row, classes.rowEnd)}>
                <div>Directed to:</div>
                <div>
                    <Dropdown
                        disabled={
                            disabled ||
                            participants?.filter((participant) => participant.role === 'assistant').length === 0 ||
                            messageTypeValue !== 'Command'
                        }
                        className={classes.fullWidth}
                        placeholder="Select participant"
                        value={directedAtName}
                        selectedOptions={[directedAtId]}
                        onOptionSelect={(_event, data) => handleDirectedToChange(data.optionValue, data.optionText)}
                    >
                        <Option key={directedAtDefaultKey} value={directedAtDefaultKey}>
                            {directedAtDefaultValue}
                        </Option>
                        {participants
                            ?.slice()
                            .sort((a, b) => a.name.localeCompare(b.name))
                            .filter((participant) => participant.role === 'assistant')
                            .map((participant) => (
                                <Option key={participant.id} value={participant.id}>
                                    {participant.name}
                                </Option>
                            ))}
                    </Dropdown>
                </div>
            </div>
        </div>
    );
};
