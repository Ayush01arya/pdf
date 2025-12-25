from flask import Flask, request, send_file, jsonify
import requests
import io
import base64

app = Flask(__name__)

VIEWPORT_WIDTH = 1024
VIEWPORT_HEIGHT = 800

@app.route('/api/html-to-pdf', methods=['POST'])
def convert_html_to_pdf():
    """Convert HTML to PDF"""
    try:
        data = request.get_json()
        
        if not data or 'html' not in data:
            return jsonify({'error': 'Missing "html" field'}), 400
        
        html_content = data['html']
        filename = data.get('filename', 'document.pdf')
        
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        # Using PDFShift API (more reliable, has free tier)
        # Alternative: Use API Ninjas (free, no auth needed)
        
        # Method 1: Try API Ninjas first (Free, no API key)
        try:
            response = requests.post(
                'https://api.api-ninjas.com/v1/htmltopdf',
                json={'html': html_content},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                pdf_io = io.BytesIO(response.content)
                pdf_io.seek(0)
                return send_file(
                    pdf_io,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=filename
                )
        except Exception as e:
            print(f"API Ninjas failed: {e}")
        
        # Method 2: Fallback to HTML-PDF-API.com (Free tier)
        try:
            response = requests.post(
                'https://api.html-pdf-api.com/v1/generate',
                json={
                    'html': html_content,
                    'pdfOptions': {
                        'format': 'A4',
                        'printBackground': True,
                        'width': f'{VIEWPORT_WIDTH}px'
                    }
                },
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                pdf_io = io.BytesIO(response.content)
                pdf_io.seek(0)
                return send_file(
                    pdf_io,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=filename
                )
        except Exception as e:
            print(f"HTML-PDF-API failed: {e}")
        
        # Method 3: Use wkhtmltopdf.org API (Free)
        try:
            # Encode HTML to base64
            html_b64 = base64.b64encode(html_content.encode()).decode()
            
            response = requests.post(
                'https://api.wkhtmltopdf.org/convert',
                json={
                    'contents': html_b64,
                    'options': {
                        'page-width': f'{VIEWPORT_WIDTH}px',
                        'enable-javascript': True,
                        'javascript-delay': 1000
                    }
                },
                timeout=10
            )
            
            if response.status_code == 200:
                pdf_io = io.BytesIO(response.content)
                pdf_io.seek(0)
                return send_file(
                    pdf_io,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=filename
                )
        except Exception as e:
            print(f"wkhtmltopdf failed: {e}")
        
        # If all methods fail
        return jsonify({
            'error': 'All PDF generation services failed',
            'message': 'Please check API limits or try again later',
            'suggestion': 'Consider using a self-hosted solution or paid API service'
        }), 503
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'viewport': f'{VIEWPORT_WIDTH}x{VIEWPORT_HEIGHT}',
        'note': 'Using multiple free PDF services with fallback'
    })

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'name': 'HTML to PDF API',
        'viewport': f'{VIEWPORT_WIDTH}x{VIEWPORT_HEIGHT}',
        'usage': 'POST /api/html-to-pdf with {"html": "...", "filename": "..."}',
        'note': 'Multiple PDF generation services with automatic fallback'
    })

# For local testing
if __name__ == '__main__':
    app.run(debug=True, port=5000)
