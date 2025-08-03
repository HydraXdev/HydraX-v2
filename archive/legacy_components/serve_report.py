#!/usr/bin/env python3
"""
Simple HTTP server to serve the BITTEN Game Rules Backtesting Report
"""

import http.server
import socketserver
import os
import webbrowser
from urllib.parse import quote

def serve_report():
    """Serve the PDF report via HTTP"""
    
    # Check if PDF exists
    pdf_path = '/root/HydraX-v2/BITTEN_GAME_RULES_BACKTEST_REPORT.pdf'
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF not found at {pdf_path}")
        return False
    
    # Change to the directory containing the PDF
    os.chdir('/root/HydraX-v2')
    
    # Get file size
    file_size = os.path.getsize(pdf_path)
    print(f"📄 PDF file size: {file_size:} bytes ({file_size/1024:.1f} KB)")
    
    PORT = 8889
    
    class PDFHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            # Add headers for PDF serving
            self.send_header('Content-Type', 'application/pdf')
            self.send_header('Content-Disposition', 'inline; filename="BITTEN_Game_Rules_Backtest_Report.pdf"')
            super().end_headers()
    
    try:
        with socketserver.TCPServer(("", PORT), PDFHandler) as httpd:
            print("🌐 HTTP Server started successfully!")
            print(f"📡 Server running on port {PORT}")
            print(f"🔗 Direct PDF URL: http://134.199.204.67:{PORT}/BITTEN_GAME_RULES_BACKTEST_REPORT.pdf")
            print(f"📁 Directory listing: http://134.199.204.67:{PORT}/")
            print()
            print("📋 DOWNLOAD INSTRUCTIONS:")
            print("1. Copy the direct PDF URL above")
            print("2. Paste it in your browser")
            print("3. The PDF will open/download automatically")
            print()
            print("⚠️  Server will run until you stop it (Ctrl+C)")
            print("🚀 Serving files...")
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        return True
    except Exception as e:
        print(f"❌ Server error: {e}")
        return False

if __name__ == "__main__":
    print("🎯 BITTEN Game Rules Report Server")
    print("=" * 50)
    serve_report()