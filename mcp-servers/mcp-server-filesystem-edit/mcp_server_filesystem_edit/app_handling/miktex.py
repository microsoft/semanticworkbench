# Copyright (c) Microsoft. All rights reserved.

import subprocess
from pathlib import Path


def compile_tex_to_pdf(tex_file: Path) -> tuple[bool, str]:
    # Get the last modified time of the pdf file, if it exists
    pdf_file = tex_file.with_suffix(".pdf")
    if pdf_file.exists():
        last_modified_time = pdf_file.stat().st_mtime
    else:
        last_modified_time = 0

    output_dir = tex_file.parent

    cmd = f'pdflatex -interaction=nonstopmode -output-directory="{output_dir}" "{str(tex_file)}"'

    try:
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        output = process.stdout + "\n" + process.stderr

        # Check if the pdf changed (by comparing the last modified time)
        if pdf_file.exists() and pdf_file.stat().st_mtime > last_modified_time:
            return True, output
        else:
            return False, output
    except Exception as e:
        output = f"Error running pdflatex: {str(e)}"
        return False, output

