# Semantic Workbench App Dev Guide

This is an early collection of notes for conventions being put in place for the development of the Semantic Workbench React/Typescript web app.

## Design System

The Semantic Workbench app uses the Fluent UI React v9 and Fluent Copilot component libraries.

Fluent UI React v9:

-   Docs: https://react.fluentui.dev/
-   GitHub: https://github.com/microsoft/fluentui

Fluent Copilot (formerly Fluent AI):

-   Docs: https://ai.fluentui.dev/
-   GitHub: https://github.com/microsoft/fluentai

### Styling components

Create a `useClasses` function that returns an object of classnames using the `mergeStyle` function from the `@fluentui/react` package. Within your component, create a `const classes = useClasses();` and use the classnames in the component.

Sample:

```
import { mergeStyle } from '@fluentui/react';

const useClasses = {
    root: mergeStyle({
        color: 'red',
    }),
};

const MyButton = () => {
    const classes = useClasses();
    return (
        <div className={classes.root}>
            <Button>
                Click me
            </Button>
        </div>
    );
};
```

Docs:

-   Fluent: Styling components: https://react.fluentui.dev/?path=/docs/concepts-developer-styling-components--docs
-   Griffel: https://griffel.js.org/

### Z-index

Use the Fluent tokens for z-index.

-   zIndex values
    -   .zIndexBackground = 0
    -   .zIndexContent = 1
    -   .zIndexOverlay = 1000
    -   .zIndexPopup = 2000
    -   .zIndexMessage = 3000
    -   .zIndexFloating = 4000
    -   .zIndexPriority = 5000
    -   .zIndexDebug = 6000

Sample:

```
import { mergeStyles, tokens } from '@fluentui/react';

const useClasses = {
    root: mergeStyle({
        position: 'relative',
        zIndex: tokens.zIndexContent,
    }),
};
```
