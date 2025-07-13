import os, threading, http.server, socketserver
PORT = int(os.environ.get("PORT", 10000))

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass  # بدون ضجيج في اللوج

def run_dummy():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()

#--- شغّل البوت الفعلي في Thread منفصل ---
def run_bot():
    import main  # ملف بدء البوت لديك
threading.Thread(target=run_bot).start()
run_dummy()
