from __future__ import annotations

from rich.markup import escape


class RichMarkup:
    def markup_link(self, link: str, title: str):
        return f"[link={link}]{self.markup_title(title)}[/]"

    @staticmethod
    def markup_title(title: str):
        return f"[green]{escape(title)}[/]"
