# Voice Assistant Deployment Guide

## 🛠️ Requirements
- **Python 3.11** or newer
- **Microphone** (built-in or external)
- **Windows/macOS/Linux** (Tested on Windows 11)

## ⚡ Quick Installation
1. Clone the repo:
   ```bash
   git clone https://github.com/yourusername/voice-assistant.git
   cd voice-assistant
Install dependencies:

bash
pip install -r requirements.txt
Run the assistant:

bash
python nova_assistant_v1.py
🔧 Detailed Setup
For Windows Users
bash
# Fix PyAudio installation (if needed):
pip install pipwin
pipwin install pyaudio
For Linux/macOS Users
bash
# Install system dependencies
sudo apt-get install portaudio19-dev python3-tk  # Debian/Ubuntu
brew install portaudio                          # macOS
API Keys (Optional)
Get a free WolframAlpha API key

Add it to assistant_settings.json:

json
{
  "wolfram_alpha_app_id": "YOUR-API-KEY-HERE"
}
🚨 Troubleshooting
Issue	Solution
Microphone not detected	Check system sound settings
"ModuleNotFound" errors	Verify Python version matches requirements.txt
GUI freezes	Close other heavy applications
Brightness control fails	Run as admin (Windows)
🌟 Pro Tips
For better accuracy, train voice recognition in Windows/macOS settings

Add custom apps in assistant_settings.json under app_paths

Use Python virtual environments for clean isolation


Key features of this deployment guide:
1. **Platform-specific instructions** (Windows/Linux/macOS)
2. **Troubleshooting table** for quick fixes
3. **Optional API key** section clearly marked
4. **Pro tips** for better performance
5. **Clean formatting** with emojis for visual scanning

