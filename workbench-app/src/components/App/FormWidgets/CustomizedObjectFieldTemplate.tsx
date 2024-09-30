// Copyright (c) Microsoft. All rights reserved.

import {
    Accordion,
    AccordionHeader,
    AccordionItem,
    AccordionPanel,
    Divider,
    Text,
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

    const hideTitle = uiSchema?.['ui:options']?.['hide_title'] ?? false;

    const isCollapsed = uiSchema?.['ui:options']?.['collapsed'] === true ?? false;
    const isCollapsible = isCollapsed || (uiSchema?.['ui:options']?.['collapsible'] === true ?? false);
    const openItems = isCollapsed ? [] : properties.map((_, index) => index);

    if (isCollapsible) {
        return (
            <Accordion multiple collapsible defaultOpenItems={openItems}>
                <AccordionItem value={idSchema.$id}>
                    <AccordionHeader>
                        <Text>{title}</Text>
                    </AccordionHeader>
                    <AccordionPanel>
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

    const descriptionValue = description ?? schema.description;

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
