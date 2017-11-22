"""
Utility for creating PDF results files.
"""
import fpdf


_table_template = """\
<table width="50%" align="center" border="0">
    <thead>
        <tr>
            <th width="60%">Name</th>
            <th width="40%">Time</th>
        </tr>
    </thead>
    <tbody>{body}</tbody>
</table>
"""

_row_template = """\
<tr>
    <td align="center">{Name}</td>
    <td align="center">{Time}</td>
</tr>
"""


class HTML2PDF(fpdf.FPDF, fpdf.HTMLMixin):
    pass


def write_pdf_results(output_file, results):
    """Write session results to a PDF file.

    Parameters
    ----------
    output_file : file
        Write PDF formatted results to this open file object. Note:
        this file should be opened in bytes mode, i.e., with mode "wb".
    results : list of dict
        List of results with the fields "name" and "time".
    """
    pdf = HTML2PDF()
    pdf.add_page()
    body = ''.join(_row_template.format(**result) for result in results)
    pdf.write_html(_table_template.format(body=body))
    output_file.write(pdf.output(dest='S'))
