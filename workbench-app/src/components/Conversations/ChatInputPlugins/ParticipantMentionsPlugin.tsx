// Copyright (c) Microsoft. All rights reserved.
// Based on code from: https://github.com/facebook/lexical/blob/main/packages/lexical-playground/src/plugins/MentionsPlugin/index.tsx

import { $createChatInputEntityNode, TextNode, useLexicalComposerContext } from '@fluentui-copilot/react-copilot';
import { Label } from '@fluentui/react-components';
import React from 'react';
import { createPortal } from 'react-dom';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import { MenuOption, MenuTextMatch } from './LexicalMenu';
import { TypeaheadMenuPlugin, useBasicTypeaheadTriggerMatch } from './TypeaheadMenuPlugin';

const punctuationCharacters = '\\.,\\+\\*\\?\\$\\@\\|#{}\\(\\)\\^\\-\\[\\]\\\\/!%\'"~=<>_:;';
const triggerCharacters = ['@'].join('');

// Chars we expect to see in a mention (non-space, non-punctuation).
const validCharacters = '[^' + triggerCharacters + punctuationCharacters + '\\s]';

// Non-standard series of chars. Each series must be preceded and followed by
// a valid char.
const validJoins =
    '(?:' +
    '\\.[ |$]|' + // E.g. "r. " in "Mr. Smith"
    ' |' + // E.g. " " in "Josh Duck"
    '[' +
    punctuationCharacters +
    ']|' + // E.g. "-' in "Smith-Jones"
    ')';

const lengthLimit = 75;

const atSignMentionsRegex = new RegExp(
    '(^|\\s|\\()([' + triggerCharacters + ']((?:' + validCharacters + validJoins + '){0,' + lengthLimit + '}))$',
);

// 50 is the longest alias length limit.
const aliasLengthLimit = 50;

// Regex used to match alias.
const atSignMentionsRegexAliasRegex = new RegExp(
    '(^|\\s|\\()([' + triggerCharacters + ']((?:' + validCharacters + '){0,' + aliasLengthLimit + '}))$',
);

// At most, 5 suggestions are shown in the popup.
const suggestionListLengthLimit = 5;

interface ParticipantMentionsPluginProps {
    participants: ConversationParticipant[];
    parent?: HTMLElement | null;
}

class MentionTypeaheadOption extends MenuOption {
    participant: ConversationParticipant;

    constructor(participant: ConversationParticipant) {
        super(participant.id);
        this.participant = participant;
    }
}

const MentionsTypeaheadMenuItem = ({
    index,
    isSelected,
    onClick,
    onMouseEnter,
    option,
}: {
    index: number;
    isSelected: boolean;
    onClick: () => void;
    onMouseEnter: () => void;
    option: MentionTypeaheadOption;
}) => {
    let className = 'item';
    if (isSelected) {
        className += ' selected';
    }
    return (
        <li
            key={option.key}
            tabIndex={-1}
            className={className}
            ref={option.setRefElement}
            role="option"
            aria-selected={isSelected}
            id={'typeahead-item-' + index}
            onMouseEnter={onMouseEnter}
            onClick={onClick}
        >
            <Label>{option.participant.name}</Label>
        </li>
    );
};

const checkForAtSignMentions = (text: string, minMatchLength: number): MenuTextMatch | null => {
    let match = atSignMentionsRegex.exec(text);

    if (match === null) {
        match = atSignMentionsRegexAliasRegex.exec(text);
    }
    if (match !== null) {
        // The strategy ignores leading whitespace but we need to know it's
        // length to add it to the leadOffset
        const maybeLeadingWhitespace = match[1];

        const matchingString = match[3];
        if (matchingString.length >= minMatchLength) {
            return {
                leadOffset: match.index + maybeLeadingWhitespace.length,
                matchingString,
                replaceableString: match[2],
            };
        }
    }
    return null;
};

const getPossibleQueryMatch = (text: string): MenuTextMatch | null => {
    return checkForAtSignMentions(text, 1);
};

export const ParticipantMentionsPlugin: React.FC<ParticipantMentionsPluginProps> = (props) => {
    const { participants, parent } = props;
    const [editor] = useLexicalComposerContext();
    const [queryString, setQueryString] = React.useState<string | null>(null);
    const [results, setResults] = React.useState<ConversationParticipant[]>([]);

    React.useEffect(() => {
        if (queryString === null) {
            setResults([]);
            return;
        }

        const query = queryString.toLowerCase();
        const results = participants.filter((participant) => participant.name.toLowerCase().includes(query));
        setResults(results);
    }, [queryString, participants]);

    const options = React.useMemo(
        () => results.map((result) => new MentionTypeaheadOption(result)).slice(0, suggestionListLengthLimit),
        [results],
    );

    const checkForSlashTriggerMatch = useBasicTypeaheadTriggerMatch('/', {
        minLength: 0,
    });

    const checkForMentionMatch = React.useCallback(
        (text: string) => {
            const slashMatch = checkForSlashTriggerMatch(text, editor);
            if (slashMatch !== null) {
                return null;
            }
            return getPossibleQueryMatch(text);
        },
        [checkForSlashTriggerMatch, editor],
    );

    const onSelectOption = React.useCallback(
        (selectedOption: MentionTypeaheadOption, nodeToReplace: TextNode | null, closeMenu: () => void) => {
            editor.update(() => {
                const data = {
                    type: 'mention',
                    participant: selectedOption.participant,
                };
                const mentionNode = $createChatInputEntityNode(
                    selectedOption.key,
                    `@${selectedOption.participant.name}`,
                    data,
                );
                if (nodeToReplace) {
                    nodeToReplace.replace(mentionNode);
                }
                closeMenu();
            });
        },
        [editor],
    );

    return (
        <TypeaheadMenuPlugin<MentionTypeaheadOption>
            onQueryChange={setQueryString}
            onSelectOption={onSelectOption}
            triggerFn={checkForMentionMatch}
            options={options}
            parent={parent ?? undefined}
            menuRenderFn={(anchorElementRef, { selectedIndex, selectOptionAndCleanUp, setHighlightedIndex }) =>
                anchorElementRef.current && results.length
                    ? createPortal(
                          <div className="typeahead-popover mentions-menu">
                              <ul>
                                  {options.map((option, i: number) => (
                                      <MentionsTypeaheadMenuItem
                                          index={i}
                                          isSelected={selectedIndex === i}
                                          onClick={() => {
                                              setHighlightedIndex(i);
                                              selectOptionAndCleanUp(option);
                                          }}
                                          onMouseEnter={() => {
                                              setHighlightedIndex(i);
                                          }}
                                          key={option.key}
                                          option={option}
                                      />
                                  ))}
                              </ul>
                          </div>,
                          anchorElementRef.current,
                      )
                    : null
            }
        />
    );
};
