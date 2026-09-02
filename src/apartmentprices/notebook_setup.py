import itables.options as itables_options
import pandas as pd
from IPython.display import HTML, display
from itables import init_notebook_mode


def setup():
    pd.set_option("display.float_format", "{:.4f}".format)

    init_notebook_mode(all_interactive=True)
    itables_options.style = "table-layout:auto;width:auto;margin:0;caption-side:bottom"

    display(
        HTML("""
    <style>
    html, body, .itables {
        background-color: var(--vscode-editor-background) !important;
        font-family: var(--vscode-editor-font-family), sans-serif !important;
        font-size: var(--vscode-editor-font-size, 13px) !important;
    }
    .dt-container,
    .dataTables_wrapper,
    .dataTables_length,
    .dataTables_filter,
    .dataTables_info,
    .dataTables_paginate {
        background-color: var(--vscode-editor-background) !important;
        color: var(--vscode-editor-foreground) !important;
    }
    .dt-container {
        border: 1px solid var(--vscode-panel-border, #444) !important;
        border-radius: 6px !important;
        padding: 10px !important;
    }
    .dataTable {
        background-color: var(--vscode-editor-background) !important;
        color: var(--vscode-editor-foreground) !important;
        border-collapse: separate !important;
        border-spacing: 0 !important;
    }
    .dataTable.dataTable thead th {
        background-color: var(--vscode-editorWidget-background) !important;
        color: var(--vscode-editor-foreground) !important;
        border-bottom: 2px solid var(--vscode-panel-border, #444) !important;
        padding: 8px 12px !important;
    }
    .dataTable.dataTable tbody td {
        padding: 6px 12px !important;
        border-bottom: 1px solid var(--vscode-panel-border, #333) !important;
    }
    .dataTable tbody tr:nth-child(even) {
        background-color: var(--vscode-editorWidget-background) !important;
    }
    .dataTable tr:hover td {
        background-color: var(--vscode-list-hoverBackground) !important;
        transition: background-color 0.15s ease-in-out;
    }
    .dt-search input, .dt-length select {
        background-color: var(--vscode-input-background) !important;
        color: var(--vscode-input-foreground) !important;
        border: 1px solid var(--vscode-input-border) !important;
        border-radius: 4px !important;
        padding: 4px 8px !important;
    }
    .dt-search input:focus {
        outline: 1px solid var(--vscode-focusBorder) !important;
    }
    .paginate_button {
        background-color: var(--vscode-editor-background) !important;
        color: var(--vscode-editor-foreground) !important;
        border-radius: 4px !important;
        margin: 0 2px !important;
    }
    .paginate_button:hover {
        background-color: var(--vscode-list-hoverBackground) !important;
    }
    .paginate_button.current {
        background-color: var(--vscode-list-activeSelectionBackground) !important;
        color: var(--vscode-list-activeSelectionForeground) !important;
        border-radius: 4px !important;
    }
    .paginate_button.disabled {
        color: var(--vscode-disabledForeground) !important;
    }
    </style>
    """)
    )
