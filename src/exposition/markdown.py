from .common import *
import abc


def normalize_leading_whitespace(lines):
    num_leading_whitespace = []
    for line in lines:
        line_len = len(line)
        num_spaces = line_len - len(line.lstrip(SPACE))
        num_tabs = line_len - len(line.lstrip(TAB))
        num_leading_whitespace.append(num_spaces + num_tabs * TAB_WIDTH)

    min_leading_spaces = min([x for x in num_leading_whitespace if x > 0])
    output = [line.expandtabs(tabsize=TAB_WIDTH)[min_leading_spaces:] for line in lines]

    # Get rid of any empty lines before the 'real code' begins.
    start_index = 0
    for i, line in enumerate(output):
        if line:
            start_index = i
            break

    return output[start_index:]


class CodeSectionError(ExpositionBaseError):
    pass


class MarkDownContext(str, Enum):
    List = SPACED_TAB
    Paragraph = EMPTY_STRING
    BlockQuote = '> '


class Element(abc.ABC):
    context = []

    @classmethod
    def resolve_context(cls) -> str:
        return ''.join([ctx.value for ctx in reversed(cls.context)])

    def __init__(self):
        pass

    def __format__(self, format_spec):
        if format_spec == Format.MD:
            return self.write()

    @abc.abstractmethod
    def write(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def can_wrap(self) -> bool:
        """
        After the element has been properly styled into the desired
        format, can it wrap -- as is -- to the next line.

        """
        pass


class Header(Element):
    def __init__(self, text, level=1, style=HeaderStyle.ATX):
        super().__init__()
        self.text = text
        self.level = level
        self.style = style

    def write(self):
        if self.level < 1:
            self.level = 1
        if self.level > 6:
            self.level = 6

        prefix = self.resolve_context()
        result = prefix
        if self.style == HeaderStyle.ATX:
            result += '#' * self.level + ' ' + self.text
        elif self.style == HeaderStyle.SETEXT:
            result += self.text + '\n' + prefix
            if self.level == 1:
                result += '=' * len(self.text)
            else:
                result += '-' * len(self.text)

        return result.rstrip()

    @property
    def can_wrap(self):
        return False


class HorizontalRule(Element):
    def __init__(self, char=None, count=3):
        super().__init__()
        self.char = char or '*'
        self.count = count if count >= 3 else 3

    def write(self) -> str:
        return SPACE.join(self.char * self.count)

    @property
    def can_wrap(self) -> bool:
        return False


class List(Element):
    def __init__(self, *items, ordered=False):
        super().__init__()
        self.items = items
        self.ordered = ordered

    def _write_markdown(self, item, toplevel: bool = True) -> str:
        result = ''
        marker = '1.  ' if self.ordered else '*   '
        if isinstance(item, List):
            self.context.append(MarkDownContext.List)
            result += item.write() + NEWLINE
            self.context.pop()
        elif isinstance(item, Element):
            if toplevel:
                prefix = self.resolve_context()
                result += prefix + marker + item.write() + NEWLINE
            else:
                self.context.append(MarkDownContext.List)
                result += NEWLINE + item.write() + NEWLINE * 2
                self.context.pop()
        else:
            prefix = self.resolve_context()
            item = str(item)
            period_index = item.find('.')
            if period_index > 0:
                try:
                    item = str(int(item[:period_index])) + '\\.' + item[period_index + 1:]
                except ValueError:
                    pass
            result += prefix + marker + item + NEWLINE

        return result

    def write(self):
        result = ''
        for item in self.items:
            if isinstance(item, list):
                for i in item:
                    result += self._write_markdown(i, toplevel=True)
            else:
                result += self._write_markdown(item, toplevel=False)

        return result.rstrip()

    @property
    def can_wrap(self) -> bool:
        return False


class CodeBlock(Element):
    def __init__(self, lines):
        super().__init__()
        self.lines = lines

    def write(self):
        prefix = self.resolve_context()
        result = ''
        for line in self.lines:
            result += prefix + SPACED_TAB + line + NEWLINE

        return result.rstrip()

    @property
    def can_wrap(self) -> bool:
        return False


class Paragraph(Element):
    def __init__(self, *contents, space_between_elements=True,
                 no_space_before_period=True):
        super().__init__()
        self.contents = contents
        self.add_space = space_between_elements
        self.no_space_before_period = no_space_before_period

    def write(self) -> str:
        prefix = self.resolve_context()
        result = EMPTY_STRING
        acc = EMPTY_STRING
        for item in self.contents:
            if isinstance(item, str):
                acc += item
                if self.add_space and len(self.contents) > 1:
                    acc += SPACE
            elif isinstance(item, LineBreak):
                if acc:
                    acc = acc[:-1]
                result += wrap_text(acc, prefix=prefix)
                result += LineBreak().write()
                acc = EMPTY_STRING
            elif isinstance(item, Element):
                if item.can_wrap:
                    self.context.append(MarkDownContext.Paragraph)
                    acc += item.write()
                    if self.add_space and len(self.contents) > 1:
                        acc += SPACE
                    self.context.pop()
                else:
                    if acc:
                        acc = acc[:-1]
                    result += wrap_text(acc, prefix=prefix) + NEWLINE
                    acc = EMPTY_STRING

                    self.context.append(MarkDownContext.Paragraph)
                    result += item.write()
                    self.context.pop()
                    result += NEWLINE

        if acc:
            result += wrap_text(acc, prefix=prefix)

        if self.no_space_before_period:
            result = result.replace(' .', '.')

        return result

    @property
    def can_wrap(self) -> bool:
        return True


class Link(Element):
    def __init__(self, target, text=None, title=None):
        super().__init__()
        self.text = text
        self.target = target
        self.title = title

    def write(self) -> str:
        prefix = self.resolve_context()
        result = prefix
        if self.text is None and self.title is None:
            result += '<{}>'.format(self.target)
            return result
        else:
            result += '[{}]'.format(self.text) if self.text else EMPTY_STRING
            if self.title is not None:
                result += '({} "{}")'.format(self.target, self.title)
            else:
                result += '({})'.format(self.target)

        return result

    @property
    def can_wrap(self) -> bool:
        return False


class RefLink(Element):
    def __init__(self, target, text, title=None, ref_id=None):
        super().__init__()
        self.target = target
        self.text = text
        self.title = title
        self.ref_id = ref_id

    def write(self) -> str:
        prefix = self.resolve_context()
        display_text = '[{}]'.format(self.text)
        result = prefix + display_text
        if self.ref_id is not None:
            result += '[{}]'.format(self.ref_id)
        else:
            result += '[]'

        return result

    def write_ref(self) -> str:
        ref_id = self.text if self.ref_id is None else str(self.ref_id)
        result = '[{}]: <{}>'.format(ref_id, self.target)
        if self.title is not None:
            result += SPACE + '({})'.format(self.title)

        return result

    @property
    def can_wrap(self) -> bool:
        return False


class Bold(Element):
    def __init__(self, text):
        super().__init__()
        self.text = text

    def write(self) -> str:
        if isinstance(self.text, Element):
            return '**{}**'.format(self.text.write())
        else:
            return '**{}**'.format(self.text)

    @property
    def can_wrap(self) -> bool:
        return True


class Italic(Element):
    def __init__(self, text):
        super().__init__()
        self.text = text

    def write(self) -> str:
        if isinstance(self.text, Element):
            return '*{}*'.format(self.text.write())
        else:
            return '*{}*'.format(self.text)

    @property
    def can_wrap(self) -> bool:
        return True


class Code(Element):
    def __init__(self, text):
        super().__init__()
        self.text = text

    def write(self) -> str:
        if isinstance(self.text, Element):
            result = self.text.write()
        else:
            result = str(self.text)

        backtick = '``' if '`' in result else '`'
        return backtick + result + backtick

    @property
    def can_wrap(self) -> bool:
        return False


class Image(Element):
    def __init__(self, alt_text, path, title=None, target=None):
        super().__init__()
        self.alt_text = alt_text
        self.path = path
        self.title = title
        self.target = target

    def write(self) -> str:
        display_text = '![{}]'.format(self.alt_text)
        result = display_text
        if self.title is not None:
            result += '({} "{}")'.format(self.path, self.title)
        else:
            result += '({})'.format(self.path)

        if self.target is not None:
            result = '[{}]({})'.format(result, self.target)

        prefix = self.resolve_context()
        return prefix + result

    @property
    def can_wrap(self) -> bool:
        return False


class CodeSection(Element):
    def __init__(self, filename, start_index, end_index=None, encoding='utf-8'):
        super().__init__()
        self.filename = filename
        self.start_index = start_index
        self.end_index = end_index
        self.encoding = encoding

    def write(self) -> str:
        lines = self.get_lines()
        prefix = self.resolve_context()
        result = ''
        for line in lines:
            if not line:
                result += prefix + NEWLINE
            else:
                result += prefix + SPACED_TAB + line

        return result.rstrip()

    def get_lines(self):
        with open(self.filename, 'r', encoding=self.encoding) as f_in:
            lines = f_in.readlines()[self.start_index: self.end_index - 1]
        lines = normalize_leading_whitespace(lines)
        return lines

    @property
    def can_wrap(self) -> bool:
        return False


class BlockQuote(Element):
    def __init__(self, *text):
        super().__init__()
        self.text = text

    def write(self) -> str:
        prefix = self.resolve_context() + '> '
        result = ''
        acc = ''
        for item in self.text:
            if isinstance(item, str):
                if item:
                    acc += item
                    acc += SPACE if len(self.text) > 1 else EMPTY_STRING
                else:
                    if acc:
                        acc = acc[:-1]
                        result += wrap_text(acc, prefix=prefix)
                        acc = ''
                        result += NEWLINE
                    result += '> ' + NEWLINE
            elif isinstance(item, LineBreak):
                if acc:
                    acc = acc[:-1]
                    result += wrap_text(acc, prefix=prefix)
                    acc = ''
                result += LineBreak().write()
            elif isinstance(item, Element):
                if item.can_wrap:
                    self.context.append(MarkDownContext.BlockQuote)
                    acc += item.write()
                    acc += SPACE if len(self.text) > 1 else EMPTY_STRING
                    self.context.pop()
                else:
                    if acc:
                        acc = acc[:-1]
                        result += wrap_text(acc, prefix=prefix) + NEWLINE
                        acc = ''

                    self.context.append(MarkDownContext.BlockQuote)
                    result += item.write()
                    self.context.pop()
                    result += NEWLINE
                    if self.context and self.context[-1] == MarkDownContext.BlockQuote:
                        result += '> '

        if acc:
            result += wrap_text(acc, prefix=prefix)

        result = result.replace(' .', '.').replace('> >', '>>')

        return result

    @property
    def can_wrap(self) -> bool:
        return False


class Table(Element):
    def __init__(self, rows):
        super().__init__()
        self.rows = rows

    def write(self) -> str:
        col_max_len = []
        for col_index in range(len(self.rows[0])):
            max_len = -1
            for row_index in range(len(self.rows)):
                max_len = max(max_len, len(str(self.rows[row_index][col_index])))
            col_max_len.append(max_len)

        result = ''
        for i, row in enumerate(self.rows):
            row_str = '| '
            for width, entry in zip(col_max_len, row):
                row_str += '{} '.format(entry) + ' ' * (width - len(str(entry))) + '| '
            result += row_str[:-1] + '\n'

            if i == 0:
                header_sep = '|'
                for width in col_max_len:
                    header_sep += '-' * (width + 2) + '|'
                result += header_sep + '\n'

        return result.rstrip()

    @property
    def can_wrap(self) -> bool:
        return False


class LineBreak(Element):
    def __init__(self):
        super().__init__()

    def write(self) -> str:
        return SPACE * 2 + NEWLINE

    @property
    def can_wrap(self) -> bool:
        return False
