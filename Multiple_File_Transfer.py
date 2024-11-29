import os
import customtkinter as ctk
from customtkinter import CTkImage
import qrcode
from PIL import Image, ImageTk
import socket
import threading
import http.server
import socketserver
import urllib.parse
import zipfile

class FileShareApp:
    def __init__(self):
        # Set up the main window
        self.root = ctk.CTk()
        self.root.title("Multi-File Share")
        self.root.geometry("700x600+500+100")

        # Configure the grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(3, weight=1)

        # File selection
        self.file_listbox = ctk.CTkTextbox(self.root, height=100)
        self.file_listbox.grid(row=0, column=0, columnspan=2, padx=20, pady=10, sticky="ew")

        self.select_file_button = ctk.CTkButton(
            self.root, 
            text="Select Files", 
            command=self.select_files
        )
        self.select_file_button.grid(row=1, column=0, columnspan=2, padx=20, pady=10)

        # QR Code display
        self.qr_canvas = ctk.CTkCanvas(
            self.root, 
            width=300, 
            height=300, 
            bg='white'
        )
        self.qr_canvas.grid(row=2, column=0, columnspan=2, padx=20, pady=10)

        # Generate QR Code button
        self.generate_qr_button = ctk.CTkButton(
            self.root, 
            text="Generate QR Code", 
            command=self.generate_qr_code,
            state="disabled"
        )
        self.generate_qr_button.grid(row=3, column=0, columnspan=2, padx=20, pady=10)

        # Status label
        self.status_label = ctk.CTkLabel(self.root, text="")
        self.status_label.grid(row=4, column=0, columnspan=2, padx=20, pady=10)

        # Selected file paths
        self.selected_file_paths = []

        # Server variables
        self.server_thread = None
        self.server_port = None
        self.serving_directory = None

    def select_files(self):
        """Open file dialog to select multiple files for sharing"""
        file_paths = ctk.filedialog.askopenfilenames()
        if file_paths:
            self.selected_file_paths = list(file_paths)
            
            # Clear previous entries
            self.file_listbox.delete('1.0', ctk.END)
            
            # Display selected files
            for path in self.selected_file_paths:
                self.file_listbox.insert(ctk.END, f"{os.path.basename(path)}\n")
            
            self.generate_qr_button.configure(state="normal")

    def get_local_ip(self):
        """Get the local IP address of the computer"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"

    def start_file_server(self):
        """Start a simple HTTP server to serve zipped files"""
        import tempfile

        # Create a temporary directory
        self.serving_directory = tempfile.mkdtemp()
        
        # Create a zip file with all selected files
        zip_path = os.path.join(self.serving_directory, "shared_files.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.selected_file_paths:
                zipf.write(file_path, os.path.basename(file_path))

        class FileHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, directory=None, **kwargs):
                super().__init__(*args, directory=directory, **kwargs)

        # Find an available port
        def find_free_port():
            with socketserver.TCPServer(("", 0), FileHandler) as tmp_server:
                return tmp_server.server_address[1]

        self.server_port = find_free_port()

        # Start server in a separate thread
        def run_server():
            os.chdir(self.serving_directory)
            with socketserver.TCPServer(("", self.server_port), FileHandler) as httpd:
                httpd.serve_forever()

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

    def generate_qr_code(self):
        """Generate QR code for file sharing with URL encoding"""
        if not self.selected_file_paths:
            self.status_label.configure(text="Please select files first")
            return

        # Start the file server
        self.start_file_server()

        # Construct the download URL
        local_ip = self.get_local_ip()
        download_url = f"http://{local_ip}:{self.server_port}/shared_files.zip"

        # Create QR code
        qr = qrcode.QRCode(
            version=1, 
            box_size=10, 
            border=0  # Remove border to maximize QR code area
        )
        qr.add_data(download_url)
        qr.make(fit=True)

        # Create an image from the QR code
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Resize image to fit canvas
        qr_image = qr_image.resize((300, 300))

        # Clear previous QR code
        self.qr_canvas.delete("all")

        # Convert PIL Image to PhotoImage
        photo = ImageTk.PhotoImage(qr_image)
        
        # Display QR code on canvas
        self.qr_canvas.create_image(0, 0, anchor=ctk.NW, image=photo)
        self.qr_canvas.image = photo  # Keep a reference

        # Update status
        self.status_label.configure(text="Scan QR Code to download zip file")

    def run(self):
        """Run the application"""
        self.root.mainloop()

def main():
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    
    app = FileShareApp()
    app.run()

if __name__ == "__main__":
    main()