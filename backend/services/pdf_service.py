# services/pdf_service.py
import os
import html
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from config import Config


class _PageCounter:
    """Helper untuk menghitung total halaman dan menggambar dekorasi halaman."""
    def __init__(self):
        self.pages = []

    def on_page(self, canvas, doc):
        self.pages.append(doc.page)
        self._draw_decorations(canvas, doc)

    def _draw_decorations(self, canvas, doc):
        canvas.saveState()

        # 1. Band warna aksen atas (Medical Teal-Blue)
        canvas.setFillColor(colors.HexColor('#0F766E'))
        canvas.rect(0, 782, 612, 10, fill=True, stroke=False)

        # 2. Garis pembatas footer halus
        canvas.setStrokeColor(colors.HexColor('#E2E8F0'))
        canvas.setLineWidth(1)
        canvas.line(40, 55, 572, 55)

        # 3. Keterangan teks footer
        canvas.setFont('Helvetica-Bold', 8)
        canvas.setFillColor(colors.HexColor('#1E293B'))
        canvas.drawString(40, 38, "AIDEB")

        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#64748B'))
        canvas.drawString(95, 38, "|   Sistem Analisis Citra Medis Epilepsi berbasis Kecerdasan Buatan")

        # Nomor halaman dinamis (akan di-overwrite saat final pass via NumberedCanvas)
        page_num = doc.page
        canvas.drawRightString(572, 38, f"Halaman {page_num}")

        canvas.restoreState()


def _build_main_page(story, report_data, image_path, styles):
    """
    Membangun halaman utama laporan: kop surat, identitas pasien,
    gambar MRI representatif, dan hasil diagnosis AI.
    Mengembalikan path file temporary jika DICOM di-convert.
    """
    temp_image_path = None

    # Proteksi karakter spesial XML agar tidak merusak parser Paragraph ReportLab
    nama_pasien = html.escape(str(report_data.get('nama_pasien', 'Anonim')))
    no_rm = html.escape(str(report_data.get('no_rm', '-')))
    timestamp = html.escape(str(report_data.get('timestamp', '-')))
    analysis_id = html.escape(str(report_data.get('analysis_id', '-')))
    prediction = html.escape(str(report_data.get('prediction', '-')))
    confidence = html.escape(str(report_data.get('confidence', '-'))).replace('.', ',')

    # Custom Styles
    title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#0F766E'),
        spaceAfter=2
    )

    subtitle_style = ParagraphStyle(
        'HeaderSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.HexColor('#0D9488'),
        spaceAfter=8
    )

    institution_style = ParagraphStyle(
        'InstInfo',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=colors.HexColor('#64748B'),
        leading=11
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.HexColor('#0F766E'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#334155'),
        leading=13
    )

    body_bold_style = ParagraphStyle(
        'BodyTextBoldCustom',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    # ==================== KOP SURAT MODERN ====================
    header_left = [
        Paragraph("AIDEB", title_style),
        Paragraph("INTELLIGENT MEDICAL IMAGING REPORT", subtitle_style)
    ]

    header_right = [
        Paragraph("<b>LABORATORIUM RADIOLOGI DIGITAL</b>", ParagraphStyle('InstBold', parent=institution_style, fontName='Helvetica-Bold', textColor=colors.HexColor('#1E293B'))),
        Paragraph("Poltekkes Kemenkes Semarang", institution_style),
        Paragraph("Email: aideb.support@poltekkes-smg.ac.id", institution_style)
    ]

    header_table = Table([[header_left, header_right]], colWidths=[300, 230])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # ==================== TABEL IDENTITAS PASIEN (CARD STYLE) ====================
    patient_info_data = [
        [Paragraph(f"<b>NAMA PASIEN</b>", body_bold_style), Paragraph(f": &nbsp; {nama_pasien}", body_style),
         Paragraph(f"<b>NO. REKAM MEDIS</b>", body_bold_style), Paragraph(f": &nbsp; {no_rm}", body_style)],
        [Paragraph(f"<b>TANGGAL ANALISIS</b>", body_bold_style), Paragraph(f": &nbsp; {timestamp}", body_style),
         Paragraph(f"<b>ID TRANSAKSI</b>", body_bold_style), Paragraph(f": &nbsp; {analysis_id}", body_style)]
    ]

    info_table = Table(patient_info_data, colWidths=[120, 145, 120, 145])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F0FDFA')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LINEBEFORE', (0,0), (0,-1), 4, colors.HexColor('#0F766E')),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#CCFBF1')),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 12))

    # ==================== LAMPIRAN CITRA MRI (FRAMED CARD) ====================
    story.append(Paragraph("CITRA MEDIS YANG DIANALISIS (MRI)", section_heading))
    try:
        image_path_to_use = image_path
        if image_path.lower().endswith('.dcm'):
            try:
                import pydicom
                import numpy as np
                import cv2

                ds = pydicom.dcmread(image_path)
                img_array = ds.pixel_array

                img_min = np.min(img_array)
                img_max = np.max(img_array)
                if img_max > img_min:
                    img_array = ((img_array - img_min) / (img_max - img_min) * 255).astype(np.uint8)
                else:
                    img_array = np.zeros_like(img_array, dtype=np.uint8)

                if len(img_array.shape) == 2:
                    img_bgr = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
                elif len(img_array.shape) == 3:
                    if img_array.shape[2] == 1:
                        img_bgr = cv2.cvtColor(img_array[:, :, 0], cv2.COLOR_GRAY2BGR)
                    elif img_array.shape[2] == 3:
                        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    elif img_array.shape[2] == 4:
                        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
                    else:
                        img_bgr = img_array
                else:
                    img_bgr = img_array

                temp_image_path = image_path + ".temp.png"
                cv2.imwrite(temp_image_path, img_bgr)
                image_path_to_use = temp_image_path
            except Exception as dcm_err:
                print(f"Error converting DICOM to PNG for PDF: {dcm_err}")

        # Menampilkan gambar tunggal asli saja
        scan_img = Image(image_path_to_use, width=200, height=200)
        scan_img.hAlign = 'CENTER'

        image_table = Table([[scan_img]], colWidths=[220], rowHeights=[220])
        image_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
            ('PADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(image_table)
    except Exception as e:
        story.append(Paragraph(f"<i>[Gagal memproses lampiran citra medis: {html.escape(str(e))}]</i>", body_style))
    story.append(Spacer(1, 12))

    # ==================== INTERPRETASI & DIAGNOSIS AI (ALERT BOX) ====================
    story.append(Paragraph("HASIL ANALISIS KECERDASAN BUATAN (AI)", section_heading))

    is_epilepsi = "epilepsi" in prediction.lower()
    bg_color = colors.HexColor('#FFF1F2') if is_epilepsi else colors.HexColor('#ECFDF5')
    text_color = colors.HexColor('#BE123C') if is_epilepsi else colors.HexColor('#047857')
    border_color = colors.HexColor('#F43F5E') if is_epilepsi else colors.HexColor('#10B981')

    status_label = "TERDETEKSI ADANYA EPILEPSI" if is_epilepsi else "NORMAL (TIDAK TERDETEKSI EPILEPSI)"

    result_title_style = ParagraphStyle(
        'ResultTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=text_color,
        spaceAfter=4
    )

    result_detail_style = ParagraphStyle(
        'ResultDetail',
        parent=body_style,
        fontSize=8.5,
        textColor=colors.HexColor('#475569')
    )

    # Tambahkan info jumlah citra jika multifile
    total_files = report_data.get('total_files', 1)
    if isinstance(total_files, str):
        try:
            total_files = int(total_files)
        except ValueError:
            total_files = 1

    multi_info = ""
    if total_files > 1:
        multi_info = f"<br/><font size=7 color='#64748B'><i>Hasil diagnosis dominan dari {total_files} citra yang dianalisis.</i></font>"

    result_box_data = [
        [Paragraph(f"<b>STATUS DIAGNOSIS: &nbsp;{status_label}</b>{multi_info}", result_title_style)],
        [Paragraph(f"<i>Klasifikasi dilakukan menggunakan arsitektur deep learning YOLOv8n-cls yang telah dioptimalkan untuk deteksi epilepsi pada citra MRI otak.</i>", ParagraphStyle('ResultDesc', parent=result_detail_style, fontSize=7.5))]
    ]

    result_table = Table(result_box_data, colWidths=[530])
    result_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_color),
        ('PADDING', (0,0), (-1,-1), 10),
        ('LINEBEFORE', (0,0), (0,-1), 4, border_color),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(result_table)
    story.append(Spacer(1, 20))

    # ==================== TANDA TANGAN / DISCLAIMER (FOOTER CARD) ====================
    disclaimer_text = (
        "<font size=7 color='#64748B'><b>DISCLAIMER MEDIS:</b><br/>"
        "Laporan analisis ini dihasilkan secara otomatis oleh sistem kecerdasan buatan komputer (AIDEB). "
        "Hasil ini bersifat sebagai diagnosis sementara untuk membantu skrining awal. Laporan ini <b>wajib</b> "
        "ditinjau, dikonfirmasi, dan ditandatangani oleh Dokter Spesialis Neurologi sebelum digunakan sebagai "
        "dasar keputusan klinis atau tindakan medis.</font>"
    )

    footer_data = [
        [Paragraph(disclaimer_text, body_style),
         Paragraph("<b>Dokter Spesialis Radiologi,</b><br/><br/><br/><br/>______________________<br/>NIP/SIP. ", ParagraphStyle('DocSign', parent=body_style, alignment=1))]
    ]

    footer_table = Table(footer_data, colWidths=[350, 180])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('LINEBEFORE', (1,0), (1,0), 0.5, colors.HexColor('#E2E8F0')),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(footer_table)

    return temp_image_path


def _convert_image_for_pdf(image_path):
    """
    Konversi file gambar (termasuk DICOM) ke path yang bisa dibaca ReportLab.
    Mengembalikan (path_to_use, temp_path_or_None).
    """
    if not image_path.lower().endswith('.dcm'):
        return image_path, None

    try:
        import pydicom
        import numpy as np
        import cv2

        ds = pydicom.dcmread(image_path)
        img_array = ds.pixel_array

        img_min = np.min(img_array)
        img_max = np.max(img_array)
        if img_max > img_min:
            img_array = ((img_array - img_min) / (img_max - img_min) * 255).astype(np.uint8)
        else:
            img_array = np.zeros_like(img_array, dtype=np.uint8)

        if len(img_array.shape) == 2:
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
        elif len(img_array.shape) == 3:
            if img_array.shape[2] == 1:
                img_bgr = cv2.cvtColor(img_array[:, :, 0], cv2.COLOR_GRAY2BGR)
            elif img_array.shape[2] == 3:
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            elif img_array.shape[2] == 4:
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
            else:
                img_bgr = img_array
        else:
            img_bgr = img_array

        temp_path = image_path + ".temp_attach.png"
        cv2.imwrite(temp_path, img_bgr)
        return temp_path, temp_path
    except Exception:
        return image_path, None


def _build_attachment_pages(story, per_image_results, styles):
    """
    Membangun halaman lampiran dengan detail deteksi tiap gambar MRI.
    Setiap gambar ditampilkan dalam card frame berisi thumbnail, nama file, dan hasil prediksi.
    Mengembalikan list path temporary file yang perlu di-cleanup.
    """
    if not per_image_results or len(per_image_results) == 0:
        return []

    temp_paths = []

    # Page break sebelum lampiran
    story.append(PageBreak())

    # Heading lampiran
    section_heading = ParagraphStyle(
        'AttachSectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#0F766E'),
        spaceBefore=4,
        spaceAfter=10
    )

    body_style = ParagraphStyle(
        'AttachBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=colors.HexColor('#334155'),
        leading=11
    )

    story.append(Paragraph("LAMPIRAN — Detail Hasil Deteksi Tiap Citra MRI", section_heading))
    story.append(Paragraph(
        f"<font size=7 color='#64748B'>Total {len(per_image_results)} citra MRI dianalisis secara individual oleh model deep learning AIDEB.</font>",
        body_style
    ))
    story.append(Spacer(1, 10))

    # Build cards untuk setiap gambar (2 per baris)
    cards = []
    for idx, item in enumerate(per_image_results):
        filename = item.get('filename', f'citra_{idx+1}')
        pred = item.get('prediction', '-')
        conf = item.get('confidence', 0)
        is_epilepsi = 'epilepsi' in str(pred).lower()
        is_error = str(pred).lower() == 'error'

        # Warna card berdasarkan hasil
        if is_error:
            card_bg = colors.HexColor('#FEF2F2')
            card_border = colors.HexColor('#FCA5A5')
            label_color = '#DC2626'
            status_text = "ERROR"
        elif is_epilepsi:
            card_bg = colors.HexColor('#FFF1F2')
            card_border = colors.HexColor('#F43F5E')
            label_color = '#BE123C'
            status_text = "EPILEPSI"
        else:
            card_bg = colors.HexColor('#ECFDF5')
            card_border = colors.HexColor('#10B981')
            label_color = '#047857'
            status_text = "NORMAL"

        # Confidence text
        conf_text = f"{str(round(conf, 2)).replace('.', ',')}%" if not is_error else "-"

        # Load gambar thumbnail
        image_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        card_elements = []

        if os.path.exists(image_path):
            img_to_use, temp_path = _convert_image_for_pdf(image_path)
            if temp_path:
                temp_paths.append(temp_path)

            try:
                thumb = Image(img_to_use, width=120, height=120)
                thumb.hAlign = 'CENTER'
                card_elements.append(thumb)
            except Exception:
                card_elements.append(Paragraph("<i>[Gagal memuat gambar]</i>", body_style))
        else:
            card_elements.append(Paragraph("<i>[File tidak ditemukan]</i>", body_style))

        card_elements.append(Spacer(1, 4))

        # Nomor urut gambar
        card_elements.append(Paragraph(
            f"<font size=7 color='#94A3B8'>Citra #{idx+1}</font>",
            ParagraphStyle('CardIdx', parent=body_style, alignment=1)
        ))

        # Nama file (truncated)
        display_name = filename if len(filename) <= 25 else filename[:22] + "..."
        card_elements.append(Paragraph(
            f"<font size=6 color='#64748B'>{html.escape(display_name)}</font>",
            ParagraphStyle('CardFilename', parent=body_style, alignment=1)
        ))

        card_elements.append(Spacer(1, 3))

        # Hasil prediksi
        card_elements.append(Paragraph(
            f"<font size=9 color='{label_color}'><b>{status_text}</b></font>",
            ParagraphStyle('CardPred', parent=body_style, alignment=1)
        ))

        # Confidence
        card_elements.append(Paragraph(
            f"<font size=6 color='#94A3B8'>Confidence: {conf_text}</font>",
            ParagraphStyle('CardConf', parent=body_style, alignment=1)
        ))

        # Bungkus semua elemen card dalam tabel 1-cell (untuk border & background)
        inner_table = Table([[card_elements]], colWidths=[240])
        inner_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), card_bg),
            ('BOX', (0,0), (-1,-1), 1, card_border),
            ('PADDING', (0,0), (-1,-1), 10),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))

        cards.append(inner_table)

    # Layout: 2 kolom per baris
    rows = []
    for i in range(0, len(cards), 2):
        if i + 1 < len(cards):
            rows.append([cards[i], cards[i+1]])
        else:
            rows.append([cards[i], ""])

    if rows:
        grid_table = Table(rows, colWidths=[265, 265])
        grid_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('PADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(grid_table)

    return temp_paths


def generate_diagnosis_pdf(report_data, image_path, output_pdf_path, per_image_results=None):
    """
    Fungsi untuk merakit lembar hasil radiologi resmi ke dalam format PDF menggunakan ReportLab.
    
    Halaman 1: Laporan utama (kop surat, identitas, gambar representatif, diagnosis dominan, disclaimer).
    Halaman 2+: Lampiran detail tiap gambar MRI (jika multifile).
    """
    # 1. Inisialisasi dokumen berukuran kertas Letter dengan margin proporsional
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=45,
        bottomMargin=70
    )
    story = []

    # 2. Pengaturan Gaya Tulisan (Styles)
    styles = getSampleStyleSheet()

    # 3. Bangun halaman utama (tidak berubah dari struktur asli)
    temp_image_main = _build_main_page(story, report_data, image_path, styles)

    # 4. Bangun halaman lampiran jika ada multifile results
    temp_paths_attachment = []
    if per_image_results and len(per_image_results) > 1:
        temp_paths_attachment = _build_attachment_pages(story, per_image_results, styles)

    # 5. Page counter untuk dekorasi
    page_counter = _PageCounter()

    try:
        doc.build(story, onFirstPage=page_counter.on_page, onLaterPages=page_counter.on_page)
    finally:
        # Hapus berkas temporary png jika ada
        all_temps = [t for t in [temp_image_main] + temp_paths_attachment if t]
        for temp_path in all_temps:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as clean_err:
                    print(f"Error cleaning up temporary PNG: {clean_err}")