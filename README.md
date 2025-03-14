📄 Scanner Server 📄
A self-hosted solution to scan, print, and manage your documents with ease!
✨ What It Does

🔍 Scan documents directly from your web browser
🔎 Create searchable PDFs with automatic OCR
🖨️ Print files by uploading them through the web interface
📂 Organize your scanned documents automatically
🔔 Get notifications on Discord when new documents are scanned

🚀 Quick Start

Make sure you have Docker installed
Run this command:
bashCopydocker run -d --name scanner-server -p 5000:5000 -e SCANNER_IP=192.168.1.100 -v scanner_data:/data/scan yourusername/scanner-server

Open http://localhost:5000 in your browser
Enjoy scanning and printing!

📱 NFC Support
Create an NFC tag with URL: http://your-server-ip:5000/nfc/single_scan
Just tap your phone on the tag to start scanning - no app needed!
⚙️ Features

📑 Single-page scanning for quick documents
📚 Multi-page scanning to create complete documents
🔤 OCR processing to make text searchable
🌐 Web interface for easy access from any device
📨 Discord notifications when scans are complete

🛠️ Configuration
Set up your scanner and customize settings through the web interface.
📝 License
MIT License - Feel free to use and modify!
👥 Contributing
Contributions welcome! Have an idea to make this better? Let us know!

Made with ❤️ for the open-source community
