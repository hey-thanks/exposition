from enum import Enum
import textwrap


class ExpositionBaseError(Exception):
    pass


NEWLINE = '\n'
EMPTY_STRING = ''
SPACE = ' '
TAB = '\t'
TAB_WIDTH = 4
SPACED_TAB = SPACE * TAB_WIDTH


def wrap_text(text, prefix=''):
    return textwrap.fill(text,
                         initial_indent=prefix,
                         subsequent_indent=prefix,
                         drop_whitespace=False,
                         replace_whitespace=False)


class HeaderStyle(Enum):
    ATX = 0
    SETEXT = 1


class Output(str, Enum):
    MD = '.md'
    ASCIIDOC = '.adoc'
    RST = '.rst'


class Format(str, Enum):
    MD = 'md'
    ASCIIDOC = 'adoc'
    RST = 'rst'
