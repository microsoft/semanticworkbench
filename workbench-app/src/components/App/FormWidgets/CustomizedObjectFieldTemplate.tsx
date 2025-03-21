// Copyright (c) Microsoft. All rights reserved.

import {
    Accordion,
    AccordionHeader,
    AccordionItem,
    AccordionPanel,
    Divider,
    Text,
    Tooltip,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import { ObjectFieldTemplateProps } from '@rjsf/utils';
import React from 'react';

const useClasses = makeStyles({
    heading: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
    },
    items: {
        display: 'flex',
        flexDirection: 'column',
        paddingLeft: tokens.spacingHorizontalM,
        gap: tokens.spacingVerticalS,
    },
});

export const CustomizedObjectFieldTemplate: React.FC<ObjectFieldTemplateProps> = (props) => {
    const { title, description, properties, uiSchema, idSchema, schema } = props;
    const classes = useClasses();

    const hideTitle = uiSchema?.['ui:options']?.['hideTitle'];

    const isCollapsed = uiSchema?.['ui:options']?.['collapsed'] !== false;
    const isCollapsible = uiSchema?.['ui:options']?.['collapsed'] !== undefined || uiSchema?.['ui:options']?.['collapsible'] !== false;
    const openItems = isCollapsed ? [] : [idSchema.$id];

    const descriptionValue = description ?? schema.description;

    if (isCollapsible) {
        return (
            <Accordion multiple collapsible defaultOpenItems={openItems}>
                <AccordionItem value={idSchema.$id}>
                    <AccordionHeader>
                        {descriptionValue &&
                            <Tooltip content={descriptionValue || ''} relationship='description'>
                                <Text>{title}</Text>
                            </Tooltip>
                        }
                        {!descriptionValue && <Text>{title}</Text>}
                    </AccordionHeader>
                    <AccordionPanel>
                        {descriptionValue && <Text italic>{descriptionValue}</Text>}
                        <div className={classes.items}>
                            {properties.map((element, index) => {
                                return <div key={index}>{element.content}</div>;
                            })}
                        </div>
                    </AccordionPanel>
                </AccordionItem>
            </Accordion>
        );
    }

    return (
        <div>
            <div className={classes.heading}>
                {!hideTitle && (
                    <>
                        <Text>{title}</Text>
                        <Divider />
                    </>
                )}
                {descriptionValue && <Text italic>{descriptionValue}</Text>}
            </div>
            <div className={classes.items}>
                {properties.map((element, index) => {
                    return <div key={index}>{element.content}</div>;
                })}
            </div>
        </div>
    );
};
