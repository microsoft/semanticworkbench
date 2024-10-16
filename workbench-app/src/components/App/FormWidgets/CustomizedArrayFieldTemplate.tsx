// Copyright (c) Microsoft. All rights reserved.

import {
    Accordion,
    AccordionHeader,
    AccordionItem,
    AccordionItemValue,
    AccordionPanel,
    Button,
    Text,
    Tooltip,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { Add16Regular, ArrowDown16Regular, ArrowUp16Regular, Delete16Regular } from '@fluentui/react-icons';
import { ArrayFieldTemplateItemType, ArrayFieldTemplateProps, RJSFSchema } from '@rjsf/utils';
import React from 'react';

const useClasses = makeStyles({
    heading: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalXXS,
    },
    panel: {
        ...shorthands.margin(0, 0, tokens.spacingVerticalM, tokens.spacingHorizontalXXXL),
        ...shorthands.padding(0, 0, 0, tokens.spacingHorizontalS),
    },
    itemActions: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
        ...shorthands.padding(0, 0, tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
    addAction: {
        ...shorthands.padding(tokens.spacingVerticalM),
    },
    inline: {
        display: 'inline',
    },
    simpleItem: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'end',
        // first item should take as much width as possible
        '& > *:first-child': {
            flexGrow: 1,
        },
        gap: tokens.spacingHorizontalS,
        ...shorthands.padding(tokens.spacingVerticalS, 0),
    },
});

export const CustomizedArrayFieldTemplate: React.FC<ArrayFieldTemplateProps> = (props) => {
    const { items, canAdd, onAddClick, className, disabled, schema, uiSchema, title, formData, rawErrors } = props;
    const classes = useClasses();

    const hideTitle = uiSchema?.['ui:options']?.['hide_title'] === true;

    const collapsed = uiSchema?.['ui:options']?.['collapsed'] === true;
    const openItems: AccordionItemValue[] = [];
    if (!collapsed) {
        for (let i = 0; i < items.length; i++) {
            openItems.push(i);
        }
    }

    const get_item_actions = (
        element: ArrayFieldTemplateItemType<any, RJSFSchema, any>,
        index: number,
        options: {
            hasRemove?: boolean;
            hasMoveUp?: boolean;
            hasMoveDown?: boolean;
            iconsOnly?: boolean;
        },
    ) => {
        const { hasRemove, hasMoveUp, hasMoveDown, iconsOnly } = options;
        return (
            <>
                {(hasRemove || hasMoveUp || hasMoveDown) && (
                    <div className={classes.itemActions}>
                        {hasRemove && (
                            <Tooltip content="Delete item" relationship="description">
                                <Button
                                    icon={<Delete16Regular />}
                                    appearance="outline"
                                    size="small"
                                    onClick={element.onDropIndexClick(index)}
                                    disabled={disabled}
                                >
                                    {iconsOnly ? null : 'Delete'}
                                </Button>
                            </Tooltip>
                        )}
                        {hasMoveUp && (
                            <Tooltip content="Move item up" relationship="description">
                                <Button
                                    icon={<ArrowUp16Regular />}
                                    appearance="outline"
                                    size="small"
                                    onClick={element.onReorderClick(index, index - 1)}
                                    disabled={disabled || index === 0}
                                >
                                    {iconsOnly ? null : 'Move Up'}
                                </Button>
                            </Tooltip>
                        )}
                        {hasMoveDown && (
                            <Tooltip content="Move item down" relationship="description">
                                <Button
                                    icon={<ArrowDown16Regular />}
                                    appearance="outline"
                                    size="small"
                                    onClick={element.onReorderClick(index, index + 1)}
                                    disabled={disabled || index === items.length - 1}
                                >
                                    {iconsOnly ? null : 'Move Down'}
                                </Button>
                            </Tooltip>
                        )}
                    </div>
                )}
            </>
        );
    };

    let content: JSX.Element | null = null;
    const isSimpleArray = items.every(
        (item) => item.schema.type === 'string' || item.schema.type === 'number' || item.schema.type === 'integer',
    );
    if (isSimpleArray && !collapsed) {
        content = (
            <div>
                {items.map((element, index) => {
                    const { children, hasRemove, hasMoveUp, hasMoveDown } = element;
                    return (
                        <div key={index} className={classes.simpleItem}>
                            {children}
                            <div className={classes.inline}>
                                {get_item_actions(element, index, {
                                    hasRemove,
                                    hasMoveUp,
                                    hasMoveDown,
                                    iconsOnly: true,
                                })}
                            </div>
                        </div>
                    );
                })}
            </div>
        );
    } else {
        content = (
            <Accordion multiple collapsible defaultOpenItems={openItems}>
                {items.map((element, index) => {
                    const { children, hasRemove, hasMoveUp, hasMoveDown } = element;

                    let itemTitle = `${schema.title}: ${index + 1}`;
                    const titleField = uiSchema?.items?.['ui:options']?.['title_field']?.toString() ?? 'title';
                    if (titleField && formData[index][titleField]) {
                        itemTitle = formData[index][titleField];
                    }

                    const descriptionValue = schema.description;

                    let itemCount = undefined;
                    const countField = uiSchema?.items?.['ui:options']?.['count_field']?.toString();
                    if (countField && formData[index][countField]) {
                        const field = formData[index][countField];
                        // if field is an array, count the length
                        if (Array.isArray(field)) {
                            itemCount = field.length;
                        }
                    }

                    return (
                        <AccordionItem key={index} value={index}>
                            <AccordionHeader>
                                <Text>{itemTitle}</Text>
                                {itemCount !== undefined && <Text>&nbsp;({itemCount})</Text>}
                            </AccordionHeader>
                            <AccordionPanel className={classes.panel}>
                                {descriptionValue && <Text italic>{descriptionValue}</Text>}
                                {get_item_actions(element, index, { hasRemove, hasMoveUp, hasMoveDown })}
                                <div>{children}</div>
                            </AccordionPanel>
                        </AccordionItem>
                    );
                })}
            </Accordion>
        );
    }

    return (
        <div className={className}>
            <div className={classes.heading}>
                {!hideTitle && <Text>{title}</Text>}
                {schema.description && <Text italic>{schema.description}</Text>}
                {canAdd && (
                    <div>
                        <Button
                            icon={<Add16Regular />}
                            appearance="outline"
                            size="small"
                            onClick={onAddClick}
                            disabled={disabled}
                        >
                            Add
                        </Button>
                    </div>
                )}
                {rawErrors && rawErrors.length > 0 && (
                    <div>
                        <Text style={{ color: 'red' }}>{rawErrors.join(', ')}</Text>
                    </div>
                )}
            </div>
            {content}
        </div>
    );
};
