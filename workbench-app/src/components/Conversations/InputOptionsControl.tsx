// Copyright (c) Microsoft. All rights reserved.

import { Caption1, Dropdown, makeStyles, mergeClasses, Option, tokens } from '@fluentui/react-components';
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
    collapsible: {
        minWidth: 'initial',
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

    const assistantParticipants =
        participants
            ?.filter((participant) => participant.role === 'assistant')
            .filter((participant) => participant.active)
            .toSorted((a, b) => a.name.localeCompare(b.name)) ?? [];

    const handleDirectedToChange = (participantId?: string, participantName?: string) => {
        setDirectedAtId(participantId ?? directedAtDefaultKey);
        setDirectedAtName(participantName ?? directedAtDefaultValue);

        onDirectedAtChange(participantId);
    };

    return (
        <div className={classes.row}>
            <div className={classes.row}>
                <Caption1>Mode: {messageTypeValue}</Caption1>
            </div>
            <div className={mergeClasses(classes.row, classes.rowEnd)}>
                <Caption1>Directed: </Caption1>
                <Dropdown
                    className={classes.collapsible}
                    disabled={disabled || assistantParticipants.length < 2 || messageTypeValue !== 'Command'}
                    placeholder="Select participant"
                    value={directedAtName}
                    selectedOptions={[directedAtId]}
                    onOptionSelect={(_event, data) => handleDirectedToChange(data.optionValue, data.optionText)}
                >
                    <Option key={directedAtDefaultKey} value={directedAtDefaultKey}>
                        {directedAtDefaultValue}
                    </Option>
                    {assistantParticipants.map((participant) => (
                        <Option key={participant.id} value={participant.id}>
                            {participant.name}
                        </Option>
                    ))}
                </Dropdown>
            </div>
        </div>
    );
};
