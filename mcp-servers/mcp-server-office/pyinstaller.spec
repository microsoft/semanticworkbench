# PyInstaller spec file to create a single executable for mcp-server-office

from PyInstaller.utils.hooks import collect_submodules

# Project-specific entry point
entry_point = 'mcp_server/start.py'

def make_spec():
    # Add required packages and collect submodules.
    hidden_imports = collect_submodules('pyngrok')

    return {
        'name': 'mcp-server-office',
        'script': entry_point,
        'onefile': True,
        'hiddenimports': hidden_imports,
        'console': True,
    }

if __name__ == '__main__':
    # Generate the specification
    make_spec()
