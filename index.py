from flask import Flask, request, send_file, jsonify
import requests
import io

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
        
        # Call external PDF service
        response = requests.post(
            'https://api.html2pdf.app/v1/generate',
            json={
                'html': html_content,
                'engine': 'chrome',
                'options': {
                    'viewport': {
                        'width': VIEWPORT_WIDTH,
                        'height': VIEWPORT_HEIGHT
                    },
                    'width': f'{VIEWPORT_WIDTH}px',
                    'printBackground': True,
                    'preferCSSPageSize': False,
                    'displayHeaderFooter': False,
                    'margin': {'top': '0', 'right': '0', 'bottom': '0', 'left': '0'}
                }
            },
            headers={'Content-Type': 'application/json'},
            timeout=8
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
        else:
            return jsonify({
                'error': 'PDF generation failed',
                'status': response.status_code
            }), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'viewport': f'{VIEWPORT_WIDTH}x{VIEWPORT_HEIGHT}'
    })

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'name': 'HTML to PDF API',
        'viewport': f'{VIEWPORT_WIDTH}x{VIEWPORT_HEIGHT}',
        'usage': 'POST /api/html-to-pdf with {"html": "...", "filename": "..."}'
    })

# For local testing
if __name__ == '__main__':
    app.run(debug=True, port=5000)
