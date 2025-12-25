from http.server import BaseHTTPRequestHandler
from playwright.sync_api import sync_playwright
import json
import base64
import os
import subprocess

VIEWPORT_WIDTH = 1024
VIEWPORT_HEIGHT = 800

# Auto-install Playwright browsers on first run
def ensure_playwright_browsers():
    """Install Playwright browsers if not already installed"""
    try:
        # Check if chromium is installed
        from playwright._impl._driver import compute_driver_executable
        driver_executable = compute_driver_executable()
        
        # Try to get browser path
        result = subprocess.run(
            [driver_executable, "print-browser-paths"],
            capture_output=True,
            text=True
        )
        
        if "chromium" not in result.stdout:
            # Install chromium
            subprocess.run(
                ["playwright", "install", "chromium", "--with-deps"],
                check=True
            )
    except Exception as e:
        # Fallback: just try to install
        try:
            subprocess.run(
                ["playwright", "install", "chromium", "--with-deps"],
                check=True
            )
        except:
            pass

# Install browsers on module load
try:
    ensure_playwright_browsers()
except:
    pass

class handler(BaseHTTPRequestHandler):
    
    def generate_pdf(self, html_content):
        """Generate PDF from HTML using Playwright"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-setuid-sandbox",
                        "--single-process",
                        "--no-zygote"
                    ]
                )

                page = browser.new_page(
                    viewport={
                        "width": VIEWPORT_WIDTH,
                        "height": VIEWPORT_HEIGHT
                    },
                    device_scale_factor=1
                )

                # Inject HTML directly (CSS + JS included)
                page.set_content(
                    html_content,
                    wait_until="networkidle",
                    timeout=60000
                )

                # Get full rendered height (important!)
                content_height = page.evaluate("document.body.scrollHeight")

                # Export PDF as bytes
                pdf_bytes = page.pdf(
                    width=f"{VIEWPORT_WIDTH}px",
                    height=f"{content_height}px",
                    print_background=True,
                    scale=1
                )

                browser.close()
                return pdf_bytes
                
        except Exception as e:
            raise Exception(f"PDF generation failed: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/generate-pdf':
            try:
                # Read request body
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                # Validate input
                if 'html' not in data:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    error = {'error': 'Missing required field: html'}
                    self.wfile.write(json.dumps(error).encode())
                    return
                
                html_content = data['html']
                return_type = data.get('return_type', 'file')
                
                # Generate PDF
                pdf_bytes = self.generate_pdf(html_content)
                
                # Return based on type
                if return_type == 'base64':
                    # Return as JSON with base64
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    response = {
                        'success': True,
                        'pdf': base64.b64encode(pdf_bytes).decode('utf-8'),
                        'size': len(pdf_bytes)
                    }
                    self.wfile.write(json.dumps(response).encode())
                else:
                    # Return as PDF file
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/pdf')
                    self.send_header('Content-Disposition', 'attachment; filename="report.pdf"')
                    self.send_header('Content-Length', str(len(pdf_bytes)))
                    self.end_headers()
                    self.wfile.write(pdf_bytes)
                    
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error = {'error': str(e)}
                self.wfile.write(json.dumps(error).encode())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error = {'error': 'Not Found'}
            self.wfile.write(json.dumps(error).encode())
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/api/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'status': 'ok',
                'message': 'PDF Generator API is running',
                'engine': 'playwright'
            }
            self.wfile.write(json.dumps(response).encode())
            
        elif self.path == '/' or self.path == '/api':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'service': 'PDF Generator API',
                'version': '1.0.0',
                'endpoints': {
                    '/api/generate-pdf': {
                        'method': 'POST',
                        'description': 'Generate PDF from HTML content',
                        'body': {
                            'html': 'HTML content as string (required)',
                            'return_type': 'file or base64 (optional, default: file)'
                        }
                    },
                    '/api/health': {
                        'method': 'GET',
                        'description': 'Health check endpoint'
                    }
                }
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error = {'error': 'Not Found'}
            self.wfile.write(json.dumps(error).encode())
