#!/usr/bin/env python3
"""
Voice Typing Assistant - VR Gaming Edition
Polls keyboard state for reliable hotkey detection
"""


import sys
import os
import time
import threading
import tempfile
import wave
import numpy as np
import sounddevice as sd
from pynput.keyboard import Controller as KeyboardController, Listener, Key, KeyCode
from openai import OpenAI
from dotenv import load_dotenv
import pyperclip

# Load environment variables
load_dotenv()


class VoiceTypingAssistant:
    def __init__(self):
        # Load configuration from environment
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            print("ERROR: OPENAI_API_KEY not found!")
            print("Please set your OpenAI API key in a .env file.")
            print("See .env.example for the required format.")
            sys.exit(1)

        # Audio recording parameters from environment
        self.CHANNELS = 1
        self.RATE = int(os.getenv("SAMPLE_RATE", "16000"))
        self.DEVICE_INDEX = int(os.getenv("AUDIO_DEVICE_INDEX", "0"))
        self.SILENCE_THRESHOLD = int(os.getenv("SILENCE_THRESHOLD", "500"))
        self.SILENCE_DURATION = float(os.getenv("SILENCE_TIMEOUT", "1.0"))

        # Hotkey configuration
        self.hotkey_str = os.getenv("HOTKEY", "ctrl+alt+0")

        # State management
        self.is_recording = False
        self.audio_frames = []
        self.recording_start_time = None
        self.hotkey_pressed = False
        self.has_detected_speech = False
        self.should_transcribe = False

        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.openai_api_key)

        # Initialize components
        self.keyboard_controller = KeyboardController()

        print("Voice Typing Assistant initialized")
        print(f"Hotkey: {self.hotkey_str}")
        print(f"Parsed hotkey: {'+'.join(self.parse_hotkey())}")
        print(f"Audio device: {self.DEVICE_INDEX}")
        print(f"Silence timeout: {self.SILENCE_DURATION} seconds")

    def audio_callback(self, indata, frames, time_info, status):
        """Callback function for sounddevice recording."""
        try:
            if self.is_recording:
                self.audio_frames.append(indata.copy())

                # Check for audio activity
                audio_data = (indata.flatten() * 32768).astype(np.int16)
                if self.is_silent(audio_data):
                    # Only start silence timer if we've already detected speech
                    if self.has_detected_speech and self.silence_start_time is None:
                        self.silence_start_time = time.time()
                    elif (
                        self.has_detected_speech
                        and time.time() - self.silence_start_time
                        >= self.SILENCE_DURATION
                    ):
                        print(
                            f"Silence detected ({self.SILENCE_DURATION}s), processing..."
                        )
                        self.should_transcribe = True
                        self.is_recording = False
                else:
                    # Detected speech - reset silence timer and mark that we've heard something
                    self.silence_start_time = None
                    self.has_detected_speech = True
        except Exception as e:
            print(f"Audio callback error: {e}")

    def is_silent(self, audio_data):
        """Check if audio data represents silence."""
        return np.abs(audio_data).mean() < self.SILENCE_THRESHOLD

    def start_recording(self):
        """Start audio recording."""
        print("Recording started... Speak now!")
        self.is_recording = True
        self.audio_frames = []
        self.recording_start_time = time.time()
        self.silence_start_time = None
        self.has_detected_speech = False

        # Start recording with callback
        self.stream = sd.InputStream(
            device=self.DEVICE_INDEX,
            channels=self.CHANNELS,
            samplerate=self.RATE,
            callback=self.audio_callback,
        )
        self.stream.start()

    def stop_recording_and_transcribe(self):
        """Stop recording and transcribe the audio."""
        if not self.is_recording:
            return

        self.is_recording = False
        print("Recording stopped. Processing...")

    def transcribe_and_type(self):
        """Transcribe audio using OpenAI API and type the result."""
        try:
            # Convert audio frames to WAV file
            audio_np = np.concatenate(self.audio_frames, axis=0).flatten()

            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_filename = temp_file.name

                # Write WAV file
                with wave.open(temp_filename, "wb") as wav_file:
                    wav_file.setnchannels(self.CHANNELS)
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(self.RATE)
                    wav_file.writeframes((audio_np * 32767).astype(np.int16).tobytes())

            # Send to OpenAI API
            with open(temp_filename, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1", file=audio_file, response_format="text"
                )

            # Clean up temp file
            os.unlink(temp_filename)

            text = (
                transcript.strip()
                if isinstance(transcript, str)
                else str(transcript).strip()
            )

            # Remove trailing punctuation (periods, commas, etc.) that Whisper may add
            # This helps prevent issues with commands or text that shouldn't have sentence endings
            if text:
                # Remove trailing sentence-ending punctuation
                while text and text[-1] in ".,;:":
                    text = text[:-1]
                text = text.strip()

            if text:
                print(f"Transcribed: '{text}'")
                self.type_text(text)
                print("Text typed! Ready for next command.")
            else:
                print("No speech detected. Ready for next command.")

        except Exception as e:
            print(f"Transcription error: {e}")

    def type_text(self, text):
        """Type the given text using clipboard paste for reliability."""
        try:
            # Ensure focus is ready
            time.sleep(0.2)

            # Copy text to clipboard
            pyperclip.copy(text)
            print(f"Copied to clipboard: '{text}'")

            # Simulate Ctrl+V to paste (try different approaches)
            time.sleep(0.1)  # Small delay after copy

            # Method 1: Use ctrl_l for more reliable control
            self.keyboard_controller.press(Key.ctrl_l)
            time.sleep(0.05)
            self.keyboard_controller.press("v")
            time.sleep(0.05)
            self.keyboard_controller.release("v")
            time.sleep(0.05)
            self.keyboard_controller.release(Key.ctrl_l)

            print("Paste simulation completed")

        except Exception as e:
            print(f"Paste error: {e}")
            import traceback

            traceback.print_exc()

            # Fallback: try typing the text character by character
            try:
                print("Falling back to typing...")
                from pynput.keyboard import KeyCode

                prev_char = None
                for char in text:
                    try:
                        key_code = KeyCode.from_char(char)
                        self.keyboard_controller.press(key_code)
                        time.sleep(0.01)
                        self.keyboard_controller.release(key_code)

                        # Extra delay for consecutive identical characters
                        delay = 0.08 if prev_char == char else 0.04
                        time.sleep(delay)
                        prev_char = char

                    except Exception:
                        # Final fallback: use type() method
                        self.keyboard_controller.type(char)
                        delay = 0.08 if prev_char == char else 0.04
                        time.sleep(delay)
                        prev_char = char

            except Exception as e2:
                print(f"All typing methods failed: {e2}")

    def run(self):
        """Start the voice typing assistant."""
        print("Starting Voice Typing Assistant...")
        print(f"Hotkey: {self.hotkey_str}")
        print(f"Silence timeout: {self.SILENCE_DURATION} seconds")
        print("Make sure your target application has keyboard focus")
        print()

        # Track currently pressed keys
        self.pressed_keys = set()

        def on_press(key):
            try:
                self.pressed_keys.add(key)

                # Check if our hotkey combination is pressed
                if self.is_hotkey_pressed():
                    if not self.hotkey_pressed:
                        self.hotkey_pressed = True
                        self.toggle_recording()
            except Exception as e:
                print(f"Key press error: {e}")

        def on_release(key):
            try:
                self.pressed_keys.discard(key)
                if key == Key.ctrl_l or key == Key.ctrl_r:
                    # Reset hotkey state when ctrl is released
                    self.hotkey_pressed = False
            except:
                pass

        # Create listener instance
        self.listener = Listener(
            on_press=on_press, on_release=on_release, suppress=False
        )

        try:
            self.listener.start()
            print("Voice Typing Assistant is ready!")

            # Keep the program running
            while self.listener.is_alive():
                time.sleep(0.1)

                # Check if we should transcribe (set by audio callback)
                if self.should_transcribe:
                    self.should_transcribe = False
                    try:
                        # Stop the stream (audio callback has already set is_recording = False)
                        if hasattr(self, "stream"):
                            self.stream.stop()
                            self.stream.close()
                        # Process the recorded audio
                        if self.audio_frames:
                            self.transcribe_and_type()
                    except Exception as e:
                        print(f"Processing error: {e}")
                    continue

        except Exception as e:
            print(f"Listener error: {e}")
        finally:
            self.cleanup()

    def parse_hotkey(self):
        """Parse the hotkey string into a list of key identifiers."""
        if not hasattr(self, '_parsed_hotkey'):
            parts = [p.strip().lower() for p in self.hotkey_str.split('+')]
            self._parsed_hotkey = parts
        return self._parsed_hotkey

    def is_hotkey_pressed(self):
        """Check if the configured hotkey is currently pressed."""
        hotkey_parts = self.parse_hotkey()
        
        # Map modifier names to their Key objects
        modifier_map = {
            'ctrl': (Key.ctrl_l, Key.ctrl_r),
            'control': (Key.ctrl_l, Key.ctrl_r),
            'alt': (Key.alt_l, Key.alt_r),
            'shift': (Key.shift_l, Key.shift_r),
            'shift_l': (Key.shift_l,),
            'shift_r': (Key.shift_r,),
            'ctrl_l': (Key.ctrl_l,),
            'ctrl_r': (Key.ctrl_r,),
            'alt_l': (Key.alt_l,),
            'alt_r': (Key.alt_r,),
            'cmd': (Key.cmd_l, Key.cmd_r),
            'cmd_l': (Key.cmd_l,),
            'cmd_r': (Key.cmd_r,),
        }
        
        # Map special key names to Key objects
        special_key_map = {
            'space': Key.space,
            'enter': Key.enter,
            'tab': Key.tab,
            'esc': Key.esc,
            'escape': Key.esc,
            'backspace': Key.backspace,
            'delete': Key.delete,
            'up': Key.up,
            'down': Key.down,
            'left': Key.left,
            'right': Key.right,
            'home': Key.home,
            'end': Key.end,
            'page_up': Key.page_up,
            'page_down': Key.page_down,
            'insert': Key.insert,
            'f1': Key.f1,
            'f2': Key.f2,
            'f3': Key.f3,
            'f4': Key.f4,
            'f5': Key.f5,
            'f6': Key.f6,
            'f7': Key.f7,
            'f8': Key.f8,
            'f9': Key.f9,
            'f10': Key.f10,
            'f11': Key.f11,
            'f12': Key.f12,
        }
        
        # Check each part of the hotkey
        for part in hotkey_parts:
            # Check if it's a modifier
            if part in modifier_map:
                modifier_keys = modifier_map[part]
                if not any(key in self.pressed_keys for key in modifier_keys):
                    return False
            # Check if it's a special key
            elif part in special_key_map:
                if special_key_map[part] not in self.pressed_keys:
                    return False
            # Check if it's a regular character key
            else:
                # Single character key
                if len(part) == 1:
                    char_pressed = False
                    for key in self.pressed_keys:
                        # Check by character (works for both regular and numpad numbers)
                        if isinstance(key, KeyCode) and key.char == part:
                            char_pressed = True
                            break
                    if not char_pressed:
                        return False
                else:
                    # Unknown key format
                    print(f"Warning: Unknown key '{part}' in hotkey '{self.hotkey_str}'")
                    return False
        
        return True

    def toggle_recording(self):
        """Toggle recording on/off."""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording_and_transcribe()

    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, "stream") and self.stream.active:
            self.stream.stop()
            self.stream.close()

        if hasattr(self, "listener"):
            try:
                self.listener.stop()
            except:
                pass


def main():
    print("Voice Typing Assistant - VR Gaming Edition")
    print("=" * 50)

    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not found!")
        print("Please create a .env file with your OpenAI API key.")
        print("See .env.example for the required format.")
        return

    # Create and run assistant
    try:
        assistant = VoiceTypingAssistant()
        assistant.run()
    except Exception as e:
        print(f"Failed to start: {e}")
        if "permission" in str(e).lower() or "access" in str(e).lower():
            print("\nPERMISSION ISSUE DETECTED!")
            print("On Windows, you may need to run as administrator:")
            print("  Right-click Command Prompt → Run as administrator")
            print("  Then run: python voice_typing.py")
            print()
            print("On Linux/WSL, you may need to run with sudo:")
            print("  sudo python voice_typing.py")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
