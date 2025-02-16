// Copyright (c) Microsoft. All rights reserved.

import { generateUuid } from '@azure/ms-rest-js';
import { makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { Info16Regular } from '@fluentui/react-icons';
import abcjs from 'abcjs';
import 'abcjs/abcjs-audio.css';
import debug from 'debug';
import React from 'react';
import { Constants } from '../../../Constants';
import { TooltipWrapper } from '../../App/TooltipWrapper';
import './MusicABCContentRenderer.css';

const log = debug(Constants.debug.root).extend('music-abc-content-renderer');

const useClasses = makeStyles({
    root: {
        whiteSpace: 'normal',
        position: 'relative',
    },
    controller: {
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalL, tokens.spacingVerticalXXXL),
    },
    infoButton: {
        position: 'absolute',
        top: tokens.spacingVerticalM,
        right: tokens.spacingHorizontalM,
    },
});

interface MusicABCContentRendererProps {
    content: string;
}

export const MusicABCContentRenderer: React.FC<MusicABCContentRendererProps> = (props) => {
    const { content } = props;
    const classes = useClasses();
    const [id] = React.useState(generateUuid());
    const abcAudioRef = React.useRef<HTMLDivElement>(null);

    React.useEffect(() => {
        void (async () => {
            abcjs.renderAbc(`abc-paper-${id}`, content, { responsive: 'resize' });

            const midi = abcjs.synth.getMidiFile(content, { midiOutputType: 'link' });
            const midiLink = document.getElementById(`abc-midi-${id}`);
            if (midiLink) {
                midiLink.innerHTML = midi;
            }
        })();
    }, [content, id]);

    React.useEffect(() => {
        void (async () => {
            if (!abcAudioRef.current || !abcjs.synth.supportsAudio()) return;

            const cursorControl = {};
            const audioParams = {
                chordsOff: false,
            };

            const visualObj = abcjs.renderAbc('*', content, { responsive: 'resize' });

            const synthControl = new abcjs.synth.SynthController();
            synthControl.load(`#abc-audio-${id}`, cursorControl, {
                displayLoop: true,
                displayRestart: true,
                displayPlay: true,
                displayProgress: true,
                displayWarp: true,
            });

            await synthControl.setTune(visualObj[0], false, audioParams);
            log('audio loaded');
        })();
    }, [content, id]);

    return (
        <div className={classes.root}>
            <div id={`abc-paper-${id}`} />
            <div id={`abc-midi-${id}`} className="abc-midi-link" />
            <div id={`abc-audio-${id}`} ref={abcAudioRef} className={classes.controller} />
            <TooltipWrapper content={content}>
                <Info16Regular className={classes.infoButton} />
            </TooltipWrapper>
        </div>
    );
};
