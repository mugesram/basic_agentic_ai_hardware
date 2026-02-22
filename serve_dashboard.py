from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import webbrowser

HOST = "127.0.0.1"
PORT = 8000


class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()


if __name__ == "__main__":
    url = f"http://{HOST}:{PORT}/led_dashboard.html"
    print(f"Serving dashboard at: {url}")
    webbrowser.open(url)
    server = ThreadingHTTPServer((HOST, PORT), NoCacheHandler)
    server.serve_forever()
