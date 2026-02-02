# Voice Typing Assistant

A voice-to-text typing assistant designed for VR gaming and hands-free text input. This application uses OpenAI's Whisper API to transcribe speech and automatically types the transcribed text into the active application.

## Features

- **Hotkey-activated recording**: Press Ctrl+Alt+0 (configurable) to start/stop voice recording
- **Automatic silence detection**: Stops recording after a period of silence (default: 1 second)
- **Real-time transcription**: Uses OpenAI Whisper API for accurate speech-to-text conversion
- **Automatic typing**: Transcribed text is automatically pasted into the active application
- **Configurable settings**: Customize audio device, silence timeout, sample rate, and hotkey via environment variables
- **Optional context vocabulary**: Use a `context.csv` file to bias transcription toward specific words (e.g. game locations and names), so Whisper prefers "Lorville" instead of "Lawville"

## Requirements

- Python 3.8 or higher
- OpenAI API key
- Microphone access
- Windows, Linux, or macOS

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/FixerSchis/sc-voice.git
   cd sc-voice
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file from the example:

   ```bash
   cp .env.example .env
   ```

4. Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Configuration

Edit the `.env` file to customize settings:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `AUDIO_DEVICE_INDEX`: Audio input device index (default: 0)
- `SILENCE_TIMEOUT`: Seconds of silence before stopping recording (default: 1.0)
- `SAMPLE_RATE`: Audio sample rate in Hz (default: 16000)
- `HOTKEY`: Hotkey combination to toggle recording (default: ctrl+alt+0)

### Context vocabulary (optional)

The default download includes **`context.csv`** with Star Citizen locations, companies, points of interest, resources, and in-universe terms. Context is **“look out for these words”**—Whisper still transcribes normal speech; the file just biases it toward these spellings when it hears them (e.g. "Lorville" instead of "Lawville", "Xi'an" when you say "Zee-an").

- **If `context.csv` exists** (default): Whisper uses it as a vocabulary hint for transcription.
- **If you delete `context.csv`**: No context is used; transcription uses Whisper’s default vocabulary.
- **To use your own vocabulary**: Edit `context.csv` or replace it with your own terms.

**CSV format**: One term per row; first column is the word. Optional **second column** is a pronunciation hint (e.g. `Xi'an,Zee-an` or `Vanduul,Van-dool`) so Whisper knows how to match what you say to the correct spelling. An optional header row with "term" / "word" / "name" is ignored.

Whisper uses only the first ~224 tokens of the context, so very long lists are truncated.

## Usage

### Running from Source

1. Ensure your `.env` file is configured with your OpenAI API key
2. Run the application:
   ```bash
   python voice_typing.py
   ```
3. The application will start and wait for the hotkey
4. Press Ctrl+Alt+0 (or your configured hotkey) to start recording
5. Speak your text
6. Recording stops automatically after silence is detected
7. The transcribed text will be typed into the active application

**Note**: On Windows, you may need to run as administrator if you encounter permission issues. On Linux/WSL, you may need to use `sudo`.

### Running Compiled Release

Pre-built executables are automatically created for Windows, Linux, and macOS. Download the latest release from the [Releases page](https://github.com/FixerSchis/sc-voice/releases) and extract the archive for your platform.

1. Extract the archive for your operating system
2. Create a `.env` file in the same directory as the executable (you can copy `.env.example` as a template)
3. Add your OpenAI API key to the `.env` file
4. Run the executable:
   - Windows: `voice_typing.exe`
   - Linux: `./voice_typing`
   - macOS: `./voice_typing`

The application behavior is identical to running from source.

## Building from Source

To build a standalone executable:

1. Install PyInstaller:

   ```bash
   pip install pyinstaller
   ```

2. Build the executable:

   ```bash
   pyinstaller --onefile --name voice_typing voice_typing.py
   ```

3. The executable will be in the `dist/` directory

For Windows, you can also use:

```bash
pyinstaller --onefile --name voice_typing --icon=NONE voice_typing.py
```

## How It Works

1. The application monitors keyboard input for the configured hotkey combination
2. When the hotkey is pressed, audio recording begins from the configured microphone
3. The application continuously monitors audio levels to detect speech and silence
4. After a period of silence (configurable), recording stops automatically
5. The recorded audio is sent to OpenAI's Whisper API for transcription
6. The transcribed text is copied to the clipboard and pasted into the active application using keyboard simulation

## Troubleshooting

**Permission errors**: On Windows, try running as administrator. On Linux, you may need to run with `sudo`.

**Audio device not found**: Check your audio device index using Python:

```python
import sounddevice as sd
print(sd.query_devices())
```

Update `AUDIO_DEVICE_INDEX` in your `.env` file accordingly.

**Hotkey not working**: Ensure no other application is using the same hotkey combination. You can change the hotkey in your `.env` file.

**Text not typing**: Make sure the target application has keyboard focus. The application uses clipboard paste (Ctrl+V) which should work in most applications.

## License

[Add your license here]

## Contributing

[Add contribution guidelines if desired]
