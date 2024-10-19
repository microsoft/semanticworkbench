import {
    Accordion,
    AccordionHeader,
    AccordionItem,
    AccordionPanel,
    Divider,
    makeStyles,
    Text,
} from '@fluentui/react-components';
import { ObjectFieldTemplateProps } from '@rjsf/utils';
import React from 'react';

const useClasses = makeStyles({
    heading: {
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
    },
    items: {
        display: 'flex',
        flexDirection: 'column',
        paddingLeft: '20px',
        gap: '10px',
    },
});

export const CustomizedObjectFieldTemplate: React.FC<ObjectFieldTemplateProps> = (props) => {
    const { properties, title, description, uiSchema } = props;
    const classes = useClasses();

    const isCollapsed = uiSchema?.['ui:options']?.['collapsed'] === true;
    const isCollapsible = isCollapsed || uiSchema?.['ui:options']?.['collapsible'] === true;
    const openItems = isCollapsed ? [] : properties.map((_, index) => index);

    return (
        <div>
            <div className={classes.heading}>
                <Text>{title}</Text>
                {description && <Text italic>{description}</Text>}
                <Divider />
            </div>
            {isCollapsible ? (
                <Accordion multiple collapsible defaultOpenItems={openItems}>
                    {properties.map((element, index) => (
                        <AccordionItem key={index} value={element.name}>
                            <AccordionHeader>
                                <Text>{element.name}</Text>
                            </AccordionHeader>
                            <AccordionPanel>{element.content}</AccordionPanel>
                        </AccordionItem>
                    ))}
                </Accordion>
            ) : (
                <div className={classes.items}>
                    {properties.map((element, index) => (
                        <div key={index}>{element.content}</div>
                    ))}
                </div>
            )}
        </div>
    );
};
