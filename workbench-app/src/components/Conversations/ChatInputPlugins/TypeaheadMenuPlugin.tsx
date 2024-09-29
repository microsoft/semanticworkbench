// Copyright (c) Microsoft. All rights reserved.
// Based on code from: https://github.com/facebook/lexical/blob/main/packages/lexical-react/src/LexicalTypeaheadMenuPlugin.tsx

import type { MenuRenderFn, MenuResolution, MenuTextMatch, TriggerFn } from './LexicalMenu';

import { useLexicalComposerContext } from '@fluentui-copilot/react-copilot';
import {
    $getSelection,
    $isRangeSelection,
    $isTextNode,
    COMMAND_PRIORITY_LOW,
    CommandListenerPriority,
    createCommand,
    LexicalCommand,
    LexicalEditor,
    RangeSelection,
    TextNode,
} from 'lexical';
import * as React from 'react';
import { useCallback, useEffect, useState } from 'react';
import './TypeaheadMenuPlugin.css';

import { LexicalMenu, MenuOption, useMenuAnchorRef } from './LexicalMenu';

export const PUNCTUATION = '\\.,\\+\\*\\?\\$\\@\\|#{}\\(\\)\\^\\-\\[\\]\\\\/!%\'"~=<>_:;';

const getTextUpToAnchor = (selection: RangeSelection): string | null => {
    const anchor = selection.anchor;
    if (anchor.type !== 'text') {
        return null;
    }
    const anchorNode = anchor.getNode();
    if (!anchorNode.isSimpleText()) {
        return null;
    }
    const anchorOffset = anchor.offset;
    return anchorNode.getTextContent().slice(0, anchorOffset);
};

const tryToPositionRange = (leadOffset: number, range: Range, editorWindow: Window): boolean => {
    const domSelection = editorWindow.getSelection();
    if (domSelection === null || !domSelection.isCollapsed) {
        return false;
    }
    const anchorNode = domSelection.anchorNode;
    const startOffset = leadOffset;
    const endOffset = domSelection.anchorOffset;

    if (anchorNode == null || endOffset == null) {
        return false;
    }

    try {
        range.setStart(anchorNode, startOffset);
        range.setEnd(anchorNode, endOffset);
    } catch (error) {
        return false;
    }

    return true;
};

const getQueryTextForSearch = (editor: LexicalEditor): string | null => {
    let text = null;
    editor.getEditorState().read(() => {
        const selection = $getSelection();
        if (!$isRangeSelection(selection)) {
            return;
        }
        text = getTextUpToAnchor(selection);
    });
    return text;
};

const isSelectionOnEntityBoundary = (editor: LexicalEditor, offset: number): boolean => {
    if (offset !== 0) {
        return false;
    }
    return editor.getEditorState().read(() => {
        const selection = $getSelection();
        if ($isRangeSelection(selection)) {
            const anchor = selection.anchor;
            const anchorNode = anchor.getNode();
            const prevSibling = anchorNode.getPreviousSibling();
            return $isTextNode(prevSibling) && prevSibling.isTextEntity();
        }
        return false;
    });
};

const startTransition = (callback: () => void) => {
    if (React.startTransition) {
        React.startTransition(callback);
    } else {
        callback();
    }
};

export const SCROLL_TYPEAHEAD_OPTION_INTO_VIEW_COMMAND: LexicalCommand<{
    index: number;
    option: MenuOption;
}> = createCommand('SCROLL_TYPEAHEAD_OPTION_INTO_VIEW_COMMAND');

export const useBasicTypeaheadTriggerMatch = (
    trigger: string,
    { minLength = 1, maxLength = 75 }: { minLength?: number; maxLength?: number },
): TriggerFn => {
    return useCallback(
        (text: string) => {
            const validChars = '[^' + trigger + PUNCTUATION + '\\s]';
            const TypeaheadTriggerRegex = new RegExp(
                '(^|\\s|\\()([' + trigger + ']((?:' + validChars + '){0,' + maxLength + '}))$',
            );
            const match = TypeaheadTriggerRegex.exec(text);
            if (match !== null) {
                const maybeLeadingWhitespace = match[1];
                const matchingString = match[3];
                if (matchingString.length >= minLength) {
                    return {
                        leadOffset: match.index + maybeLeadingWhitespace.length,
                        matchingString,
                        replaceableString: match[2],
                    };
                }
            }
            return null;
        },
        [maxLength, minLength, trigger],
    );
};

export type TypeaheadMenuPluginProps<TOption extends MenuOption> = {
    onQueryChange: (matchingString: string | null) => void;
    onSelectOption: (
        option: TOption,
        textNodeContainingQuery: TextNode | null,
        closeMenu: () => void,
        matchingString: string,
    ) => void;
    options: Array<TOption>;
    menuRenderFn: MenuRenderFn<TOption>;
    triggerFn: TriggerFn;
    onOpen?: (resolution: MenuResolution) => void;
    onClose?: () => void;
    anchorClassName?: string;
    commandPriority?: CommandListenerPriority;
    parent?: HTMLElement;
};

export const TypeaheadMenuPlugin = <TOption extends MenuOption>({
    options,
    onQueryChange,
    onSelectOption,
    onOpen,
    onClose,
    menuRenderFn,
    triggerFn,
    anchorClassName,
    commandPriority = COMMAND_PRIORITY_LOW,
    parent,
}: TypeaheadMenuPluginProps<TOption>): JSX.Element | null => {
    const [editor] = useLexicalComposerContext();
    const [resolution, setResolution] = useState<MenuResolution | null>(null);
    const anchorElementRef = useMenuAnchorRef(resolution, setResolution, anchorClassName, parent);

    const closeTypeahead = useCallback(() => {
        setResolution(null);
        if (onClose != null && resolution !== null) {
            onClose();
        }
    }, [onClose, resolution]);

    const openTypeahead = useCallback(
        (res: MenuResolution) => {
            setResolution(res);
            if (onOpen != null && resolution === null) {
                onOpen(res);
            }
        },
        [onOpen, resolution],
    );

    useEffect(() => {
        const updateListener = () => {
            editor.getEditorState().read(() => {
                const editorWindow = editor._window || window;
                const range = editorWindow.document.createRange();
                const selection = $getSelection();
                const text = getQueryTextForSearch(editor);

                if (!$isRangeSelection(selection) || !selection.isCollapsed() || text === null || range === null) {
                    closeTypeahead();
                    return;
                }

                const match = triggerFn(text, editor);
                onQueryChange(match ? match.matchingString : null);

                if (match !== null && !isSelectionOnEntityBoundary(editor, match.leadOffset)) {
                    const isRangePositioned = tryToPositionRange(match.leadOffset, range, editorWindow);
                    if (isRangePositioned !== null) {
                        startTransition(() =>
                            openTypeahead({
                                getRect: () => range.getBoundingClientRect(),
                                match,
                            }),
                        );
                        return;
                    }
                }
                closeTypeahead();
            });
        };

        const removeUpdateListener = editor.registerUpdateListener(updateListener);

        return () => {
            removeUpdateListener();
        };
    }, [editor, triggerFn, onQueryChange, resolution, closeTypeahead, openTypeahead]);

    return resolution === null || editor === null ? null : (
        <LexicalMenu
            close={closeTypeahead}
            resolution={resolution}
            editor={editor}
            anchorElementRef={anchorElementRef}
            options={options}
            menuRenderFn={menuRenderFn}
            shouldSplitNodeWithQuery={true}
            onSelectOption={onSelectOption}
            commandPriority={commandPriority}
        />
    );
};

export { MenuOption, MenuRenderFn, MenuResolution, MenuTextMatch, TriggerFn };
