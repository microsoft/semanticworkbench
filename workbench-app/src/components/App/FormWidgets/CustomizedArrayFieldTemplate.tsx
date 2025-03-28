// Copyright (c) Microsoft. All rights reserved.

import {
    Accordion,
    AccordionHeader,
    AccordionItem,
    AccordionItemValue,
    AccordionPanel,
    Button,
    Text,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import { Add16Regular, ArrowDown16Regular, ArrowUp16Regular, Delete16Regular } from '@fluentui/react-icons';
import { ArrayFieldTemplateItemType, ArrayFieldTemplateProps, RJSFSchema } from '@rjsf/utils';
import React from 'react';
import { TooltipWrapper } from '../TooltipWrapper';

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

    const hideTitle = uiSchema?.['ui:options']?.['hideTitle'] === true;
    const collapsed = uiSchema?.['ui:options']?.['collapsed'] !== false;
    const isCollapsible = collapsed || uiSchema?.['ui:options']?.['collapsible'] !== false;
    const itemTitleFields: string[] = uiSchema?.items?.['ui:options']?.['titleFields'] ??  [];
    const itemCollapsed = uiSchema?.items?.['ui:options']?.['collapsed'] !== false;
    const itemCollapsible = itemCollapsed || uiSchema?.items?.['ui:options']?.['collapsible'] !== false;

    const openItems: AccordionItemValue[] = [];
    if (!itemCollapsed) {
        for (let i = 0; i < items.length; i++) {
            openItems.push(i);
        }
    }

    const getItemActions = (
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
                            <TooltipWrapper content="Delete item">
                                <Button
                                    icon={<Delete16Regular />}
                                    appearance="outline"
                                    size="small"
                                    onClick={element.onDropIndexClick(index)}
                                    disabled={disabled}
                                >
                                    {iconsOnly ? null : 'Delete'}
                                </Button>
                            </TooltipWrapper>
                        )}
                        {hasMoveUp && (
                            <TooltipWrapper content="Move item up">
                                <Button
                                    icon={<ArrowUp16Regular />}
                                    appearance="outline"
                                    size="small"
                                    onClick={element.onReorderClick(index, index - 1)}
                                    disabled={disabled || index === 0}
                                >
                                    {iconsOnly ? null : 'Move Up'}
                                </Button>
                            </TooltipWrapper>
                        )}
                        {hasMoveDown && (
                            <TooltipWrapper content="Move item down">
                                <Button
                                    icon={<ArrowDown16Regular />}
                                    appearance="outline"
                                    size="small"
                                    onClick={element.onReorderClick(index, index + 1)}
                                    disabled={disabled || index === items.length - 1}
                                >
                                    {iconsOnly ? null : 'Move Down'}
                                </Button>
                            </TooltipWrapper>
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
    if (isSimpleArray) {
        content = (
            <div>
                {items.map((element, index) => {
                    const { children, hasRemove, hasMoveUp, hasMoveDown } = element;
                    return (
                        <div key={index} className={classes.simpleItem}>
                            {children}
                            <div className={classes.inline}>
                                {getItemActions(element, index, {
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
            <Accordion multiple collapsible={itemCollapsible} defaultOpenItems={openItems}>
                {items.map((element, index) => {
                    const { children, hasRemove, hasMoveUp, hasMoveDown } = element;

                    let itemTitle = `${schema.title}: ${index + 1}`;
                    if (itemTitleFields && itemTitleFields.length > 0) {
                        itemTitle = itemTitleFields
                            // @ts-ignore
                            .map((field) => `${items[index].schema.properties?.[field]?.title ?? field}: ${formData[index][field]}`)
                            .join(', ');
                    }

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
                                {getItemActions(element, index, { hasRemove, hasMoveUp, hasMoveDown })}
                                <div>{children}</div>
                            </AccordionPanel>
                        </AccordionItem>
                    );
                })}
            </Accordion>
        );
    }

    const descriptionAndControls =
        <>
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
        </>;

    if (isCollapsible) {
        return (
            <Accordion multiple collapsible defaultOpenItems={openItems}>
                <AccordionItem value={schema.$id}>
                    <AccordionHeader>
                        <Text>{title}</Text>
                    </AccordionHeader>
                    <AccordionPanel>
                        <div className={classes.heading}>
                            {descriptionAndControls}
                        </div>
                        {content}
                    </AccordionPanel>
                </AccordionItem>
            </Accordion>
        );
    }

    return (
        <div className={className}>
            <div className={classes.heading}>
                {!hideTitle && <Text>{title}</Text>}
                {descriptionAndControls}
            </div>
            {content}
        </div>
    );
};
