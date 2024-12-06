import pygetwindow as gw
import mss
import cv2
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
import os
import time
from threading import Thread
import logging
import json

# Configure logging
logging.basicConfig(
    filename="detection_log.txt",  # Log file name
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger("").addHandler(console)


class MinimapApp:
    def __init__(self, root, interval=0.1):
        self.root = root
        self.root.title("Minimap Viewer with Object Detection")

        # Label to display the minimap
        self.minimap_label = tk.Label(self.root)
        self.minimap_label.pack()

        # Interval between captures
        self.interval = interval

        # Stop flag for the capture loop
        self.stop_flag = False

        # Minimap boundaries (to be set after initial detection)
        self.static_region = None

        # Template paths
        self.template_paths = {
            "friend": "friend_template.png",
            "player": "player_template.png",
            "rune": "rune_template.png",
            "guild": "guild_template.png",
            "people": "people_template.png"
        }

        # Load templates
        self.templates = self.load_templates()

        # Start the capture thread
        self.capture_thread = Thread(target=self.capture_minimap_continuously)
        self.capture_thread.start()

    def load_templates(self):
        """
        Load all templates into a dictionary.
        Returns:
            dict: A dictionary with object names as keys and template images as values.
        """
        templates = {}
        for object_type, path in self.template_paths.items():
            if os.path.exists(path):
                template = cv2.imread(path, cv2.IMREAD_COLOR)
                if template is None:
                    logging.error(f"Failed to load {object_type} template from {path}.")
                else:
                    logging.info(f"{object_type} template loaded successfully.")
                templates[object_type] = template
            else:
                logging.error(f"Template file for {object_type} not found at {path}.")
                templates[object_type] = None
        return templates

    def detect_minimap_region(self, sct, initial_region):
        """
        Detect the minimap region dynamically during the first capture.
        """
        screenshot = sct.grab(initial_region)
        image = np.array(screenshot)

        # Convert the image to grayscale for boundary detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours based on dynamic aspect ratio and size
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h
            if 2.0 < aspect_ratio < 4.0 and 50 < w < 250 and 30 < h < 150:
                return {
                    "top": initial_region["top"] + y,
                    "left": initial_region["left"] + x,
                    "width": w,
                    "height": h,
                }

        # If no valid minimap is detected, return the entire initial region
        return initial_region

    def detect_objects(self, image):
        """
        Detect objects on the minimap using OpenCV template matching.
        Args:
            image (numpy array): The source image (minimap) to search in.
        Returns:
            dict: Detected objects with their positions.
        """
        detected_objects = {}

        # Convert source image to grayscale (if it's not already)
        if len(image.shape) == 3:  # Check if image is colored (3 channels)
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        else:
            image_gray = image  # Already grayscale

        for object_type, template in self.templates.items():
            if template is None:
                logging.warning(f"Skipping detection for {object_type}: template is missing or invalid.")
                continue

            # Ensure the template is grayscale
            if len(template.shape) == 3:  # Check if template is colored
                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            else:
                template_gray = template  # Already grayscale

            # Positions to store detected matches
            positions = []

            # Multi-scale matching
            for scale in [0.8, 1.0, 1.2]:  # Adjust scales as needed
                # Resize the template for the current scale
                try:
                    scaled_template = cv2.resize(template_gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
                except Exception as e:
                    logging.error(f"Error resizing template for {object_type} at scale {scale}: {e}")
                    continue

                # Perform template matching
                try:
                    result = cv2.matchTemplate(image_gray, scaled_template, cv2.TM_CCOEFF_NORMED)
                    loc = np.where(result > 0.99999)  # Adjust threshold as needed
                    for pt in zip(*loc[::-1]):  # Switch x and y
                        positions.append(pt)
                        logging.info(f"Detected {object_type} at position {pt}.")
                except Exception as e:
                    logging.error(f"Error during template matching for {object_type}: {e}")
                    continue

            detected_objects[object_type] = positions

        return detected_objects

    def draw_detections(self, image, detected_objects):
        """
        Draw rectangles around detected objects on the minimap.
        """
        for object_type, positions in detected_objects.items():
            color = (0, 255, 0)  # Default rectangle color (green)
            if object_type == "friend":
                color = (255, 0, 0)  # Blue
            elif object_type == "npc":
                color = (0, 255, 255)  # Yellow
            elif object_type == "player":
                color = (0, 0, 255)  # Red
            elif object_type == "rune":
                color = (128, 0, 128)  # Purple

            # Get the template dimensions for consistent box sizes
            template = self.templates.get(object_type)
            if template is not None:
                template_height, template_width = template.shape[:2]
            else:
                template_width, template_height = 20, 20  # Default size if template not found

            for pt in positions:
                # Draw the rectangle around the detected object
                top_left = pt
                bottom_right = (pt[0] + template_width, pt[1] + template_height)
                cv2.rectangle(image, top_left, bottom_right, color, 2)

                # Add a label above the rectangle
                label_position = (pt[0], pt[1] - 10)
                cv2.putText(
                    image,
                    object_type,
                    label_position,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    color,
                    1,
                )

    def capture_minimap_continuously(self):
        try:
            # Locate the MapleStory window
            window = gw.getWindowsWithTitle('MapleStory')[0]
        except IndexError:
            logging.error("MapleStory window not found. Make sure the game is running.")
            return

        # Get the window position and dimensions
        left, top, width, height = window.left, window.top, window.width, window.height

        # Define the initial region to capture (larger area around the minimap)
        initial_region = {
            "top": top + 62,
            "left": left + 8,
            "width": 350,
            "height": 150,
        }

        with mss.mss() as sct:
            # Detect the minimap region during the first capture
            if self.static_region is None:
                logging.info("Detecting minimap region...")
                self.static_region = self.detect_minimap_region(sct, initial_region)
                logging.info(f"Static region detected: {self.static_region}")

            while not self.stop_flag:
                # Use the static region for all subsequent captures
                screenshot = sct.grab(self.static_region)
                image = np.array(screenshot)

                # Detect objects on the minimap
                detected_objects = self.detect_objects(image)

                # Draw rectangles around detected objects
                self.draw_detections(image, detected_objects)

                # --- Data Export ---
                data = {
                    "player_x": 100,  # Replace with actual player x-coordinate
                    "player_y": 50,  # Replace with actual player y-coordinate
                    "detected_objects": []  # Initialize an empty list for detected objects
                }

                # Add all detected objects to the data dictionary
                for object_type, positions in detected_objects.items():
                    for pt in positions:
                        data["detected_objects"].append({
                            "type": object_type,
                            "x": pt[0],
                            "y": pt[1]
                        })

                with open("minimap_data.json", "w") as f:
                    json.dump(data, f)
                # --- End of Data Export ---

                # Convert to RGB for display
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)

                # Convert to Tkinter-compatible image
                minimap_image = Image.fromarray(image_rgb)
                image_tk = ImageTk.PhotoImage(minimap_image)

                # Update the label with the new image
                self.minimap_label.config(image=image_tk)
                self.minimap_label.image = image_tk

                # Wait before the next capture
                time.sleep(self.interval)

    def on_close(self):
        # Stop the capture thread and close the GUI
        self.stop_flag = True
        self.capture_thread.join()
        self.root.destroy()


# Create the Tkinter window
root = tk.Tk()

# Create the MinimapApp
app = MinimapApp(root, interval=0.5)

# Set the close event
root.protocol("WM_DELETE_WINDOW", app.on_close)

# Start the Tkinter main loop
root.mainloop()