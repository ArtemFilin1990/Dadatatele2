from __future__ import annotations

import io


def build_pdf(text: str) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        stream = io.BytesIO()
        c = canvas.Canvas(stream, pagesize=A4)
        y = 800
        for line in text.splitlines():
            c.drawString(30, y, line[:110])
            y -= 14
            if y < 40:
                c.showPage()
                y = 800
        c.save()
        stream.seek(0)
        return stream.read()
    except Exception:
        return text.encode("utf-8")
