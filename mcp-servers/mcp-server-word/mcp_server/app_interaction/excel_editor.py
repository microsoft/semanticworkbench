# Copyright (c) Microsoft. All rights reserved.

import pythoncom
import win32com.client as win32


def get_excel_app():
    """Connect to Excel if it is running, or start a new instance."""
    try:
        # Try connecting to an existing instance of Excel
        excel = win32.GetActiveObject("Excel.Application")
    except Exception:
        # If not running, create a new instance
        excel = win32.Dispatch("Excel.Application")
    # Make Excel visible
    excel.Visible = True
    return excel


def get_active_workbook(excel):
    """Return an active Excel workbook, or create one if none is open."""
    if excel.Workbooks.Count == 0:
        # If there are no workbooks, add a new one
        return excel.Workbooks.Add()
    else:
        return excel.ActiveWorkbook


def get_worksheet_content(worksheet):
    """Return the content of the worksheet formatted as a markdown table."""
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


def get_workbook_content(workbook):
    """Return the content of the first worksheet in the workbook."""
    # Get the first worksheet
    worksheet = workbook.Worksheets(1)
    return get_worksheet_content(worksheet)


def main():
    # Initialize COM
    pythoncom.CoInitialize()

    # Connect to Excel application and get the active workbook
    excel = get_excel_app()
    workbook = get_active_workbook(excel)

    print("Connected to Excel.")

    # Read the content of the first worksheet
    content = get_workbook_content(workbook)

    # Print the markdown table
    print(content)


if __name__ == "__main__":
    main()
