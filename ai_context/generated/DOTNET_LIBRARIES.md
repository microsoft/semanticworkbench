# libraries/dotnet

[collect-files]

**Search:** ['libraries/dotnet']
**Exclude:** ['.venv', 'node_modules', '*.lock', '.git', '__pycache__', '*.pyc', '*.ruff_cache', 'logs', 'output']
**Include:** ['*.csproj', 'README.md']
**Date:** 5/29/2025, 11:45:28 AM
**Files:** 31

=== File: README.md ===
# Semantic Workbench

Semantic Workbench is a versatile tool designed to help prototype intelligent assistants quickly.
It supports the creation of new assistants or the integration of existing ones, all within a
cohesive interface. The workbench provides a user-friendly UI for creating conversations with one
or more assistants, configuring settings, and exposing various behaviors.

The Semantic Workbench is composed of three main components:

- [Workbench Service](workbench-service/README.md) (Python): The backend service that
  handles core functionalities.
- [Workbench App](workbench-app/README.md) (React/Typescript): The frontend web user
  interface for interacting with workbench and assistants.
- [Assistant Services](examples) (Python, C#, etc.): any number of assistant services that implement the service protocols/APIs,
  developed using any framework and programming language of your choice.

Designed to be agnostic of any agent framework, language, or platform, the Semantic Workbench
facilitates experimentation, development, testing, and measurement of agent behaviors and workflows.
Assistants integrate with the workbench via a RESTful API, allowing for flexibility and broad applicability in various development environments.

![Semantic Workbench architecture](https://raw.githubusercontent.com/microsoft/semanticworkbench/main/docs/images/architecture-animation.gif)

# Workbench interface examples

![Configured dashboard example](docs/images/dashboard_configured_view.png)

![Prospector Assistant example](docs/images/prospector_example.png)

![Message debug inspection](docs/images/message_inspection.png)

![Mermaid graph example](examples/dotnet/dotnet-02-message-types-demo/docs/mermaid.png)

![ABC music example](examples/dotnet/dotnet-02-message-types-demo/docs/abc.png)

# Quick start (Recommended) - GitHub Codespaces for turn-key development environment

GitHub Codespaces provides a cloud-based development environment for your repository. It allows you to develop, build, and test your code
in a consistent environment, without needing to install dependencies or configure your local machine. It works with any system with a web
browser and internet connection, including Windows, MacOS, Linux, Chromebooks, tablets, and mobile devices.

See the [GitHub Codespaces / devcontainer README](.devcontainer/README.md) for more information on how to set up and use GitHub Codespaces
with Semantic Workbench.

## Local development environment

See the [setup guide](docs/SETUP_DEV_ENVIRONMENT.md) on how to configure your dev environment. Or if you have Docker installed you can use dev containers with VS Code which will function similarly to Codespaces.

## Using VS Code

Codespaces will is configured to use `semantic-workbench.code-workspace`, if you are working locally that is recommended over opening the repo root. This ensures that all project configurations, such as tools, formatters, and linters, are correctly applied in VS Code. This avoids issues like incorrect error reporting and non-functional tools.

Workspace files allow us to manage multiple projects within a monorepo more effectively. Each project can use its own virtual environment (venv), maintaining isolation and avoiding dependency conflicts. Multi-root workspaces (\*.code-workspace files) can point to multiple projects, each configured with its own Python interpreter, ensuring seamless functionality of Python tools and extensions.

### Start the app and service

- Use VS Code > `Run and Debug` (Ctrl/Cmd+Shift+D) > `semantic-workbench` to start the project
- Open your browser and navigate to `https://127.0.0.1:4000`
  - You may receive a warning about the app not being secure; click `Advanced` and `Proceed to localhost` to continue
- You can now interact with the app and service in the browser

### Start an assistant service:

- Launch an example an [example](examples/) assistant service:
  - No llm api keys needed
    - Use VS Code > `Run and Debug` (Ctrl/Cmd+Shift+D) > `examples: python-01-echo-bot` to start the example assistant that echos your messages. This is a good base to understand the basics of building your own assistant.
  - Bring your own llm api keys
    - Use VS Code > `Run and Debug` (Ctrl/Cmd+Shift+D) > `examples: python-02-simple-chatbot` to start the example chatbot assistant. Either set your keys in your .env file or after creating the assistant as described below, select it and provide the keys in the configuration page.

## Open the Workbench and create an Assistant

Open the app in your browser at [`https://localhost:4000`](https://localhost:4000). When you first log into the Semantic Workbench, follow these steps to get started:

1. **Create an Assistant**: On the dashboard, click the `New Assistant` button. Select a template from the available assistant services, provide a name, and click `Save`.

2. **Start a Conversation**: On the dashboard, click the `New Conversation` button. Provide a title for the conversation and click `Save`.

3. **Add the Assistant**: In the conversation window, click the conversation canvas icon and add your assistant to the conversation from the conversation canvas. Now you can converse with your assistant using the message box at the bottom of the conversation window.

   ![Open Conversation Canvas](docs/images/conversation_canvas_open.png)

   ![Open Canvas](docs/images/open_conversation_canvas.png)

Expected: You get a response from your assistant!

Note that the workbench provides capabilities that not all examples use, for example providing attachments. See the [Semantic Workbench](docs/WORKBENCH_APP.md) for more details.

# Developing your own assistants

To develop new assistants and connect existing ones, see the [Assistant Development Guide](docs/ASSISTANT_DEVELOPMENT_GUIDE.md) or any check out one of the [examples](examples).

- [Python example 1](examples/python/python-01-echo-bot/README.md): a simple assistant echoing text back.
- [Python example 2](examples/python/python-02-simple-chatbot/README.md): a simple chatbot implementing metaprompt guardrails and content moderation.
- [Python example 3](examples/python/python-03-multimodel-chatbot/README.md): an extension of the simple chatbot that supports configuration against additional llms.
- [.NET example 1](examples/dotnet/dotnet-01-echo-bot/README.md): a simple agent with echo and support for a basic `/say` command.
- [.NET example 2](examples/dotnet/dotnet-02-message-types-demo/README.md): a simple assistants showcasing Azure AI Content Safety integration and some workbench features like Mermaid graphs.
- [.NET example 3](examples/dotnet/dotnet-03-simple-chatbot/README.md): a functional chatbot implementing metaprompt guardrails and content moderation.

## Starting the workbench from the command line

- Run the script `tools\run-workbench-chatbot.sh` or `tools\run-workbench-chatbot.ps` which does the following:
  - Starts the backend service, see [here for instructions](workbench-service/README.md).
  - Starts the frontend app, see [here for instructions](workbench-app/README.md).
  - Starts the [Python chatbot example](examples/python/python-02-simple-chatbot/README.md)

## Refreshing Dev Environment

- Use the `tools\reset-service-data.sh` or `tools\reset-service-data.sh` script to reset all service data. You can also delete `~/workbench-service/.data` or specific files if you know which one(s).
- From repo root, run `make clean install`.
  - This will perform a `git clean` and run installs in all sub-directories
- Or a faster option if you just want to install semantic workbench related stuff:
  - From repo root, run `make clean`
  - From `~/workbench-app`, run `make install`
  - From `~/workbench-service`, run `make install`

# Contributing

This project welcomes contributions and suggestions. Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit <https://cla.opensource.microsoft.com>.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

Please see the detailed [contributing guide](CONTRIBUTING.md) for more information on how you can get involved.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

# Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.


=== File: libraries/dotnet/.editorconfig ===
# To learn more about .editorconfig see https://aka.ms/editorconfigdocs
###############################
# Core EditorConfig Options   #
###############################
root = true
# All files
[*]
indent_style = space
end_of_line = lf

# XML project files
[*.{vbproj,vcxproj,vcxproj.filters,proj,projitems,shproj}]
indent_size = 2

# XML config files
[*.{targets,ruleset,config,nuspec,resx,vsixmanifest,vsct}]
indent_size = 2

# XML config files
[*.csproj]
indent_size = 4

# XML config files
[*.props]
indent_size = 4

[Directory.Packages.props]
indent_size = 2

# YAML config files
[*.{yml,yaml}]
tab_width = 2
indent_size = 2
insert_final_newline = true
trim_trailing_whitespace = true

# JSON config files
[*.json]
tab_width = 2
indent_size = 2
insert_final_newline = false
trim_trailing_whitespace = true

# Typescript files
[*.{ts,tsx}]
insert_final_newline = true
trim_trailing_whitespace = true
tab_width = 4
indent_size = 4
file_header_template = Copyright (c) Microsoft. All rights reserved.

# Stylesheet files
[*.{css,scss,sass,less}]
insert_final_newline = true
trim_trailing_whitespace = true
tab_width = 4
indent_size = 4

# Code files
[*.{cs,csx,vb,vbx}]
tab_width = 4
indent_size = 4
insert_final_newline = true
trim_trailing_whitespace = true
charset = utf-8-bom
file_header_template = Copyright (c) Microsoft. All rights reserved.

###############################
# .NET Coding Conventions     #
###############################
[*.{cs,vb}]
# Organize usings
dotnet_sort_system_directives_first = true
# this. preferences
dotnet_style_qualification_for_field = true:error
dotnet_style_qualification_for_property = true:error
dotnet_style_qualification_for_method = true:error
dotnet_style_qualification_for_event = true:error
# Language keywords vs BCL types preferences
dotnet_style_predefined_type_for_locals_parameters_members = true:suggestion
dotnet_style_predefined_type_for_member_access = true:suggestion
# Parentheses preferences
dotnet_style_parentheses_in_arithmetic_binary_operators = always_for_clarity:suggestion
dotnet_style_parentheses_in_relational_binary_operators = always_for_clarity:suggestion
dotnet_style_parentheses_in_other_binary_operators = always_for_clarity:silent
dotnet_style_parentheses_in_other_operators = never_if_unnecessary:silent
# Modifier preferences
dotnet_style_require_accessibility_modifiers = for_non_interface_members:error
dotnet_style_readonly_field = true:suggestion
# Expression-level preferences
dotnet_style_object_initializer = true:suggestion
dotnet_style_collection_initializer = true:suggestion
dotnet_style_explicit_tuple_names = true:suggestion
dotnet_style_null_propagation = true:suggestion
dotnet_style_coalesce_expression = true:suggestion
dotnet_style_prefer_is_null_check_over_reference_equality_method = true:suggestion
dotnet_style_prefer_inferred_tuple_names = true:suggestion
dotnet_style_prefer_inferred_anonymous_type_member_names = true:silent
dotnet_style_prefer_auto_properties = true:suggestion
dotnet_style_prefer_conditional_expression_over_assignment = true:silent
dotnet_style_prefer_conditional_expression_over_return = true:silent
dotnet_style_prefer_simplified_interpolation = true:suggestion
dotnet_style_operator_placement_when_wrapping = beginning_of_line
dotnet_style_prefer_simplified_boolean_expressions = true:suggestion
dotnet_style_prefer_compound_assignment = true:suggestion
# Code quality rules
dotnet_code_quality_unused_parameters = all:suggestion

[*.cs]

# TODO: enable this but stop "dotnet format" from applying incorrect fixes and introducing a lot of unwanted changes.
dotnet_analyzer_diagnostic.severity = none

# Note: these settings cause "dotnet format" to fix the code. You should review each change if you uses "dotnet format".
dotnet_diagnostic.RCS1007.severity = warning # Add braces
dotnet_diagnostic.RCS1036.severity = warning # Remove unnecessary blank line.
dotnet_diagnostic.RCS1037.severity = warning # Remove trailing white-space.
dotnet_diagnostic.RCS1097.severity = warning # Remove redundant 'ToString' call.
dotnet_diagnostic.RCS1138.severity = warning # Add summary to documentation comment.
dotnet_diagnostic.RCS1139.severity = warning # Add summary element to documentation comment.
dotnet_diagnostic.RCS1168.severity = warning # Parameter name 'foo' differs from base name 'bar'.
dotnet_diagnostic.RCS1175.severity = warning # Unused 'this' parameter 'operation'.
dotnet_diagnostic.RCS1192.severity = warning # Unnecessary usage of verbatim string literal.
dotnet_diagnostic.RCS1194.severity = warning # Implement exception constructors.
dotnet_diagnostic.RCS1211.severity = warning # Remove unnecessary else clause.
dotnet_diagnostic.RCS1214.severity = warning # Unnecessary interpolated string.
dotnet_diagnostic.RCS1225.severity = warning # Make class sealed.
dotnet_diagnostic.RCS1232.severity = warning # Order elements in documentation comment.

# Diagnostics elevated as warnings
dotnet_diagnostic.CA1000.severity = warning # Do not declare static members on generic types
dotnet_diagnostic.CA1031.severity = warning # Do not catch general exception types
dotnet_diagnostic.CA1050.severity = warning # Declare types in namespaces
dotnet_diagnostic.CA1063.severity = warning # Implement IDisposable correctly
dotnet_diagnostic.CA1064.severity = warning # Exceptions should be public
dotnet_diagnostic.CA1303.severity = warning # Do not pass literals as localized parameters
dotnet_diagnostic.CA1416.severity = warning # Validate platform compatibility
dotnet_diagnostic.CA1508.severity = warning # Avoid dead conditional code
dotnet_diagnostic.CA1852.severity = warning # Sealed classes
dotnet_diagnostic.CA1859.severity = warning # Use concrete types when possible for improved performance
dotnet_diagnostic.CA1860.severity = warning # Prefer comparing 'Count' to 0 rather than using 'Any()', both for clarity and for performance
dotnet_diagnostic.CA2000.severity = warning # Call System.IDisposable.Dispose on object before all references to it are out of scope
dotnet_diagnostic.CA2007.severity = error # Do not directly await a Task
dotnet_diagnostic.CA2201.severity = warning # Exception type System.Exception is not sufficiently specific
dotnet_diagnostic.CA2225.severity = warning # Operator overloads have named alternates

dotnet_diagnostic.IDE0001.severity = warning # Simplify name
dotnet_diagnostic.IDE0005.severity = warning # Remove unnecessary using directives
dotnet_diagnostic.IDE1006.severity = warning # Code style errors, e.g. dotnet_naming_rule rules violations
dotnet_diagnostic.IDE0009.severity = warning # Add this or Me qualification
dotnet_diagnostic.IDE0011.severity = warning # Add braces
dotnet_diagnostic.IDE0018.severity = warning # Inline variable declaration
dotnet_diagnostic.IDE0032.severity = warning # Use auto-implemented property
dotnet_diagnostic.IDE0034.severity = warning # Simplify 'default' expression
dotnet_diagnostic.IDE0035.severity = warning # Remove unreachable code
dotnet_diagnostic.IDE0040.severity = warning # Add accessibility modifiers
dotnet_diagnostic.IDE0049.severity = warning # Use language keywords instead of framework type names for type references
dotnet_diagnostic.IDE0050.severity = warning # Convert anonymous type to tuple
dotnet_diagnostic.IDE0051.severity = warning # Remove unused private member
dotnet_diagnostic.IDE0055.severity = warning # Formatting rule
dotnet_diagnostic.IDE0060.severity = warning # Remove unused parameter
dotnet_diagnostic.IDE0070.severity = warning # Use 'System.HashCode.Combine'
dotnet_diagnostic.IDE0071.severity = warning # Simplify interpolation
dotnet_diagnostic.IDE0073.severity = warning # Require file header
dotnet_diagnostic.IDE0082.severity = warning # Convert typeof to nameof
dotnet_diagnostic.IDE0090.severity = warning # Simplify new expression
dotnet_diagnostic.IDE0130.severity = warning # Namespace does not match folder structure
dotnet_diagnostic.IDE0161.severity = warning # Use file-scoped namespace

dotnet_diagnostic.RCS1032.severity = warning # Remove redundant parentheses.
dotnet_diagnostic.RCS1118.severity = warning # Mark local variable as const.
dotnet_diagnostic.RCS1141.severity = warning # Add 'param' element to documentation comment.
dotnet_diagnostic.RCS1197.severity = warning # Optimize StringBuilder.AppendLine call.
dotnet_diagnostic.RCS1205.severity = warning # Order named arguments according to the order of parameters.
dotnet_diagnostic.RCS1229.severity = warning # Use async/await when necessary.

dotnet_diagnostic.VSTHRD111.severity = error # Use .ConfigureAwait(bool)

# Suppressed diagnostics

# Commented out because `dotnet format` change can be disruptive.
# dotnet_diagnostic.RCS1085.severity = warning # Use auto-implemented property.

# Commented out because `dotnet format` removes the xmldoc element, while we should add the missing documentation instead.
# dotnet_diagnostic.RCS1228.severity = warning # Unused element in documentation comment.

dotnet_diagnostic.CA1002.severity = none # Change 'List<string>' in '...' to use 'Collection<T>' ...
dotnet_diagnostic.CA1032.severity = none # We're using RCS1194 which seems to cover more ctors
dotnet_diagnostic.CA1034.severity = none # Do not nest type. Alternatively, change its accessibility so that it is not externally visible
dotnet_diagnostic.CA1054.severity = none # URI parameters should not be strings
dotnet_diagnostic.CA1062.severity = none # Disable null check, C# already does it for us
dotnet_diagnostic.CS1591.severity = none # Missing XML comment for publicly visible type or member
dotnet_diagnostic.CA1805.severity = none # Member is explicitly initialized to its default value
dotnet_diagnostic.CA1822.severity = none # Member does not access instance data and can be marked as static
dotnet_diagnostic.CA1848.severity = none # For improved performance, use the LoggerMessage delegates
dotnet_diagnostic.CA2227.severity = none # Change to be read-only by removing the property setter
dotnet_diagnostic.CA2253.severity = none # Named placeholders in the logging message template should not be comprised of only numeric characters
dotnet_diagnostic.RCS1021.severity = none # Use expression-bodied lambda.
dotnet_diagnostic.RCS1061.severity = none # Merge 'if' with nested 'if'.
dotnet_diagnostic.RCS1069.severity = none # Remove unnecessary case label.
dotnet_diagnostic.RCS1074.severity = none # Remove redundant constructor.
dotnet_diagnostic.RCS1077.severity = none # Optimize LINQ method call.
dotnet_diagnostic.RCS1124.severity = none # Inline local variable.
dotnet_diagnostic.RCS1129.severity = none # Remove redundant field initialization.
dotnet_diagnostic.RCS1140.severity = none # Add exception to documentation comment.
dotnet_diagnostic.RCS1142.severity = none # Add 'typeparam' element to documentation comment.
dotnet_diagnostic.RCS1146.severity = none # Use conditional access.
dotnet_diagnostic.RCS1151.severity = none # Remove redundant cast.
dotnet_diagnostic.RCS1158.severity = none # Static member in generic type should use a type parameter.
dotnet_diagnostic.RCS1161.severity = none # Enum should declare explicit value
dotnet_diagnostic.RCS1163.severity = none # Unused parameter 'foo'.
dotnet_diagnostic.RCS1170.severity = none # Use read-only auto-implemented property.
dotnet_diagnostic.RCS1173.severity = none # Use coalesce expression instead of 'if'.
dotnet_diagnostic.RCS1181.severity = none # Convert comment to documentation comment.
dotnet_diagnostic.RCS1186.severity = none # Use Regex instance instead of static method.
dotnet_diagnostic.RCS1188.severity = none # Remove redundant auto-property initialization.
dotnet_diagnostic.RCS1189.severity = none # Add region name to #endregion.
dotnet_diagnostic.RCS1201.severity = none # Use method chaining.
dotnet_diagnostic.RCS1212.severity = none # Remove redundant assignment.
dotnet_diagnostic.RCS1217.severity = none # Convert interpolated string to concatenation.
dotnet_diagnostic.RCS1222.severity = none # Merge preprocessor directives.
dotnet_diagnostic.RCS1226.severity = none # Add paragraph to documentation comment.
dotnet_diagnostic.RCS1234.severity = none # Enum duplicate value
dotnet_diagnostic.RCS1238.severity = none # Avoid nested ?: operators.
dotnet_diagnostic.RCS1241.severity = none # Implement IComparable when implementing IComparable<T><T>.
dotnet_diagnostic.IDE0001.severity = none # Simplify name
dotnet_diagnostic.IDE0002.severity = none # Simplify member access
dotnet_diagnostic.IDE0004.severity = none # Remove unnecessary cast
dotnet_diagnostic.IDE0035.severity = none # Remove unreachable code
dotnet_diagnostic.IDE0051.severity = none # Remove unused private member
dotnet_diagnostic.IDE0052.severity = none # Remove unread private member
dotnet_diagnostic.IDE0058.severity = none # Remove unused expression value
dotnet_diagnostic.IDE0059.severity = none # Unnecessary assignment of a value
dotnet_diagnostic.IDE0060.severity = none # Remove unused parameter
dotnet_diagnostic.IDE0080.severity = none # Remove unnecessary suppression operator
dotnet_diagnostic.IDE0100.severity = none # Remove unnecessary equality operator
dotnet_diagnostic.IDE0110.severity = none # Remove unnecessary discards
dotnet_diagnostic.IDE0032.severity = none # Use auto property
dotnet_diagnostic.IDE0160.severity = none # Use block-scoped namespace
dotnet_diagnostic.VSTHRD111.severity = none # Use .ConfigureAwait(bool) is hidden by default, set to none to prevent IDE from changing on autosave
dotnet_diagnostic.xUnit1004.severity = none # Test methods should not be skipped. Remove the Skip property to start running the test again.

dotnet_diagnostic.SKEXP0003.severity = none # XYZ is for evaluation purposes only
dotnet_diagnostic.SKEXP0010.severity = none
dotnet_diagnostic.SKEXP0010.severity = none
dotnet_diagnostic.SKEXP0011.severity = none
dotnet_diagnostic.SKEXP0052.severity = none
dotnet_diagnostic.SKEXP0101.severity = none

dotnet_diagnostic.KMEXP00.severity = none # XYZ is for evaluation purposes only
dotnet_diagnostic.KMEXP01.severity = none
dotnet_diagnostic.KMEXP02.severity = none
dotnet_diagnostic.KMEXP03.severity = none

###############################
# C# Coding Conventions       #
###############################

# var preferences
csharp_style_var_for_built_in_types = false:none
csharp_style_var_when_type_is_apparent = false:none
csharp_style_var_elsewhere = false:none
# Expression-bodied members
csharp_style_expression_bodied_methods = false:silent
csharp_style_expression_bodied_constructors = false:silent
csharp_style_expression_bodied_operators = false:silent
csharp_style_expression_bodied_properties = true:silent
csharp_style_expression_bodied_indexers = true:silent
csharp_style_expression_bodied_accessors = true:silent
# Pattern matching preferences
csharp_style_pattern_matching_over_is_with_cast_check = true:suggestion
csharp_style_pattern_matching_over_as_with_null_check = true:suggestion
# Null-checking preferences
csharp_style_throw_expression = true:suggestion
csharp_style_conditional_delegate_call = true:suggestion
# Modifier preferences
csharp_preferred_modifier_order = public, private, protected, internal, static, extern, new, virtual, abstract, sealed, override, readonly, unsafe, volatile, async:suggestion
# Expression-level preferences
csharp_prefer_braces = true:error
csharp_style_deconstructed_variable_declaration = true:suggestion
csharp_prefer_simple_default_expression = true:suggestion
csharp_style_prefer_local_over_anonymous_function = true:error
csharp_style_inlined_variable_declaration = true:suggestion

###############################
# C# Formatting Rules         #
###############################

# New line preferences
csharp_new_line_before_open_brace = all
csharp_new_line_before_else = true
csharp_new_line_before_catch = true
csharp_new_line_before_finally = true
csharp_new_line_before_members_in_object_initializers = false # Does not work with resharper, forcing code to be on long lines instead of wrapping
csharp_new_line_before_members_in_anonymous_types = true
csharp_new_line_between_query_expression_clauses = true
# Indentation preferences
csharp_indent_braces = false
csharp_indent_case_contents = true
csharp_indent_case_contents_when_block = false
csharp_indent_switch_labels = true
csharp_indent_labels = flush_left
# Space preferences
csharp_space_after_cast = false
csharp_space_after_keywords_in_control_flow_statements = true
csharp_space_between_method_call_parameter_list_parentheses = false
csharp_space_between_method_declaration_parameter_list_parentheses = false
csharp_space_between_parentheses = false
csharp_space_before_colon_in_inheritance_clause = true
csharp_space_after_colon_in_inheritance_clause = true
csharp_space_around_binary_operators = before_and_after
csharp_space_between_method_declaration_empty_parameter_list_parentheses = false
csharp_space_between_method_call_name_and_opening_parenthesis = false
csharp_space_between_method_call_empty_parameter_list_parentheses = false
# Wrapping preferences
csharp_preserve_single_line_statements = true
csharp_preserve_single_line_blocks = true
csharp_using_directive_placement = outside_namespace:warning
csharp_prefer_simple_using_statement = true:suggestion
csharp_style_namespace_declarations = file_scoped:warning
csharp_style_prefer_method_group_conversion = true:silent
csharp_style_prefer_top_level_statements = true:silent
csharp_style_expression_bodied_lambdas = true:silent
csharp_style_expression_bodied_local_functions = false:silent

###############################
# Global Naming Conventions   #
###############################

# Styles

dotnet_naming_style.pascal_case_style.capitalization = pascal_case

dotnet_naming_style.camel_case_style.capitalization = camel_case

dotnet_naming_style.static_underscored.capitalization = camel_case
dotnet_naming_style.static_underscored.required_prefix = s_

dotnet_naming_style.underscored.capitalization = camel_case
dotnet_naming_style.underscored.required_prefix = _

dotnet_naming_style.uppercase_with_underscore_separator.capitalization = all_upper
dotnet_naming_style.uppercase_with_underscore_separator.word_separator = _

dotnet_naming_style.end_in_async.required_prefix =
dotnet_naming_style.end_in_async.required_suffix = Async
dotnet_naming_style.end_in_async.capitalization = pascal_case
dotnet_naming_style.end_in_async.word_separator =

# Symbols

dotnet_naming_symbols.constant_fields.applicable_kinds = field
dotnet_naming_symbols.constant_fields.applicable_accessibilities = *
dotnet_naming_symbols.constant_fields.required_modifiers = const

dotnet_naming_symbols.local_constant.applicable_kinds = local
dotnet_naming_symbols.local_constant.applicable_accessibilities = *
dotnet_naming_symbols.local_constant.required_modifiers = const

dotnet_naming_symbols.private_constant_fields.applicable_kinds = field
dotnet_naming_symbols.private_constant_fields.applicable_accessibilities = private
dotnet_naming_symbols.private_constant_fields.required_modifiers = const

dotnet_naming_symbols.private_static_fields.applicable_kinds = field
dotnet_naming_symbols.private_static_fields.applicable_accessibilities = private
dotnet_naming_symbols.private_static_fields.required_modifiers = static

dotnet_naming_symbols.private_fields.applicable_kinds = field
dotnet_naming_symbols.private_fields.applicable_accessibilities = private

dotnet_naming_symbols.any_async_methods.applicable_kinds = method
dotnet_naming_symbols.any_async_methods.applicable_accessibilities = *
dotnet_naming_symbols.any_async_methods.required_modifiers = async

# Rules

dotnet_naming_rule.constant_fields_should_be_pascal_case.symbols = constant_fields
dotnet_naming_rule.constant_fields_should_be_pascal_case.style = pascal_case_style
dotnet_naming_rule.constant_fields_should_be_pascal_case.severity = error

dotnet_naming_rule.local_constant_should_be_pascal_case.symbols = local_constant
dotnet_naming_rule.local_constant_should_be_pascal_case.style = pascal_case_style
dotnet_naming_rule.local_constant_should_be_pascal_case.severity = error

dotnet_naming_rule.private_constant_fields.symbols = private_constant_fields
dotnet_naming_rule.private_constant_fields.style = pascal_case_style
dotnet_naming_rule.private_constant_fields.severity = error

dotnet_naming_rule.private_static_fields_underscored.symbols = private_static_fields
dotnet_naming_rule.private_static_fields_underscored.style = static_underscored
dotnet_naming_rule.private_static_fields_underscored.severity = error

dotnet_naming_rule.private_fields_underscored.symbols = private_fields
dotnet_naming_rule.private_fields_underscored.style = underscored
dotnet_naming_rule.private_fields_underscored.severity = error

#####################################################################################################
# Naming Conventions by folder                                                                      #
# See also https://www.jetbrains.com/help/resharper/Coding_Assistance__Naming_Style.html#configure  #
#####################################################################################################

[{clients,extensions,service,tools}/**.cs]

dotnet_naming_style.end_in_async.required_prefix =
dotnet_naming_style.end_in_async.required_suffix = Async
dotnet_naming_style.end_in_async.capitalization = pascal_case
dotnet_naming_style.end_in_async.word_separator =

dotnet_naming_symbols.any_async_methods.applicable_kinds = method
dotnet_naming_symbols.any_async_methods.applicable_accessibilities = *
dotnet_naming_symbols.any_async_methods.required_modifiers = async

dotnet_naming_rule.async_methods_end_in_async.symbols = any_async_methods
dotnet_naming_rule.async_methods_end_in_async.style = end_in_async
dotnet_naming_rule.async_methods_end_in_async.severity = error

[{examples,experiments}/**.cs]

dotnet_naming_style.end_in_async.required_prefix =
dotnet_naming_style.end_in_async.required_suffix = Async
dotnet_naming_style.end_in_async.capitalization = pascal_case
dotnet_naming_style.end_in_async.word_separator =

dotnet_naming_symbols.any_async_methods.applicable_kinds = method
dotnet_naming_symbols.any_async_methods.applicable_accessibilities = *
dotnet_naming_symbols.any_async_methods.required_modifiers = async

dotnet_naming_rule.async_methods_end_in_async.symbols = any_async_methods
dotnet_naming_rule.async_methods_end_in_async.style = end_in_async
dotnet_naming_rule.async_methods_end_in_async.severity = silent

#####################################
# Exceptions for Tests and Examples #
#####################################

# dotnet_diagnostic.IDE1006.severity = none # No need for Async suffix on test names[*.cs]
# dotnet_diagnostic.IDE0130.severity = none # No namespace checks

[**/{*.{FunctionalTests,TestApplication,UnitTests},TestHelpers}/**.cs]

dotnet_diagnostic.CA1031.severity = none # catch a more specific allowed exception type, or rethrow the exception
dotnet_diagnostic.CA1051.severity = none # Do not declare visible instance fields
dotnet_diagnostic.CA1303.severity = none # Passing literal strings as values
dotnet_diagnostic.CA1305.severity = none # The behavior of 'DateTimeOffset.ToString(string)' could vary based on the current user's locale settings
dotnet_diagnostic.CA1307.severity = none # 'string.Contains(string)' has a method overload that takes a 'StringComparison' parameter. Replace this call
dotnet_diagnostic.CA1711.severity = none # Rename type name so that it does not end in 'Collection'
dotnet_diagnostic.CA1826.severity = none # Do not use Enumerable methods on indexable collections. Instead use the collection directly
dotnet_diagnostic.CA1859.severity = none # Change return type of method for improved performance
dotnet_diagnostic.CA1861.severity = none # Prefer 'static readonly' fields over constant array arguments
dotnet_diagnostic.CA2000.severity = none # Call System.IDisposable.Dispose on object
dotnet_diagnostic.CA2007.severity = none # no need of ConfigureAwait(false) in tests
dotnet_diagnostic.CA2201.severity = none # Exception type XYZ is not sufficiently specific
dotnet_diagnostic.IDE0005.severity = none # No need for documentation
dotnet_diagnostic.IDE1006.severity = none # No need for Async suffix on test names

resharper_inconsistent_naming_highlighting = none
# resharper_check_namespace_highlighting = none
# resharper_arrange_attributes_highlighting = none
# resharper_unused_member_global_highlighting = none
# resharper_comment_typo_highlighting = none

[examples/**.cs]

dotnet_diagnostic.CA1031.severity = none # catch a more specific allowed exception type, or rethrow the exception
dotnet_diagnostic.CA1050.severity = none # Declare types in namespaces
dotnet_diagnostic.CA1303.severity = none # Passing literal strings as values
dotnet_diagnostic.CA1859.severity = none # Change return type of method for improved performance
dotnet_diagnostic.CA2000.severity = none # Call System.IDisposable.Dispose on object
dotnet_diagnostic.CA2007.severity = none # no need of ConfigureAwait(false) in examples
dotnet_diagnostic.IDE0005.severity = none # No need for documentation
dotnet_diagnostic.IDE1006.severity = none # No need for Async suffix on test names

resharper_comment_typo_highlighting = none



=== File: libraries/dotnet/README.md ===
# Semantic Workbench

Semantic Workbench is a versatile tool designed for quickly prototyping intelligent assistants.
Whether you're building new assistants or integrating existing ones, the workbench offers a unified
interface for managing conversations, configuring settings, and customizing behavior.

# Connector

The Connector allows to seamlessly integrate .NET agents, built with any framework, into Semantic
Workbench. By using HTTP for communication, the connector enables your agent to handle instructions
and exchange data with both the frontend and backend of Semantic Workbench.

# Setup Guide

To integrate your agent:

1. Add the `Microsoft.SemanticWorkbench.Connector` nuget to the .NET project containing your agent.

2. **Define an agent configuration**: Create a configuration class for your agent. This can be empty
   if no configuration is needed from the workbench UI.

3. **Extend Agent Functionality**: Inherit from `Microsoft.SemanticWorkbench.Connector.AgentBase`
   and implement the `GetDefaultConfig` and `ParseConfig` methods in your agent class. Examples
   are available in the repository.

4. **Create a Connector**: Implement `Microsoft.SemanticWorkbench.Connector.WorkbenchConnector` and
   its `CreateAgentAsync` method to allow the workbench to create multiple agent instances.

5. Start a `Microsoft.SemanticWorkbench.Connector.WorkbenchConnector` calling the `ConnectAsync`
   method.

6. Start a Web service using the endpoints defined in `Microsoft.SemanticWorkbench.Connector.Webservice`.

# Examples

Find sample .NET agents and assistants using this connector in the
[official repository](https://github.com/microsoft/semanticworkbench/tree/main/examples).


=== File: libraries/dotnet/SemanticWorkbench.sln ===
﻿
Microsoft Visual Studio Solution File, Format Version 12.00
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "WorkbenchConnector", "WorkbenchConnector\WorkbenchConnector.csproj", "{F7DBFD56-5A7C-41D1-8F0A-B00E51477E19}"
EndProject
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "dotnet-01-echo-bot", "..\..\examples\dotnet\dotnet-01-echo-bot\dotnet-01-echo-bot.csproj", "{3A6FE36E-B186-458C-984B-C1BBF4BFB440}"
EndProject
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "dotnet-02-message-types-demo", "..\..\examples\dotnet\dotnet-02-message-types-demo\dotnet-02-message-types-demo.csproj", "{46BC33EC-AA35-428D-A8B4-2C0E693C7C51}"
EndProject
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "dotnet-03-simple-chatbot", "..\..\examples\dotnet\dotnet-03-simple-chatbot\dotnet-03-simple-chatbot.csproj", "{C6CA301B-11B3-4EF5-A18A-D5840F23115B}"
EndProject
Project("{2150E333-8FDC-42A3-9474-1A3956D46DE8}") = "examples", "examples", "{11BDE565-F05E-495A-9407-4E403C3DE93D}"
EndProject
Global
	GlobalSection(SolutionConfigurationPlatforms) = preSolution
		Debug|Any CPU = Debug|Any CPU
		Release|Any CPU = Release|Any CPU
	EndGlobalSection
	GlobalSection(ProjectConfigurationPlatforms) = postSolution
		{F7DBFD56-5A7C-41D1-8F0A-B00E51477E19}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{F7DBFD56-5A7C-41D1-8F0A-B00E51477E19}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{F7DBFD56-5A7C-41D1-8F0A-B00E51477E19}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{F7DBFD56-5A7C-41D1-8F0A-B00E51477E19}.Release|Any CPU.Build.0 = Release|Any CPU
		{3A6FE36E-B186-458C-984B-C1BBF4BFB440}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{3A6FE36E-B186-458C-984B-C1BBF4BFB440}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{3A6FE36E-B186-458C-984B-C1BBF4BFB440}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{46BC33EC-AA35-428D-A8B4-2C0E693C7C51}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{46BC33EC-AA35-428D-A8B4-2C0E693C7C51}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{46BC33EC-AA35-428D-A8B4-2C0E693C7C51}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{C6CA301B-11B3-4EF5-A18A-D5840F23115B}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{C6CA301B-11B3-4EF5-A18A-D5840F23115B}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{C6CA301B-11B3-4EF5-A18A-D5840F23115B}.Release|Any CPU.ActiveCfg = Release|Any CPU
	EndGlobalSection
	GlobalSection(NestedProjects) = preSolution
		{3A6FE36E-B186-458C-984B-C1BBF4BFB440} = {11BDE565-F05E-495A-9407-4E403C3DE93D}
		{46BC33EC-AA35-428D-A8B4-2C0E693C7C51} = {11BDE565-F05E-495A-9407-4E403C3DE93D}
		{C6CA301B-11B3-4EF5-A18A-D5840F23115B} = {11BDE565-F05E-495A-9407-4E403C3DE93D}
	EndGlobalSection
EndGlobal


=== File: libraries/dotnet/SemanticWorkbench.sln.DotSettings ===
﻿<wpf:ResourceDictionary xml:space="preserve" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" xmlns:s="clr-namespace:System;assembly=mscorlib" xmlns:ss="urn:shemas-jetbrains-com:settings-storage-xaml" xmlns:wpf="http://schemas.microsoft.com/winfx/2006/xaml/presentation">
	<s:Boolean x:Key="/Default/CodeEditing/ContextActionTable/DisabledContextActions/=JetBrains_002EReSharper_002EIntentions_002ECSharp_002EContextActions_002EMisc_002ESurroundWithQuotesAction/@EntryIndexedValue">False</s:Boolean>
	<s:Boolean x:Key="/Default/CodeEditing/ContextActionTable/DisabledContextActions/=JetBrains_002EReSharper_002EIntentions_002ECSharp_002EContextActions_002ENullPropagationToIfStatementAction/@EntryIndexedValue">False</s:Boolean>
	<s:Boolean x:Key="/Default/CodeEditing/TypingAssist/Asp/FormatOnClosingTag/@EntryValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/CodeEditing/TypingAssist/Asp/FormatOnEnter/@EntryValue">True</s:Boolean>
	<s:String x:Key="/Default/CodeEditing/TypingAssist/FormatOnPaste/@EntryValue">FullFormat</s:String>
	<s:Boolean x:Key="/Default/CodeInspection/ExcludedFiles/FileMasksToSkip/=_002A_002Ecshtml/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/CodeInspection/ExcludedFiles/FileMasksToSkip/=_002A_002Ecss/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/CodeInspection/ExcludedFiles/FileMasksToSkip/=_002A_002Eini/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/CodeInspection/ExcludedFiles/FileMasksToSkip/=_002A_002Ejs/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/CodeInspection/ExcludedFiles/FileMasksToSkip/=_002A_002Esvg/@EntryIndexedValue">True</s:Boolean>
	<s:String x:Key="/Default/CodeInspection/Highlighting/AnalysisEnabled/@EntryValue">SOLUTION</s:String>
	<s:Boolean x:Key="/Default/CodeInspection/Highlighting/CalculateUnusedTypeMembers/@EntryValue">False</s:Boolean>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=ArrangeAttributes/@EntryIndexedValue">SUGGESTION</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=ArrangeThisQualifier/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadAttributeBracketsSpaces/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadBracesSpaces/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadChildStatementIndent/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadColonSpaces/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadCommaSpaces/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadControlBracesIndent/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadControlBracesLineBreaks/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadDeclarationBracesIndent/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadDeclarationBracesLineBreaks/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadEmptyBracesLineBreaks/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadExpressionBracesIndent/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadExpressionBracesLineBreaks/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadGenericBracketsSpaces/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadIndent/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadLinqLineBreaks/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadListLineBreaks/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadMemberAccessSpaces/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadNamespaceBracesIndent/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadParensLineBreaks/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadParensSpaces/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadPreprocessorIndent/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadSemicolonSpaces/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadSpacesAfterKeyword/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadSquareBracketsSpaces/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadSwitchBracesIndent/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BadSymbolSpaces/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=BuiltInTypeReferenceStyle/@EntryIndexedValue">SUGGESTION</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=CheckNamespace/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=CommentTypo/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=ConditionalTernaryEqualBranch/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=CSharpWarnings_003A_003ACS1571/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=IdentifierTypo/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=InconsistentNaming/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=IncorrectBlankLinesNearBraces/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=MissingBlankLines/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=MissingIndent/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=MissingLinebreak/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=MissingSpace/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=MultipleSpaces/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=MultipleStatementsOnOneLine/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=MultipleTypeMembersOnOneLine/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=OutdentIsOffPrevLevel/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=RedundantBlankLines/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=RedundantLinebreak/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=RedundantSpace/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=RedundantUsingDirective/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=TabsAndSpacesMismatch/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=TabsOutsideIndent/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=UnusedImportClause/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=WrongIndentSize/@EntryIndexedValue">ERROR</s:String>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=Xunit_002EXunitTestWithConsoleOutput/@EntryIndexedValue">ERROR</s:String>
	<s:Boolean x:Key="/Default/CodeStyle/CodeFormatting/CSharpCodeStyle/APPLY_ON_COMPLETION/@EntryValue">True</s:Boolean>
	<s:String x:Key="/Default/CodeStyle/CodeFormatting/CSharpCodeStyle/ThisQualifier/INSTANCE_MEMBERS_QUALIFY_MEMBERS/@EntryValue">Field, Property, Event, Method</s:String>
	<s:Boolean x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/ALIGN_LINQ_QUERY/@EntryValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/ALIGN_MULTIPLE_DECLARATION/@EntryValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/ALIGN_MULTLINE_TYPE_PARAMETER_LIST/@EntryValue">True</s:Boolean>
	<s:String x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/CASE_BLOCK_BRACES/@EntryValue">NEXT_LINE</s:String>
	<s:Boolean x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/INDENT_NESTED_FIXED_STMT/@EntryValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/INDENT_NESTED_FOR_STMT/@EntryValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/INDENT_NESTED_FOREACH_STMT/@EntryValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/INDENT_NESTED_LOCK_STMT/@EntryValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/INDENT_NESTED_USINGS_STMT/@EntryValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/INDENT_NESTED_WHILE_STMT/@EntryValue">True</s:Boolean>
	<s:Int64 x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/KEEP_BLANK_LINES_IN_CODE/@EntryValue">1</s:Int64>
	<s:Int64 x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/KEEP_BLANK_LINES_IN_DECLARATIONS/@EntryValue">1</s:Int64>
	<s:Boolean x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/KEEP_EXISTING_ATTRIBUTE_ARRANGEMENT/@EntryValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/KEEP_EXISTING_EMBEDDED_BLOCK_ARRANGEMENT/@EntryValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/LINE_FEED_AT_FILE_END/@EntryValue">True</s:Boolean>
	<s:String x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/PLACE_EXPR_METHOD_ON_SINGLE_LINE/@EntryValue">ALWAYS</s:String>
	<s:Boolean x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/PLACE_SIMPLE_EMBEDDED_BLOCK_ON_SAME_LINE/@EntryValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/SPACE_WITHIN_SINGLE_LINE_ARRAY_INITIALIZER_BRACES/@EntryValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/STICK_COMMENT/@EntryValue">False</s:Boolean>
	<s:Int64 x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/WRAP_LIMIT/@EntryValue">512</s:Int64>
	<s:Boolean x:Key="/Default/CodeStyle/CodeFormatting/CSharpFormat/WRAP_LINES/@EntryValue">True</s:Boolean>
	<s:String x:Key="/Default/CodeStyle/FileHeader/FileHeaderText/@EntryValue">Copyright (c) Microsoft. All rights reserved.</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=ABC/@EntryIndexedValue">ABC</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=ACS/@EntryIndexedValue">ACS</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=AI/@EntryIndexedValue">AI</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=AIGPT/@EntryIndexedValue">AIGPT</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=AMQP/@EntryIndexedValue">AMQP</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=API/@EntryIndexedValue">API</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=BOM/@EntryIndexedValue">BOM</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=CORS/@EntryIndexedValue">CORS</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=DB/@EntryIndexedValue">DB</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=DI/@EntryIndexedValue">DI</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=GPT/@EntryIndexedValue">GPT</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=GRPC/@EntryIndexedValue">GRPC</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=HMAC/@EntryIndexedValue">HMAC</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=HTTP/@EntryIndexedValue">HTTP</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=IM/@EntryIndexedValue">IM</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=IO/@EntryIndexedValue">IO</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=IOS/@EntryIndexedValue">IOS</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=JSON/@EntryIndexedValue">JSON</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=JWT/@EntryIndexedValue">JWT</s:String>
    <s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=HTML/@EntryIndexedValue">HTML</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=MQ/@EntryIndexedValue">MQ</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=MQTT/@EntryIndexedValue">MQTT</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=MS/@EntryIndexedValue">MS</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=MSAL/@EntryIndexedValue">MSAL</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=OCR/@EntryIndexedValue">OCR</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=OID/@EntryIndexedValue">OID</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=OK/@EntryIndexedValue">OK</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=OS/@EntryIndexedValue">OS</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=PR/@EntryIndexedValue">PR</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=QA/@EntryIndexedValue">QA</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=SHA/@EntryIndexedValue">SHA</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=SK/@EntryIndexedValue">SK</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=SKHTTP/@EntryIndexedValue">SKHTTP</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=SSL/@EntryIndexedValue">SSL</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=TTL/@EntryIndexedValue">TTL</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=UI/@EntryIndexedValue">UI</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=UID/@EntryIndexedValue">UID</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=URL/@EntryIndexedValue">URL</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=XML/@EntryIndexedValue">XML</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=YAML/@EntryIndexedValue">YAML</s:String>
	<s:Boolean x:Key="/Default/CodeStyle/Naming/CSharpNaming/ApplyAutoDetectedRules/@EntryValue">False</s:Boolean>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/PredefinedNamingRules/=Constants/@EntryIndexedValue">&lt;Policy Inspect="True" Prefix="" Suffix="" Style="AaBb" /&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/PredefinedNamingRules/=LocalConstants/@EntryIndexedValue">&lt;Policy Inspect="True" Prefix="" Suffix="" Style="AA_BB"&gt;&lt;ExtraRule Prefix="" Suffix="" Style="aaBb" /&gt;&lt;/Policy&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/PredefinedNamingRules/=LocalFunctions/@EntryIndexedValue">&lt;Policy Inspect="True" Prefix="" Suffix="" Style="AaBb"&gt;&lt;ExtraRule Prefix="" Suffix="Async" Style="AaBb" /&gt;&lt;/Policy&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/PredefinedNamingRules/=Locals/@EntryIndexedValue">&lt;Policy Inspect="True" Prefix="" Suffix="" Style="aaBb"&gt;&lt;ExtraRule Prefix="" Suffix="Async" Style="aaBb" /&gt;&lt;/Policy&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/PredefinedNamingRules/=Method/@EntryIndexedValue">&lt;Policy Inspect="True" Prefix="" Suffix="" Style="AaBb"&gt;&lt;ExtraRule Prefix="" Suffix="Async" Style="AaBb" /&gt;&lt;/Policy&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/PredefinedNamingRules/=Parameters/@EntryIndexedValue">&lt;Policy Inspect="True" Prefix="" Suffix="" Style="aaBb"&gt;&lt;ExtraRule Prefix="" Suffix="Async" Style="aaBb" /&gt;&lt;/Policy&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/PredefinedNamingRules/=PrivateConstants/@EntryIndexedValue">&lt;Policy Inspect="True" Prefix="" Suffix="" Style="AaBb" /&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/PredefinedNamingRules/=PrivateInstanceFields/@EntryIndexedValue">&lt;Policy Inspect="True" Prefix="_" Suffix="" Style="aaBb" /&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/PredefinedNamingRules/=PrivateStaticFields/@EntryIndexedValue">&lt;Policy Inspect="True" Prefix="s_" Suffix="" Style="aaBb" /&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/PredefinedNamingRules/=Property/@EntryIndexedValue">&lt;Policy Inspect="True" Prefix="" Suffix="" Style="AaBb"&gt;&lt;ExtraRule Prefix="" Suffix="Async" Style="AaBb" /&gt;&lt;/Policy&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/PredefinedNamingRules/=TypesAndNamespaces/@EntryIndexedValue">&lt;Policy Inspect="True" Prefix="" Suffix="" Style="AaBb"&gt;&lt;ExtraRule Prefix="" Suffix="" Style="AaBb_AaBb" /&gt;&lt;/Policy&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/UserRules/=236f7aa5_002D7b06_002D43ca_002Dbf2a_002D9b31bfcff09a/@EntryIndexedValue">&lt;Policy&gt;&lt;Descriptor Staticness="Any" AccessRightKinds="Private" Description="Constant fields (private)"&gt;&lt;ElementKinds&gt;&lt;Kind Name="CONSTANT_FIELD" /&gt;&lt;/ElementKinds&gt;&lt;/Descriptor&gt;&lt;Policy Inspect="True" Prefix="" Suffix="" Style="AaBb" /&gt;&lt;/Policy&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/UserRules/=4a98fdf6_002D7d98_002D4f5a_002Dafeb_002Dea44ad98c70c/@EntryIndexedValue">&lt;Policy&gt;&lt;Descriptor Staticness="Instance" AccessRightKinds="Private" Description="Instance fields (private)"&gt;&lt;ElementKinds&gt;&lt;Kind Name="FIELD" /&gt;&lt;Kind Name="READONLY_FIELD" /&gt;&lt;/ElementKinds&gt;&lt;/Descriptor&gt;&lt;Policy Inspect="True" Prefix="_" Suffix="" Style="aaBb" /&gt;&lt;/Policy&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/UserRules/=61a991a4_002Dd0a3_002D4d19_002D90a5_002Df8f4d75c30c1/@EntryIndexedValue">&lt;Policy&gt;&lt;Descriptor Staticness="Any" AccessRightKinds="Any" Description="Local variables"&gt;&lt;ElementKinds&gt;&lt;Kind Name="LOCAL_VARIABLE" /&gt;&lt;/ElementKinds&gt;&lt;/Descriptor&gt;&lt;Policy Inspect="True" Prefix="" Suffix="" Style="aaBb"&gt;&lt;ExtraRule Prefix="" Suffix="Async" Style="aaBb" /&gt;&lt;/Policy&gt;&lt;/Policy&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/UserRules/=669e5282_002Dfb4b_002D4e90_002D91e7_002D07d269d04b60/@EntryIndexedValue">&lt;Policy&gt;&lt;Descriptor Staticness="Any" AccessRightKinds="Protected, ProtectedInternal, Internal, Public, PrivateProtected" Description="Constant fields (not private)"&gt;&lt;ElementKinds&gt;&lt;Kind Name="CONSTANT_FIELD" /&gt;&lt;/ElementKinds&gt;&lt;/Descriptor&gt;&lt;Policy Inspect="True" Prefix="" Suffix="" Style="AaBb" /&gt;&lt;/Policy&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/UserRules/=76f79b1e_002Dece7_002D4df2_002Da322_002D1bd7fea25eb7/@EntryIndexedValue">&lt;Policy&gt;&lt;Descriptor Staticness="Any" AccessRightKinds="Any" Description="Local functions"&gt;&lt;ElementKinds&gt;&lt;Kind Name="LOCAL_FUNCTION" /&gt;&lt;/ElementKinds&gt;&lt;/Descriptor&gt;&lt;Policy Inspect="True" Prefix="" Suffix="" Style="AaBb"&gt;&lt;ExtraRule Prefix="" Suffix="Async" Style="AaBb" /&gt;&lt;/Policy&gt;&lt;/Policy&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/UserRules/=8284009d_002De743_002D4d89_002D9402_002Da5bf9a89b657/@EntryIndexedValue">&lt;Policy&gt;&lt;Descriptor Staticness="Any" AccessRightKinds="Any" Description="Methods"&gt;&lt;ElementKinds&gt;&lt;Kind Name="METHOD" /&gt;&lt;/ElementKinds&gt;&lt;/Descriptor&gt;&lt;Policy Inspect="True" Prefix="" Suffix="" Style="AaBb"&gt;&lt;ExtraRule Prefix="" Suffix="Async" Style="AaBb" /&gt;&lt;/Policy&gt;&lt;/Policy&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/UserRules/=8a85b61a_002D1024_002D4f87_002Db9ef_002D1fdae19930a1/@EntryIndexedValue">&lt;Policy&gt;&lt;Descriptor Staticness="Any" AccessRightKinds="Any" Description="Parameters"&gt;&lt;ElementKinds&gt;&lt;Kind Name="PARAMETER" /&gt;&lt;/ElementKinds&gt;&lt;/Descriptor&gt;&lt;Policy Inspect="True" Prefix="" Suffix="" Style="aaBb"&gt;&lt;ExtraRule Prefix="" Suffix="Async" Style="aaBb" /&gt;&lt;/Policy&gt;&lt;/Policy&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/UserRules/=a0b4bc4d_002Dd13b_002D4a37_002Db37e_002Dc9c6864e4302/@EntryIndexedValue">&lt;Policy&gt;&lt;Descriptor Staticness="Any" AccessRightKinds="Any" Description="Types and namespaces"&gt;&lt;ElementKinds&gt;&lt;Kind Name="NAMESPACE" /&gt;&lt;Kind Name="CLASS" /&gt;&lt;Kind Name="STRUCT" /&gt;&lt;Kind Name="ENUM" /&gt;&lt;Kind Name="DELEGATE" /&gt;&lt;/ElementKinds&gt;&lt;/Descriptor&gt;&lt;Policy Inspect="True" Prefix="" Suffix="" Style="AaBb"&gt;&lt;ExtraRule Prefix="" Suffix="" Style="AaBb_AaBb" /&gt;&lt;/Policy&gt;&lt;/Policy&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/UserRules/=a4f433b8_002Dabcd_002D4e55_002Da08f_002D82e78cef0f0c/@EntryIndexedValue">&lt;Policy&gt;&lt;Descriptor Staticness="Any" AccessRightKinds="Any" Description="Local constants"&gt;&lt;ElementKinds&gt;&lt;Kind Name="LOCAL_CONSTANT" /&gt;&lt;/ElementKinds&gt;&lt;/Descriptor&gt;&lt;Policy Inspect="True" Prefix="" Suffix="" Style="AA_BB"&gt;&lt;ExtraRule Prefix="" Suffix="" Style="aaBb" /&gt;&lt;/Policy&gt;&lt;/Policy&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/UserRules/=c85a0503_002D4de2_002D40f1_002D9cd6_002Da4054c05d384/@EntryIndexedValue">&lt;Policy&gt;&lt;Descriptor Staticness="Any" AccessRightKinds="Any" Description="Properties"&gt;&lt;ElementKinds&gt;&lt;Kind Name="PROPERTY" /&gt;&lt;/ElementKinds&gt;&lt;/Descriptor&gt;&lt;Policy Inspect="True" Prefix="" Suffix="" Style="AaBb"&gt;&lt;ExtraRule Prefix="" Suffix="Async" Style="AaBb" /&gt;&lt;/Policy&gt;&lt;/Policy&gt;</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/UserRules/=f9fce829_002De6f4_002D4cb2_002D80f1_002D5497c44f51df/@EntryIndexedValue">&lt;Policy&gt;&lt;Descriptor Staticness="Static" AccessRightKinds="Private" Description="Static fields (private)"&gt;&lt;ElementKinds&gt;&lt;Kind Name="FIELD" /&gt;&lt;/ElementKinds&gt;&lt;/Descriptor&gt;&lt;Policy Inspect="True" Prefix="s_" Suffix="" Style="aaBb" /&gt;&lt;/Policy&gt;</s:String>
	<s:String x:Key="/Default/CustomTools/CustomToolsData/@EntryValue"></s:String>
	<s:Int64 x:Key="/Default/Environment/Hierarchy/Build/BuildTool/MsBuildSolutionLoadingNodeCount/@EntryValue">2</s:Int64>
	<s:Boolean x:Key="/Default/Environment/Hierarchy/Build/SolutionBuilderNext/LogToFile/@EntryValue">False</s:Boolean>
	<s:Boolean x:Key="/Default/Environment/Hierarchy/Build/SolutionBuilderNext/ShouldRestoreNugetPackages/@EntryValue">True</s:Boolean>
	<s:String x:Key="/Default/Environment/Hierarchy/NuGetOptions/IntegratedRestoreEngine/@EntryValue">Console</s:String>
	<s:String x:Key="/Default/Environment/InlayHints/GeneralInlayHintsOptions/DefaultMode/@EntryValue">PushToShowHints</s:String>
	<s:Boolean x:Key="/Default/Environment/SettingsMigration/IsMigratorApplied/=JetBrains_002EReSharper_002EFeature_002EServices_002ECodeCleanup_002EFileHeader_002EFileHeaderSettingsMigrate/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/Environment/SettingsMigration/IsMigratorApplied/=JetBrains_002EReSharper_002EPsi_002ECSharp_002ECodeStyle_002ECSharpAttributeForSingleLineMethodUpgrade/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/Environment/SettingsMigration/IsMigratorApplied/=JetBrains_002EReSharper_002EPsi_002ECSharp_002ECodeStyle_002ECSharpKeepExistingMigration/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/Environment/SettingsMigration/IsMigratorApplied/=JetBrains_002EReSharper_002EPsi_002ECSharp_002ECodeStyle_002ECSharpPlaceEmbeddedOnSameLineMigration/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/Environment/SettingsMigration/IsMigratorApplied/=JetBrains_002EReSharper_002EPsi_002ECSharp_002ECodeStyle_002ECSharpRenamePlacementToArrangementMigration/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/Environment/SettingsMigration/IsMigratorApplied/=JetBrains_002EReSharper_002EPsi_002ECSharp_002ECodeStyle_002ECSharpUseContinuousIndentInsideBracesMigration/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/Environment/SettingsMigration/IsMigratorApplied/=JetBrains_002EReSharper_002EPsi_002ECSharp_002ECodeStyle_002ESettingsUpgrade_002EAddAccessorOwnerDeclarationBracesMigration/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/Environment/SettingsMigration/IsMigratorApplied/=JetBrains_002EReSharper_002EPsi_002ECSharp_002ECodeStyle_002ESettingsUpgrade_002ECSharpPlaceAttributeOnSameLineMigration/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/Environment/SettingsMigration/IsMigratorApplied/=JetBrains_002EReSharper_002EPsi_002ECSharp_002ECodeStyle_002ESettingsUpgrade_002EMigrateBlankLinesAroundFieldToBlankLinesAroundProperty/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/Environment/SettingsMigration/IsMigratorApplied/=JetBrains_002EReSharper_002EPsi_002ECSharp_002ECodeStyle_002ESettingsUpgrade_002EMigrateThisQualifierSettings/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/Environment/SettingsMigration/IsMigratorApplied/=JetBrains_002EReSharper_002EPsi_002ECSharp_002ECodeStyle_002ESettingsUpgrade_002EPredefinedNamingRulesToUserRulesUpgrade/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/Environment/SettingsMigration/IsMigratorApplied/=JetBrains_002EReSharper_002EUnitTestFramework_002ESettings_002EMigrations_002ERemoveBuildPolicyAlwaysMigration/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/Housekeeping/Layout/SolBuilderDuoView/ShowBuildProgressInToolWindow/@EntryValue">False</s:Boolean>
	<s:String x:Key="/Default/Housekeeping/UnitTestingMru/UnitTestSessionDefault/LogSeverity/@EntryValue">TRACE</s:String>
	<s:Int64 x:Key="/Default/Housekeeping/UnitTestingMru/UnitTestSessionDefault/OutputLineNumberLimit/@EntryValue">8201</s:Int64>
	<s:String x:Key="/Default/Housekeeping/UnitTestingMru/UnitTestSessionDefault/PlatformType/@EntryValue">Automatic</s:String>
	<s:Boolean x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=938AB0AF2F87A1479305AF74828124DA/@KeyIndexDefined">True</s:Boolean>
	<s:Boolean x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=938AB0AF2F87A1479305AF74828124DA/Applicability/=Live/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=938AB0AF2F87A1479305AF74828124DA/IsBlessed/@EntryValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=938AB0AF2F87A1479305AF74828124DA/Reformat/@EntryValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=938AB0AF2F87A1479305AF74828124DA/Scope/=C3001E7C0DA78E4487072B7E050D86C5/@KeyIndexDefined">True</s:Boolean>
	<s:String x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=938AB0AF2F87A1479305AF74828124DA/Scope/=C3001E7C0DA78E4487072B7E050D86C5/CustomProperties/=minimumLanguageVersion/@EntryIndexedValue">2.0</s:String>
	<s:String x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=938AB0AF2F87A1479305AF74828124DA/Scope/=C3001E7C0DA78E4487072B7E050D86C5/Type/@EntryValue">InCSharpFile</s:String>
	<s:String x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=938AB0AF2F87A1479305AF74828124DA/Shortcut/@EntryValue">pragma</s:String>
	<s:Boolean x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=938AB0AF2F87A1479305AF74828124DA/ShortenQualifiedReferences/@EntryValue">True</s:Boolean>
	<s:String x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=938AB0AF2F87A1479305AF74828124DA/Text/@EntryValue">#pragma warning disable CA0000 // reason

#pragma warning restore CA0000</s:String>
	<s:Boolean x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=CC90F25BDE5075498DCA20E411C14A16/@KeyIndexDefined">True</s:Boolean>
	<s:Boolean x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=CC90F25BDE5075498DCA20E411C14A16/Applicability/=Live/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=CC90F25BDE5075498DCA20E411C14A16/Field/=METHOD/@KeyIndexDefined">False</s:Boolean>
	<s:Boolean x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=CC90F25BDE5075498DCA20E411C14A16/Field/=SOMENAME/@KeyIndexDefined">True</s:Boolean>
	<s:String x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=CC90F25BDE5075498DCA20E411C14A16/Field/=SOMENAME/Expression/@EntryValue">guid()</s:String>
	<s:Int64 x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=CC90F25BDE5075498DCA20E411C14A16/Field/=SOMENAME/Order/@EntryValue">0</s:Int64>
	<s:Boolean x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=CC90F25BDE5075498DCA20E411C14A16/IsBlessed/@EntryValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=CC90F25BDE5075498DCA20E411C14A16/Reformat/@EntryValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=CC90F25BDE5075498DCA20E411C14A16/Scope/=ABDFB0613102DF4DBB59387506ADA616/@KeyIndexDefined">False</s:Boolean>
	<s:Boolean x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=CC90F25BDE5075498DCA20E411C14A16/Scope/=B68999B9D6B43E47A02B22C12A54C3CC/@KeyIndexDefined">False</s:Boolean>
	<s:Boolean x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=CC90F25BDE5075498DCA20E411C14A16/Scope/=C3001E7C0DA78E4487072B7E050D86C5/@KeyIndexDefined">True</s:Boolean>
	<s:String x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=CC90F25BDE5075498DCA20E411C14A16/Scope/=C3001E7C0DA78E4487072B7E050D86C5/CustomProperties/=minimumLanguageVersion/@EntryIndexedValue">2.0</s:String>
	<s:String x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=CC90F25BDE5075498DCA20E411C14A16/Scope/=C3001E7C0DA78E4487072B7E050D86C5/Type/@EntryValue">InCSharpFile</s:String>
	<s:String x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=CC90F25BDE5075498DCA20E411C14A16/Shortcut/@EntryValue">aaa</s:String>
	<s:Boolean x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=CC90F25BDE5075498DCA20E411C14A16/ShortenQualifiedReferences/@EntryValue">True</s:Boolean>
	<s:String x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=CC90F25BDE5075498DCA20E411C14A16/Text/@EntryValue">[Fact]
public void It$SOMENAME$()
{
    // Arrange

    // Act

    // Assert

}</s:String>
	<s:Boolean x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=DEC4D140B393B04F8A18C0913BDE0592/@KeyIndexDefined">True</s:Boolean>
	<s:Boolean x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=DEC4D140B393B04F8A18C0913BDE0592/Applicability/=Live/@EntryIndexedValue">True</s:Boolean>
	<s:String x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=DEC4D140B393B04F8A18C0913BDE0592/Description/@EntryValue">MSFT copyright</s:String>
	<s:Boolean x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=DEC4D140B393B04F8A18C0913BDE0592/Scope/=C3001E7C0DA78E4487072B7E050D86C5/@KeyIndexDefined">True</s:Boolean>
	<s:String x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=DEC4D140B393B04F8A18C0913BDE0592/Scope/=C3001E7C0DA78E4487072B7E050D86C5/CustomProperties/=minimumLanguageVersion/@EntryIndexedValue">2.0</s:String>
	<s:String x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=DEC4D140B393B04F8A18C0913BDE0592/Scope/=C3001E7C0DA78E4487072B7E050D86C5/Type/@EntryValue">InCSharpFile</s:String>
	<s:String x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=DEC4D140B393B04F8A18C0913BDE0592/Shortcut/@EntryValue">copy</s:String>
	<s:String x:Key="/Default/PatternsAndTemplates/LiveTemplates/Template/=DEC4D140B393B04F8A18C0913BDE0592/Text/@EntryValue">// Copyright (c) Microsoft. All rights reserved.
</s:String>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=abcdefghijklmnopqrstuvwxyz/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=AOAI/@EntryIndexedValue">True</s:Boolean>
    <s:Boolean x:Key="/Default/UserDictionary/Words/=AWSS3/@EntryIndexedValue">True</s:Boolean>
    <s:Boolean x:Key="/Default/UserDictionary/Words/=AWS/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=AZAI/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=AZDOCINTEL/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=AZSEARCH/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=AZUREBLOBS/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=AZUREIDENTITY/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=AZUREQUEUE/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=CONNECTIONSTRING/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=daa/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=appsettings/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=arrivederci/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=ask_0027s/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=awaiters/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=CHATGPT/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=childrens/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Chunker/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Ctors/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=davinci/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Devis/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Dotproduct/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=embedder/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=ENDPART/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=facetable/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=fareweller/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=fffffff/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=FILEBASEDQUEUE/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Formattable/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=gguf/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=greaterthan/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=hhmmssfffffff/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Hmmss/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=HNSW/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=inheritdoc/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=INPROCESS/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Joinable/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=keyvault/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Kitto/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=KMEXP/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=lessthan/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=liveness/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Logit/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Mddhhmmssfffffff/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=mergeresults/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Milvus/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Mirostat/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Mixtral/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=msword/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=myfile/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=mypipelinestep/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Notegen/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=pgvector/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Pinecone/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Pinecone_0027s/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Qdrant/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=reserialization/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=retriable/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Roundtrips/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Reranker/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=sandboxing/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=SK/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=SKHTTP/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=skillname/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=skmemory/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=skprompt/@EntryIndexedValue">True</s:Boolean>
	<s:String x:Key="/Default/CodeInspection/Highlighting/InspectionSeverities/=Xunit_002EXunitTestWithConsoleOutput/@EntryIndexedValue">DO_NOT_SHOW</s:String>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=smemory/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=subdir/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=SVCS/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=syntaxes/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=testsettings/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=tiktoken/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=tldr/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=typeparam/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Untrust/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=upserted/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Upserting/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Upserts/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Weaviate/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=wellknown/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=Wordprocessing/@EntryIndexedValue">True</s:Boolean>
	<s:Boolean x:Key="/Default/UserDictionary/Words/=xact/@EntryIndexedValue">True</s:Boolean>
</wpf:ResourceDictionary>


=== File: libraries/dotnet/WorkbenchConnector/AgentBase.cs ===
﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticWorkbench.Connector;

public abstract class AgentBase<TAgentConfig> : IAgentBase
    where TAgentConfig : AgentConfigBase, new()
{
    // Agent instance ID
    public string Id { get; protected set; } = string.Empty;

    // Agent instance name
    public string Name { get; protected set; } = string.Empty;

    // Agent settings
    public TAgentConfig Config { get; protected set; } = new();

    // Simple storage layer to persist agents data
    protected IAgentServiceStorage Storage { get; private set; }

    // Reference to agent service
    protected WorkbenchConnector<TAgentConfig> WorkbenchConnector { get; private set; }

    // Agent logger
    protected ILogger Log { get; private set; }

    /// <summary>
    /// Agent instantiation
    /// </summary>
    /// <param name="workbenchConnector">Semantic Workbench connector</param>
    /// <param name="storage">Agent data storage</param>
    /// <param name="log">Agent logger</param>
    protected AgentBase(
        WorkbenchConnector<TAgentConfig> workbenchConnector,
        IAgentServiceStorage storage,
        ILogger log)
    {
        this.WorkbenchConnector = workbenchConnector;
        this.Storage = storage;
        this.Log = log;
    }

    /// <summary>
    /// Convert agent config to a persistent data model
    /// </summary>
    public virtual AgentInfo ToDataModel()
    {
        return new AgentInfo
        {
            Id = this.Id,
            Name = this.Name,
            Config = this.Config,
        };
    }

    /// <summary>
    /// Parse object to agent configuration instance
    /// </summary>
    /// <param name="data">Untyped configuration data</param>
    public virtual TAgentConfig? ParseConfig(object data)
    {
        return JsonSerializer.Deserialize<TAgentConfig>(JsonSerializer.Serialize(data));
    }

    /// <summary>
    /// Update the configuration of an agent instance
    /// </summary>
    /// <param name="config">Configuration data</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    /// <returns>Agent configuration</returns>
    public virtual async Task<TAgentConfig> UpdateAgentConfigAsync(
        TAgentConfig? config,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Updating agent '{0}' config", this.Id.HtmlEncode());
        this.Config = config ?? new TAgentConfig();
        await this.Storage.SaveAgentAsync(this, cancellationToken).ConfigureAwait(false);
        return this.Config;
    }

    /// <summary>
    /// Start the agent
    /// </summary>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task StartAsync(
        CancellationToken cancellationToken = default)
    {
        return this.Storage.SaveAgentAsync(this, cancellationToken);
    }

    /// <summary>
    /// Stop the agent
    /// </summary>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task StopAsync(
        CancellationToken cancellationToken = default)
    {
        return this.Storage.DeleteAgentAsync(this, cancellationToken);
    }

    /// <summary>
    /// Return the list of states in the given conversation.
    /// TODO: Support states with UI
    /// </summary>
    /// <param name="conversationId">Conversation Id</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task<List<Insight>> GetConversationInsightsAsync(
        string conversationId,
        CancellationToken cancellationToken = default)
    {
        return this.Storage.GetAllInsightsAsync(this.Id, conversationId, cancellationToken);
    }

    /// <summary>
    /// Notify the workbench about an update of the given state.
    /// States are visible in a conversation, on the right panel.
    /// </summary>
    /// <param name="conversationId">Conversation Id</param>
    /// <param name="insight">State ID and content</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task SetConversationInsightAsync(
        string conversationId,
        Insight insight,
        CancellationToken cancellationToken = default)
    {
        await Task.WhenAll([
            this.Storage.SaveInsightAsync(this.Id, conversationId, insight, cancellationToken),
            this.WorkbenchConnector.UpdateAgentConversationInsightAsync(this.Id, conversationId, insight, cancellationToken)
        ]).ConfigureAwait(false);
    }

    /// <summary>
    /// Create a new conversation
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task CreateConversationAsync(
        string conversationId,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Creating conversation '{0}' on agent '{1}'",
            conversationId.HtmlEncode(), this.Id.HtmlEncode());

        Conversation conversation = await this.Storage.GetConversationAsync(conversationId, this.Id, cancellationToken).ConfigureAwait(false)
                                    ?? new Conversation(conversationId, this.Id);

        await Task.WhenAll([
            this.SetConversationInsightAsync(conversation.Id, new Insight("log", "Log", $"Conversation started at {DateTimeOffset.UtcNow}"), cancellationToken),
            this.Storage.SaveConversationAsync(conversation, cancellationToken)
        ]).ConfigureAwait(false);
    }

    /// <summary>
    /// Delete a conversation
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task DeleteConversationAsync(
        string conversationId,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Deleting conversation '{0}' on agent '{1}'",
            conversationId.HtmlEncode(), this.Id.HtmlEncode());
        return this.Storage.DeleteConversationAsync(conversationId, this.Id, cancellationToken);
    }

    /// <summary>
    /// Check if a conversation with a given ID exists
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    /// <returns>True if the conversation exists</returns>
    public virtual async Task<bool> ConversationExistsAsync(
        string conversationId,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Checking if conversation '{0}' on agent '{1}' exists",
            conversationId.HtmlEncode(), this.Id.HtmlEncode());
        var conversation = await this.Storage.GetConversationAsync(conversationId, this.Id, cancellationToken).ConfigureAwait(false);
        return conversation != null;
    }

    /// <summary>
    /// Add a new participant to an existing conversation
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="participant">Participant information</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task AddParticipantAsync(
        string conversationId,
        Participant participant,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Adding participant to conversation '{0}' on agent '{1}'",
            conversationId.HtmlEncode(), this.Id.HtmlEncode());

        Conversation conversation = await this.Storage.GetConversationAsync(conversationId, this.Id, cancellationToken).ConfigureAwait(false)
                                    ?? new Conversation(conversationId, this.Id);

        conversation.AddParticipant(participant);
        await this.Storage.SaveConversationAsync(conversation, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Remove a participant from a conversation
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="participant">Participant information</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task RemoveParticipantAsync(
        string conversationId,
        Participant participant,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Removing participant from conversation '{0}' on agent '{1}'",
            conversationId.HtmlEncode(), this.Id.HtmlEncode());

        Conversation? conversation = await this.Storage.GetConversationAsync(conversationId, this.Id, cancellationToken).ConfigureAwait(false);
        if (conversation == null) { return; }

        conversation.RemoveParticipant(participant);
        await this.Storage.SaveConversationAsync(conversation, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Add a message (received from the backend) to a conversation
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="message">Message information</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task ReceiveMessageAsync(
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Received {0} chat message in conversation '{1}' with agent '{2}' from '{3}' '{4}'",
            message.ContentType.HtmlEncode(), conversationId.HtmlEncode(), this.Id.HtmlEncode(), message.Sender.Role.HtmlEncode(), message.Sender.Id.HtmlEncode());

        // Update the chat history to include the message received
        return this.AddMessageToHistoryAsync(conversationId, message, cancellationToken);
    }

    /// <summary>
    /// Receive a notice, a special type of message.
    /// A notice is a message type for sending short, one-line updates that persist in the chat history
    /// and are displayed differently from regular chat messages.
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="message">Message information</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task ReceiveNoticeAsync(
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Received {0} notice in conversation '{1}' with agent '{2}' from '{3}' '{4}': {5}",
            message.ContentType.HtmlEncode(), conversationId.HtmlEncode(), this.Id.HtmlEncode(), message.Sender.Role.HtmlEncode(), message.Sender.Id.HtmlEncode(), message.Content.HtmlEncode());

        return Task.CompletedTask;
    }

    /// <summary>
    /// Receive a note, a special type of message.
    /// A note is used to display additional information separately from the main conversation.
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="message">Message information</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task ReceiveNoteAsync(
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Received {0} note in conversation '{1}' with agent '{2}' from '{3}' '{4}': {5}",
            message.ContentType.HtmlEncode(), conversationId.HtmlEncode(), this.Id.HtmlEncode(), message.Sender.Role.HtmlEncode(), message.Sender.Id.HtmlEncode(), message.Content.HtmlEncode());

        return Task.CompletedTask;
    }

    /// <summary>
    /// Receive a command, a special type of message
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="command">Command information</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task ReceiveCommandAsync(
        string conversationId,
        Command command,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Received '{0}' command in conversation '{1}' with agent '{2}' from '{3}' '{4}': {5}",
            command.CommandName.HtmlEncode(), conversationId.HtmlEncode(), this.Id.HtmlEncode(), command.Sender.Role.HtmlEncode(), command.Sender.Id.HtmlEncode(), command.Content.HtmlEncode());

        return Task.CompletedTask;
    }

    /// <summary>
    /// Receive a command response, a special type of message
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="message">Message information</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual Task ReceiveCommandResponseAsync(
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Received {0} command response in conversation '{1}' with agent '{2}' from '{3}' '{4}': {5}",
            message.ContentType.HtmlEncode(), conversationId.HtmlEncode(), this.Id.HtmlEncode(), message.Sender.Role.HtmlEncode(), message.Sender.Id.HtmlEncode(), message.Content.HtmlEncode());

        return Task.CompletedTask;
    }

    /// <summary>
    /// Remove a message from a conversation
    /// </summary>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="message">Message information</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task DeleteMessageAsync(
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Deleting message in conversation '{0}' with agent '{1}', message from '{2}' '{3}'",
            conversationId.HtmlEncode(), this.Id.HtmlEncode(), message.Sender.Role.HtmlEncode(), message.Sender.Id.HtmlEncode());

        // return this.DeleteMessageFromHistoryAsync(conversationId, message, cancellationToken);
        Conversation? conversation = await this.Storage.GetConversationAsync(conversationId, this.Id, cancellationToken).ConfigureAwait(false);
        if (conversation == null) { return; }

        conversation.RemoveMessage(message);
        await this.Storage.SaveConversationAsync(conversation, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Add message to chat history
    /// </summary>
    /// <param name="conversationId">Conversation Id</param>
    /// <param name="message">Message content</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task<Conversation> AddMessageToHistoryAsync(
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        Conversation conversation = await this.Storage.GetConversationAsync(conversationId, this.Id, cancellationToken).ConfigureAwait(false)
                                    ?? new Conversation(conversationId, this.Id);

        conversation.AddMessage(message);
        await this.Storage.SaveConversationAsync(conversation, cancellationToken).ConfigureAwait(false);
        return conversation;
    }

    // Send a new message to a conversation, communicating with semantic workbench backend
    /// <summary>
    /// Send message to workbench backend
    /// </summary>
    /// <param name="conversationId">Conversation Id</param>
    /// <param name="message">Message content</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    protected virtual Task SendTextMessageAsync(
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        return this.WorkbenchConnector.SendMessageAsync(this.Id, conversationId, message, cancellationToken);
    }

    /// <summary>
    /// Send a status update to a conversation, communicating with semantic workbench backend
    /// </summary>
    /// <param name="conversationId">Conversation Id</param>
    /// <param name="content"></param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    protected virtual Task SetAgentStatusAsync(
        string conversationId,
        string content,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogWarning("Change agent '{0}' status in conversation '{1}'", this.Id.HtmlEncode(), conversationId.HtmlEncode());
        return this.WorkbenchConnector.SetAgentStatusAsync(this.Id, conversationId, content, cancellationToken);
    }

    /// <summary>
    /// Reset the agent status update in a conversation, communicating with semantic workbench backend
    /// </summary>
    /// <param name="conversationId">Conversation Id</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    protected virtual Task ResetAgentStatusAsync(
        string conversationId,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogWarning("Reset agent '{0}' status in conversation '{1}'", this.Id.HtmlEncode(), conversationId.HtmlEncode());
        return this.WorkbenchConnector.ResetAgentStatusAsync(this.Id, conversationId, cancellationToken);
    }
}


=== File: libraries/dotnet/WorkbenchConnector/AgentConfig/AgentConfigBase.cs ===
// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Reflection;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public abstract class AgentConfigBase
{
    public object ToWorkbenchFormat()
    {
        Dictionary<string, object> result = [];
        Dictionary<string, object> defs = [];
        Dictionary<string, object> properties = [];
        Dictionary<string, object> jsonSchema = [];
        Dictionary<string, object> uiSchema = [];

        foreach (var property in this.GetType().GetProperties())
        {
            var config = new Dictionary<string, object>();
            var attributes = property.GetCustomAttributes<AgentConfigPropertyAttribute>();
            foreach (var attribute in attributes)
            {
                config[attribute.Name] = attribute.Value;
            }

            properties[property.Name] = config;

            if (config.TryGetValue("uischema", out var uiSchemaValue))
            {
                switch (uiSchemaValue)
                {
                    case "textarea":
                        ConfigUtils.UseTextAreaFor(property.Name, uiSchema);
                        break;
                    case "radiobutton":
                        ConfigUtils.UseRadioButtonsFor(property.Name, uiSchema);
                        break;
                    default:
                        break;
                }
            }
        }

        jsonSchema["type"] = "object";
        jsonSchema["title"] = "ConfigStateModel";
        jsonSchema["additionalProperties"] = false;
        jsonSchema["properties"] = properties;
        jsonSchema["$defs"] = defs;

        result["json_schema"] = jsonSchema;
        result["ui_schema"] = uiSchema;
        result["config"] = this;

        return result;
    }
}


=== File: libraries/dotnet/WorkbenchConnector/AgentConfig/AgentConfigPropertyAttribute.cs ===
// Copyright (c) Microsoft. All rights reserved.

using System;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

[AttributeUsage(AttributeTargets.Property, AllowMultiple = true)]
public class AgentConfigPropertyAttribute : Attribute
{
    public string Name { get; }
    public object Value { get; }

    public AgentConfigPropertyAttribute(string name, object value)
    {
        this.Name = name;
        this.Value = value;
    }
}


=== File: libraries/dotnet/WorkbenchConnector/AgentConfig/ConfigUtils.cs ===
﻿// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public static class ConfigUtils
{
    // Use "text area" instead of default "input box"
    public static void UseTextAreaFor(string propertyName, Dictionary<string, object> uiSchema)
    {
        uiSchema[propertyName] = new Dictionary<string, object>
        {
            { "ui:widget", "textarea" }
        };
    }

    // Use "list of radio buttons" instead of default "select box"
    public static void UseRadioButtonsFor(string propertyName, Dictionary<string, object> uiSchema)
    {
        uiSchema[propertyName] = new Dictionary<string, object>
        {
            { "ui:widget", "radio" }
        };
    }
}


=== File: libraries/dotnet/WorkbenchConnector/Constants.cs ===
﻿// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticWorkbench.Connector;

public static class Constants
{
    // Unique service ID
    public const string HeaderServiceId = "X-Assistant-Service-ID";

    // Agent ID
    public const string HeaderAgentId = "X-Assistant-ID";

    // HTTP methods
    public static readonly HttpMethod[] HttpMethodsWithBody = [HttpMethod.Post, HttpMethod.Put, HttpMethod.Patch];

    // Registering the multi-agent service into the workbench connector
    public static class AgentServiceRegistration
    {
        public const string Placeholder = "{assistant_service_id}";
        public const string Path = "/assistant-service-registrations/{assistant_service_id}";
    }

    // Sending a message into an existing conversation
    public static class SendAgentMessage
    {
        public const string ConversationPlaceholder = "{conversation_id}";
        public const string Path = "/conversations/{conversation_id}/messages";
    }

    // Sending a temporary status to show inline in a conversation, before sending a message
    public static class SendAgentStatusMessage
    {
        public const string AgentPlaceholder = "{agent_id}";
        public const string ConversationPlaceholder = "{conversation_id}";
        public const string Path = "/conversations/{conversation_id}/participants/{agent_id}";
    }

    // Sending a notification about a state content change
    public static class SendAgentConversationInsightsEvent
    {
        public const string AgentPlaceholder = "{agent_id}";
        public const string ConversationPlaceholder = "{conversation_id}";
        public const string Path = "/assistants/{agent_id}/states/events?conversation_id={conversation_id}";
    }

    // Get list of files
    public static class GetConversationFiles
    {
        public const string ConversationPlaceholder = "{conversation_id}";
        public const string Path = "/conversations/{conversation_id}/files";
    }

    // Download/Delete file
    public static class ConversationFile
    {
        public const string ConversationPlaceholder = "{conversation_id}";
        public const string FileNamePlaceholder = "{filename}";
        public const string Path = "/conversations/{conversation_id}/files/{filename}";
    }

    // Upload file
    public static class UploadConversationFile
    {
        public const string ConversationPlaceholder = "{conversation_id}";
        public const string Path = "/conversations/{conversation_id}/files";
    }
}


=== File: libraries/dotnet/WorkbenchConnector/IAgentBase.cs ===
﻿// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticWorkbench.Connector;

public interface IAgentBase
{
    public string Id { get; }
    public AgentInfo ToDataModel();
}


=== File: libraries/dotnet/WorkbenchConnector/Models/Command.cs ===
﻿// Copyright (c) Microsoft. All rights reserved.

using System;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class Command : Message
{
    public string CommandName { get; set; }

    public string CommandParams { get; set; }

    public Command(Message message)
    {
        this.Id = message.Id;
        this.MessageType = message.MessageType;
        this.ContentType = message.ContentType;
        this.Content = message.Content;
        this.Timestamp = message.Timestamp;
        this.Sender = message.Sender;
        this.Metadata = message.Metadata;

        var p = this.Content?.Split(" ", 2, StringSplitOptions.TrimEntries);
        this.CommandName = p?.Length > 0 ? p[0].TrimStart('/') : "";
        this.CommandParams = p?.Length > 1 ? p[1] : "";
    }
}


=== File: libraries/dotnet/WorkbenchConnector/Models/Conversation.cs ===
﻿// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class Conversation
{
    [JsonPropertyName("id")]
    [JsonPropertyOrder(0)]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("agent_id")]
    [JsonPropertyOrder(1)]
    public string AgentId { get; set; } = string.Empty;

    [JsonPropertyName("participants")]
    [JsonPropertyOrder(2)]
    public Dictionary<string, Participant> Participants { get; set; } = [];

    [JsonPropertyName("messages")]
    [JsonPropertyOrder(3)]
    public List<Message> Messages { get; set; } = [];

    public Conversation()
    {
    }

    public Conversation(string id, string agentId)
    {
        this.Id = id;
        this.AgentId = agentId;
    }

    public void AddParticipant(Participant participant)
    {
        this.Participants[participant.Id] = participant;
    }

    public void RemoveParticipant(Participant participant)
    {
        this.Participants.Remove(participant.Id, out _);
    }

    public void AddMessage(Message? msg)
    {
        if (msg == null) { return; }

        this.Messages.Add(msg);
    }

    public void RemoveMessage(Message? msg)
    {
        if (msg == null) { return; }

        this.Messages = this.Messages.Where(x => x.Id != msg.Id).ToList();
    }
}


=== File: libraries/dotnet/WorkbenchConnector/Models/ConversationEvent.cs ===
﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class ConversationEvent
{
    public class EventData
    {
        [JsonPropertyName("participant")]
        public Participant Participant { get; set; } = new();

        [JsonPropertyName("message")]
        public Message Message { get; set; } = new();
    }

    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("conversation_id")]
    public string ConversationId { get; set; } = string.Empty;

    [JsonPropertyName("timestamp")]
    public DateTimeOffset Timestamp { get; set; } = DateTimeOffset.MinValue;

    [JsonPropertyName("data")]
    public EventData Data { get; set; } = new();
}


=== File: libraries/dotnet/WorkbenchConnector/Models/DebugInfo.cs ===
﻿// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class DebugInfo : Dictionary<string, object?>
{
    public DebugInfo()
    {
    }

    public DebugInfo(string key, object? info)
    {
        this.Add(key, info);
    }
}


=== File: libraries/dotnet/WorkbenchConnector/Models/Insight.cs ===
﻿// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

// TODO: Support states with UI
public class Insight
{
    [JsonPropertyName("id")]
    [JsonPropertyOrder(0)]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("display_name")]
    [JsonPropertyOrder(1)]
    public string DisplayName { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    [JsonPropertyOrder(2)]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("content")]
    [JsonPropertyOrder(3)]
    public string Content { get; set; } = string.Empty;

    public Insight()
    {
    }

    public Insight(string id, string displayName, string? content, string? description = "")
    {
        this.Id = id;
        this.DisplayName = displayName;
        this.Description = description ?? string.Empty;
        this.Content = content ?? string.Empty;
    }
}


=== File: libraries/dotnet/WorkbenchConnector/Models/Message.cs ===
// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class Message
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    // "notice" | "chat" | "note" | "command" | "command-response"
    [JsonPropertyName("message_type")]
    public string MessageType { get; set; } = string.Empty;

    // "text/plain"
    [JsonPropertyName("content_type")]
    public string ContentType { get; set; } = string.Empty;

    [JsonPropertyName("content")]
    public string? Content { get; set; } = string.Empty;

    [JsonPropertyName("timestamp")]
    public DateTimeOffset Timestamp { get; set; }

    [JsonPropertyName("sender")]
    public Sender Sender { get; set; } = new();

    [JsonPropertyName("metadata")]
    public MessageMetadata Metadata { get; set; } = new();

    /// <summary>
    /// Prepare a chat message instance
    /// <note>
    /// Content types:
    /// - text/plain
    /// - text/html
    /// - application/json (requires "json_schema" metadata)
    /// </note>
    /// </summary>
    /// <param name="agentId">Agent ID</param>
    /// <param name="content">Chat content</param>
    /// <param name="debug">Optional debugging data</param>
    /// <param name="contentType">Message content type</param>
    public static Message CreateChatMessage(
        string agentId,
        string content,
        object? debug = null,
        string contentType = "text/plain")
    {
        var result = new Message
        {
            Id = Guid.NewGuid().ToString("D"),
            Timestamp = DateTimeOffset.UtcNow,
            MessageType = "chat",
            ContentType = contentType,
            Content = content,
            Sender = new Sender
            {
                Role = "assistant",
                Id = agentId
            }
        };

        if (debug != null)
        {
            result.Metadata.Debug = debug;
        }

        return result;
    }

    public static Message CreateNotice(
        string agentId,
        string content,
        object? debug = null,
        string contentType = "text/plain")
    {
        var result = CreateChatMessage(agentId: agentId, content: content, debug: debug, contentType: contentType);
        result.MessageType = "notice";
        return result;
    }

    public static Message CreateNote(
        string agentId,
        string content,
        object? debug = null,
        string contentType = "text/plain")
    {
        var result = CreateChatMessage(agentId: agentId, content: content, debug: debug, contentType: contentType);
        result.MessageType = "note";
        return result;
    }

    public static Message CreateCommand(
        string agentId,
        string content,
        object? debug = null,
        string contentType = "text/plain")
    {
        var result = CreateChatMessage(agentId: agentId, content: content, debug: debug, contentType: contentType);
        result.MessageType = "command";
        return result;
    }

    public static Message CreateCommandResponse(
        string agentId,
        string content,
        object? debug = null,
        string contentType = "text/plain")
    {
        var result = CreateChatMessage(agentId: agentId, content: content, debug: debug, contentType: contentType);
        result.MessageType = "command-response";
        return result;
    }
}


=== File: libraries/dotnet/WorkbenchConnector/Models/MessageMetadata.cs ===
// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class MessageMetadata
{
    [JsonPropertyName("attribution")]
    public string Attribution { get; set; } = string.Empty;

    [JsonPropertyName("debug")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public object? Debug { get; set; } = null;
}


=== File: libraries/dotnet/WorkbenchConnector/Models/Participant.cs ===
﻿// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class Participant
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("role")]
    public string Role { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("active_participant")]
    public bool ActiveParticipant { get; set; } = false;

    [JsonPropertyName("online")]
    public bool? Online { get; set; } = null;
}


=== File: libraries/dotnet/WorkbenchConnector/Models/Sender.cs ===
// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class Sender
{
    [JsonPropertyName("participant_role")]
    public string Role { get; set; } = string.Empty;

    [JsonPropertyName("participant_id")]
    public string Id { get; set; } = string.Empty;
}


=== File: libraries/dotnet/WorkbenchConnector/Models/ServiceInfo.cs ===
﻿// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class ServiceInfo<TAgentConfig>(TAgentConfig cfg)
    where TAgentConfig : AgentConfigBase, new()
{
    [JsonPropertyName("assistant_service_id")]
    public string ServiceId { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    [JsonPropertyName("metadata")]
    public Dictionary<string, object> Metadata { get; set; } = [];

    [JsonPropertyName("default_config")]
    public object DefaultConfiguration => cfg.ToWorkbenchFormat() ?? new();
}


=== File: libraries/dotnet/WorkbenchConnector/Storage/AgentInfo.cs ===
﻿// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class AgentInfo
{
    [JsonPropertyName("id")]
    [JsonPropertyOrder(0)]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    [JsonPropertyOrder(1)]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("config")]
    [JsonPropertyOrder(2)]
    public object Config { get; set; } = null!;
}


=== File: libraries/dotnet/WorkbenchConnector/Storage/AgentServiceStorage.cs ===
﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public class AgentServiceStorage : IAgentServiceStorage
{
    private static readonly JsonSerializerOptions s_jsonOptions = new() { WriteIndented = true };

    private static readonly char[] s_notSafe =
    [
        '\0', '\n', '\r',
        Path.PathSeparator, // ':' (nix) or ';' (win)
        Path.DirectorySeparatorChar, // '/' (nix) or '\' (win)
        Path.VolumeSeparatorChar, // '/' (nix) or ':' (win)
        Path.AltDirectorySeparatorChar, // '/'
    ];

    private static readonly char[] s_notSafe2 = Path.GetInvalidPathChars();

    private readonly ILogger<AgentServiceStorage> _log;
    private readonly string _path;

    public AgentServiceStorage(
        IConfiguration appConfig,
        ILoggerFactory logFactory)
    {
        this._log = logFactory.CreateLogger<AgentServiceStorage>();

        var connectorId = appConfig.GetSection("Workbench").GetValue<string>("ConnectorId") ?? "undefined";
        var tmpPath = appConfig.GetSection("Workbench").GetValue<string>(
            RuntimeInformation.IsOSPlatform(OSPlatform.Windows)
                ? "StoragePathWindows"
                : "StoragePathLinux") ?? string.Empty;
        this._path = Path.Join(tmpPath, connectorId);

        if (this._path.Contains("$tmp", StringComparison.OrdinalIgnoreCase))
        {
            this._path = this._path.Replace("$tmp", Path.GetTempPath(), StringComparison.OrdinalIgnoreCase);
        }

        this._path = Path.Join(this._path, "agents");

        if (!Directory.Exists(this._path))
        {
            Directory.CreateDirectory(this._path);
        }
    }

    public Task SaveAgentAsync(IAgentBase agent, CancellationToken cancellationToken = default)
    {
        return File.WriteAllTextAsync(this.GetAgentFilename(agent), JsonSerializer.Serialize(agent.ToDataModel(), s_jsonOptions), cancellationToken);
    }

    public Task DeleteAgentAsync(IAgentBase agent, CancellationToken cancellationToken = default)
    {
        File.Delete(this.GetAgentFilename(agent)); // codeql [cs/path-injection]: safe
        return Task.CompletedTask;
    }

    public Task<List<AgentInfo>> GetAllAgentsAsync(CancellationToken cancellationToken = default)
    {
        return this.GetAllAsync<AgentInfo>("", ".agent.json", cancellationToken);
    }

    public Task SaveConversationAsync(Conversation conversation, CancellationToken cancellationToken = default)
    {
        var filename = this.GetConversationFilename(conversation);
        var json = JsonSerializer.Serialize(conversation, s_jsonOptions);
        return File.WriteAllTextAsync(filename, json, cancellationToken);
    }

    public async Task<Conversation?> GetConversationAsync(string conversationId, string agentId, CancellationToken cancellationToken = default)
    {
        var filename = this.GetConversationFilename(agentId: agentId, conversationId: conversationId);
        if (!File.Exists(filename)) { return null; }

        var content = await File.ReadAllTextAsync(filename, cancellationToken).ConfigureAwait(false);
        return JsonSerializer.Deserialize<Conversation>(content);
    }

    public async Task DeleteConversationAsync(string conversationId, string agentId, CancellationToken cancellationToken = default)
    {
        var filename = this.GetConversationFilename(agentId: agentId, conversationId: conversationId);
        File.Delete(filename); // codeql [cs/path-injection]: safe

        var insights = await this.GetAllInsightsAsync(agentId: agentId, conversationId: conversationId, cancellationToken).ConfigureAwait(false);
        foreach (Insight x in insights)
        {
            await this.DeleteInsightAsync(agentId: agentId, conversationId: conversationId, insightId: x.Id, cancellationToken: cancellationToken).ConfigureAwait(false);
        }
    }

    public Task DeleteConversationAsync(Conversation conversation, CancellationToken cancellationToken = default)
    {
        var filename = this.GetConversationFilename(conversation);
        File.Delete(filename); // codeql [cs/path-injection]: safe
        return Task.CompletedTask;
    }

    public Task<List<Insight>> GetAllInsightsAsync(string agentId, string conversationId, CancellationToken cancellationToken = default)
    {
        return this.GetAllAsync<Insight>($"{agentId}.{conversationId}.", ".insight.json", cancellationToken);
    }

    public Task SaveInsightAsync(string agentId, string conversationId, Insight insight, CancellationToken cancellationToken = default)
    {
        var filename = this.GetInsightFilename(agentId: agentId, conversationId: conversationId, insightId: insight.Id);
        return File.WriteAllTextAsync(filename, JsonSerializer.Serialize(insight, s_jsonOptions), cancellationToken);
    }

    public Task DeleteInsightAsync(string agentId, string conversationId, string insightId, CancellationToken cancellationToken = default)
    {
        var filename = this.GetInsightFilename(agentId: agentId, conversationId: conversationId, insightId: insightId);
        File.Delete(filename); // codeql [cs/path-injection]: safe
        return Task.CompletedTask;
    }

    private async Task<List<T>> GetAllAsync<T>(string prefix, string suffix, CancellationToken cancellationToken = default)
    {
        this._log.LogTrace("Searching all files with prefix '{0}' and suffix '{1}'",
            prefix.HtmlEncode(), suffix.HtmlEncode());

        var result = new List<T>();
        string[] fileEntries = Directory.GetFiles(this._path);
        foreach (string filePath in fileEntries)
        {
            var filename = Path.GetFileName(filePath);
            if (!filename.StartsWith(prefix, StringComparison.OrdinalIgnoreCase)) { continue; }

            if (!filename.EndsWith(suffix, StringComparison.OrdinalIgnoreCase)) { continue; }

            var content = await File.ReadAllTextAsync(filePath, cancellationToken).ConfigureAwait(false);
            if (string.IsNullOrEmpty(content)) { continue; }

            result.Add(JsonSerializer.Deserialize<T>(content)!);
        }

        this._log.LogTrace("Files found: {0}", result.Count);

        return result;
    }

    private string GetAgentFilename(IAgentBase agent)
    {
        EnsureSafe(agent.Id);
        return Path.Join(this._path, $"{agent.Id}.agent.json");
    }

    private string GetConversationFilename(Conversation conversation)
    {
        return this.GetConversationFilename(conversation.AgentId, conversation.Id);
    }

    private string GetConversationFilename(string agentId, string conversationId)
    {
        EnsureSafe(agentId);
        EnsureSafe(conversationId);
        return Path.Join(this._path, $"{agentId}.{conversationId}.conversation.json");
    }

    private string GetInsightFilename(string agentId, string conversationId, string insightId)
    {
        EnsureSafe(agentId);
        EnsureSafe(conversationId);
        EnsureSafe(insightId);
        return Path.Join(this._path, $"{agentId}.{conversationId}.{insightId}.insight.json");
    }

    private static void EnsureSafe(string input)
    {
        if (input.IndexOfAny(s_notSafe) < 0 && input.IndexOfAny(s_notSafe2) < 0) { return; }

        throw new ArgumentException("The file or path value contains invalid chars");
    }
}


=== File: libraries/dotnet/WorkbenchConnector/Storage/IAgentServiceStorage.cs ===
// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticWorkbench.Connector;

public interface IAgentServiceStorage
{
    Task SaveAgentAsync(IAgentBase agent, CancellationToken cancellationToken = default);
    Task DeleteAgentAsync(IAgentBase agent, CancellationToken cancellationToken = default);
    Task<List<AgentInfo>> GetAllAgentsAsync(CancellationToken cancellationToken = default);

    Task SaveConversationAsync(Conversation conversation, CancellationToken cancellationToken = default);
    Task<Conversation?> GetConversationAsync(string conversationId, string agentId, CancellationToken cancellationToken = default);
    Task DeleteConversationAsync(string conversationId, string agentId, CancellationToken cancellationToken = default);
    Task DeleteConversationAsync(Conversation conversation, CancellationToken cancellationToken = default);

    Task<List<Insight>> GetAllInsightsAsync(string agentId, string conversationId, CancellationToken cancellationToken = default);
    Task SaveInsightAsync(string agentId, string conversationId, Insight insight, CancellationToken cancellationToken = default);
    Task DeleteInsightAsync(string agentId, string conversationId, string insightId, CancellationToken cancellationToken = default);
}


=== File: libraries/dotnet/WorkbenchConnector/StringLoggingExtensions.cs ===
﻿// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Web;
using Microsoft.AspNetCore.Http;

namespace Microsoft.SemanticWorkbench.Connector;

public static class StringLoggingExtensions
{
    public static string HtmlEncode(this string? value)
    {
        return string.IsNullOrWhiteSpace(value)
            ? $"{value}"
            : HttpUtility.HtmlEncode(value);
    }

    public static string HtmlEncode(this PathString value)
    {
        return string.IsNullOrWhiteSpace(value)
            ? $"{value}"
            : HttpUtility.HtmlEncode(value);
    }

    public static string HtmlEncode(this StringBuilder value)
    {
        var s = value.ToString();
        return string.IsNullOrWhiteSpace(s)
            ? $"{s}"
            : HttpUtility.HtmlEncode(s);
    }

    public static string HtmlEncode(this object? value)
    {
        return value == null
            ? string.Empty
            : HttpUtility.HtmlEncode(value.ToString() ?? string.Empty);
    }
}


=== File: libraries/dotnet/WorkbenchConnector/Webservice.cs ===
﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Primitives;

namespace Microsoft.SemanticWorkbench.Connector;

public static class Webservice
{
    // Used for logging
    private sealed class SemanticWorkbenchWebservice
    {
    }

    public static WorkbenchConnector<TAgentConfig> UseAgentWebservice<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix, bool enableCatchAll = false)
        where TAgentConfig : AgentConfigBase, new()
    {
        WorkbenchConnector<TAgentConfig>? workbenchConnector = builder.ServiceProvider.GetService<WorkbenchConnector<TAgentConfig>>();
        if (workbenchConnector == null)
        {
            throw new InvalidOperationException("Unable to create instance of " + nameof(WorkbenchConnector<TAgentConfig>));
        }

        builder
            .UseFetchServiceInfo<TAgentConfig>(prefix)
            .UseCreateAgentEndpoint<TAgentConfig>(prefix)
            .UseDeleteAgentEndpoint<TAgentConfig>(prefix)
            .UseFetchAgentConfigEndpoint<TAgentConfig>(prefix)
            .UseSaveAgentConfigEndpoint<TAgentConfig>(prefix)
            .UseCreateConversationEndpoint<TAgentConfig>(prefix)
            .UseDeleteConversationEndpoint<TAgentConfig>(prefix)
            .UseFetchConversationStatesEndpoint<TAgentConfig>(prefix)
            .UseFetchConversationInsightEndpoint<TAgentConfig>(prefix)
            .UseCreateConversationEventEndpoint<TAgentConfig>(prefix);

        if (enableCatchAll)
        {
            builder.UseCatchAllEndpoint(prefix);
        }

        return workbenchConnector;
    }

    // Return service details and default agent configuration
    public static IEndpointRouteBuilder UseFetchServiceInfo<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapGet(prefix + "/", (
            [FromServicesAttribute] WorkbenchConnector<TAgentConfig> workbenchConnector,
            [FromServices] ILogger<SemanticWorkbenchWebservice> log) =>
        {
            var result = workbenchConnector.GetServiceInfo();
            return Results.Json(result);
        });

        return builder;
    }

    // Create new agent instance
    public static IEndpointRouteBuilder UseCreateAgentEndpoint<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapPut(prefix + "/{agentId}",
                async (
                    [FromRoute] string agentId,
                    [FromForm(Name = "assistant")] string data,
                    [FromServices] WorkbenchConnector<TAgentConfig> workbenchConnector,
                    [FromServices] ILogger<SemanticWorkbenchWebservice> log,
                    CancellationToken cancellationToken) =>
                {
                    string? name = agentId;
                    Dictionary<string, string>? settings = JsonSerializer.Deserialize<Dictionary<string, string>>(data);
                    settings?.TryGetValue("assistant_name", out name);

                    log.LogDebug("Received request to create/update agent instance '{0}', name '{1}'",
                        agentId.HtmlEncode(), name.HtmlEncode());

                    var agent = workbenchConnector.GetAgent(agentId);
                    if (agent == null)
                    {
                        await workbenchConnector.CreateAgentAsync(agentId, name, null, cancellationToken)
                            .ConfigureAwait(false);
                    }

                    return Results.Ok();
                })
            .DisableAntiforgery();

        return builder;
    }

    // Delete agent instance
    public static IEndpointRouteBuilder UseDeleteAgentEndpoint<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapDelete(prefix + "/{agentId}",
            async (
                [FromRoute] string agentId,
                [FromServices] WorkbenchConnector<TAgentConfig> workbenchConnector,
                [FromServices] ILogger<SemanticWorkbenchWebservice> log,
                CancellationToken cancellationToken) =>
            {
                log.LogDebug("Received request to deleting agent instance '{0}'", agentId.HtmlEncode());
                await workbenchConnector.DeleteAgentAsync(agentId, cancellationToken).ConfigureAwait(false);
                return Results.Ok();
            });

        return builder;
    }

    // Fetch agent configuration
    public static IEndpointRouteBuilder UseFetchAgentConfigEndpoint<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapGet(prefix + "/{agentId}/config",
            (
                [FromRoute] string agentId,
                [FromServices] WorkbenchConnector<TAgentConfig> workbenchConnector,
                [FromServices] ILogger<SemanticWorkbenchWebservice> log) =>
            {
                log.LogDebug("Received request to fetch agent '{0}' configuration", agentId.HtmlEncode());

                var agent = workbenchConnector.GetAgent(agentId);
                if (agent == null)
                {
                    return Results.NotFound("Agent Not Found");
                }

                return Results.Json(agent.Config.ToWorkbenchFormat());
            });

        return builder;
    }

    // Save agent configuration
    public static IEndpointRouteBuilder UseSaveAgentConfigEndpoint<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapPut(prefix + "/{agentId}/config",
                async (
                    [FromRoute] string agentId,
                    [FromBody] Dictionary<string, object> data,
                    [FromServices] WorkbenchConnector<TAgentConfig> workbenchConnector,
                    [FromServices] ILogger<SemanticWorkbenchWebservice> log,
                    CancellationToken cancellationToken) =>
                {
                    log.LogDebug("Received request to update agent '{0}' configuration", agentId.HtmlEncode());

                    var agent = workbenchConnector.GetAgent(agentId);
                    if (agent == null) { return Results.NotFound("Agent Not Found"); }

                    var config = agent.ParseConfig(data["config"]);
                    AgentConfigBase newConfig =
                        await agent.UpdateAgentConfigAsync(config, cancellationToken).ConfigureAwait(false);

                    var tmp = workbenchConnector.GetAgent(agentId);

                    return Results.Json(newConfig.ToWorkbenchFormat());
                })
            .DisableAntiforgery();

        return builder;
    }

    // Create new conversation
    private static IEndpointRouteBuilder UseCreateConversationEndpoint<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapPut(prefix + "/{agentId}/conversations/{conversationId}",
                async (
                    [FromRoute] string agentId,
                    [FromRoute] string conversationId,
                    [FromForm(Name = "conversation")] string data, // e.g. conversation={"id":"34460523-d2be-4388-837d-bda92282ffde"}
                    [FromServices] WorkbenchConnector<TAgentConfig> workbenchConnector,
                    [FromServices] ILogger<SemanticWorkbenchWebservice> log,
                    CancellationToken cancellationToken) =>
                {
                    log.LogDebug("Received request to create conversation '{0}' on agent '{1}'",
                        conversationId.HtmlEncode(), agentId.HtmlEncode());

                    var agent = workbenchConnector.GetAgent(agentId);
                    if (agent == null) { return Results.NotFound("Agent Not Found"); }

                    await agent.CreateConversationAsync(conversationId, cancellationToken).ConfigureAwait(false);
                    return Results.Ok();
                })
            .DisableAntiforgery();

        return builder;
    }

    // Fetch conversation states
    public static IEndpointRouteBuilder UseFetchConversationStatesEndpoint<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapGet(prefix + "/{agentId}/conversations/{conversationId}/states",
            async (
                [FromRoute] string agentId,
                [FromRoute] string conversationId,
                [FromServices] WorkbenchConnector<TAgentConfig> workbenchConnector,
                [FromServices] ILogger<SemanticWorkbenchWebservice> log,
                CancellationToken cancellationToken) =>
            {
                log.LogDebug("Received request to fetch agent '{0}' conversation '{1}' states",
                    agentId.HtmlEncode(), conversationId.HtmlEncode());

                var agent = workbenchConnector.GetAgent(agentId);
                if (agent == null) { return Results.NotFound("Conversation Not Found"); }

                if (!await agent.ConversationExistsAsync(conversationId, cancellationToken).ConfigureAwait(false))
                {
                    return Results.NotFound("Conversation Not Found");
                }

                List<Insight> states = await agent.GetConversationInsightsAsync(conversationId, cancellationToken).ConfigureAwait(false);

                if (states.Count == 0)
                {
                    // Special case required by UI bug
                    var result = new
                    {
                        states = new[]
                        {
                            new Insight
                            {
                                Id = "__none",
                                DisplayName = "Assistant Info",
                                Description = $"""
                                               Agent ID: **{agent.Id}**

                                               Name: **{agent.Name}**

                                               Config: **{agent.Config}**
                                               end of description
                                               """,
                                Content = $"""
                                           Agent ID: **{agent.Id}**

                                           Name: **{agent.Name}**

                                           Config: **{agent.Config}**
                                           end of content
                                           """
                            }
                        }
                    };
                    return Results.Json(result);
                }
                else
                {
                    var result = new
                    {
                        states = states.Select(x => new Insight { Id = x.Id, DisplayName = x.DisplayName, Description = x.Description })
                    };
                    return Results.Json(result);
                }
            });

        return builder;
    }

    // Fetch conversation states
    public static IEndpointRouteBuilder UseFetchConversationInsightEndpoint<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapGet(prefix + "/{agentId}/conversations/{conversationId}/states/{insightId}",
            async (
                [FromRoute] string agentId,
                [FromRoute] string conversationId,
                [FromRoute] string insightId,
                [FromServices] WorkbenchConnector<TAgentConfig> workbenchConnector,
                [FromServices] ILogger<SemanticWorkbenchWebservice> log,
                CancellationToken cancellationToken) =>
            {
                log.LogDebug("Received request to fetch agent '{0}' conversation '{1}' insight '{2}'",
                    agentId.HtmlEncode(), conversationId.HtmlEncode(), insightId.HtmlEncode());

                var agent = workbenchConnector.GetAgent(agentId);
                if (agent == null) { return Results.NotFound("Agent Not Found"); }

                if (!await agent.ConversationExistsAsync(conversationId, cancellationToken).ConfigureAwait(false))
                {
                    return Results.NotFound("Conversation Not Found");
                }

                var insights = await agent.GetConversationInsightsAsync(conversationId, cancellationToken).ConfigureAwait(false);
                Insight? insight = insights.FirstOrDefault(x => x.Id == insightId);

                if (insight == null)
                {
                    // Special case required by UI bug
                    if (insightId == "__none")
                    {
                        return Results.Json(new
                        {
                            id = insightId,
                            data = new { content = string.Empty },
                            json_schema = (object)null!,
                            ui_schema = (object)null!
                        });
                    }

                    return Results.NotFound($"State '{insightId}' Not Found");
                }

                // TODO: support schemas
                var result = new
                {
                    id = insightId,
                    data = new
                    {
                        content = insight.Content
                    },
                    json_schema = (object)null!,
                    ui_schema = (object)null!
                };

                return Results.Json(result);
            });

        return builder;
    }

    // New conversation event
    private static IEndpointRouteBuilder UseCreateConversationEventEndpoint<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapPost(prefix + "/{agentId}/conversations/{conversationId}/events",
                async (
                    [FromRoute] string agentId,
                    [FromRoute] string conversationId,
                    [FromBody] Dictionary<string, object>? data,
                    [FromServices] WorkbenchConnector<TAgentConfig> workbenchConnector,
                    [FromServices] ILogger<SemanticWorkbenchWebservice> log,
                    CancellationToken cancellationToken) =>
                {
                    log.LogDebug("Received request to process new event for agent '{0}' on conversation '{1}'",
                        agentId.HtmlEncode(), conversationId.HtmlEncode());

                    if (data == null || !data.TryGetValue("event", out object? eventType))
                    {
                        log.LogError("Event payload doesn't contain an 'event' property");
                        return Results.BadRequest("Event payload doesn't contain an 'event' property");
                    }

                    var agent = workbenchConnector.GetAgent(agentId);
                    if (agent == null) { return Results.NotFound("Agent Not Found"); }

                    if (!await agent.ConversationExistsAsync(conversationId, cancellationToken).ConfigureAwait(false))
                    {
                        return Results.NotFound("Conversation Not Found");
                    }

                    var json = JsonSerializer.Serialize(data);
                    log.LogDebug("Agent '{0}', conversation '{1}', Event '{2}'",
                        agentId.HtmlEncode(), conversationId.HtmlEncode(), eventType.HtmlEncode());
                    switch (eventType.ToString())
                    {
                        case "participant.created":
                        {
                            var x = JsonSerializer.Deserialize<ConversationEvent>(json);
                            if (x?.Data.Participant == null) { break; }

                            await agent.AddParticipantAsync(conversationId, x.Data.Participant, cancellationToken).ConfigureAwait(false);
                            break;
                        }

                        case "participant.updated":
                        {
                            var x = JsonSerializer.Deserialize<ConversationEvent>(json);
                            if (x?.Data.Participant == null) { break; }

                            if (x is { Data.Participant.ActiveParticipant: false })
                            {
                                await agent.RemoveParticipantAsync(conversationId, x.Data.Participant, cancellationToken).ConfigureAwait(false);
                            }

                            break;
                        }

                        case "message.created":
                        {
                            var x = JsonSerializer.Deserialize<ConversationEvent>(json);
                            if (x == null) { break; }

                            // Ignore messages sent from the agent itself
                            var message = x.Data.Message;
                            if (message.Sender.Role == "assistant" && message.Sender.Id == agentId) { break; }

                            // Ignore empty messages
                            if (string.IsNullOrWhiteSpace(message.Content)) { break; }

                            switch (message.MessageType)
                            {
                                case "chat":
                                    await agent.ReceiveMessageAsync(conversationId, message, cancellationToken).ConfigureAwait(false);
                                    break;

                                case "notice":
                                    await agent.ReceiveNoticeAsync(conversationId, message, cancellationToken).ConfigureAwait(false);
                                    break;

                                case "note":
                                    await agent.ReceiveNoteAsync(conversationId, message, cancellationToken).ConfigureAwait(false);
                                    break;

                                case "command":
                                    var command = new Command(message);
                                    await agent.ReceiveCommandAsync(conversationId, command, cancellationToken).ConfigureAwait(false);
                                    break;

                                case "command-response":
                                    await agent.ReceiveCommandResponseAsync(conversationId, message, cancellationToken).ConfigureAwait(false);
                                    break;

                                default:
                                    log.LogInformation("{0}: {1}", message.MessageType.HtmlEncode(),
                                        message.Content.HtmlEncode());
                                    log.LogWarning("Agent '{0}', conversation '{1}', Message type '{2}' ignored",
                                        agentId.HtmlEncode(), conversationId.HtmlEncode(),
                                        message.MessageType.HtmlEncode());
                                    break;
                            }

                            break;
                        }

                        case "message.deleted":
                        {
                            var x = JsonSerializer.Deserialize<ConversationEvent>(json);
                            if (x == null) { break; }

                            await agent.DeleteMessageAsync(conversationId, x.Data.Message, cancellationToken).ConfigureAwait(false);
                            break;
                        }

                        case "assistant.state.created": // TODO
                        case "assistant.state.updated": // TODO
                        case "file.created": // TODO
                        case "file.deleted": // TODO
                            /*
                            {
                               "event":            "assistant.state.created",
                                "id":              "ded0986ca0824e109e5bad8593b5fb1f",
                                "correlation_id":  "4358b84cffec4255b41be26fbf6d7829",
                                "conversation_id": "d7896b39-ad3f-4a10-a595-a7e47f6735b0",
                                "timestamp":       "2024-01-12T23:08:05.689296",
                                "data": {
                                    "assistant_id":    "69b841ff-909c-4fd7-b364-f5f962d5f021",
                                    "state_id":        "state01",
                                    "conversation_id": "d7896b39-ad3f-4a10-a595-a7e47f6735b0"
                                }
                            }

                           {
                                "event":           "assistant.state.updated",
                                "id":              "9ea3f9e2923045599f3ecfdbb07713b2",
                                "correlation_id":  "26c74d31a35b4a2aa301720af2615196",
                                "conversation_id": "483f6253-b5e1-478a-ac9e-4d1a58499c9d",
                                "timestamp":       "2024-11-26T19:01:54.446203Z",
                                "data": {
                                    "assistant_id": "9e58298d-dbe4-4ed3-bfdf-422d1c275de4",
                                    "state_id": "history",
                                    "conversation_id": "483f6253-b5e1-478a-ac9e-4d1a58499c9d"
                                }
                           }

                           {
                                "event":           "file.created",
                                "id":              "9b7ba8b35699482bbe368023796a978d",
                                "correlation_id":  "40877ed10f104090a9996fbe9dd6d716",
                                "conversation_id": "7f8c72a3-dd19-44ef-b86c-dbe712a538df",
                                "timestamp":       "2024-01-12T10:51:16.847854",
                                "data":
                                {
                                    "file":
                                    {
                                        "conversation_id":  "7f8c72a3-dd19-44ef-b86c-dbe712a538df",
                                        "created_datetime": "2024-01-12T10:51:16.845539Z",
                                        "updated_datetime": "2024-01-12T10:51:16.846093Z",
                                        "filename":         "LICENSE",
                                        "current_version":  1,
                                        "content_type":     "application/octet-stream",
                                        "file_size":        1141,
                                        "participant_id":   "72f988bf-86f1-41af-91ab-2d7cd011db47.37348b50-e200-4d93-9602-f1344b1f3cde",
                                        "participant_role": "user",
                                        "metadata": {}
                                    }
                                }
                            }

                            {
                                "event":           "file.deleted",
                                "id":              "75a3c347d7a644708548065098fa1b0b",
                                "correlation_id":  "7e2aa0f64dc140dbb82a68c50c2f3461",
                                "conversation_id": "7f8c72a3-dd19-44ef-b86c-dbe712a538df",
                                "timestamp":       "2024-07-28T10:55:51.257584",
                                "data": {
                                    "file": {
                                        "conversation_id":  "7f8c72a3-dd19-44ef-b86c-dbe712a538df",
                                        "created_datetime": "2024-07-28T10:51:16.845539",
                                        "updated_datetime": "2024-07-28T10:51:16.846093",
                                        "filename":         "LICENSE",
                                        "current_version":  1,
                                        "content_type":     "application/octet-stream",
                                        "file_size":        1141,
                                        "participant_id":   "72f988bf-86f1-41af-91ab-2d7cd011db47.37348b50-e200-4d93-9602-f1344b1f3cde",
                                        "participant_role": "user",
                                        "metadata": {}
                                    }
                                }
                            }
                            */
                            log.LogInformation("Event type '{0}' not supported [TODO]", eventType.HtmlEncode());
                            break;

                        default:
                            log.LogWarning("Unknown event type '{0}' not supported", eventType.HtmlEncode());
                            log.LogTrace(json);
                            break;
                    }

                    return Results.Ok();
                })
            .DisableAntiforgery();

        return builder;
    }

    // Delete conversation
    public static IEndpointRouteBuilder UseDeleteConversationEndpoint<TAgentConfig>(
        this IEndpointRouteBuilder builder, string prefix)
        where TAgentConfig : AgentConfigBase, new()
    {
        builder.MapDelete(prefix + "/{agentId}/conversations/{conversationId}",
            async (
                [FromRoute] string agentId,
                [FromRoute] string conversationId,
                [FromServices] WorkbenchConnector<TAgentConfig> workbenchConnector,
                [FromServices] ILogger<SemanticWorkbenchWebservice> log,
                CancellationToken cancellationToken) =>
            {
                log.LogDebug("Received request to delete conversation '{0}' on agent instance '{1}'",
                    conversationId.HtmlEncode(), agentId.HtmlEncode());

                var agent = workbenchConnector.GetAgent(agentId);
                if (agent == null) { return Results.Ok(); }

                await agent.DeleteConversationAsync(conversationId, cancellationToken).ConfigureAwait(false);

                return Results.Ok();
            });

        return builder;
    }

    // Catch all endpoint
    private static IEndpointRouteBuilder UseCatchAllEndpoint(
        this IEndpointRouteBuilder builder, string prefix)
    {
        builder.Map(prefix + "/{*catchAll}", async (
            HttpContext context,
            ILogger<SemanticWorkbenchWebservice> log) =>
        {
            context.Request.EnableBuffering();

            // Read headers
            StringBuilder headersStringBuilder = new();
            foreach (KeyValuePair<string, StringValues> header in context.Request.Headers)
            {
                headersStringBuilder.AppendLine(CultureInfo.InvariantCulture, $"{header.Key}: {header.Value}");
            }

            // Read body
            using StreamReader reader = new(context.Request.Body, leaveOpen: true);
            string requestBody = await reader.ReadToEndAsync().ConfigureAwait(false);
            context.Request.Body.Position = 0;

            log.LogWarning("Unknown request: {0} Path: {1}", context.Request.Method, context.Request.Path.HtmlEncode());

            string? query = context.Request.QueryString.Value;
            if (!string.IsNullOrEmpty(query)) { log.LogDebug("Query: {0}", context.Request.QueryString.Value.HtmlEncode()); }

            log.LogDebug("Headers: {0}", headersStringBuilder.HtmlEncode());
            log.LogDebug("Body: {0}", requestBody.HtmlEncode());

            return Results.NotFound("Request not supported");
        });

        return builder;
    }
}


=== File: libraries/dotnet/WorkbenchConnector/WorkbenchConfig.cs ===
﻿// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticWorkbench.Connector;

public class WorkbenchConfig
{
    /// <summary>
    /// Semantic Workbench endpoint.
    /// </summary>
    public string WorkbenchEndpoint { get; set; } = "http://127.0.0.1:3000";

    /// <summary>
    /// The host where the connector receives requests sent by the workbench.
    /// Locally, this is usually "http://127.0.0.1:[some port]"
    /// On Azure, this will be something like "https://contoso.azurewebsites.net"
    /// Leave this setting empty to use "127.0.0.1" and autodetect the port in use.
    /// You can use an env var to set this value, e.g. Workbench__ConnectorHost=https://contoso.azurewebsites.net
    /// </summary>
    public string ConnectorHost { get; set; } = string.Empty;

    /// <summary>
    /// This is the prefix of all the endpoints exposed by the connector
    /// </summary>
    public string ConnectorApiPrefix { get; set; } = "/myagents";

    /// <summary>
    /// Unique ID of the service. Semantic Workbench will store this event to identify the server
    /// so you should keep the value fixed to match the conversations tracked across service restarts.
    /// </summary>
    public string ConnectorId { get; set; } = Guid.NewGuid().ToString("D");

    /// <summary>
    /// Name of your agent service
    /// </summary>
    public string ConnectorName { get; set; } = ".NET Multi Agent Service";

    /// <summary>
    /// Description of your agent service.
    /// </summary>
    public string ConnectorDescription { get; set; } = "Multi-agent service for .NET agents";
}


=== File: libraries/dotnet/WorkbenchConnector/WorkbenchConnector.cs ===
﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Hosting.Server;
using Microsoft.AspNetCore.Hosting.Server.Features;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticWorkbench.Connector;

public abstract class WorkbenchConnector<TAgentConfig> : IDisposable
    where TAgentConfig : AgentConfigBase, new()
{
    protected IAgentServiceStorage Storage { get; private set; }
    protected WorkbenchConfig WorkbenchConfig { get; private set; }
    protected TAgentConfig DefaultAgentConfig { get; private set; }
    protected HttpClient HttpClient { get; private set; }
    protected string ConnectorEndpoint { get; private set; } = string.Empty;
    protected ILogger Log { get; private set; }
    protected Dictionary<string, AgentBase<TAgentConfig>> Agents { get; private set; }

    private Timer? _initTimer;
    private Timer? _pingTimer;

    private readonly IServer _httpServer;

    protected WorkbenchConnector(
        WorkbenchConfig? workbenchConfig,
        TAgentConfig? defaultAgentConfig,
        IAgentServiceStorage storage,
        IServer httpServer,
        ILogger logger)
    {
        this._httpServer = httpServer;
        this.WorkbenchConfig = workbenchConfig ?? new();
        this.DefaultAgentConfig = defaultAgentConfig ?? new();

        this.Log = logger;
        this.Storage = storage;
        this.HttpClient = new HttpClient
        {
            BaseAddress = new Uri(this.WorkbenchConfig.WorkbenchEndpoint)
        };
        this.Agents = [];

        this.Log.LogTrace("Service instance created");
    }

    /// <summary>
    /// Get service details and default agent configuration
    /// </summary>
    public virtual ServiceInfo<TAgentConfig> GetServiceInfo()
    {
        return new ServiceInfo<TAgentConfig>(this.DefaultAgentConfig)
        {
            ServiceId = this.WorkbenchConfig.ConnectorId,
            Name = this.WorkbenchConfig.ConnectorName,
            Description = this.WorkbenchConfig.ConnectorDescription,
        };
    }

    /// <summary>
    /// Connect the agent service to workbench backend
    /// </summary>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task ConnectAsync(CancellationToken cancellationToken = default)
    {
        this.Log.LogInformation("Connecting {ConnectorName} {ConnectorId} to {WorkbenchEndpoint}...",
            this.WorkbenchConfig.ConnectorName, this.WorkbenchConfig.ConnectorId, this.WorkbenchConfig.WorkbenchEndpoint);
#pragma warning disable CS4014 // ping runs in the background without blocking
        this._initTimer ??= new Timer(_ => this.Init(), null, 0, 500);
        this._pingTimer ??= new Timer(_ => this.PingSemanticWorkbenchBackendAsync(cancellationToken), null, Timeout.Infinite, Timeout.Infinite);
#pragma warning restore CS4014

        List<AgentInfo> agents = await this.Storage.GetAllAgentsAsync(cancellationToken).ConfigureAwait(false);
        this.Log.LogInformation("Starting {0} agents", agents.Count);
        foreach (var agent in agents)
        {
            await this.CreateAgentAsync(agent.Id, agent.Name, agent.Config, cancellationToken).ConfigureAwait(false);
        }
    }

    /// <summary>
    /// Disconnect the agent service from the workbench backend
    /// </summary>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task DisconnectAsync(CancellationToken cancellationToken = default)
    {
        this.Log.LogInformation("Disconnecting {1} {2} ...", this.WorkbenchConfig.ConnectorName, this.WorkbenchConfig.ConnectorId);
        if (this._pingTimer != null)
        {
            await this._pingTimer.DisposeAsync().ConfigureAwait(false);
        }

        this._pingTimer = null;
    }

    /// <summary>
    /// Create a new agent instance
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="name">Agent name</param>
    /// <param name="configData">Configuration content</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public abstract Task CreateAgentAsync(
        string agentId,
        string? name,
        object? configData,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Get agent with the given ID
    /// </summary>
    /// <param name="agentId">Agent ID</param>
    /// <returns>Agent instance</returns>
    public virtual AgentBase<TAgentConfig>? GetAgent(string agentId)
    {
        return this.Agents.GetValueOrDefault(agentId);
    }

    /// <summary>
    /// Delete an agent instance
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task DeleteAgentAsync(
        string agentId,
        CancellationToken cancellationToken = default)
    {
        var agent = this.GetAgent(agentId);
        if (agent == null) { return; }

        this.Log.LogInformation("Deleting agent '{0}'", agentId.HtmlEncode());
        await agent.StopAsync(cancellationToken).ConfigureAwait(false);
        this.Agents.Remove(agentId);
        await agent.StopAsync(cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Set a state content, visible in the state inspector.
    /// The content is visible in the state inspector, on the right side panel.
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="insight">Insight content. Markdown and HTML are supported.</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task UpdateAgentConversationInsightAsync(
        string agentId,
        string conversationId,
        Insight insight,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Updating agent '{0}' '{1}' insight", agentId.HtmlEncode(), insight.Id.HtmlEncode());

        var data = new
        {
            state_id = insight.Id,
            @event = "updated",
            state = new
            {
                id = insight.Id,
                data = new
                {
                    content = insight.Content
                },
                json_schema = new { },
                ui_schema = new { }
            }
        };

        string url = Constants.SendAgentConversationInsightsEvent.Path
            .Replace(Constants.SendAgentConversationInsightsEvent.AgentPlaceholder, agentId, StringComparison.OrdinalIgnoreCase)
            .Replace(Constants.SendAgentConversationInsightsEvent.ConversationPlaceholder, conversationId, StringComparison.OrdinalIgnoreCase);

        await this.SendAsync(HttpMethod.Post, url, data, agentId, "UpdateAgentConversationInsight", cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Set a temporary agent status within a conversation.
    /// The status is shown inline in the conversation, as a temporary brief message.
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="status">Short status description</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task SetAgentStatusAsync(
        string agentId,
        string conversationId,
        string status,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Setting agent status in conversation '{0}' with agent '{1}'",
            conversationId.HtmlEncode(), agentId.HtmlEncode());

        var data = new
        {
            status = status,
            active_participant = true
        };

        string url = Constants.SendAgentStatusMessage.Path
            .Replace(Constants.SendAgentStatusMessage.ConversationPlaceholder, conversationId, StringComparison.OrdinalIgnoreCase)
            .Replace(Constants.SendAgentStatusMessage.AgentPlaceholder, agentId, StringComparison.OrdinalIgnoreCase);

        await this.SendAsync(HttpMethod.Put, url, data, agentId, $"SetAgentStatus[{status}]", cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Reset the temporary agent status within a conversation
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task ResetAgentStatusAsync(
        string agentId,
        string conversationId,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Setting agent status in conversation '{0}' with agent '{1}'",
            conversationId.HtmlEncode(), agentId.HtmlEncode());

        const string Payload = """
                               {
                                 "status": null,
                                 "active_participant": true
                               }
                               """;

        var data = JsonSerializer.Deserialize<object>(Payload);

        string url = Constants.SendAgentStatusMessage.Path
            .Replace(Constants.SendAgentStatusMessage.ConversationPlaceholder, conversationId, StringComparison.OrdinalIgnoreCase)
            .Replace(Constants.SendAgentStatusMessage.AgentPlaceholder, agentId, StringComparison.OrdinalIgnoreCase);

        await this.SendAsync(HttpMethod.Put, url, data!, agentId, "ResetAgentStatus", cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Send a message from an agent to a conversation
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="message">Message content</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task SendMessageAsync(
        string agentId,
        string conversationId,
        Message message,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Sending message in conversation '{0}' with agent '{1}'",
            conversationId.HtmlEncode(), agentId.HtmlEncode());

        string url = Constants.SendAgentMessage.Path
            .Replace(Constants.SendAgentMessage.ConversationPlaceholder, conversationId, StringComparison.OrdinalIgnoreCase);

        await this.SendAsync(HttpMethod.Post, url, message, agentId, "SendMessage", cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Get list of files. TODO.
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task GetFilesAsync(
        string agentId,
        string conversationId,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Fetching list of files in conversation '{0}'", conversationId.HtmlEncode());

        string url = Constants.GetConversationFiles.Path
            .Replace(Constants.GetConversationFiles.ConversationPlaceholder, conversationId, StringComparison.OrdinalIgnoreCase);

        HttpResponseMessage result = await this.SendAsync(HttpMethod.Get, url, null, agentId, "GetFiles", cancellationToken).ConfigureAwait(false);

        // TODO: parse response and return list

        /*
        {
            "files": [
                {
                    "conversation_id": "7f8c72a3-dd19-44ef-b86c-dbe712a538df",
                    "created_datetime": "2024-01-12T11:04:38.923626",
                    "updated_datetime": "2024-01-12T11:04:38.923789",
                    "filename": "LICENSE",
                    "current_version": 1,
                    "content_type": "application/octet-stream",
                    "file_size": 1141,
                    "participant_id": "72f988bf-86f1-41af-91ab-2d7cd011db47.37348b50-e200-4d93-9602-f1344b1f3cde",
                    "participant_role": "user",
                    "metadata": {}
                }
            ]
        }
        */
    }

    /// <summary>
    /// Download file. TODO.
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="fileName">File name</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task DownloadFileAsync(
        string agentId,
        string conversationId,
        string fileName,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Downloading file from conversation '{0}'", conversationId.HtmlEncode());

        string url = Constants.ConversationFile.Path
            .Replace(Constants.ConversationFile.ConversationPlaceholder, conversationId, StringComparison.OrdinalIgnoreCase)
            .Replace(Constants.ConversationFile.FileNamePlaceholder, fileName, StringComparison.OrdinalIgnoreCase);

        HttpResponseMessage result = await this.SendAsync(HttpMethod.Get, url, null, agentId, "DownloadFile", cancellationToken).ConfigureAwait(false);

        // TODO: parse response and return file

        /*
        < HTTP/1.1 200 OK
        < date: Fri, 12 Jan 2024 11:12:23 GMT
        < content-disposition: attachment; filename="LICENSE"
        < content-type: application/octet-stream
        < transfer-encoding: chunked
        <
        ...
         */
    }

    /// <summary>
    /// Upload a file. TODO.
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="fileName">File name</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task UploadFileAsync(
        string agentId,
        string conversationId,
        string fileName,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Deleting file {0} from a conversation '{1}'", fileName.HtmlEncode(), conversationId.HtmlEncode());

        string url = Constants.UploadConversationFile.Path
            .Replace(Constants.UploadConversationFile.ConversationPlaceholder, conversationId, StringComparison.OrdinalIgnoreCase);

        // TODO: include file using multipart/form-data

        await this.SendAsync(HttpMethod.Put, url, null, agentId, "UploadFile", cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Delete a file
    /// </summary>
    /// <param name="agentId">Agent instance ID</param>
    /// <param name="conversationId">Conversation ID</param>
    /// <param name="fileName">File name</param>
    /// <param name="cancellationToken">Async task cancellation token</param>
    public virtual async Task DeleteFileAsync(
        string agentId,
        string conversationId,
        string fileName,
        CancellationToken cancellationToken = default)
    {
        this.Log.LogDebug("Deleting file {0} from a conversation '{1}'", fileName.HtmlEncode(), conversationId.HtmlEncode());

        string url = Constants.ConversationFile.Path
            .Replace(Constants.ConversationFile.ConversationPlaceholder, conversationId, StringComparison.OrdinalIgnoreCase)
            .Replace(Constants.ConversationFile.FileNamePlaceholder, fileName, StringComparison.OrdinalIgnoreCase);

        await this.SendAsync(HttpMethod.Delete, url, null, agentId, "DeleteFile", cancellationToken).ConfigureAwait(false);
    }

    public virtual void DisablePingTimer()
    {
        this._pingTimer?.Change(Timeout.Infinite, Timeout.Infinite);
    }

    public virtual void DisableInitTimer()
    {
        this._initTimer?.Change(Timeout.Infinite, Timeout.Infinite);
    }

    public virtual void EnablePingTimer()
    {
        this._pingTimer?.Change(TimeSpan.FromMilliseconds(PingFrequencyMsecs), TimeSpan.FromMilliseconds(PingFrequencyMsecs));
    }

    public virtual void EnableInitTimer()
    {
        this._initTimer?.Change(TimeSpan.FromMilliseconds(500), TimeSpan.FromMilliseconds(500));
    }

    /// <summary>
    /// Detect the port where the connector is listening and define the value of this.ConnectorEndpoint
    /// which is then passed to the workbench backend for incoming connections.
    /// </summary>
    public virtual void Init()
    {
        this.DisableInitTimer();

        this.Log.LogTrace("Initialization in progress...");

        // If the connector endpoint is ready (to be passed to workbench backend)
        if (!string.IsNullOrWhiteSpace(this.ConnectorEndpoint))
        {
            this.Log.LogTrace("Initialization complete, connector endpoint: {Endpoint}", this.ConnectorEndpoint);
            this.EnablePingTimer();
            return;
        }

        // If the connector host is set via configuration, rather than autodetected
        if (!string.IsNullOrWhiteSpace(this.WorkbenchConfig.ConnectorHost))
        {
            this.ConnectorEndpoint = $"{this.WorkbenchConfig.ConnectorHost.TrimEnd('/')}/{this.WorkbenchConfig.ConnectorApiPrefix.TrimStart('/')}";
            this.Log.LogTrace("Initialization complete, connector endpoint: {Endpoint}", this.ConnectorEndpoint);
            this.EnablePingTimer();
            return;
        }

        // Autodetect the port in use and define the connector endpoint
        try
        {
            IServerAddressesFeature? feat = this._httpServer.Features.Get<IServerAddressesFeature>();
            if (feat == null || feat.Addresses.Count == 0)
            {
                this.EnableInitTimer();
                return;
            }

            // Example: http://[::]:64351 - Prefer non-HTTPS to avoid cert validation errors
            string first = feat.Addresses.Any(x => !x.Contains("https:", StringComparison.OrdinalIgnoreCase))
                ? feat.Addresses.First(x => !x.Contains("https:", StringComparison.OrdinalIgnoreCase)).Replace("[::]", "host", StringComparison.OrdinalIgnoreCase)
                : feat.Addresses.First().Replace("[::]", "host", StringComparison.OrdinalIgnoreCase);

            this.Log.LogTrace("Address: {Address}", first);
            Uri uri = new(first);
            this.ConnectorEndpoint = uri.Port > 0
                ? $"{uri.Scheme}://127.0.0.1:{uri.Port}/{this.WorkbenchConfig.ConnectorApiPrefix.TrimStart('/')}"
                : $"{uri.Scheme}://127.0.0.1:/{this.WorkbenchConfig.ConnectorApiPrefix.TrimStart('/')}";

            this.Log.LogTrace("Initialization complete, connector endpoint: {Endpoint}", this.ConnectorEndpoint);
            this.EnablePingTimer();
        }
#pragma warning disable CA1031
        catch (Exception e)
        {
            this.Log.LogError(e, "Initialization error: {Message}", e.Message);
            this.EnableInitTimer();
        }
#pragma warning restore CA1031
    }

    public virtual async Task PingSemanticWorkbenchBackendAsync(CancellationToken cancellationToken)
    {
        this.DisablePingTimer();

        try
        {
            string path = Constants.AgentServiceRegistration.Path
                .Replace(Constants.AgentServiceRegistration.Placeholder, this.WorkbenchConfig.ConnectorId, StringComparison.OrdinalIgnoreCase);
            this.Log.LogTrace("Pinging workbench backend at {Path}", path);

            var data = new
            {
                name = $"{this.WorkbenchConfig.ConnectorName} [{this.WorkbenchConfig.ConnectorId}]",
                description = this.WorkbenchConfig.ConnectorDescription,
                url = this.ConnectorEndpoint,
                online_expires_in_seconds = 1 + (2 * (int)(PingFrequencyMsecs / 1000))
            };

            await this.SendAsync(HttpMethod.Put, path, data, null, "PingSWBackend", cancellationToken).ConfigureAwait(false);
        }
        finally
        {
            this.EnablePingTimer();
        }
    }

    #region internals ===========================================================================

    private const int PingFrequencyMsecs = 15000;

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._pingTimer?.Dispose();
            this._pingTimer = null;
            this.HttpClient.Dispose();
        }
    }

    protected virtual async Task<HttpResponseMessage> SendAsync(
        HttpMethod method,
        string url,
        object? data,
        string? agentId,
        string description,
        CancellationToken cancellationToken)
    {
        url = url.TrimStart('/');
        try
        {
            this.Log.LogTrace("Preparing request: {2}", description);
            HttpRequestMessage request = this.PrepareRequest(method, url, data, agentId);
            this.Log.LogTrace("Sending request {Method} {BaseAddress}{Path} [{Description}]", method, this.HttpClient.BaseAddress, url, description);
            this.Log.LogTrace("{0}: {1}", description, ToCurl(this.HttpClient, request, data));
            HttpResponseMessage result = await this.HttpClient
                .SendAsync(request, cancellationToken)
                .ConfigureAwait(false);
            request.Dispose();
            this.Log.LogTrace("Response status code: {StatusCodeInt} {StatusCode}", (int)result.StatusCode, result.StatusCode);

            return result;
        }
        catch (HttpRequestException e)
        {
            this.Log.LogError("HTTP request failed: {Message} [{Error}, {Exception}, Status Code: {StatusCode}]. Request: {Method} {URL} [{RequestDescription}]",
                e.Message.HtmlEncode(), e.HttpRequestError.ToString("G"), e.GetType().FullName, e.StatusCode, method, url, description);
            throw;
        }
        catch (Exception e)
        {
            this.Log.LogError(e, "Unexpected error");
            throw;
        }
    }

    protected virtual HttpRequestMessage PrepareRequest(
        HttpMethod method,
        string url,
        object? data,
        string? agentId)
    {
        HttpRequestMessage request = new(method, url);
        if (Constants.HttpMethodsWithBody.Contains(method))
        {
            var json = JsonSerializer.Serialize(data);
            request.Content = new StringContent(json, Encoding.UTF8, "application/json");
            this.Log.LogTrace("Request body: {Content}", json);
        }

        request.Headers.Add(Constants.HeaderServiceId, this.WorkbenchConfig.ConnectorId);
        this.Log.LogTrace("Request header: {Content}: {Value}", Constants.HeaderServiceId, this.WorkbenchConfig.ConnectorId);
        if (!string.IsNullOrEmpty(agentId))
        {
            request.Headers.Add(Constants.HeaderAgentId, agentId);
            this.Log.LogTrace("Request header: {Content}: {Value}", Constants.HeaderAgentId, agentId);
        }

        return request;
    }

#pragma warning disable CA1305
    private static string ToCurl(HttpClient httpClient, HttpRequestMessage? request, object? data)
    {
        ArgumentNullException.ThrowIfNull(request);
        ArgumentNullException.ThrowIfNull(request.RequestUri);

        var curl = new StringBuilder("curl -v ");

        foreach (var header in request.Headers)
        {
            foreach (var value in header.Value)
            {
                curl.Append($"-H '{header.Key}: {value}' ");
            }
        }

        if (request.Content?.Headers != null)
        {
            foreach (var header in request.Content.Headers)
            {
                foreach (var value in header.Value)
                {
                    curl.Append($"-H '{header.Key}: {value}' ");
                }
            }
        }

        if (Constants.HttpMethodsWithBody.Contains(request.Method))
        {
            curl.Append($"--data '{JsonSerializer.Serialize(data)}' ");
        }

        curl.Append($"-X {request.Method.Method} '{httpClient.BaseAddress}{request.RequestUri}' ");

        return curl.ToString().TrimEnd();
    }
#pragma warning restore CA1305

    #endregion
}


=== File: libraries/dotnet/WorkbenchConnector/WorkbenchConnector.csproj ===
﻿<Project Sdk="Microsoft.NET.Sdk">

    <PropertyGroup>
        <Version>0.4.0</Version>
        <AssemblyName>Microsoft.SemanticWorkbench.Connector</AssemblyName>
        <RootNamespace>Microsoft.SemanticWorkbench.Connector</RootNamespace>
        <TargetFramework>net8.0</TargetFramework>
        <ImplicitUsings>disable</ImplicitUsings>
        <Nullable>enable</Nullable>
        <LangVersion>12</LangVersion>
        <RollForward>LatestMajor</RollForward>
        <NoWarn>$(NoWarn);IDE0130;CA2254;CA1812;CA1813;IDE0290;</NoWarn>
    </PropertyGroup>

    <ItemGroup>
        <FrameworkReference Include="Microsoft.AspNetCore.App" />
    </ItemGroup>

    <PropertyGroup>
        <RunAnalyzersDuringBuild>true</RunAnalyzersDuringBuild>
        <EnableNETAnalyzers>true</EnableNETAnalyzers>
        <AnalysisMode>All</AnalysisMode>
        <AnalysisLevel>latest</AnalysisLevel>
        <!-- Used by IDE0005 -->
        <GenerateDocumentationFile>true</GenerateDocumentationFile>
    </PropertyGroup>

    <ItemGroup>
        <PackageReference Include="Microsoft.CodeAnalysis.CSharp" Version="4.11.0" />
        <PackageReference Include="Microsoft.CodeAnalysis.CSharp.CodeStyle" Version="4.11.0">
            <PrivateAssets>all</PrivateAssets>
            <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
        </PackageReference>
        <PackageReference Include="Microsoft.CodeAnalysis.NetAnalyzers" Version="9.0.0">
            <PrivateAssets>all</PrivateAssets>
            <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
        </PackageReference>
        <PackageReference Include="Microsoft.CodeAnalysis.Analyzers" Version="3.11.0">
            <PrivateAssets>all</PrivateAssets>
            <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
        </PackageReference>
        <PackageReference Include="Microsoft.VisualStudio.Threading.Analyzers" Version="17.12.19">
            <PrivateAssets>all</PrivateAssets>
            <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
        </PackageReference>
        <PackageReference Include="Roslynator.Analyzers" Version="4.12.9">
            <PrivateAssets>all</PrivateAssets>
            <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
        </PackageReference>
        <PackageReference Include="Roslynator.CodeAnalysis.Analyzers" Version="4.12.9">
            <PrivateAssets>all</PrivateAssets>
            <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
        </PackageReference>
        <PackageReference Include="Roslynator.Formatting.Analyzers" Version="4.12.9">
            <PrivateAssets>all</PrivateAssets>
            <IncludeAssets>runtime; build; native; contentfiles; analyzers; buildtransitive</IncludeAssets>
        </PackageReference>
    </ItemGroup>

    <PropertyGroup Condition=" '$(Configuration)' == 'Debug' ">
        <IsPackable>false</IsPackable>
        <GeneratePackageOnBuild>false</GeneratePackageOnBuild>
    </PropertyGroup>

    <PropertyGroup Condition=" '$(Configuration)' == 'Release' ">
        <IsPackable>true</IsPackable>
        <GeneratePackageOnBuild>true</GeneratePackageOnBuild>
    </PropertyGroup>

    <PropertyGroup>
        <PackageId>Microsoft.SemanticWorkbench.Connector</PackageId>
        <Product>Connector for Agents and Assistants developed with Semantic Workbench</Product>
        <Description>The connector allow Agents and Assistants to be used within Semantic Workbench.</Description>
        <PackageTags>Copilot, Agent, Agentic AI, Assistant, AI, Artificial Intelligence</PackageTags>
        <DocumentationFile>bin/$(Configuration)/$(TargetFramework)/$(AssemblyName).xml</DocumentationFile>
        <Authors>Microsoft</Authors>
        <Company>Microsoft</Company>
        <PackageLicenseExpression>MIT</PackageLicenseExpression>
        <Copyright>© Microsoft Corporation. All rights reserved.</Copyright>
        <PackageProjectUrl>https://github.com/microsoft/semanticworkbench</PackageProjectUrl>
        <RepositoryUrl>https://github.com/microsoft/semanticworkbench</RepositoryUrl>
        <PublishRepositoryUrl>true</PublishRepositoryUrl>
        <PackageIcon>icon.png</PackageIcon>
        <PackageIconUrl>icon.png</PackageIconUrl>
        <PackageReadmeFile>README.md</PackageReadmeFile>
        <EmbedAllSources>true</EmbedAllSources>
        <DebugSymbols>true</DebugSymbols>
        <DebugType>full</DebugType>
        <IncludeSymbols>true</IncludeSymbols>
        <SymbolPackageFormat>snupkg</SymbolPackageFormat>
    </PropertyGroup>

    <ItemGroup Condition=" '$(Configuration)' == 'Release' ">
        <!-- SourceLink allows step-through debugging for source hosted on GitHub. -->
        <!-- https://github.com/dotnet/sourcelink -->
        <PackageReference Include="Microsoft.SourceLink.GitHub" Version="8.0.0" PrivateAssets="All" />

        <None Include="..\README.md" Link="README.md" Pack="true" PackagePath="." Visible="false" />
        <None Include="icon.png" Link="icon.png" Pack="true" PackagePath="." Visible="false" />
    </ItemGroup>

    <ItemGroup Condition=" '$(Configuration)' == 'Debug' ">
        <None Include="icon.png" Link="icon.png" Pack="true" PackagePath="." Visible="false" />
    </ItemGroup>

</Project>


=== File: libraries/dotnet/WorkbenchConnector/icon.png ===
[ERROR reading file: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte]


=== File: libraries/dotnet/pack.sh ===
#!/usr/bin/env bash

set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
cd $HERE

cd WorkbenchConnector
dotnet build -c Release --nologo


