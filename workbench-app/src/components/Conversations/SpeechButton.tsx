// Copyright (c) Microsoft. All rights reserved.

import { Button, Tooltip } from '@fluentui/react-components';
import { Mic20Regular } from '@fluentui/react-icons';
import debug from 'debug';
import * as speechSdk from 'microsoft-cognitiveservices-speech-sdk';
import React from 'react';
import { Constants } from '../../Constants';
import { useWorkbenchService } from '../../libs/useWorkbenchService';

const log = debug(Constants.debug.root).extend('SpeechButton');

interface SpeechButtonProps {
    disabled?: boolean;
    onListeningChange: (isListening: boolean) => void;
    onSpeechRecognizing?: (text: string) => void;
    onSpeechRecognized: (text: string) => void;
}

export const SpeechButton: React.FC<SpeechButtonProps> = (props) => {
    const { disabled, onListeningChange, onSpeechRecognizing, onSpeechRecognized } = props;
    const [recognizer, setRecognizer] = React.useState<speechSdk.SpeechRecognizer>();
    const [isFetching, setIsFetching] = React.useState(false);
    const [isListening, setIsListening] = React.useState(false);
    const [lastSpeechResultTimestamp, setLastSpeechResultTimestamp] = React.useState(0);

    const [azureSpeechTokenAcquisitionTimestamp, setAzureSpeechTokenAcquisitionTimestamp] = React.useState(0);
    const [tokenResult, setTokenResult] = React.useState({ token: '', region: '' });

    const workbenchService = useWorkbenchService();

    const getAzureSpeechTokenAsync = React.useCallback(async () => {
        if (Date.now() - azureSpeechTokenAcquisitionTimestamp <= Constants.app.azureSpeechTokenRefreshIntervalMs) {
            return tokenResult;
        }

        log('Refreshing Azure Speech token');
        // Fetch the Azure Speech token
        const { token, region } = await workbenchService.getAzureSpeechTokenAsync();

        // Save the token acquisition timestamp
        setAzureSpeechTokenAcquisitionTimestamp(Date.now());
        setTokenResult({ token, region });
        return { token, region };
    }, [azureSpeechTokenAcquisitionTimestamp, workbenchService, tokenResult]);

    const getRecognizer = React.useCallback(async () => {
        // Get the Azure Speech token
        const { token, region } = await getAzureSpeechTokenAsync();
        if (!token || !region) {
            log('No Azure Speech token or region available, disabling speech input');
            return;
        }

        // Create the speech recognizer
        const speechConfig = speechSdk.SpeechConfig.fromAuthorizationToken(token, region);
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
    }, [getAzureSpeechTokenAsync, onSpeechRecognized, onSpeechRecognizing]);

    React.useEffect(() => {
        // If the recognizer is already available or we are fetching it, do nothing
        if (recognizer || isFetching) return;

        // Indicate that we are fetching the recognizer to prevent multiple fetches
        setIsFetching(true);

        // Fetch the recognizer, then indicate that we are no longer fetching even if the fetch fails
        getRecognizer().finally(() => setIsFetching(false));
    }, [getRecognizer, isFetching, recognizer]);

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
    const recognizeContinuously = React.useCallback(async () => {
        if (isListening || !recognizer) return;

        const { token } = await getAzureSpeechTokenAsync();
        if (token === '') {
            log('No Azure Speech token available for refresh');
            return;
        }

        recognizer.authorizationToken = token;

        // Start the speech recognizer
        recognizer.startContinuousRecognitionAsync();
    }, [getAzureSpeechTokenAsync, isListening, recognizer]);

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

    if (!recognizer) return null;

    return (
        <Tooltip content={isListening ? 'Click to stop listening.' : 'Click to start listening.'} relationship="label">
            <Button
                appearance="transparent"
                // should ignore the disabled prop when isListening is true so that
                // the button can still be clicked to stop listening
                disabled={(!isListening && disabled) || !recognizer}
                style={{ color: isListening ? 'red' : undefined }}
                icon={<Mic20Regular color={isListening ? 'green' : undefined} />}
                onClick={isListening ? stopListening : recognizeContinuously}
            />
        </Tooltip>
    );
};
