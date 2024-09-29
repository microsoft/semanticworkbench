// Copyright (c) Microsoft. All rights reserved.

import { Button, Tooltip } from '@fluentui/react-components';
import { Mic20Regular } from '@fluentui/react-icons';
import debug from 'debug';
import * as speechSdk from 'microsoft-cognitiveservices-speech-sdk';
import React from 'react';
import { Constants } from '../../Constants';
import { useAppSelector } from '../../redux/app/hooks';

const log = debug(Constants.debug.root).extend('SpeechButton');

interface SpeechButtonProps {
    disabled?: boolean;
    onListeningChange: (isListening: boolean) => void;
    onSpeechRecognizing?: (text: string) => void;
    onSpeechRecognized: (text: string) => void;
}

export const SpeechButton: React.FC<SpeechButtonProps> = (props) => {
    const { disabled, onListeningChange, onSpeechRecognizing, onSpeechRecognized } = props;
    const { speechKey, speechRegion } = useAppSelector((state) => state.settings);
    const [recognizer, setRecognizer] = React.useState<speechSdk.SpeechRecognizer>();
    const [isListening, setIsListening] = React.useState(false);
    const [lastSpeechResultTimestamp, setLastSpeechResultTimestamp] = React.useState(0);

    React.useEffect(() => {
        if (recognizer) return;
        if (!speechKey || !speechRegion) return;

        const speechConfig = speechSdk.SpeechConfig.fromSubscription(speechKey, speechRegion);
        speechConfig.outputFormat = speechSdk.OutputFormat.Detailed;
        const speechRecognizer = new speechSdk.SpeechRecognizer(speechConfig);

        // Setup the recognizer

        // Triggered when the speech recognizer has started listening
        speechRecognizer.sessionStarted = (_sender, event) => {
            log('Session started', event);
            setIsListening(true);
            setLastSpeechResultTimestamp(Date.now());
        };

        // Triggered when the speech recognizer has detected that speech has started
        speechRecognizer.speechStartDetected = (_sender, event) => {
            log('Speech started', event);
            setLastSpeechResultTimestamp(Date.now());
        };

        // Triggered periodically while the speech recognizer is recognizing speech
        speechRecognizer.recognizing = (_sender, event) => {
            log('Speech Recognizing', event);

            const text = event.result.text;
            if (text.trim() === '') return;

            onSpeechRecognizing?.(text);
            setLastSpeechResultTimestamp(Date.now());
        };

        // Triggered when the speech recognizer has recognized speech
        speechRecognizer.recognized = (_sender, event) => {
            log('Speech Recognized', event);

            const text = event.result.text;
            if (text.trim() === '') return;

            onSpeechRecognized(text);
            setLastSpeechResultTimestamp(Date.now());
        };

        // Triggered when the speech recognizer has detected that speech has stopped
        speechRecognizer.speechEndDetected = (_sender, event) => {
            log('Speech ended', event);
        };

        // Triggered when the speech recognizer has stopped listening
        speechRecognizer.sessionStopped = (_sender, event) => {
            log('Session stopped', event);
            setIsListening(false);
        };

        // Triggered when the speech recognizer has canceled
        speechRecognizer.canceled = (_sender, event) => {
            log('Speech Canceled', event);
            setIsListening(false);
        };

        setRecognizer(speechRecognizer);
    }, [onSpeechRecognized, onSpeechRecognizing, recognizer, speechKey, speechRegion]);

    React.useEffect(() => {
        onListeningChange(isListening);
    }, [isListening, onListeningChange]);

    // Call this function to stop the speech recognizer
    const stopListening = React.useCallback(() => {
        if (!isListening) return;
        recognizer?.stopContinuousRecognitionAsync();
        setIsListening(false);
    }, [isListening, recognizer]);

    // Call this function to start the speech recognizer to recognize speech continuously until stopped
    const recognizeContinuously = React.useCallback(() => {
        if (isListening) return;
        recognizer?.startContinuousRecognitionAsync();
    }, [isListening, recognizer]);

    // check if the last speech result is too old, if so, stop listening
    React.useEffect(() => {
        // check in an interval
        const interval = setInterval(() => {
            if (isListening && Date.now() - lastSpeechResultTimestamp > Constants.app.speechIdleTimeoutMs) {
                stopListening();
            }
        }, 1000);

        return () => clearInterval(interval);
    }, [isListening, lastSpeechResultTimestamp, stopListening]);

    const speechButton = (
        <Button
            appearance="transparent"
            // should ignore the disabled prop when isListening is true so that
            // the button can still be clicked to stop listening
            disabled={(!isListening && disabled) || !recognizer}
            style={{ color: isListening ? 'red' : undefined }}
            icon={<Mic20Regular color={isListening ? 'green' : undefined} />}
            onClick={isListening ? stopListening : recognizeContinuously}
        />
    );

    return recognizer ? (
        <Tooltip content={isListening ? 'Click to stop listening.' : 'Click to start listening.'} relationship="label">
            {speechButton}
        </Tooltip>
    ) : (
        <Tooltip content="Enable speech in settings" relationship="label">
            {speechButton}
        </Tooltip>
    );
};
