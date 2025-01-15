import sys
import os
import threading
import time
import tkinter as tk
import webbrowser
from tkinter import scrolledtext
import pyautogui
from PIL import Image, ImageTk
from pynput import keyboard

def resource_path(relative_path):
    """ Get the absolute path to the resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class ScreenshotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ChatShot")

        # Set window icon
        icon_path = resource_path("logo.ico")
        self.icon_image = Image.open(icon_path)
        self.icon_photo = ImageTk.PhotoImage(self.icon_image)
        self.root.iconphoto(False, self.icon_photo)

        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=50, height=20,
                                                   font=("Times New Roman", 15))
        self.text_area.grid(column=0, row=1, pady=10, padx=10)
        self.text_area.insert(tk.INSERT,
                              "Running... Press Shift + Command + 4 to take a screenshot and paste to ChatGPT\n")
        self.text_area.configure(state='disabled')

        # Set up the slider label
        self.delay_label = tk.Label(root, text="Select time you need to take screenshot (seconds):",
                                    font=("Arial", 13, "bold"))
        self.delay_label.grid(column=0, row=2, pady=(10, 10))

        # Set up the slider
        self.delay_slider = tk.Scale(root, from_=4, to=12, orient=tk.HORIZONTAL, length=400, tickinterval=2)
        self.delay_slider.set(4)  # Set default value
        self.delay_slider.grid(column=0, row=3, pady=(0, 5))

        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        # Start the keyboard listener in a separate daemon thread
        self.listener_thread = threading.Thread(target=self.run_listener, daemon=True)
        self.listener_thread.start()

    def log(self, message):
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, message + "\n")
        self.text_area.configure(state='disabled')
        self.text_area.yview(tk.END)

    def hide_window(self):
        self.root.withdraw()

    def capture_screenshot(self):
        self.log("Press Shift-Command-4 to capture a screenshot")

    def copy_screenshot_to_clipboard(self):
        delay_time = self.delay_slider.get()
        time.sleep(delay_time)  # Wait for the screenshot to be saved

        desktop_path = os.path.expanduser("~/Desktop")
        screenshots = [f for f in os.listdir(desktop_path) if f.startswith("Screenshot") and f.endswith(".png")]
        if not screenshots:
            self.log("No screenshot found")
            return None, False

        latest_screenshot = max([os.path.join(desktop_path, f) for f in screenshots], key=os.path.getctime)

        try:
            # Use osascript to copy the screenshot to the clipboard
            os.system(f"osascript -e 'set the clipboard to (read (POSIX file \"{latest_screenshot}\") as JPEG picture)'")

            self.log("Screenshot copied to clipboard.")
            return latest_screenshot, True
        except Exception as e:
            self.log(f"Error copying screenshot to clipboard: {e}")
            return None, False

    def delete_screenshot(self, file_path):
        try:
            os.remove(file_path)
            self.log(f"Deleted screenshot: {file_path}")
        except Exception as e:
            self.log(f"Error deleting screenshot: {e}")

    def open_chatgpt(self):
        webbrowser.open("https://chat.openai.com/")
        pyautogui.sleep(3)  # Wait for the browser to open and be ready

    def paste(self):
        pyautogui.hotkey('command', 'v')  # Paste the image
        self.log("Opened ChatGPT and pasted the image.")

    def on_hotkey(self):
        time.sleep(6)  # waits for the user to take the screenshot
        self.open_chatgpt()  # opens chatgpt after the 6 seconds
        screenshot_path, copied = self.copy_screenshot_to_clipboard()
        if copied:
            self.paste()  # paste the copied screenshot
            time.sleep(5)  # Delay before deleting the screenshot to ensure it's pasted
            self.delete_screenshot(screenshot_path)  # delete the screenshot after using it

    def on_press(self, key):
        try:
            if key == keyboard.Key.shift:
                current_keys.add(keyboard.Key.shift)
            elif key == keyboard.Key.cmd:
                current_keys.add(keyboard.Key.cmd)
            elif key == keyboard.KeyCode(char='4'):
                current_keys.add(keyboard.KeyCode(char='4'))

            if keyboard.Key.shift in current_keys and keyboard.Key.cmd in current_keys and keyboard.KeyCode(
                    char='4') in current_keys:
                self.capture_screenshot()
                self.on_hotkey()
        except AttributeError:
            pass

    def on_release(self, key):
        if key in current_keys:
            current_keys.remove(key)

    def run_listener(self):
        global current_keys
        current_keys = set()

        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()

def run_gui():
    root = tk.Tk()
    app = ScreenshotApp(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()
