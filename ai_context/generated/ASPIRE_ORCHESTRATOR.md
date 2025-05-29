# aspire-orchestrator

[collect-files]

**Search:** ['aspire-orchestrator']
**Exclude:** ['.venv', 'node_modules', '*.lock', '.git', '__pycache__', '*.pyc', '*.ruff_cache', 'logs', 'output']
**Include:** ['*.csproj', '*.sln', 'appsettings.json']
**Date:** 5/29/2025, 11:45:28 AM
**Files:** 20

=== File: aspire-orchestrator/.editorconfig ===
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
dotnet_diagnostic.CA1050.severity = none # Declare types in namespaces
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
dotnet_diagnostic.IDE0130.severity = none # Namespace does not match folder structure
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


resharper_check_namespace_highlighting = none

#resharper_inconsistent_naming_highlighting = none
#resharper_comment_typo_highlighting = none






=== File: aspire-orchestrator/Aspire.AppHost/.gitignore ===
.azure


=== File: aspire-orchestrator/Aspire.AppHost/Aspire.AppHost.csproj ===
<Project Sdk="Microsoft.NET.Sdk">

    <Sdk Name="Aspire.AppHost.Sdk" Version="9.0.0" />

    <PropertyGroup>
        <OutputType>Exe</OutputType>
        <TargetFramework>net8.0</TargetFramework>
        <ImplicitUsings>enable</ImplicitUsings>
        <Nullable>enable</Nullable>
        <IsAspireHost>true</IsAspireHost>
        <UserSecretsId>b43d9a6d-f7bd-491d-b1f9-82372d537e4e</UserSecretsId>
        <RootNamespace>SemanticWorkbench.Aspire.AppHost</RootNamespace>
    </PropertyGroup>

    <ItemGroup>
        <PackageReference Include="Aspire.Hosting" Version="9.0.0" />
        <PackageReference Include="Aspire.Hosting.AppHost" Version="9.0.0" />
        <PackageReference Include="Aspire.Hosting.Python" Version="9.0.0" />
        <PackageReference Include="CommunityToolkit.Aspire.Hosting.NodeJS.Extensions" Version="9.0.1-beta.77" />
    </ItemGroup>

    <ItemGroup>
        <ProjectReference Include="..\..\examples\dotnet\dotnet-01-echo-bot\dotnet-01-echo-bot.csproj" />
        <ProjectReference Include="..\..\examples\dotnet\dotnet-02-message-types-demo\dotnet-02-message-types-demo.csproj" />
        <ProjectReference Include="..\..\examples\dotnet\dotnet-03-simple-chatbot\dotnet-03-simple-chatbot.csproj" />
        <ProjectReference Include="..\Aspire.Extensions\Aspire.Extensions.csproj" IsAspireProjectResource="false" />
    </ItemGroup>

</Project>

=== File: aspire-orchestrator/Aspire.AppHost/Program.cs ===
// Copyright (c) Microsoft. All rights reserved.

using Aspire.Hosting.Extensions;
using Projects;

internal static class Program
{
    public static void Main(string[] args)
    {
        var builder = DistributedApplication.CreateBuilder(args);

        builder
            .AddSemanticWorkbench(out IResourceBuilder<ExecutableResource> workbenchBackend, out EndpointReference workbenchEndpoint)
            .AddPythonAssistant("skill-assistant", workbenchEndpoint)
            .AddDotnetExample<dotnet_03_simple_chatbot>("simple-chatbot-dotnet", workbenchBackend, workbenchEndpoint);

        // When running locally
        if (!builder.ExecutionContext.IsPublishMode)
        {
            builder
                .AddPythonExample("python-01-echo-bot", workbenchEndpoint)
                .AddPythonExample("python-02-simple-chatbot", workbenchEndpoint)
                .AddPythonExample("python-03-multimodel-chatbot", workbenchEndpoint)
                .AddPythonAssistant("explorer-assistant", workbenchEndpoint)
                .AddPythonAssistant("guided-conversation-assistant", workbenchEndpoint)
                .AddPythonAssistant("prospector-assistant", workbenchEndpoint)
                .AddDotnetExample<dotnet_01_echo_bot>("echo-bot-dotnet", workbenchBackend, workbenchEndpoint)
                .AddDotnetExample<dotnet_02_message_types_demo>("sw-tutorial-bot-dotnet", workbenchBackend, workbenchEndpoint);
        }

        builder
            .ShowDashboardUrl(true)
            .LaunchDashboard(delay: 5000)
            .Build()
            .Run();
    }

    /// <summary>
    /// Add the workbench frontend and backend components
    /// </summary>
    private static IDistributedApplicationBuilder AddSemanticWorkbench(this IDistributedApplicationBuilder builder,
        out IResourceBuilder<ExecutableResource> workbenchBackend, out EndpointReference workbenchServiceEndpoint)
    {
        var authority = builder.AddParameterFromConfiguration("authority", "EntraId:Authority");
        var clientId = builder.AddParameterFromConfiguration("clientId", "EntraId:ClientId");

        // Workbench backend
        workbenchBackend = builder.AddWorkbenchService(
            name: "workbenchservice",
            projectDirectory: Path.Combine("..", "..", "workbench-service"),
            clientId: clientId);

        workbenchServiceEndpoint = workbenchBackend.GetSemanticWorkbenchEndpoint(builder.ExecutionContext.IsPublishMode);

        // Workbench frontend
        var workbenchApp = builder.AddViteApp(
                name: "workbenchapp",
                workingDirectory: Path.Combine("..", "..", "workbench-app"),
                packageManager: "pnpm")
            .WithPnpmPackageInstallation()
            .WithEnvironment(name: "VITE_SEMANTIC_WORKBENCH_SERVICE_URL", workbenchServiceEndpoint)
            .WaitFor(workbenchBackend)
            .PublishAsDockerFile([
                new DockerBuildArg("VITE_SEMANTIC_WORKBENCH_CLIENT_ID", clientId.Resource.Value),
                new DockerBuildArg("VITE_SEMANTIC_WORKBENCH_AUTHORITY", authority.Resource.Value),
            ]);

        // When running locally
        if (!builder.ExecutionContext.IsPublishMode)
        {
            if (!int.TryParse(builder.Configuration["Workbench:AppPort"], out var appPort)) { appPort = 4000; }
            workbenchApp.WithHttpsEndpoint(port: appPort, env: "PORT", isProxied: false);
        }

        return builder;
    }

    private static IDistributedApplicationBuilder AddPythonAssistant(this IDistributedApplicationBuilder builder,
        string name, EndpointReference workbenchServiceEndpoint)
    {
        builder
            .AddAssistantUvPythonApp(
                name: name,
                projectDirectory: Path.Combine("..", "..", "assistants", name),
                assistantModuleName: name)
            .WithEnvironment(name: "assistant__workbench_service_url", workbenchServiceEndpoint);

        return builder;
    }

    private static IDistributedApplicationBuilder AddPythonExample(this IDistributedApplicationBuilder builder,
        string name, EndpointReference workbenchServiceEndpoint)
    {
        builder
            .AddAssistantUvPythonApp(
                name: name,
                projectDirectory: Path.Combine("..", "..", "examples", "python", name),
                assistantModuleName: "assistant")
            .WithEnvironment(name: "assistant__workbench_service_url", workbenchServiceEndpoint);

        return builder;
    }

    // .NET Agent Example 1
    private static IDistributedApplicationBuilder AddDotnetExample<T>(this IDistributedApplicationBuilder builder,
        string name, IResourceBuilder<ExecutableResource> workbenchBackend, EndpointReference workbenchServiceEndpoint) where T : IProjectMetadata, new()
    {
        var agent = builder
            .AddProject<T>(name: name)
            .WithHttpEndpoint()
            .WaitFor(workbenchBackend)
            .WithEnvironment(name: "Workbench__WorkbenchEndpoint", workbenchServiceEndpoint);

        agent.WithEnvironment("Workbench__ConnectorHost", $"{agent.GetEndpoint("http")}");

        return builder;
    }
}


=== File: aspire-orchestrator/Aspire.AppHost/Properties/launchSettings.json ===
{
  "$schema": "https://json.schemastore.org/launchsettings.json",
  "profiles": {
    "https": {
      "commandName": "Project",
      "dotnetRunMessages": true,
      "launchBrowser": true,
      "applicationUrl": "https://localhost:17149;http://localhost:15061",
      "environmentVariables": {
        "ASPNETCORE_ENVIRONMENT": "Development",
        "DOTNET_ENVIRONMENT": "Development",
        "DOTNET_DASHBOARD_OTLP_ENDPOINT_URL": "https://localhost:21236",
        "DOTNET_RESOURCE_SERVICE_ENDPOINT_URL": "https://localhost:22204"
      }
    },
    "http": {
      "commandName": "Project",
      "dotnetRunMessages": true,
      "launchBrowser": true,
      "applicationUrl": "http://localhost:15061",
      "environmentVariables": {
        "ASPNETCORE_ENVIRONMENT": "Development",
        "DOTNET_ENVIRONMENT": "Development",
        "DOTNET_DASHBOARD_OTLP_ENDPOINT_URL": "http://localhost:19243",
        "DOTNET_RESOURCE_SERVICE_ENDPOINT_URL": "http://localhost:20261"
      }
    }
  }
}


=== File: aspire-orchestrator/Aspire.AppHost/appsettings.json ===
{
  "Logging": {
    "LogLevel": {
      "Default": "Information",
      "Microsoft.AspNetCore": "Warning",
      "Aspire.Hosting.Dcp": "Warning"
    }
  },
  "Workbench": {
    // Used only when running Aspire locally, ie not in the cloud
    // Port 4000 is the default port used also when not using Aspire.
    // Using the same port allows to keep cookies and other local settings.
    "AppPort": 4000
  },
  "EntraID": {
    "Authority": "https://login.microsoftonline.com/common",
    "ClientId": "22cb77c3-ca98-4a26-b4db-ac4dcecba690"
  }
}


=== File: aspire-orchestrator/Aspire.Extensions/Aspire.Extensions.csproj ===
﻿<Project Sdk="Microsoft.NET.Sdk">

    <PropertyGroup>
        <TargetFramework>net8.0</TargetFramework>
        <nullable>enable</nullable>
        <ImplicitUsings>enable</ImplicitUsings>
        <AdditionalPackageTags>semantic workbench extensions</AdditionalPackageTags>
        <Description>An Aspire integration for Semantic Workbench.</Description>
        <RootNamespace>Aspire.Hosting.Extensions</RootNamespace>
    </PropertyGroup>

    <ItemGroup>
        <PackageReference Include="Aspire.Hosting" Version="9.0.0" />
        <PackageReference Include="Aspire.Hosting.AppHost" Version="9.0.0" />
    </ItemGroup>

</Project>

=== File: aspire-orchestrator/Aspire.Extensions/Dashboard.cs ===
// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;

namespace Aspire.Hosting.Extensions;

public static class Dashboard
{
    /// <summary>
    /// Show Aspire dashboard URL before the logging start.
    /// </summary>
    public static IDistributedApplicationBuilder ShowDashboardUrl(this IDistributedApplicationBuilder builder, bool withStyle = false)
    {
        Console.WriteLine(withStyle
            ? $"\u001b[1mAspire dashboard URL: {GetUrl(builder)}\u001b[0m\n\n"
            : $"Aspire dashboard URL: {GetUrl(builder)}\n\n");
        return builder;
    }

    /// <summary>
    /// Wait 5 seconds and automatically open the browser (when using 'dotnet run' the browser doesn't open)
    /// </summary>
    public static IDistributedApplicationBuilder LaunchDashboard(this IDistributedApplicationBuilder builder, int delay = 5000)
    {
        Task.Run(async () =>
        {
            await Task.Delay(delay).ConfigureAwait(false);
            Process.Start(new ProcessStartInfo { FileName = GetUrl(builder), UseShellExecute = true });
        });

        return builder;
    }

    private static string GetUrl(IDistributedApplicationBuilder builder)
    {
        string token = builder.Configuration["AppHost:BrowserToken"] ?? string.Empty;
        string url = builder.Configuration["ASPNETCORE_URLS"]?.Split(";")[0] ?? throw new ArgumentException("ASPNETCORE_URLS is empty");
        return $"{url}/login?t={token}";
    }
}


=== File: aspire-orchestrator/Aspire.Extensions/DockerFileExtensions.cs ===
// Copyright (c) Microsoft. All rights reserved.

namespace Aspire.Hosting;

public static class DockerFileExtensions
{
    public static IResourceBuilder<ExecutableResource> PublishAsDockerImage(this IResourceBuilder<ExecutableResource> builder,
        string? dockerContext = null,
        string? dockerFilePath = "Dockerfile",
        Action<IResourceBuilder<ContainerResource>>? configure = null)
    {
        if (!builder.ApplicationBuilder.ExecutionContext.IsPublishMode)
        {
            return builder;
        }

        // Bait and switch the ExecutableResource with a ContainerResource
        builder.ApplicationBuilder.Resources.Remove(builder.Resource);

        var container = new ExecutableContainerResource(builder.Resource);
        var cb = builder.ApplicationBuilder.AddResource(container);
        cb.WithImage(builder.Resource.Name);
        cb.WithDockerfile(contextPath: dockerContext ?? builder.Resource.WorkingDirectory, dockerfilePath: dockerFilePath);
        // Clear the runtime args
        cb.WithArgs(c => c.Args.Clear());

        configure?.Invoke(cb);

        return builder;
    }

    private sealed class ExecutableContainerResource(ExecutableResource er) : ContainerResource(er.Name)
    {
        public override ResourceAnnotationCollection Annotations => er.Annotations;
    }
}


=== File: aspire-orchestrator/Aspire.Extensions/PathNormalizer.cs ===
// Copyright (c) Microsoft. All rights reserved.

namespace Aspire.Hosting.Extensions;

internal static class PathNormalizer
{
    /// <summary>
    /// Normalizes the path for the current platform.
    /// </summary>
    /// <param name="path">The path value.</param>
    /// <returns>Returns the normalized path value for the current platform.</returns>
    public static string NormalizePathForCurrentPlatform(this string path)
    {
        if (string.IsNullOrWhiteSpace(path))
        {
            return path;
        }

        // Fix slashes
        path = path.Replace('\\', Path.DirectorySeparatorChar).Replace('/', Path.DirectorySeparatorChar);

        return Path.GetFullPath(path);
    }
}

=== File: aspire-orchestrator/Aspire.Extensions/UvAppHostingExtensions.cs ===
﻿// Copyright (c) Microsoft. All rights reserved.

using Aspire.Hosting.ComponentModel;
using Aspire.Hosting.Extensions;

namespace Aspire.Hosting;

public static class UvAppHostingExtensions
{
    public static IResourceBuilder<UvAppResource> AddUvApp(
        this IDistributedApplicationBuilder builder,
        string name,
        string projectDirectory,
        string scriptPath,
        params string[] scriptArgs)
    {
        ArgumentNullException.ThrowIfNull(builder);

        return builder.AddUvApp(name, scriptPath, projectDirectory, ".venv", scriptArgs);
    }

    private static IResourceBuilder<UvAppResource> AddUvApp(this IDistributedApplicationBuilder builder,
        string name,
        string scriptPath,
        string? projectDirectory,
        string virtualEnvironmentPath,
        params string[] args)
    {
        ArgumentNullException.ThrowIfNull(builder);
        ArgumentNullException.ThrowIfNull(name);
        ArgumentNullException.ThrowIfNull(scriptPath);

        string wd = projectDirectory ?? Path.Combine("..", name);

        projectDirectory = Path.Combine(builder.AppHostDirectory, wd).NormalizePathForCurrentPlatform();

        var virtualEnvironment = new VirtualEnvironment(Path.IsPathRooted(virtualEnvironmentPath)
            ? virtualEnvironmentPath
            : Path.Join(projectDirectory, virtualEnvironmentPath));

        var instrumentationExecutable = virtualEnvironment.GetExecutable("opentelemetry-instrument");
        // var pythonExecutable = virtualEnvironment.GetRequiredExecutable("python");
        // var projectExecutable = instrumentationExecutable ?? pythonExecutable;

        string[] allArgs = args is { Length: > 0 }
            ? ["run", "--frozen", scriptPath, .. args]
            : ["run", "--frozen", scriptPath];

        var projectResource = new UvAppResource(name, projectDirectory);

        var resourceBuilder = builder.AddResource(projectResource)
            .WithArgs(allArgs)
            .WithArgs(context =>
            {
                // If the project is to be automatically instrumented, add the instrumentation executable arguments first.
                if (!string.IsNullOrEmpty(instrumentationExecutable))
                {
                    AddOpenTelemetryArguments(context);

                    // // Add the python executable as the next argument so we can run the project.
                    // context.Args.Add(pythonExecutable!);
                }
            });

        if (!string.IsNullOrEmpty(instrumentationExecutable))
        {
            resourceBuilder.WithOtlpExporter();

            // Make sure to attach the logging instrumentation setting, so we can capture logs.
            // Without this you'll need to configure logging yourself. Which is kind of a pain.
            resourceBuilder.WithEnvironment("OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED", "true");
        }

        return resourceBuilder;
    }

    private static void AddOpenTelemetryArguments(CommandLineArgsCallbackContext context)
    {
        context.Args.Add("--traces_exporter");
        context.Args.Add("otlp");

        context.Args.Add("--logs_exporter");
        context.Args.Add("console,otlp");

        context.Args.Add("--metrics_exporter");
        context.Args.Add("otlp");
    }
}


=== File: aspire-orchestrator/Aspire.Extensions/UvAppResource.cs ===
// Copyright (c) Microsoft. All rights reserved.

namespace Aspire.Hosting.ComponentModel;

public class UvAppResource(string name, string workingDirectory)
    : ExecutableResource(name, "uv", workingDirectory), IResourceWithServiceDiscovery
{
    internal const string HttpEndpointName = "http";
}


=== File: aspire-orchestrator/Aspire.Extensions/VirtualEnvironment.cs ===
// Copyright (c) Microsoft. All rights reserved.

namespace Aspire.Hosting.ComponentModel;

internal sealed class VirtualEnvironment(string virtualEnvironmentPath)
{
    /// <summary>
    /// Locates an executable in the virtual environment.
    /// </summary>
    /// <param name="name">The name of the executable.</param>
    /// <returns>Returns the path to the executable if it exists in the virtual environment.</returns>
    public string? GetExecutable(string name)
    {
        if (OperatingSystem.IsWindows())
        {
            string[] allowedExtensions = [".exe", ".cmd", ".bat"];

            return allowedExtensions
                .Select(allowedExtension => Path.Join(virtualEnvironmentPath, "Scripts", name + allowedExtension))
                .FirstOrDefault(File.Exists);
        }

        var executablePath = Path.Join(virtualEnvironmentPath, "bin", name);
        return File.Exists(executablePath) ? executablePath : null;
    }

    /// <summary>
    /// Locates a required executable in the virtual environment.
    /// </summary>
    /// <param name="name">The name of the executable.</param>
    /// <returns>The path to the executable in the virtual environment.</returns>
    /// <exception cref="DistributedApplicationException">Gets thrown when the executable couldn't be located.</exception>
    public string GetRequiredExecutable(string name)
    {
        return this.GetExecutable(name) ?? throw new DistributedApplicationException(
            $"The executable {name} could not be found in the virtual environment at '{virtualEnvironmentPath}' . " +
            "Make sure the virtual environment is initialized and the executable is installed.");
    }
}


=== File: aspire-orchestrator/Aspire.Extensions/WorkbenchServiceHostingExtensions.cs ===
// Copyright (c) Microsoft. All rights reserved.

namespace Aspire.Hosting;

public static class WorkbenchServiceHostingExtensions
{
    public static IResourceBuilder<ExecutableResource> AddWorkbenchService(
        this IDistributedApplicationBuilder builder,
        string name,
        string projectDirectory,
        IResourceBuilder<ParameterResource> clientId,
        params string[] scriptArgs)
    {
        ArgumentNullException.ThrowIfNull(builder);

        var workbenchService = builder
            .AddUvApp(name, projectDirectory, "start-semantic-workbench-service", scriptArgs)
            .PublishAsDockerImage(dockerContext: Path.Combine("..", ".."),
                dockerFilePath: Path.Combine("workbench-service", "Dockerfile"),
                configure: new(configure => configure
                    .WithBuildArg("SSHD_ENABLED", "false")))
            .WithEnvironment(name: "WORKBENCH__AUTH__ALLOWED_APP_ID", clientId.Resource.Value);

        if (builder.ExecutionContext.IsPublishMode)
        {
            // When running on Azure
            workbenchService.WithHttpsEndpoint(port: 3000);
        }
        else
        {
            // When running locally
            workbenchService.WithHttpEndpoint(env: "PORT");
        }

        workbenchService.WithExternalHttpEndpoints();

        return workbenchService;
    }

    public static EndpointReference GetSemanticWorkbenchEndpoint(this IResourceBuilder<ExecutableResource> workbenchService, bool isPublishMode)
    {
        ArgumentNullException.ThrowIfNull(workbenchService);

        return workbenchService.GetEndpoint(isPublishMode ? "https" : "http");
    }

    public static IResourceBuilder<ExecutableResource> AddAssistantUvPythonApp(
        this IDistributedApplicationBuilder builder,
        string name,
        string projectDirectory,
        string assistantModuleName)
    {
        ArgumentNullException.ThrowIfNull(builder);

        var assistant = builder
            .AddUvApp(name, projectDirectory, "start-assistant")
            .PublishAsDockerImage(dockerContext: Path.Combine("..", ".."),
                dockerFilePath: Path.Combine("tools", "docker", "Dockerfile.assistant"),
                configure: new(configure => configure
                    .WithBuildArg("package", assistantModuleName)
                    .WithBuildArg("app", $"assistant.{assistantModuleName.Replace('-', '_')}:app")
                ));

        if (builder.ExecutionContext.IsPublishMode)
        {
            // When running on Azure
            assistant.WithHttpEndpoint(port: 3001, env: "ASSISTANT__PORT");
        }
        else
        {
            // When running locally
            assistant.WithHttpEndpoint(env: "ASSISTANT__PORT");
        }

        var assistantEndpoint = assistant.GetEndpoint("http");
        assistant.WithEnvironment(name: "assistant__assistant_service_url", assistantEndpoint);

        return assistant;
    }
}


=== File: aspire-orchestrator/Aspire.ServiceDefaults/Aspire.ServiceDefaults.csproj ===
<Project Sdk="Microsoft.NET.Sdk">

    <PropertyGroup>
        <TargetFramework>net8.0</TargetFramework>
        <ImplicitUsings>enable</ImplicitUsings>
        <Nullable>enable</Nullable>
        <IsAspireSharedProject>true</IsAspireSharedProject>
        <RootNamespace>SemanticWorkbench.Aspire.ServiceDefaults</RootNamespace>
    </PropertyGroup>

    <ItemGroup>
        <FrameworkReference Include="Microsoft.AspNetCore.App" />

        <PackageReference Include="Microsoft.Extensions.Http.Resilience" Version="8.10.0" />
        <PackageReference Include="Microsoft.Extensions.ServiceDiscovery" Version="9.0.0" />
        <PackageReference Include="OpenTelemetry.Exporter.OpenTelemetryProtocol" Version="1.9.0" />
        <PackageReference Include="OpenTelemetry.Extensions.Hosting" Version="1.9.0" />
        <PackageReference Include="OpenTelemetry.Instrumentation.AspNetCore" Version="1.9.0" />
        <PackageReference Include="OpenTelemetry.Instrumentation.Http" Version="1.9.0" />
        <PackageReference Include="OpenTelemetry.Instrumentation.Runtime" Version="1.9.0" />
    </ItemGroup>

</Project>

=== File: aspire-orchestrator/Aspire.ServiceDefaults/Extensions.cs ===
// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Diagnostics.HealthChecks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Diagnostics.HealthChecks;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using OpenTelemetry;
using OpenTelemetry.Metrics;
using OpenTelemetry.Trace;

namespace SemanticWorkbench.Aspire.ServiceDefaults;

// Adds common .NET Aspire services: service discovery, resilience, health checks, and OpenTelemetry.
// This project should be referenced by each service project in your solution.
// To learn more about using this project, see https://aka.ms/dotnet/aspire/service-defaults
public static class Extensions
{
    public static TBuilder AddServiceDefaults<TBuilder>(this TBuilder builder) where TBuilder : IHostApplicationBuilder
    {
        builder.ConfigureOpenTelemetry();

        builder.AddDefaultHealthChecks();

        builder.Services.AddServiceDiscovery();

        builder.Services.ConfigureHttpClientDefaults(http =>
        {
            // Turn on resilience by default
            http.AddStandardResilienceHandler();

            // Turn on service discovery by default
            http.AddServiceDiscovery();
        });

        // Uncomment the following to restrict the allowed schemes for service discovery.
        // builder.Services.Configure<ServiceDiscoveryOptions>(options =>
        // {
        //     options.AllowedSchemes = ["https"];
        // });

        return builder;
    }

    public static TBuilder ConfigureOpenTelemetry<TBuilder>(this TBuilder builder) where TBuilder : IHostApplicationBuilder
    {
        builder.Logging.AddOpenTelemetry(logging =>
        {
            logging.IncludeFormattedMessage = true;
            logging.IncludeScopes = true;
        });

        builder.Services.AddOpenTelemetry()
            .WithMetrics(metrics =>
            {
                metrics.AddAspNetCoreInstrumentation()
                    .AddHttpClientInstrumentation()
                    .AddRuntimeInstrumentation();
            })
            .WithTracing(tracing =>
            {
                tracing.AddSource(builder.Environment.ApplicationName)
                    .AddAspNetCoreInstrumentation()
                    // Uncomment the following line to enable gRPC instrumentation (requires the OpenTelemetry.Instrumentation.GrpcNetClient package)
                    //.AddGrpcClientInstrumentation()
                    .AddHttpClientInstrumentation();
            });

        builder.AddOpenTelemetryExporters();

        return builder;
    }

    private static TBuilder AddOpenTelemetryExporters<TBuilder>(this TBuilder builder) where TBuilder : IHostApplicationBuilder
    {
        var useOtlpExporter = !string.IsNullOrWhiteSpace(builder.Configuration["OTEL_EXPORTER_OTLP_ENDPOINT"]);

        if (useOtlpExporter)
        {
            builder.Services.AddOpenTelemetry().UseOtlpExporter();
        }

        // Uncomment the following lines to enable the Azure Monitor exporter (requires the Azure.Monitor.OpenTelemetry.AspNetCore package)
        //if (!string.IsNullOrEmpty(builder.Configuration["APPLICATIONINSIGHTS_CONNECTION_STRING"]))
        //{
        //    builder.Services.AddOpenTelemetry()
        //       .UseAzureMonitor();
        //}

        return builder;
    }

    public static TBuilder AddDefaultHealthChecks<TBuilder>(this TBuilder builder) where TBuilder : IHostApplicationBuilder
    {
        builder.Services.AddHealthChecks()
            // Add a default liveness check to ensure app is responsive
            .AddCheck("self", () => HealthCheckResult.Healthy(), ["live"]);

        return builder;
    }

    public static WebApplication MapDefaultEndpoints(this WebApplication app)
    {
        // Adding health checks endpoints to applications in non-development environments has security implications.
        // See https://aka.ms/dotnet/aspire/healthchecks for details before enabling these endpoints in non-development environments.
        if (app.Environment.IsDevelopment())
        {
            // All health checks must pass for app to be considered ready to accept traffic after starting
            app.MapHealthChecks("/health");

            // Only health checks tagged with the "live" tag must pass for app to be considered alive
            app.MapHealthChecks("/alive", new HealthCheckOptions
            {
                Predicate = r => r.Tags.Contains("live")
            });
        }

        return app;
    }
}


=== File: aspire-orchestrator/README.md ===
# .NET Aspire Integration

## Run Prerequisites

- [dotnet (8 or greater)](https://dotnet.microsoft.com/download)
- [Python 3.8 or greater](https://www.python.org/downloads)
- [NodeJs v18.12 or greater](https://nodejs.org/en/download)

## Deployment Prerequisites

- [Azure Developer CLI](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- [Docker for Desktop](https://docs.docker.com/get-started/introduction/get-docker-desktop)
- [dotnet (9 or greater)](https://dotnet.microsoft.com/download)
- [Python 3.8 or greater](https://www.python.org/downloads)
- [NodeJs v18.12 or greater](https://nodejs.org/en/download)

## Run with .NET Aspire

1.  Make sure your workstation trusts
    [ASP.NET Core HTTPS development certificate](https://learn.microsoft.com/en-us/aspnet/core/security/enforcing-ssl?#trust-the-aspnet-core-https-development-certificate)

        dotnet dev-certs https --trust

2.  Clone the repository

        make
        cd aspire-orchestrator
        cd Aspire.AppHost
        dotnet run

## Deployment Steps with azd

1.  Clone the repository

2.  [Configure the Entra app registration](../docs/CUSTOM_APP_REGISTRATION.md).
    Copy the Entra **Application Id** and **Tenant Id** into
    `aspire-orchestrator/Aspire.AppHost/appsettings.json` file.

    If your Entra App allows both organizational and personal accounts
    use `common` as Tenant Id, e.g. setting
    `"Authority": "https://login.microsoftonline.com/common"`. For other special
    authority values refer to https://learn.microsoft.com/en-us/entra/identity-platform/v2-protocols-oidc

        {
          "EntraID": {
            "ClientId": "<CLIENT_ID>",
            "Authority": "https://login.microsoftonline.com/<TENANT_ID>"
          }
        }

3.  In the root folder of the repository, run

        make

4.  Authenticate with Azure Developer CLI

        azd login

5.  Generate the Azure config files required in the next step

        azd init --from-code --environment semanticworkbench

6.  Create Azure resources and deploy the application

        azd up

    When asked for "**authority**", enter the same value set in appsettings.json.

    When asked for "**clientId**", enter the same value set in appsettings.json.

    These values are stored as Environment Variables and can be modified in Azure
    Portal if needed.

    The deployment will take a few minutes to complete, taking care also of
    creating and deploying the required docker images.

7.  After the deployment is complete, a few URLs will be printed, in particular
    the Aspire Dashboard URL and Semantic Workbench App URL.

    Copy the `service workbenchapp` endpoint value for the next step:
    | ![Image](https://github.com/user-attachments/assets/0aae7518-bfa6-4f76-962a-df3d152e0155) |
    |:--:|

8.  Update the [Entra App Registration](https://portal.azure.com/#view/Microsoft_AAD_IAM/ActiveDirectoryMenuBlade/~/RegisteredApps),
    adding the URL from the previous step as one of the SPA Redirection URIs:
    | ![Image](https://github.com/user-attachments/assets/e709ee12-a3ef-4be3-9f2d-46d33c929f42) |
    |:-:|

9.  Open your browser and navigate to the same URL.


=== File: aspire-orchestrator/SemanticWorkbench.Aspire.sln ===
﻿Microsoft Visual Studio Solution File, Format Version 12.00
# Visual Studio Version 17
VisualStudioVersion = 17.8.0.0
MinimumVisualStudioVersion = 17.8.0.0
Project("{9A19103F-16F7-4668-BE54-9A1E7A4F7556}") = "Aspire.AppHost", "Aspire.AppHost\Aspire.AppHost.csproj", "{85D9E2AF-8F25-4006-A375-A66E2259CB69}"
EndProject
Project("{9A19103F-16F7-4668-BE54-9A1E7A4F7556}") = "Aspire.ServiceDefaults", "Aspire.ServiceDefaults\Aspire.ServiceDefaults.csproj", "{1A1BA42B-F071-42ED-BF6D-4BD51F2D7A41}"
EndProject
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "dotnet-03-simple-chatbot", "..\examples\dotnet\dotnet-03-simple-chatbot\dotnet-03-simple-chatbot.csproj", "{670F22E3-71CC-4A9B-8BB8-DA855CFC0EEC}"
EndProject
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "Aspire.Extensions", "Aspire.Extensions\Aspire.Extensions.csproj", "{773468A0-6628-4D14-8EE8-7C3F790B6192}"
EndProject
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "dotnet-01-echo-bot", "..\examples\dotnet\dotnet-01-echo-bot\dotnet-01-echo-bot.csproj", "{9AB1A55C-A7D7-45E4-9C4C-D3F5BBD78D64}"
EndProject
Project("{FAE04EC0-301F-11D3-BF4B-00C04F79EFBC}") = "dotnet-02-message-types-demo", "..\examples\dotnet\dotnet-02-message-types-demo\dotnet-02-message-types-demo.csproj", "{B604ADC1-7FF3-449A-9BE7-BC553A810ADE}"
EndProject
Global
	GlobalSection(SolutionConfigurationPlatforms) = preSolution
		Debug|Any CPU = Debug|Any CPU
		Release|Any CPU = Release|Any CPU
	EndGlobalSection
	GlobalSection(ProjectConfigurationPlatforms) = postSolution
		{85D9E2AF-8F25-4006-A375-A66E2259CB69}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{85D9E2AF-8F25-4006-A375-A66E2259CB69}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{85D9E2AF-8F25-4006-A375-A66E2259CB69}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{85D9E2AF-8F25-4006-A375-A66E2259CB69}.Release|Any CPU.Build.0 = Release|Any CPU
		{1A1BA42B-F071-42ED-BF6D-4BD51F2D7A41}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{1A1BA42B-F071-42ED-BF6D-4BD51F2D7A41}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{1A1BA42B-F071-42ED-BF6D-4BD51F2D7A41}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{1A1BA42B-F071-42ED-BF6D-4BD51F2D7A41}.Release|Any CPU.Build.0 = Release|Any CPU
		{670F22E3-71CC-4A9B-8BB8-DA855CFC0EEC}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{670F22E3-71CC-4A9B-8BB8-DA855CFC0EEC}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{670F22E3-71CC-4A9B-8BB8-DA855CFC0EEC}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{670F22E3-71CC-4A9B-8BB8-DA855CFC0EEC}.Release|Any CPU.Build.0 = Release|Any CPU
		{773468A0-6628-4D14-8EE8-7C3F790B6192}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{773468A0-6628-4D14-8EE8-7C3F790B6192}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{773468A0-6628-4D14-8EE8-7C3F790B6192}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{773468A0-6628-4D14-8EE8-7C3F790B6192}.Release|Any CPU.Build.0 = Release|Any CPU
		{9AB1A55C-A7D7-45E4-9C4C-D3F5BBD78D64}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{9AB1A55C-A7D7-45E4-9C4C-D3F5BBD78D64}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{9AB1A55C-A7D7-45E4-9C4C-D3F5BBD78D64}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{9AB1A55C-A7D7-45E4-9C4C-D3F5BBD78D64}.Release|Any CPU.Build.0 = Release|Any CPU
		{B604ADC1-7FF3-449A-9BE7-BC553A810ADE}.Debug|Any CPU.ActiveCfg = Debug|Any CPU
		{B604ADC1-7FF3-449A-9BE7-BC553A810ADE}.Debug|Any CPU.Build.0 = Debug|Any CPU
		{B604ADC1-7FF3-449A-9BE7-BC553A810ADE}.Release|Any CPU.ActiveCfg = Release|Any CPU
		{B604ADC1-7FF3-449A-9BE7-BC553A810ADE}.Release|Any CPU.Build.0 = Release|Any CPU
	EndGlobalSection
	GlobalSection(SolutionProperties) = preSolution
		HideSolutionNode = FALSE
	EndGlobalSection
	GlobalSection(ExtensibilityGlobals) = postSolution
		SolutionGuid = {30B8E5F7-972C-4722-B57A-0626109F80B6}
	EndGlobalSection
EndGlobal


=== File: aspire-orchestrator/SemanticWorkbench.Aspire.sln.DotSettings ===
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
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=HTML/@EntryIndexedValue">HTML</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=HTTP/@EntryIndexedValue">HTTP</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=IM/@EntryIndexedValue">IM</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=IO/@EntryIndexedValue">IO</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=IOS/@EntryIndexedValue">IOS</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=JSON/@EntryIndexedValue">JSON</s:String>
	<s:String x:Key="/Default/CodeStyle/Naming/CSharpNaming/Abbreviations/=JWT/@EntryIndexedValue">JWT</s:String>
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
	<s:Boolean x:Key="/Default/UserDictionary/Words/=multimodel/@EntryIndexedValue">True</s:Boolean>
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


=== File: aspire-orchestrator/run.sh ===
#!/usr/bin/env bash

set -e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/"
cd "$HERE"

# Check node version, it must be major version 20 (any minor), otherwise show an error and exit
NODE_VERSION=$(node -v)
if [[ ! $NODE_VERSION =~ ^v(1[8-9]|[2-9][0-9]).* ]]; then
    echo "Node version is $NODE_VERSION, expected 18.x.x or higher."

  # Attempt to source nvm
  if [ -s "$NVM_DIR/nvm.sh" ]; then
    . "$NVM_DIR/nvm.sh"
  elif [ -s "$HOME/.nvm/nvm.sh" ]; then
    export NVM_DIR="$HOME/.nvm"
    . "$NVM_DIR/nvm.sh"
  else
    echo "nvm not found. Please install Node 18 or higher manually."
    echo "See also README.md for instructions."
    exit 1
  fi

  echo "Installing latest LTS Node version via nvm..."
  nvm install --lts
  nvm use --lts

  NODE_VERSION=$(node -v)
  if [[ ! $NODE_VERSION =~ ^v(1[8-9]|[2-9][0-9]).* ]]; then
    echo "Failed to switch to Node 18 or higher via nvm. You have $NODE_VERSION."
    exit 1
  fi
fi

cd Aspire.AppHost

dotnet run --launch-profile https


