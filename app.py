import streamlit as st
from PyPDF2 import PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from pdf2image import convert_from_bytes
import tempfile
import os
import io
import zipfile

def draw_grid(canvas_obj, a4_width, a4_height, spacing_mm=5):
    spacing = spacing_mm * mm
    for x in range(0, int(a4_width), int(spacing)):
        canvas_obj.setStrokeColor(colors.lightgrey)
        canvas_obj.setLineWidth(0.25)
        canvas_obj.line(x, 0, x, a4_height)
    for y in range(0, int(a4_height), int(spacing)):
        canvas_obj.setStrokeColor(colors.lightgrey)
        canvas_obj.setLineWidth(0.25)
        canvas_obj.line(0, y, a4_width, y)

def merge_pdf_slides(pdf_bytes, num_slide_per_page):
    images = convert_from_bytes(pdf_bytes, fmt='jpeg', grayscale=True)
    a4_width, a4_height = A4
    output_buffer = io.BytesIO()
    c = canvas.Canvas(output_buffer, pagesize=A4)

    for i in range(0, len(images), num_slide_per_page):
        draw_grid(c, a4_width, a4_height)
        for j in range(num_slide_per_page):
            if i + j < len(images):
                img = images[i + j]
                target_height = a4_height / num_slide_per_page
                aspect = img.width / img.height
                target_width = target_height * aspect

                x_pos = a4_width - target_width - 10  # align right with 10pt margin
                y_pos = a4_height - (j + 1) * target_height

                with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as img_file:
                    img.save(img_file.name, 'JPEG')
                    c.drawImage(img_file.name, x_pos, y_pos, width=target_width, height=target_height)
        c.showPage()
    c.save()
    output_buffer.seek(0)
    return output_buffer

st.title("Merge Slides to A4 with Grid")

uploaded_files = st.file_uploader("Upload one or more PDF files", type="pdf", accept_multiple_files=True)
num_slides = st.slider("Slides per A4 page", min_value=1, max_value=6, value=3)

if uploaded_files:
    if st.button("Run Merge"):
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zipf:
                for file in uploaded_files:
                    merged_pdf = merge_pdf_slides(file.read(), num_slides)
                    pdf_name = os.path.splitext(file.name)[0] + "_merged.pdf"
                    zipf.writestr(pdf_name, merged_pdf.read())

            st.success("\u2705 All files processed. Click below to download the ZIP.")
            st.download_button("Download ZIP of Merged PDFs", zip_buffer.getvalue(), "merged_pdfs.zip", "application/zip")
