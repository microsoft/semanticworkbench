def get_worksheet_content_as_md_table(doc) -> str:
    """
    Return the content of the worksheet formatted as a markdown table.
    """
    # Assume the first worksheet is the one we want
    worksheet = doc.Worksheets(1)

    # Get the used range of the worksheet
    used_range = worksheet.UsedRange

    # Get the values as a tuple of tuples
    values = used_range.Value

    # Convert to markdown table format
    if not values:  # Handle empty worksheet
        return "| Empty worksheet |"

    # Convert rows to lists and handle empty cells
    rows = []
    for row in values:
        row_data = [str(cell) if cell is not None else "" for cell in row]
        rows.append(row_data)

    # Calculate column widths for better formatting
    col_widths = []
    for col in range(len(rows[0])):
        width = max(len(str(row[col])) for row in rows)
        col_widths.append(width)

    # Build the markdown table
    md_table = []

    # Header row
    header = "| " + " | ".join(str(rows[0][i]).ljust(col_widths[i]) for i in range(len(rows[0]))) + " |"
    md_table.append(header)

    # Separator row
    separator = "| " + " | ".join("-" * width for width in col_widths) + " |"
    md_table.append(separator)

    # Data rows
    for row in rows[1:]:
        row_str = "| " + " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row))) + " |"
        md_table.append(row_str)

    return "\n".join(md_table)
