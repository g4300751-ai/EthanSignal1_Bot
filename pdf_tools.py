"""
PDF merge/split helpers. Files are handled as in-memory byte streams
so nothing needs to persist on disk between requests.
"""
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter


def merge_pdfs(file_streams: list) -> BytesIO:
    writer = PdfWriter()
    for stream in file_streams:
        reader = PdfReader(stream)
        for page in reader.pages:
            writer.add_page(page)
    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output


def split_pdf(file_stream, start_page: int, end_page: int) -> BytesIO:
    reader = PdfReader(file_stream)
    total_pages = len(reader.pages)
    start = max(1, start_page)
    end = min(total_pages, end_page)

    if start > end or start > total_pages:
        raise ValueError(
            f"Invalid page range. This PDF has {total_pages} pages."
        )

    writer = PdfWriter()
    for i in range(start - 1, end):
        writer.add_page(reader.pages[i])

    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output
