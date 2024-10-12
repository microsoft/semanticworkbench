// Copyright (c) Microsoft. All rights reserved.

import { Button, Tooltip } from '@fluentui/react-components';
import { Mic20Regular } from '@fluentui/react-icons';
import debug from 'debug';
import * as speechSdk from 'microsoft-cognitiveservices-speech-sdk';
import React from 'react';
import { Constants } from '../../Constants';
import { workbenchApi } from '../../services/workbench';
import { useGetAzureSpeechServiceTokenQuery } from '../../services/workbench/azureSpeech';

const log = debug(Constants.debug.root).extend('SpeechButton');

interface SpeechButtonProps {
    disabled?: boolean;
    onListeningChange: (isListening: boolean) => void;
    onSpeechRecognizing?: (text: string) => void;
    onSpeechRecognized: (text: string) => void;
}

export const SpeechButton: React.FC<SpeechButtonProps> = (props) => {
    const { disabled, onListeningChange, onSpeechRecognizing, onSpeechRecognized } = props;
    const {
        data: azureSpeechServiceToken,
        error: azureSpeechServiceTokenError,
        isLoading: isAzureSpeechServiceTokenLoading,
        refetch: refetchAzureSpeechServiceToken,
    } = useGetAzureSpeechServiceTokenQuery();
    const [recognizer, setRecognizer] = React.useState<speechSdk.SpeechRecognizer>();
    const [isListening, setIsListening] = React.useState(false);
    const [lastSpeechResultTimestamp, setLastSpeechResultTimestamp] = React.useState(0);

    if (azureSpeechServiceTokenError) {
        log('Failed to get Azure Speech token', azureSpeechServiceTokenError);
    }

    React.useEffect(() => {
        if (isAzureSpeechServiceTokenLoading) return;
        if (!azureSpeechServiceToken?.token || !azureSpeechServiceToken?.region) return;

        const timer = setTimeout(() => {
            // Invalidate the token after the refresh interval to force a new token to be fetched
            workbenchApi.util.invalidateTags(['AzureSpeechServiceToken']);
        }, Constants.app.azureSpeechTokenRefreshIntervalMs);

        return () => clearTimeout(timer);
    }, [azureSpeechServiceToken?.region, azureSpeechServiceToken?.token, isAzureSpeechServiceTokenLoading]);

    React.useEffect(() => {
        if (recognizer) return;
        if (isAzureSpeechServiceTokenLoading || !azureSpeechServiceToken?.token || !azureSpeechServiceToken.region)
            return;

        const speechConfig = speechSdk.SpeechConfig.fromAuthorizationToken(
            azureSpeechServiceToken.token,
            azureSpeechServiceToken.region,
        );
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
    }, [
        onSpeechRecognized,
        onSpeechRecognizing,
        recognizer,
        azureSpeechServiceToken,
        isAzureSpeechServiceTokenLoading,
    ]);

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

        let token = azureSpeechServiceToken?.token;
        if (!azureSpeechServiceToken?.token) {
            token = (await refetchAzureSpeechServiceToken()).data?.token;
        }
        if (!token) return;

        // Use the latest token
        recognizer.authorizationToken = token;
        recognizer.startContinuousRecognitionAsync();
    }, [isListening, recognizer, azureSpeechServiceToken?.token, refetchAzureSpeechServiceToken]);

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
