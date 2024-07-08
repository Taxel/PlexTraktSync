from __future__ import annotations

from rich.highlighter import RegexHighlighter


class RichHighlighter(RegexHighlighter):
    base_style = "repr."

    highlights = [
        r"(?P<path>\B(\/[\w\.\-\_\+]+)*\/)(?P<filename>[\w\.\-\_\+]*)?",
        r"(?P<number>(?<!\w)\-?[0-9]+\.?[0-9]*(e[\-\+]?\d+?)?\b|0x[0-9a-fA-F]*)",
        r"(?P<attrib_name>[\w_]{1,50})=(?P<attrib_value>\"?[\w_]+\"?)?",
        r"(?P<tag_start>\<)(?P<tag_name>(?:Movie|Episode|Show):\d+:[^>]+)(?P<tag_end>\>)",
        r"(?P<tag_start>\<)(?P<tag_name>(?:PlexGuid|Guid|PlexLibrarySection):[^>]+)(?P<tag_end>\>)",
        r"(?P<tag_start>\<)(?P<tag_name>(?:imdb|tmdb|tvdb|local):(?:(?:tt)?\d+:)[^>]+)(?P<tag_end>\>)",
        r"\b(?P<bool_true>True)\b|\b(?P<bool_false>False)\b|\b(?P<none>None)\b",
        r"(?<![\\\w])(?P<str>b?\'\'\'.*?(?<!\\)\'\'\'|b?\'.*?(?<!\\)\'|b?\"\"\".*?(?<!\\)\"\"\"|b?\".*?(?<!\\)\")",
        r"(?P<url>(file|https|http|ws|wss):\/\/[0-9a-zA-Z\$\-\_\+\!`\(\)\,\.\?\/\;\:\&\=\%\#]*)",
    ]
