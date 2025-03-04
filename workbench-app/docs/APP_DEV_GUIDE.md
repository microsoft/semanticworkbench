# Semantic Workbench App Dev Guide

This guide covers the conventions and patterns used in the development of the Semantic Workbench React/TypeScript web app.

## Design System

The Semantic Workbench app uses the Fluent UI React v9 and Fluent Copilot component libraries.

Fluent UI React v9:

-   Docs: https://react.fluentui.dev/
-   GitHub: https://github.com/microsoft/fluentui

Fluent Copilot (formerly Fluent AI):

-   Docs: https://ai.fluentui.dev/
-   GitHub: https://github.com/microsoft/fluentai

## Architecture Patterns

### Component Organization

The app follows these organizational patterns:

- **Feature-based organization**: Components are organized by feature (Conversations, Assistants, etc.)
- **Composition**: Complex components are broken down into smaller, reusable components
- **Container/Presentation separation**: Logic and presentation are separated when possible

### State Management

The app uses Redux Toolkit for state management:

- **Redux store**: Central state for application data
- **Redux Toolkit Query**: Used for API integration and data fetching
- **Slices**: State is divided into slices by feature
- **Custom hooks**: Encapsulate Redux interactions (e.g., `useConversationEvents.ts`)

## Component Guidelines

### Styling components

Create styles using the `makeStyles` function from the `@fluentui/react-components` package:

```tsx
import { makeStyles, shorthands, tokens } from '@fluentui/react-components';

// Define styles as a hook function
const useClasses = makeStyles({
    root: {
        display: 'flex',
        backgroundColor: tokens.colorNeutralBackground3,
        ...shorthands.padding(tokens.spacingVerticalM),
        ...shorthands.borderRadius(tokens.borderRadiusMedium),
    },
    content: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
    },
});

const MyComponent = () => {
    // Use the styles in your component
    const classes = useClasses();
    return (
        <div className={classes.root}>
            <div className={classes.content}>
                <Button>Click me</Button>
            </div>
        </div>
    );
};
```

Documentation:
-   Fluent styling components: https://react.fluentui.dev/?path=/docs/concepts-developer-styling-components--docs
-   Griffel: https://griffel.js.org/

### Z-index

Use Fluent tokens for z-index values to maintain consistency:

```tsx
import { makeStyles, tokens } from '@fluentui/react-components';

const useClasses = makeStyles({
    overlay: {
        position: 'absolute',
        zIndex: tokens.zIndexOverlay,
    },
});
```

Z-index token values:
- `tokens.zIndexBackground` = 0
- `tokens.zIndexContent` = 1
- `tokens.zIndexOverlay` = 1000
- `tokens.zIndexPopup` = 2000
- `tokens.zIndexMessage` = 3000
- `tokens.zIndexFloating` = 4000
- `tokens.zIndexPriority` = 5000
- `tokens.zIndexDebug` = 6000

## Common Patterns

### Custom Hooks

Create custom hooks to encapsulate reusable logic:

```tsx
import { useCallback, useState } from 'react';

export function useToggle(initialState = false) {
    const [state, setState] = useState(initialState);
    
    const toggle = useCallback(() => {
        setState(state => !state);
    }, []);
    
    return [state, toggle];
}
```

# Design Principles and Technical Standards

## Form and Configuration UIs

The Semantic Workbench uses React JSON Schema Form (@rjsf) with Fluent UI bindings as the **standard approach** for all configuration UIs. This is an intentional architectural decision that:

1. Ensures consistency across the application
2. Allows rapid development through declarative UI
3. Supports runtime-generated forms based on server schemas
4. Maintains compatibility with our existing components

### Standard Implementation

All configuration and form UIs **must** use the RJSF approach with Fluent UI:

```tsx
import Form from '@rjsf/fluentui-rc';
import validator from '@rjsf/validator-ajv8';
import { RJSFSchema } from '@rjsf/utils';

// Use our customized templates
import { CustomizedFieldTemplate } from '../App/FormWidgets/CustomizedFieldTemplate';
import { CustomizedObjectFieldTemplate } from '../App/FormWidgets/CustomizedObjectFieldTemplate';
import { CustomizedArrayFieldTemplate } from '../App/FormWidgets/CustomizedArrayFieldTemplate';

const schema: RJSFSchema = {
    type: 'object',
    properties: {
        name: { type: 'string', title: 'Name' },
        description: { type: 'string', title: 'Description' }
    }
};

const FormComponent = ({ onSubmit }) => {
    return (
        <Form 
            schema={schema}
            validator={validator}
            ObjectFieldTemplate={CustomizedObjectFieldTemplate}
            ArrayFieldTemplate={CustomizedArrayFieldTemplate}
            FieldTemplate={CustomizedFieldTemplate}
            onSubmit={onSubmit}
        />
    );
};
```

### Extending Form Functionality

When customization is needed, extend the standard approach through:

1. **Custom Widgets**: Create specialized widgets in the `FormWidgets` directory
2. **Custom Templates**: Extend existing templates rather than creating new ones
3. **UISchema**: Use UISchema for layout/appearance changes without custom code

```tsx
// Example of registering a custom widget
const widgets: RegistryWidgetsType = {
    BaseModelEditor: BaseModelEditorWidget,
    Inspectable: InspectableWidget
};

<Form 
    schema={schema}
    uiSchema={uiSchema}
    validator={validator}
    widgets={widgets}
/>
```

This standardized approach is a core architectural principle - any significant UI improvements should work within this framework rather than introducing alternative patterns.

### Error Handling

Use consistent error handling patterns:

```tsx
try {
    // Operation that might fail
} catch (error) {
    // Log the error
    console.error('Failed to perform operation', error);
    
    // Show error notification to user
    notifyError('Operation failed', error.message);
}
```

## Accessibility

- Use semantic HTML elements (`button`, `nav`, `header`, etc.)
- Ensure proper keyboard navigation
- Add appropriate ARIA attributes
- Maintain sufficient color contrast
- Support screen readers with meaningful labels

## Testing

The app uses React Testing Library for component testing:

```tsx
import { render, screen, fireEvent } from '@testing-library/react';

test('button click increments counter', () => {
    render(<Counter />);
    const button = screen.getByRole('button', { name: /increment/i });
    fireEvent.click(button);
    expect(screen.getByText('Count: 1')).toBeInTheDocument();
});
```
