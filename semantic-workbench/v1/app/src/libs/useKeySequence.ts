// Copyright (c) Microsoft. All rights reserved.
import React from 'react';

export const useKeySequence = (sequence: string[], onKeySequenceComplete: () => void) => {
    const buffer = React.useRef<string[]>([]);

    const keySequence = React.useCallback(
        (event: KeyboardEvent) => {
            if (event.defaultPrevented) return;

            if (event.key === sequence[buffer.current.length]) {
                buffer.current = [...buffer.current, event.key];
            } else {
                buffer.current = [];
            }

            if (buffer.current.length === sequence.length) {
                const bufferString = buffer.current.toString();
                const sequenceString = sequence.toString();

                if (sequenceString === bufferString) {
                    buffer.current = [];
                    onKeySequenceComplete();
                }
            }
        },
        [onKeySequenceComplete, sequence],
    );

    React.useEffect(() => {
        document.addEventListener('keydown', keySequence);
        return () => document.removeEventListener('keydown', keySequence);
    }, [keySequence]);
};
