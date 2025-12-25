from flask import Flask, request, send_file, jsonify
from pyppeteer import launch
import asyncio
import io
import os

app = Flask(__name__)

VIEWPORT_WIDTH = 1024
VIEWPORT_HEIGHT = 800

async def html_to_pdf_async(html_content: str) -> bytes:
    """Convert HTML string to PDF bytes"""
    browser = await launch(
        headless=True,
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu'
        ]
    )
    
    page = await browser.newPage()
    await page.setViewport({
        'width': VIEWPORT_WIDTH,
        'height': VIEWPORT_HEIGHT
    })
    
    # Set HTML content
    await page.setContent(html_content, {'waitUntil': 'networkidle0'})
    
    # Get content height
    content_height = await page.evaluate('document.body.scrollHeight')
    
    # Generate PDF
    pdf_bytes = await page.pdf({
        'width': f'{VIEWPORT_WIDTH}px',
        'height': f'{content_height}px',
        'printBackground': True,
        'scale': 1
    })
    
    await browser.close()
    return pdf_bytes

@app.route('/api/html-to-pdf', methods=['POST'])
def convert_html_to_pdf():
    """
    API endpoint to convert HTML to PDF
    
    Request body (JSON):
    {
        "html": "<html>...</html>",
        "filename": "output.pdf" (optional)
    }
    """
    try:
        # Get JSON data
        data = request.get_json()
        
        if not data or 'html' not in data:
            return jsonify({
                'error': 'Missing "html" field in request body'
            }), 400
        
        html_content = data['html']
        filename = data.get('filename', 'document.pdf')
        
        # Ensure filename ends with .pdf
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        # Convert HTML to PDF
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        pdf_bytes = loop.run_until_complete(html_to_pdf_async(html_content))
        loop.close()
        
        # Create BytesIO object
        pdf_io = io.BytesIO(pdf_bytes)
        pdf_io.seek(0)
        
        # Return PDF file
        return send_file(
            pdf_io,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'HTML to PDF API is running'
    })

@app.route('/', methods=['GET'])
def home():
    """Home page with API documentation"""
    return jsonify({
        'name': 'HTML to PDF API',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/html-to-pdf': {
                'description': 'Convert HTML to PDF',
                'body': {
                    'html': 'string (required) - HTML content',
                    'filename': 'string (optional) - Output filename'
                },
                'example': {
                    'html': '<!DOCTYPE html><html>...</html>',
                    'filename': 'report.pdf'
                }
            },
            'GET /api/health': {
                'description': 'Health check endpoint'
            }
        }
    })

# For local testing
if __name__ == '__main__':
    app.run(debug=True, port=5000)
