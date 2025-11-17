"""
Simple HTTP server for SpeakSense Admin Portal
Serves the admin portal with CORS support
"""
import http.server
import socketserver
from pathlib import Path

PORT = 8090
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
║          SpeakSense Admin Portal                         ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

🌐 Admin Portal: http://localhost:{PORT}/portal/index.html

📋 Features:
   - FAQ Management (Add, Edit, Delete)
   - Dashboard & Analytics
   - System Settings

🔗 Testing Portal: http://localhost:8080/web/index.html

Press Ctrl+C to stop the server
""")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down admin portal server...")
