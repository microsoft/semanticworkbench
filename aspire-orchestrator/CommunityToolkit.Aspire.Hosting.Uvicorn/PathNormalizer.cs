using System;

namespace CommunityToolkit.Aspire.Hosting.Uvicorn;

internal static class PathNormalizer
{
    /// <summary>
    /// Normalizes the path for the current platform.
    /// </summary>
    /// <param name="path">The path value.</param>
    /// <returns>Returns the normalized path value for the current platform.</returns>
    public static string NormalizePathForCurrentPlatform(this string path)
    {
        if (string.IsNullOrWhiteSpace(path) == true)
        {
            return path;
        }

        // Fix slashes
        path = path.Replace('\\', Path.DirectorySeparatorChar).Replace('/', Path.DirectorySeparatorChar);

        return Path.GetFullPath(path);
    }
}