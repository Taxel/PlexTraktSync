from rich.console import Console

from plextraktsync.rich_addons import RichHighlighter

console = Console(highlighter=RichHighlighter())
print = console.print
