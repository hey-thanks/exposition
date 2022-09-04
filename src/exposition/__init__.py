from pathlib import Path
import inspect

from . import markdown as md
from .common import *


__all__ = ['Document']


class Document:
    def __init__(self):
        self._doc = []
        self._ref_links = []

    def create_ref_link(self, format, target, text, title=None, ref_id=None):
        if format == Format.MD:
            link = md.RefLink(target, text, title=title, ref_id=ref_id)
        self._ref_links.append(link)
        return link

    def begin_code_section(self, format):
        if format == Format.MD:
            filename, lineno, *_ = inspect.getframeinfo(inspect.stack()[1].frame)
        self._doc.append(md.CodeSection(filename, lineno))

    def end_code_section(self):
        filename, lineno, *_ = inspect.getframeinfo(inspect.stack()[1].frame)

        # Get the most recently added CodeSection.
        try:
            code_section = [item for item in self._doc if isinstance(item, md.CodeSection)].pop()
        except IndexError:
            raise md.CodeSectionError('end_code_section found before begin_code_section')

        code_section.end_index = lineno

    def add_element(self, element):
        self._doc.append(element)
        if isinstance(element, md.RefLink):
            self._ref_links.append(element)

    def add_elements(self, *elements):
        for e in elements:
            self.add_element(e)

    def as_string(self):
        sep = NEWLINE * 3
        result = sep.join([item.write() for item in self._doc])
        if self._ref_links:
            result += sep
            result += NEWLINE.join([item.write_ref() for item in self._ref_links])

        return result

    def write_to_file(self, path, encoding='utf-8'):
        doc = self.as_string()
        Path(path).write_text(doc, encoding=encoding)
