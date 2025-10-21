import os
import fitz  # PyMuPDF
from PIL import Image
import time
import sys
import traceback
import gc
import shutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Configuration ---
INPUT_DIR = "pdf_input"
OUTPUT_DIR = "images_output"
PROCESSED_DIR = "pdf_processed"
ERROR_DIR = "pdf_error"

# --- Reusing your Ultra Log and Memory Logger ---
def ultra_log(message, level="INFO"):
    """Ultra detailed logging with timestamp"""
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    prefix = {"INFO": "ℹ️ ", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️ ", "DEBUG": "🔍", "STEP": "📍"}.get(level, "  ")
    print(f"[{timestamp}] {prefix} [{level}] {message}", flush=True)

def log_memory_usage():
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        ultra_log(f"Memory Usage: RSS={mem_info.rss/1024/1024:.2f} MB", "DEBUG")
    except ImportError: pass

# --- Conversion Logic (Adapted for file paths) ---
def pdf_to_images_from_path(pdf_path, output_folder):
    """Converts a PDF file to images."""
    filename = os.path.basename(pdf_path)
    ultra_log("="*80, "STEP")
    ultra_log(f"STARTING CONVERSION FOR: {filename}", "STEP")
    log_memory_usage()
    start_time = time.time()
    pdf_document = None
    try:
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(pdf_document)
        ultra_log(f"PDF opened. Pages: {total_pages}", "SUCCESS")

        for page_num in range(total_pages):
            ultra_log(f"PROCESSING PAGE {page_num + 1} of {total_pages}", "STEP")
            page = pdf_document[page_num]
            matrix = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=matrix)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            base_filename = os.path.splitext(filename)[0]
            image_filename = f"{base_filename}_page_{page_num + 1:04d}.png"
            image_path = os.path.join(output_folder, image_filename)
            
            img.save(image_path, "PNG", optimize=False)
            ultra_log(f"  ✅ Saved Page {page_num + 1} to {image_path}", "SUCCESS")
            del pix, img
            if (page_num + 1) % 20 == 0: gc.collect()

        total_elapsed = time.time() - start_time
        ultra_log(f"🎉 CONVERSION COMPLETE for {filename} in {total_elapsed:.2f}s", "SUCCESS")
        log_memory_usage()
        return True

    except Exception as e:
        ultra_log(f"💥 PDF CONVERSION FAILED for {filename}: {str(e)}", "ERROR")
        traceback.print_exc()
        return False
    finally:
        if pdf_document:
            try: pdf_document.close()
            except: pass
        gc.collect()

# --- Watchdog Event Handler ---
class PDFHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith('.pdf'):
            ultra_log(f"New PDF detected: {event.src_path}", "INFO")
            
            # Wait a moment to ensure the file is fully written
            time.sleep(2) 
            
            pdf_path = event.src_path
            filename = os.path.basename(pdf_path)
            
            success = pdf_to_images_from_path(pdf_path, OUTPUT_DIR)
            
            if success:
                dest_path = os.path.join(PROCESSED_DIR, filename)
                shutil.move(pdf_path, dest_path)
                ultra_log(f"Moved {filename} to processed folder.", "SUCCESS")
            else:
                dest_path = os.path.join(ERROR_DIR, filename)
                shutil.move(pdf_path, dest_path)
                ultra_log(f"Moved {filename} to error folder.", "ERROR")

# --- Main Execution ---
if __name__ == "__main__":
    # Ensure all directories exist
    for d in [INPUT_DIR, OUTPUT_DIR, PROCESSED_DIR, ERROR_DIR]:
        os.makedirs(d, exist_ok=True)
        
    ultra_log("🚀 STARTING PDF CONVERTER DAEMON", "STEP")
    ultra_log(f"Watching for new PDFs in: ./{INPUT_DIR}", "INFO")
    
    event_handler = PDFHandler()
    observer = Observer()
    observer.schedule(event_handler, INPUT_DIR, recursive=False)
    
    observer.start()
    ultra_log("✅ Observer started successfully. Press Ctrl+C to stop.", "SUCCESS")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        ultra_log("🛑 Observer stopped by user.", "WARNING")
    
    observer.join()
    ultra_log("👋 Exiting script. Goodbye!", "INFO")
