// Copyright (c) Microsoft. All rights reserved.
// based on code from: https://github.com/facebook/lexical/blob/main/packages/lexical-react/src/LexicalClearEditorPlugin.ts

import { useLexicalComposerContext } from '@fluentui-copilot/react-copilot';
import {
    $createParagraphNode,
    $getRoot,
    $getSelection,
    $isRangeSelection,
    CLEAR_EDITOR_COMMAND,
    COMMAND_PRIORITY_EDITOR,
} from 'lexical';
import React from 'react';

interface ClearEditorPluginProps {
    onClear?: () => void;
}

export const ClearEditorPlugin = ({ onClear }: ClearEditorPluginProps): JSX.Element | null => {
    const [editor] = useLexicalComposerContext();

    React.useLayoutEffect(() => {
        return editor.registerCommand(
            CLEAR_EDITOR_COMMAND,
            () => {
                editor.update(() => {
                    if (onClear == null) {
                        const root = $getRoot();
                        const selection = $getSelection();
                        const paragraph = $createParagraphNode();
                        root.clear();
                        root.append(paragraph);

                        if (selection !== null) {
                            paragraph.select();
                        }
                        if ($isRangeSelection(selection)) {
                            selection.format = 0;
                        }
                    } else {
                        onClear();
                    }
                });
                return true;
            },
            COMMAND_PRIORITY_EDITOR,
        );
    }, [editor, onClear]);

    return null;
};
