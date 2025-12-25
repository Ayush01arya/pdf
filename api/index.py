from flask import Flask, request, send_file, jsonify
import requests
import io

app = Flask(__name__)

VIEWPORT_WIDTH = 1024
VIEWPORT_HEIGHT = 800

@app.route('/api/html-to-pdf', methods=['POST'])
def convert_html_to_pdf():
    """
    Convert HTML to PDF using external service (optimized for Vercel Free Plan)
    
    Request body (JSON):
    {
        "html": "<html>...</html>",
        "filename": "output.pdf" (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'html' not in data:
            return jsonify({
                'error': 'Missing "html" field in request body'
            }), 400
        
        html_content = data['html']
        filename = data.get('filename', 'document.pdf')
        
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        # Using api.html2pdf.app with custom viewport dimensions
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
                    'margin': {
                        'top': '0',
                        'right': '0',
                        'bottom': '0',
                        'left': '0'
                    }
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
                'status': response.status_code,
                'details': response.text
            }), 500
    
    except requests.Timeout:
        return jsonify({
            'error': 'Request timeout - HTML might be too large or complex'
        }), 504
    
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'HTML to PDF API is running',
        'viewport': {
            'width': VIEWPORT_WIDTH,
            'height': VIEWPORT_HEIGHT
        },
        'plan': 'Vercel Free (Hobby)',
        'limits': {
            'memory': '1024 MB',
            'timeout': '10 seconds'
        }
    })

@app.route('/', methods=['GET'])
def home():
    """API documentation"""
    return jsonify({
        'name': 'HTML to PDF API',
        'version': '1.0.0',
        'viewport': f'{VIEWPORT_WIDTH}x{VIEWPORT_HEIGHT}',
        'endpoints': {
            'POST /api/html-to-pdf': {
                'description': f'Convert HTML to PDF with {VIEWPORT_WIDTH}x{VIEWPORT_HEIGHT} viewport',
                'body': {
                    'html': 'string (required) - Complete HTML content with CSS/JS',
                    'filename': 'string (optional) - Output filename (default: document.pdf)'
                },
                'example': {
                    'html': '<!DOCTYPE html><html><head><style>body{font-family:Arial;}</style></head><body><h1>Hello World</h1></body></html>',
                    'filename': 'report.pdf'
                },
                'response': 'PDF file download'
            },
            'GET /api/health': {
                'description': 'Health check endpoint',
                'response': 'API status, viewport dimensions, and limits'
            }
        },
        'usage': {
            'curl': 'curl -X POST https://your-app.vercel.app/api/html-to-pdf -H "Content-Type: application/json" -d \'{"html":"<html><body><h1>Test</h1></body></html>"}\' --output result.pdf'
        }
    })

# For local testing
if __name__ == '__main__':
    app.run(debug=True, port=5000)
