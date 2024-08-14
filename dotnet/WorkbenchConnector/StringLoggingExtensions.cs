// Copyright (c) Microsoft. All rights reserved.

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
        return string.IsNullOrWhiteSpace(value.ToString())
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
