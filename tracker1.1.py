import os
import time
from datetime import datetime
import base64
import requests
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging
import threading

# Configuration for multiple trackers
TRACKERS = [
    {
        "name": "DuinoMiner Tracker",
        "url": "https://explorer.duinocoin.com/?search=TwilightFi",
        "webhook_url": "https://discord.com/api/webhooks/1409684620081106954/ougGF6G5G9zFgJEOLOkKaucIIvn0gAi0YFNA08Sd_LxDqQZ3L98Qol8ObSj_QsawuqhZ",
        "color": 0xFF6200,  # Orange
        "heart_emoji": "🧡"
    },
    {
        "name": "MoneroMiner Tracker",
        "url": "https://monero.hashvault.pro/en/",
        "webhook_url": "https://discord.com/api/webhooks/1409684517312135289/mD8ryWuo5lNA6d-eYs3O4XfW4SwvLkFhe1LJPJLRL-w7WOozerMKv8H7trb9tofXizTB",
        "color": 0x00FF00,  # Green
        "heart_emoji": "💚"
    },
    {
        "name": "SoloMinerBTC Tracker",
        "url": "https://web.public-pool.io/#/",
        "webhook_url": "https://discord.com/api/webhooks/1409684430393704581/xsX79YIjsq7yZFOPxHVq7PmMrZNJJiiSMUm-oX8Xx57DAvJA120QWrfMMUbkQyoBa51h",
        "color": 0x0000FF,  # Blue
        "heart_emoji": "💙"
    },
    {
        "name": "ServerUptime Tracker",
        "url": "https://uptimerobot.com/dashboard",
        "webhook_url": "https://discord.com/api/webhooks/1409685135305085079/WnBuTVuF0iXYPc8ahfuyGK1qBOvhRoH9n214tHkOIm6TvHFhUSMwu_D5ByCYsV3UrJ9l",
        "color": 0x800080,  # Purple
        "heart_emoji": "💜"
    }
]

SCREENSHOT_DIR = "screenshots"
CHECK_INTERVAL_SECONDS = 5  # 5 seconds
LOG_FILE = "bot.log"

# Set up lightweight logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Create screenshot directory if it doesn't exist
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def setup_driver():
    """Set up a lightweight headless Chrome driver optimized for Linux."""
    options = Options()
    options.add_argument("--headless=new")  # Use new headless mode
    options.add_argument("--no-sandbox")  # Required for Linux environments
    options.add_argument("--disable-dev-shm-usage")  # Reduce memory usage in containers
    options.add_argument("--disable-gpu")  # Disable GPU acceleration
    options.add_argument("--disable-extensions")  # Disable extensions
    options.add_argument("--disable-infobars")  # Disable infobars
    options.add_argument("--disable-notifications")  # Disable notifications
    options.add_argument("--blink-settings=imagesEnabled=false")  # Disable images
    options.add_argument("--window-size=1280,720")  # Smaller window size
    options.add_argument("--disable-background-timer-throttling")  # Prevent throttling
    options.add_argument("--disable-renderer-backgrounding")  # Prevent renderer throttling
    options.add_argument("--disable-background-networking")  # Disable background network
    options.add_argument("--disable-client-side-phishing-detection")  # Disable phishing detection
    options.add_argument("--disable-default-apps")  # Disable default apps
    options.add_argument("--no-zygote")  # Reduce memory usage in Linux

    # Use webdriver_manager to handle ChromeDriver
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        logging.error(f"Error setting up Chrome driver: {str(e)}")
        raise

def send_discord_embed(screenshot_path, tracker_name, webhook_url, url, color, heart_emoji):
    """Send a Discord embed with the screenshot."""
    try:
        timestamp = datetime.utcnow().isoformat()
        
        # Read and encode the screenshot to base64
        with open(screenshot_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Create Discord embed payload
        embed = {
            "title": f"{tracker_name} Screenshot {heart_emoji}",
            "description": f"Screenshot of {url}",
            "color": color,
            "timestamp": timestamp,
            "footer": {"text": f"{tracker_name} {heart_emoji}"},
            "image": {"url": f"attachment://{os.path.basename(screenshot_path)}"}
        }

        # Prepare the webhook payload
        payload = {"embeds": [embed]}
        files = {"file": (os.path.basename(screenshot_path), open(screenshot_path, "rb"))}

        # Send the webhook
        response = requests.post(webhook_url, data={"payload_json": json.dumps(payload)}, files=files)
        
        if response.status_code == 204:
            logging.info(f"[{tracker_name}] Successfully sent screenshot to Discord: {screenshot_path}")
        else:
            logging.error(f"[{tracker_name}] Failed to send screenshot to Discord: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"[{tracker_name}] Error sending Discord embed: {str(e)}")
        send_error_to_discord(f"Error sending Discord embed: {str(e)}", tracker_name, webhook_url, color, heart_emoji)

def send_error_to_discord(error_message, tracker_name, webhook_url, color, heart_emoji):
    """Send an error message to Discord."""
    try:
        error_embed = {
            "title": f"Error in {tracker_name} {heart_emoji}",
            "description": error_message,
            "color": 0xff0000,  # Red for errors
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": f"{tracker_name} {heart_emoji}"}
        }
        requests.post(webhook_url, json={"embeds": [error_embed]})
    except Exception as e:
        logging.error(f"[{tracker_name}] Failed to send error to Discord: {str(e)}")

def capture_screenshot(driver, url, tracker_name):
    """Capture a screenshot of the webpage."""
    try:
        driver.get(url)
        time.sleep(5)  # Wait for dynamic content

        # Get page dimensions
        full_width = driver.execute_script(
            "return Math.max(document.body.scrollWidth, document.body.offsetWidth, "
            "document.documentElement.clientWidth, document.documentElement.scrollWidth, "
            "document.documentElement.offsetWidth);"
        )
        full_height = driver.execute_script(
            "return Math.max(document.body.scrollHeight, document.body.offsetHeight, "
            "document.documentElement.clientHeight, document.documentElement.scrollHeight, "
            "document.documentElement.offsetHeight);"
        )

        # Cap window size
        max_width = min(full_width, 1920)
        max_height = min(full_height, 1080)
        driver.set_window_size(max_width, max_height)

        # Generate timestamp for filename
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        screenshot_path = os.path.join(SCREENSHOT_DIR, f"{tracker_name.replace(' ', '_')}_screenshot_{timestamp}.png")

        # Take screenshot
        driver.save_screenshot(screenshot_path)
        logging.info(f"[{tracker_name}] Screenshot saved: {screenshot_path}")
        return screenshot_path
    except Exception as e:
        logging.error(f"[{tracker_name}] Error capturing screenshot: {str(e)}")
        raise

def monitor_tracker(tracker):
    """Monitoring loop for a single tracker."""
    name = tracker["name"]
    url = tracker["url"]
    webhook_url = tracker["webhook_url"]
    color = tracker["color"]
    heart_emoji = tracker["heart_emoji"]
    
    logging.info(f"[{name}] started. Checking every {CHECK_INTERVAL_SECONDS} seconds...")
    
    while True:
        driver = None
        try:
            driver = setup_driver()
            screenshot_path = capture_screenshot(driver, url, name)
            send_discord_embed(screenshot_path, name, webhook_url, url, color, heart_emoji)
        except Exception as e:
            logging.error(f"[{name}] Error in main loop: {str(e)}")
            send_error_to_discord(f"Error in main loop: {str(e)}", name, webhook_url, color, heart_emoji)
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    logging.error(f"[{name}] Error closing driver: {str(e)}")
        
        time.sleep(CHECK_INTERVAL_SECONDS)

def main():
    """Start monitoring threads for all trackers."""
    threads = []
    for tracker in TRACKERS:
        thread = threading.Thread(target=monitor_tracker, args=(tracker,))
        thread.daemon = True
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()