# exposition

A Python package designed to help you write documents, reports, etc.


## Output Formats

The goal is to implement the following output formats.

- [X] Markdown
- [ ] reStructuredText
- [ ] AsciiDoc


## Example

The following example demonstrates how this package could be used to write a
portion of this README.md file.

    from exposition import Document
    from exposition.markdown import *
    
    report = Document()
    
    report.add_elements(
        Header('exposition'),
        Paragraph('A Python package designed to help you write documents, reports, etc.'),
        Header('Output Formats', level=2),
        Paragraph('The goal is to implement the following output formats.'),
        List(['Markdown',          # Standard list; extensions not yet implemented.
              'reStructuredText',
              'AsciiDoc'])
    )
    
    report.write_to_file('README.md')