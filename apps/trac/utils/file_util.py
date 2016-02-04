import xlrd


def xls_to_dictreader(xls_contents, sheet_index=0):
    """Create a `csv.DictReader` object from a .xls file.
    
    Parameters
    ----------
    xls_contents : string
        Input file contents stored as a string.
    sheet_index : int, optional
        Read the data from this sheet in the workbook.

    Returns
    -------
    List of dicts
        That can be iterated over in the same way as `csv.DictReader` can be
        iterated over.
    """
    book = xlrd.open_workbook(file_contents=xls_contents)
    sheet = book.sheet_by_index(sheet_index)
    headers = sheet.row_values(0)
    return [dict(zip(headers, sheet.row_values(row)))
            for row in xrange(1, sheet.nrows)]
