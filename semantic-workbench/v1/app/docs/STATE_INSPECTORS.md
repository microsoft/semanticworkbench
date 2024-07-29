# State Inspectors

Each assistant can have one or more state inspectors. A state inspector is a component that can be used to inspect the state of the assistant. The `config` editor for an assistant is an example of a special state inspector that is required for each assistant.

States beyond the required `config` state exposed by an assistant will be available in the assistant's conversation view. Clicking on the `Show Inspectors` UI will cause a tabbed view to be rendered, with each tab mapping to an exposed state. The inspector view will attempt to render the state in the most user-friendly way, based upon the content/data provided.

-   If the state `data` property contains a key of `content` that is a string, it will be rendered as text, supporting markdown and/or html formatting, in addition to plain text.
-   If there is a `JsonSchema` property in the state, it will be rendered as custom UI, based upon the schema. If `UISchema` is also provided, it will be used to customize the UI.
-   Lastly, the state will be rendered as formatted JSON.

If `JsonSchema` is provided, the state inspector will also provide a button to allow the user to edit the state. The user will be presented with a dialog that will allow them to edit the state. The dialog will be rendered based upon the `JsonSchema` and `UISchema` properties of the state. The user will be able to save the changes, or cancel the dialog. If the user saves the changes, the state will be updated, and the assistant will be notified of the change.

Assistant state change events can be fired to cause the inspector UI to be updated for real-time state inspection. This can be useful for debugging purposes, or for providing a real-time view of the state of the assistant.
