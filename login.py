import pyautogui
import time
import json
import os
from datetime import datetime
import logging
import sys

try:
    import pyotp
except ImportError:
    print("Installing pyotp library...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyotp"])
    import pyotp

# Set up logging
logging.basicConfig(
    filename=f'maplesea_login_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def save_credentials(username, password, second_password, otp_secret=None, filename='maplesea_credentials.json'):
    """Save credentials to file."""
    data = {
        'username': username,
        'password': password,
        'second_password': second_password,
        'otp_secret': otp_secret
    }
    with open(filename, 'w') as f:
        json.dump(data, f)
    logging.info("Credentials saved to file")

def load_credentials(filename='maplesea_credentials.json'):
    """Load credentials from file."""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            data = json.load(f)
        return data.get('username'), data.get('password'), data.get('second_password'), data.get('otp_secret')
    return None, None, None, None

def get_current_otp(secret):
    """Generate current OTP from secret key."""
    if not secret:
        return None
    
    try:
        totp = pyotp.TOTP(secret)
        return totp.now()
    except Exception as e:
        logging.error(f"Error generating OTP: {str(e)}")
        return None

def contains_only_special_characters(text):
    """Check if text contains ONLY special characters."""
    special_chars = "!@#$%^&*()-_=+[]{}|;:'\",.<>/?\\\`~"
    return all(char in special_chars for char in text)

def contains_letters_or_numbers(text):
    """Check if text contains any letters or numbers."""
    return any(char.isalnum() for char in text)

def type_using_onscreen_keyboard(text):
    """Type using the on-screen keyboard by finding and clicking key images."""
    logging.info("Using on-screen keyboard to type")
    print("Using on-screen keyboard to type...")
    
    for char in text:
        # Look for the character on the keyboard and click it
        try:
            # Try to locate the character button using its reference image
            key_image = f'images/2nd_pw_{char}.png'
            print(f"Looking for key: {char} (file: {key_image})")
            
            if os.path.exists(key_image):
                try:
                    key_location = pyautogui.locateOnScreen(key_image, confidence=0.8)
                except TypeError:
                    key_location = pyautogui.locateOnScreen(key_image)
                
                if key_location:
                    logging.info(f"Found key '{char}', clicking it")
                    print(f"Found key '{char}', clicking it...")
                    pyautogui.click(pyautogui.center(key_location))
                    time.sleep(0.3)  # Short delay between clicks
                else:
                    logging.warning(f"Could not find key '{char}' on screen")
                    print(f"Could not find key '{char}' on screen. Please click it manually.")
                    # Wait a moment for manual intervention
                    time.sleep(2)
            else:
                logging.warning(f"No reference image for key '{char}'")
                print(f"No reference image for key '{char}'. Please take a screenshot of this key for future use.")
                # Wait a moment for manual intervention
                time.sleep(2)
            
        except Exception as e:
            logging.error(f"Error clicking character '{char}': {str(e)}")
            print(f"Error clicking character '{char}': {str(e)}")
            # Wait a moment for manual intervention
            time.sleep(2)
    
    # Click OK button
    try:
        ok_button = 'images/2nd_pw_OK.png'
        if os.path.exists(ok_button):
            try:
                ok_location = pyautogui.locateOnScreen(ok_button, confidence=0.8)
            except TypeError:
                ok_location = pyautogui.locateOnScreen(ok_button)
            
            if ok_location:
                logging.info("Found OK button, clicking it")
                print("Found OK button, clicking it...")
                pyautogui.click(pyautogui.center(ok_location))
            else:
                logging.warning("Could not find OK button")
                print("Could not find OK button. Please click it manually.")
                # Wait for manual intervention
                time.sleep(3)
        else:
            logging.warning("No reference image for OK button")
            print("No reference image for OK button. Please click it manually.")
            # Wait for manual intervention
            time.sleep(3)
            
    except Exception as e:
        logging.error(f"Error clicking OK button: {str(e)}")
        print(f"Error clicking OK button: {str(e)}")
        # Wait for manual intervention
        time.sleep(3)

def launch_maplesea():
    """Launch MapleSEA from Start Menu."""
    logging.info("Starting MapleSEA launch process")
    print("Starting MapleSEA launch process...")
    
    # Load credentials
    username, password, second_password, otp_secret = load_credentials()
    if not username or not password or not second_password:
        username = input("Please enter your MapleSEA username: ")
        password = input("Please enter your MapleSEA password: ")
        second_password = input("Please enter your MapleSEA second password: ")
        
        if not otp_secret:
            print("\nFor automatic OTP generation, you need to provide your OTP secret key.")
            print("This is the secret key used by your authenticator app (Google Authenticator, Authy, etc.)")
            print("Example: JBSWY3DPEHPK3PXP")
            otp_secret = input("Enter your OTP secret key (leave blank to skip): ").strip()
            
        save_credentials(username, password, second_password, otp_secret)
    
    try:
        # Press Windows key to open Start menu
        logging.info("Opening Start menu")
        print("Opening Start menu...")
        pyautogui.press('win')
        time.sleep(1)
        
        # Type "maple" to search for MapleSEA
        logging.info("Searching for MapleSEA")
        print("Searching for MapleSEA...")
        pyautogui.write('maple')
        time.sleep(1)
        
        # Press Enter to launch the application
        logging.info("Launching MapleSEA")
        print("Launching MapleSEA...")
        pyautogui.press('enter')
        
        # Wait for the application to start
        logging.info("Waiting for MapleSEA to start")
        print("Waiting for MapleSEA to start...")
        wait_time = 15  # Default wait time in seconds
        
        # Wait for the login screen
        print(f"Waiting {wait_time} seconds for MapleSEA to fully load...")
        time.sleep(wait_time)
        
        # Attempt to locate login screen
        login_found = False
        for attempt in range(5):
            try:
                # Try to find login screen
                login_image = 'images/maplesea_login_screen.png'
                if os.path.exists(login_image):
                    try:
                        login_location = pyautogui.locateOnScreen(login_image, confidence=0.7)
                    except TypeError:
                        login_location = pyautogui.locateOnScreen(login_image)
                    
                    if login_location:
                        login_found = True
                        logging.info("Login screen found")
                        print("Login screen found!")
                        break
            except Exception as e:
                logging.error(f"Error finding login screen: {str(e)}")
            
            print(f"Waiting for login screen... (attempt {attempt+1}/5)")
            time.sleep(3)
        
        # Look for and click ID field
        try:
            id_field = 'images/maplesea_id_field.png'
            if os.path.exists(id_field):
                try:
                    id_location = pyautogui.locateOnScreen(id_field, confidence=0.7)
                except TypeError:
                    id_location = pyautogui.locateOnScreen(id_field)
                
                if id_location:
                    logging.info("ID field found, clicking it")
                    print("ID field found, clicking it...")
                    pyautogui.click(pyautogui.center(id_location))
                    time.sleep(0.5)
        except Exception as e:
            logging.error(f"Error finding ID field: {str(e)}")
            print(f"Error finding ID field: {str(e)}")

        # Enter username
        logging.info("Entering username")
        print("Entering username...")
        pyautogui.write(username)
        time.sleep(0.5)
        
        # Press Tab to move to password field
        logging.info("Moving to password field")
        print("Moving to password field...")
        pyautogui.press('tab')
        time.sleep(0.5)
        
        # Enter password
        logging.info("Entering password")
        print("Entering password...")
        pyautogui.write(password)
        time.sleep(0.5)
        
        # Press Enter to login
        logging.info("Submitting login")
        print("Submitting login...")
        pyautogui.press('enter')
        
        # Wait for OTP dialog
        logging.info("Waiting for OTP dialog")
        print("Waiting for OTP dialog to appear...")
        time.sleep(3)
        
        # Look for OTP dialog
        otp_found = False
        for attempt in range(3):
            try:
                otp_dialog = 'images/maplesea_otp_dialog.png'
                if os.path.exists(otp_dialog):
                    try:
                        otp_location = pyautogui.locateOnScreen(otp_dialog, confidence=0.7)
                    except TypeError:
                        otp_location = pyautogui.locateOnScreen(otp_dialog)
                    
                    if otp_location:
                        otp_found = True
                        logging.info("OTP dialog found")
                        print("OTP dialog found!")
                        break
            except Exception as e:
                logging.error(f"Error finding OTP dialog: {str(e)}")
            
            print(f"Looking for OTP dialog... (attempt {attempt+1}/3)")
            time.sleep(2)
        
        # Handle OTP
        if otp_secret:
            try:
                totp = pyotp.TOTP(otp_secret)
                otp = totp.now()
                logging.info("OTP generated automatically")
                print(f"Generated OTP: {otp}")
                
                # Enter OTP
                pyautogui.write(otp)
                time.sleep(0.5)
                
                # Press Enter to submit
                pyautogui.press('enter')
            except Exception as e:
                logging.error(f"Error with OTP: {str(e)}")
                print(f"Error with OTP: {str(e)}")
        else:
            print("No OTP secret provided. Please enter OTP manually and press Enter.")
            time.sleep(10)  # Give time for manual OTP entry
        
        # Wait for server selection
        logging.info("Waiting for server selection")
        print("Waiting for server selection...")
        time.sleep(5)
        
        # Look for Aquila server
        try:
            aquila_server = 'images/aquila_server.png'
            if os.path.exists(aquila_server):
                try:
                    aquila_location = pyautogui.locateOnScreen(aquila_server, confidence=0.7)
                except TypeError:
                    aquila_location = pyautogui.locateOnScreen(aquila_server)
                
                if aquila_location:
                    logging.info("Aquila server found, clicking it")
                    print("Aquila server found, clicking it...")
                    pyautogui.click(pyautogui.center(aquila_location))
                    time.sleep(1)
                    
                    # Press Enter to select character
                    logging.info("Pressing Enter to select character")
                    print("Pressing Enter to select character...")
                    pyautogui.press('enter')
                    time.sleep(1)
                else:
                    logging.warning("Aquila server not found")
                    print("Aquila server not found. Please click it manually.")
                    time.sleep(3)  # Wait for manual intervention
                    
                    # Press Enter to select character
                    logging.info("Pressing Enter to select character")
                    print("Pressing Enter to select character...")
                    pyautogui.press('enter')
                    time.sleep(1)
            else:
                logging.warning("No Aquila server image")
                print("No Aquila server image found. Please click on Aquila server manually.")
                time.sleep(3)  # Wait for manual intervention
                
                # Press Enter to select character
                logging.info("Pressing Enter to select character")
                print("Pressing Enter to select character...")
                pyautogui.press('enter')
                time.sleep(1)
        except Exception as e:
            logging.error(f"Error finding Aquila server: {str(e)}")
            print(f"Error finding Aquila server: {str(e)}")
            print("Please click on Aquila server manually.")
            time.sleep(3)  # Wait for manual intervention
            
            # Press Enter to select character
            logging.info("Pressing Enter to select character")
            print("Pressing Enter to select character...")
            pyautogui.press('enter')
            time.sleep(1)
        
        # Wait for channel selection
        time.sleep(2)
        
        # Look for and double-click on a channel
        try:
            channel = 'images/maplesea_channel.png'
            if os.path.exists(channel):
                try:
                    channel_location = pyautogui.locateOnScreen(channel, confidence=0.7)
                except TypeError:
                    channel_location = pyautogui.locateOnScreen(channel)
                
                if channel_location:
                    logging.info("Channel found, double-clicking it")
                    print("Channel found, double-clicking it...")
                    pyautogui.doubleClick(pyautogui.center(channel_location))
                    time.sleep(1)
                else:
                    logging.warning("Channel not found")
                    print("Channel not found. Please double-click a channel manually.")
                    time.sleep(3)  # Wait for manual intervention
            else:
                logging.warning("No channel image")
                print("No channel image found. Please double-click a channel manually.")
                time.sleep(3)  # Wait for manual intervention
        except Exception as e:
            logging.error(f"Error finding channel: {str(e)}")
            print(f"Error finding channel: {str(e)}")
            print("Please double-click a channel manually.")
            time.sleep(3)  # Wait for manual intervention
        
        # Wait for second password dialog
        logging.info("Waiting for second password dialog")
        print("Waiting for second password dialog...")
        time.sleep(3)
        
        # Look for second password dialog
        second_pw_found = False
        for attempt in range(3):
            try:
                second_pw_dialog = 'images/maplesea_second_pw_dialog.png'
                if os.path.exists(second_pw_dialog):
                    try:
                        pw_dialog_location = pyautogui.locateOnScreen(second_pw_dialog, confidence=0.7)
                    except TypeError:
                        pw_dialog_location = pyautogui.locateOnScreen(second_pw_dialog)
                    
                    if pw_dialog_location:
                        second_pw_found = True
                        logging.info("Second password dialog found")
                        print("Second password dialog found!")
                        break
            except Exception as e:
                logging.error(f"Error finding second password dialog: {str(e)}")
            
            print(f"Looking for second password dialog... (attempt {attempt+1}/3)")
            time.sleep(2)
        
        # Handle second password entry
        if contains_only_special_characters(second_password):
            # Type special characters directly
            logging.info("Entering second password (special characters only)")
            print("Entering second password (special characters only)...")
            pyautogui.write(second_password)
            time.sleep(0.5)
        elif contains_letters_or_numbers(second_password):
            # Check if has both special chars and alphanumeric
            has_special = any(not char.isalnum() for char in second_password)
            
            if has_special:
                # Mixed password
                logging.info("Processing mixed password")
                print("Processing mixed password...")
                
                # Process each character
                for char in second_password:
                    if char.isalnum():
                        # Use on-screen keyboard for letters/numbers
                        try:
                            key_image = f'images/2nd_pw_{char}.png'
                            if os.path.exists(key_image):
                                try:
                                    key_location = pyautogui.locateOnScreen(key_image, confidence=0.8)
                                except TypeError:
                                    key_location = pyautogui.locateOnScreen(key_image)
                                
                                if key_location:
                                    logging.info(f"Found key '{char}', clicking it")
                                    print(f"Found key '{char}', clicking it...")
                                    pyautogui.click(pyautogui.center(key_location))
                                    time.sleep(0.3)
                                else:
                                    logging.warning(f"Could not find key '{char}'")
                                    print(f"Could not find key '{char}'. Please click it manually.")
                                    time.sleep(2)  # Wait for manual intervention
                            else:
                                logging.warning(f"No reference image for key '{char}'")
                                print(f"No reference image for key '{char}'. Please click it manually.")
                                time.sleep(2)  # Wait for manual intervention
                        except Exception as e:
                            logging.error(f"Error with key '{char}': {str(e)}")
                            print(f"Error with key '{char}': {str(e)}")
                            time.sleep(2)  # Wait for manual intervention
                    else:
                        # Type special characters directly
                        print(f"Typing special character '{char}'...")
                        pyautogui.write(char)
                        time.sleep(0.3)
                
                # Click OK
                try:
                    ok_button = 'images/2nd_pw_OK.png'
                    if os.path.exists(ok_button):
                        try:
                            ok_location = pyautogui.locateOnScreen(ok_button, confidence=0.8)
                        except TypeError:
                            ok_location = pyautogui.locateOnScreen(ok_button)
                        
                        if ok_location:
                            logging.info("Found OK button, clicking it")
                            print("Found OK button, clicking it...")
                            pyautogui.click(pyautogui.center(ok_location))
                        else:
                            logging.warning("Could not find OK button")
                            print("Could not find OK button. Please click it manually.")
                            time.sleep(3)  # Wait for manual intervention
                    else:
                        logging.warning("No reference image for OK button")
                        print("No reference image for OK button. Please click it manually.")
                        time.sleep(3)  # Wait for manual intervention
                except Exception as e:
                    logging.error(f"Error clicking OK button: {str(e)}")
                    print(f"Error clicking OK button: {str(e)}")
                    time.sleep(3)  # Wait for manual intervention
            else:
                # Only letters/numbers
                logging.info("Using on-screen keyboard for all characters")
                print("Using on-screen keyboard for all characters...")
                type_using_onscreen_keyboard(second_password)
        
        # Press Enter if needed
        pyautogui.press('enter')
        
        logging.info("Login process completed")
        print("Login process completed. You should now be logged into MapleSEA!")
        
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        print(f"An error occurred: {str(e)}")
        print("You may need to adjust the script for your specific setup.")

if __name__ == "__main__":
    print("MapleSEA Auto-Login Tool")
    print("========================")
    
    print("Note: For first-time setup, the script will:")
    print("1. Ask for your MapleSEA username and password")
    print("2. Ask for your second password (for character selection)")
    print("3. Ask for your OTP secret key for automatic OTP generation")
    print("\nFor full automation, make sure you have these screenshots in the 'images' folder:")
    print("- maplesea_login_screen.png - The login screen")
    print("- maplesea_id_field.png - The ID field")
    print("- maplesea_otp_dialog.png - The OTP dialog")
    print("- aquila_server.png - The Aquila server button")
    print("- maplesea_channel.png - Any channel button")
    print("- maplesea_second_pw_dialog.png - The second password dialog")
    print("- 2nd_pw_a.png, 2nd_pw_b.png, etc. - Screenshots of each letter/number on the keyboard")
    print("- 2nd_pw_OK.png - The OK button on the on-screen keyboard")
    print("\nCredentials will be saved in the current directory.\n")
    
    launch_maplesea()
    input("Press Enter to exit...")