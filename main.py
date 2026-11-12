import os
import sys
import logging
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Format logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# 1. Pelayan HTTP ringkas untuk memenuhi syarat Free Web Service di Render
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"FIMS Automation Bot is Running Live!")

def start_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    logging.info(f"Pelayan HTTP percuma berjalan di port {port}")
    server.serve_forever()

# 2. Skrip Automasi Utama FIMS UUM
def run_fims_automation():
    username = os.environ.get("FIMS_USERNAME")
    password = os.environ.get("FIMS_PASSWORD")

    if not username or not password:
        logging.error("Ralat: FIMS_USERNAME atau FIMS_PASSWORD belum ditetapkan di Environment Variables!")
        return

    logging.info("--- MULA AUTOMATION FIMS UUM ---")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        try:
            logging.info("Memuatkan halaman log masuk FIMS UUM...")
            page.goto("https://fims.uum.edu.my/login.php?a=NDUxNzc3", wait_until="networkidle")

            if page.locator(".input-mask").first.is_visible():
                page.locator(".input-mask").first.click()

            logging.info("Memasukkan maklumat log masuk...")
            page.fill("#userID", username)
            page.fill("#userPassword", password)

            logging.info("Menekan butang 'Sign In'...")
            page.click("#login")

            page.wait_for_load_state("networkidle")

            error_element = page.locator("#error")
            if error_element.is_visible() and error_element.inner_text().strip() != "":
                err_text = error_element.inner_text().strip()
                logging.warning(f"LOG MASUK GAGAL: {err_text}")
                return

            if "login.php" in page.url:
                logging.warning("LOG MASUK GAGAL: Semak semula kredensial atau akaun terhalang.")
                return

            logging.info("✅ BERJAYA LOG MASUK KE FIMS UUM!")
            page_title = page.title()
            logging.info(f"Tajuk Halaman Utama: {page_title}")

        except PlaywrightTimeoutError:
            logging.error("RALAT: Masa tamat (Timeout) semasa memuatkan laman web.")
        except Exception as e:
            logging.error(f"RALAT TIDAK DIJANGKA: {str(e)}")
        finally:
            browser.close()
            logging.info("--- SELESAI AUTOMASI FIMS ---")

if __name__ == "__main__":
    # Jalankan pelayan HTTP di latar belakang
    server_thread = Thread(target=start_dummy_server)
    server_thread.daemon = True
    server_thread.start()

    # Jalankan automasi log masuk
    run_fims_automation()

    # Pastikan perkhidmatan kekal aktif di Render
    server_thread.join()