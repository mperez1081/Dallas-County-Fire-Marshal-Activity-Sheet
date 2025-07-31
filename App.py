"""
Lightweight HTTP server for generating Daily Beat Activity Report PDFs.

This backend avoids external dependencies by using Python's standard library to
serve HTTP requests and Pillow (PIL), which is available in this environment,
to render the PDF.  A single endpoint (/generate-pdf) accepts POST requests
containing JSON data from the frontend, generates a two‑page PDF using the
provided information, and returns it as a downloadable attachment.

To run the server, execute this script:
    python3 app.py

Then open the index.html file in a browser (e.g., Chrome) and fill in the
form.  When you click "Generate PDF" the browser will download a PDF
rendering of your report.  Ensure that the dallas_seal.png image is present
in the same directory as this script so it can be included in the header.
"""

import json
import io
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
from urllib.parse import urlparse
from PIL import Image, ImageDraw, ImageFont


def draw_text(draw, position, text, font, fill=(0, 0, 0)):
    """Helper function to draw multiline text.

    Splits the input text on newline characters and draws each line with
    consistent vertical spacing.  Returns the y coordinate after drawing.
    """
    x, y = position
    for line in text.split('\n'):
        draw.text((x, y), line, font=font, fill=fill)
        y += font.getsize(line)[1] + 2  # add small spacing between lines
    return y


def build_pdf(data: dict) -> io.BytesIO:
    """Create a two‑page PDF using Pillow based on the provided data.

    The first page contains the header, location, report information, post
    specific/completion times, reports generated, vehicle report cards, and
    vehicle inspection sections.  The second page contains notes and the
    signature fields.

    Args:
        data: A dictionary with form field values.

    Returns:
        BytesIO containing the PDF data.
    """
    # Define page dimensions (US letter at 72 DPI)
    PAGE_WIDTH, PAGE_HEIGHT = 612, 792
    margin_left = 40
    margin_right = 40
    margin_top = 40
    margin_bottom = 40

    # Load the seal image if available
    try:
        seal = Image.open('dallas_seal.png').convert('RGBA')
        seal.thumbnail((60, 60), Image.ANTIALIAS)
    except Exception:
        seal = None

    # Use default font; fallback if truetype not available
    try:
        header_font = ImageFont.truetype('arial.ttf', 14)
        subheader_font = ImageFont.truetype('arial.ttf', 10)
        normal_font = ImageFont.truetype('arial.ttf', 9)
        bold_font = ImageFont.truetype('arialbd.ttf', 9)
    except Exception:
        header_font = ImageFont.load_default()
        subheader_font = ImageFont.load_default()
        normal_font = ImageFont.load_default()
        bold_font = ImageFont.load_default()

    # Create two blank pages
    pages = []
    page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), 'white')
    draw = ImageDraw.Draw(page)
    y = margin_top

    # Draw header
    if seal:
        page.paste(seal, (margin_left, y), seal)
    header_x = margin_left + 70
    # Underlined main title
    title_text = 'Dallas County Fire Marshal'
    draw.text((header_x, y), title_text, font=header_font, fill=(0, 0, 0))
    title_width, title_height = header_font.getsize(title_text)
    # Draw underline
    underline_y = y + title_height + 2
    draw.line((header_x, underline_y, header_x + title_width, underline_y), fill=(0, 0, 0), width=1)
    # Subtitles
    y_sub = underline_y + 4
    draw.text((header_x, y_sub), 'Police, Fire and Safety Services (GLOA)', font=subheader_font, fill=(0, 0, 0))
    draw.text((header_x, y_sub + 14), 'Service First, Always', font=subheader_font, fill=(0, 0, 0))
    # Report title
    draw.text((header_x, y_sub + 28), 'DAILY BEAT ACTIVITY REPORT', font=header_font, fill=(0, 0, 0))
    y = y + 60

    # Location
    draw.text((margin_left, y), f'Location: {data.get("location", "")}', font=normal_font, fill=(0, 0, 0))
    y += 20

    # Report Information
    draw.text((margin_left, y), 'Report Information', font=bold_font, fill=(0, 0, 0))
    y += 16
    report_rows = [
        (f"Officer Name: {data.get('officerName', '')}", f"Badge Number: {data.get('badgeNumber', '')}"),
        (f"Key Set: {data.get('keySet', '')}", f"Date: {data.get('reportDate', '')}"),
        (f"Radio Number: {data.get('radioNumber', '')}", f"Number of Patrols: {data.get('patrols', '')}"),
        (f"OIC/Sgt Name: {data.get('oicName', '')}", f"Dispatcher(s): {data.get('dispatchers', '')}")
    ]
    for left_text, right_text in report_rows:
        draw.text((margin_left, y), left_text, font=normal_font, fill=(0, 0, 0))
        draw.text((PAGE_WIDTH/2, y), right_text, font=normal_font, fill=(0, 0, 0))
        y += 14

    y += 10
    # Post Specific / Completion Times
    draw.text((margin_left, y), 'Post Specific / Completion Times', font=bold_font, fill=(0, 0, 0))
    y += 16
    post_rows = [
        (f"Key/Equip Inventory Complete: {data.get('inventoryComplete', '')}", f"HHS Lock Up: {data.get('hhsLockUp', '')}"),
        (f"Basement: {data.get('basement', '')}", f"Roof Access: {data.get('roof', '')}"),
        (f"Upper Levels: {data.get('upperLevels', '')}", f"Mid-Levels: {data.get('midLevels', '')}"),
        (f"Lower Levels: {data.get('lowerLevels', '')}", f"Parking Lots: {data.get('parkingLots', '')}"),
        (f"Alarms: {data.get('alarms', '')}", f"Special Assignments: {data.get('specialAssignments', '')}"),
        (f"Other: {data.get('otherTasks', '')}", '')
    ]
    for left_text, right_text in post_rows:
        draw.text((margin_left, y), left_text, font=normal_font, fill=(0, 0, 0))
        if right_text:
            draw.text((PAGE_WIDTH/2, y), right_text, font=normal_font, fill=(0, 0, 0))
        y += 14

    y += 10
    # Reports Generated
    draw.text((margin_left, y), 'Reports Generated', font=bold_font, fill=(0, 0, 0))
    y += 16
    # Table header
    draw.text((margin_left, y), 'RMS #', font=bold_font, fill=(0, 0, 0))
    draw.text((margin_left + 100, y), 'Submitted?', font=bold_font, fill=(0, 0, 0))
    draw.text((margin_left + 200, y), 'Description', font=bold_font, fill=(0, 0, 0))
    y += 14
    reports = data.get('reports', [])
    if not reports:
        reports = [{'rms': '', 'submitted': False, 'description': ''}]
    for report in reports:
        rms = report.get('rms', '')
        submitted = 'Yes' if report.get('submitted') else 'No'
        desc = report.get('description', '')
        draw.text((margin_left, y), str(rms), font=normal_font, fill=(0, 0, 0))
        draw.text((margin_left + 100, y), submitted, font=normal_font, fill=(0, 0, 0))
        draw.text((margin_left + 200, y), desc, font=normal_font, fill=(0, 0, 0))
        y += 14
        # Check if we need to break to next page
        if y > PAGE_HEIGHT - margin_bottom - 200:
            # Start second page early if there is not enough space
            pages.append(page)
            page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), 'white')
            draw = ImageDraw.Draw(page)
            y = margin_top

    y += 10
    # Vehicle Report Cards
    draw.text((margin_left, y), 'Vehicle Report Cards', font=bold_font, fill=(0, 0, 0))
    y += 16
    vehicles = data.get('vehicles', [])
    if not vehicles:
        vehicles = [{'index': i+1, 'status': '', 'make': '', 'time': '', 'lic': '', 'reason': '', 'ow': '', 'loc': ''} for i in range(4)]
    for vehicle in vehicles:
        card_lines = [
            f"Card #{vehicle.get('index', '')} - Status: {vehicle.get('status', '')}",
            f"Make/Model: {vehicle.get('make', '')}",
            f"Time: {vehicle.get('time', '')}",
            f"Lic#: {vehicle.get('lic', '')}",
            f"Reason: {vehicle.get('reason', '')}",
            f"OW/Prop/Other: {vehicle.get('ow', '')}",
            f"Loc: {vehicle.get('loc', '')}"
        ]
        for line in card_lines:
            draw.text((margin_left + 10, y), line, font=normal_font, fill=(0, 0, 0))
            y += 14
            if y > PAGE_HEIGHT - margin_bottom - 200:
                pages.append(page)
                page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), 'white')
                draw = ImageDraw.Draw(page)
                y = margin_top
        y += 10  # extra spacing between cards

    # Vehicle Inspection
    draw.text((margin_left, y), 'Vehicle Inspection', font=bold_font, fill=(0, 0, 0))
    y += 16
    inspection_rows = [
        (f"Beginning Mileage: {data.get('beginningMileage', '')}", f"Ending Mileage: {data.get('endingMileage', '')}"),
        (f"Exterior Damage: {data.get('exteriorDamage', '')}", f"Interior Damage: {data.get('interiorDamage', '')}"),
        (f"Fluid Levels Checked: {data.get('fluidLevels', '')}", f"Tire Condition: {data.get('tireCondition', '')}"),
        (f"Other Notes: {data.get('vehicleOther', '')}", '')
    ]
    for left_text, right_text in inspection_rows:
        draw.text((margin_left, y), left_text, font=normal_font, fill=(0, 0, 0))
        if right_text:
            draw.text((PAGE_WIDTH/2, y), right_text, font=normal_font, fill=(0, 0, 0))
        y += 14
        if y > PAGE_HEIGHT - margin_bottom - 200:
            pages.append(page)
            page = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), 'white')
            draw = ImageDraw.Draw(page)
            y = margin_top

    # At this point, append the current page before starting a new one for notes
    pages.append(page)
    # Create second page for notes and signature
    page2 = Image.new('RGB', (PAGE_WIDTH, PAGE_HEIGHT), 'white')
    draw2 = ImageDraw.Draw(page2)
    y2 = margin_top

    # Notes
    draw2.text((margin_left, y2), 'Notes', font=bold_font, fill=(0, 0, 0))
    y2 += 16
    # Wrap long notes text into multiple lines if necessary
    notes_text = data.get('notes', '')
    # Manual wrap: break text into lines that fit the page width (~500 px) using simple splitting
    max_width = PAGE_WIDTH - margin_left - margin_right
    words = notes_text.split()
    line = ''
    for word in words:
        test_line = line + word + ' '
        # measure width of test line
        if bold_font.getsize(test_line)[0] > max_width:
            draw2.text((margin_left, y2), line.strip(), font=normal_font, fill=(0, 0, 0))
            y2 += 14
            line = word + ' '
        else:
            line = test_line
    # Draw any remaining text
    draw2.text((margin_left, y2), line.strip(), font=normal_font, fill=(0, 0, 0))
    y2 += 40  # Leave space after notes

    # Signature
    draw2.text((margin_left, y2), 'Signature', font=bold_font, fill=(0, 0, 0))
    y2 += 16
    draw2.text((margin_left, y2), f"Rec by Watch OIC/SGT: {data.get('receivedBy', '')}", font=normal_font, fill=(0, 0, 0))
    y2 += 14
    draw2.text((margin_left, y2), f"Date: {data.get('signatureDate', '')}", font=normal_font, fill=(0, 0, 0))

    pages.append(page2)

    # Combine pages into a PDF
    pdf_buffer = io.BytesIO()
    pages[0].save(pdf_buffer, format='PDF', save_all=True, append_images=pages[1:])
    pdf_buffer.seek(0)
    return pdf_buffer


class RequestHandler(BaseHTTPRequestHandler):
    """Simple HTTP request handler for PDF generation."""
    def do_OPTIONS(self):
        # Respond to CORS preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path != '/generate-pdf':
            self.send_error(404, 'Endpoint not found')
            return
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body.decode('utf-8')) if body else {}
        except json.JSONDecodeError:
            self.send_error(400, 'Invalid JSON')
            return
        # Generate PDF
        pdf_buffer = build_pdf(data)
        pdf_bytes = pdf_buffer.getvalue()
        filename = f"report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
        self.send_response(200)
        self.send_header('Content-Type', 'application/pdf')
        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.send_header('Content-Length', str(len(pdf_bytes)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(pdf_bytes)

    def do_GET(self):
        """
        Serve static files (HTML, CSS, JS and image) so that the frontend can be
        accessed via http://127.0.0.1:5000/ instead of file://.  This avoids
        cross‑origin restrictions when the browser tries to POST data back
        to this server.
        """
        parsed_path = urlparse(self.path)
        # Normalize path; default document
        if parsed_path.path in ('', '/', '/index.html'):
            filename = 'index.html'
            content_type = 'text/html'
        else:
            # Remove leading slash
            filename = parsed_path.path.lstrip('/')
            # Map file extensions to MIME types
            if filename.endswith('.css'):
                content_type = 'text/css'
            elif filename.endswith('.js'):
                content_type = 'application/javascript'
            elif filename.endswith('.png'):
                content_type = 'image/png'
            elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
                content_type = 'image/jpeg'
            else:
                # For unknown file types, guess binary
                content_type = 'application/octet-stream'
        try:
            with open(filename, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            # Allow resources to be loaded by any origin (not strictly necessary for GET)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, 'File not found')


def run_server(server_class=HTTPServer, handler_class=RequestHandler, host='127.0.0.1', port=5000):
    """Starts the HTTP server."""
    server_address = (host, port)
    httpd = server_class(server_address, handler_class)
    print(f'Serving HTTP on {host}:{port} ...')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('Server is shutting down.')
    finally:
        httpd.server_close()


if __name__ == '__main__':
    run_server()