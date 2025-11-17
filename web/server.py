"""
Simple HTTP server for SpeakSense web interface
Serves the testing portal and handles CORS
"""
import http.server
import socketserver
from pathlib import Path
import os

PORT = 8080
DIRECTORY = Path(__file__).parent


class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with CORS support"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY.parent), **kwargs)

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
        print(f"""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║          SpeakSense Web Testing Portal                   ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

🌐 Web Interface: http://localhost:{PORT}/web/index.html

📝 Make sure all services are running:
   - ASR Service (8001)
   - Retrieval Service (8002)
   - Admin Service (8003)

Press Ctrl+C to stop the server
""")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down web server...")
