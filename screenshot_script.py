import subprocess
import os
import pyautogui
import time
import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

def open_website(url):
    driver = webdriver.Chrome()
    driver.get(url)
    return driver

def change_screen_content(website):
    return open_website(website)

def capture_screenshots(driver, index, num_screenshots=5, output_dir=os.getcwd()):
    data_dir = os.path.join(output_dir, 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    screen_width, screen_height = pyautogui.size()
    for _ in range(num_screenshots):
        x, y = random.randint(0, screen_width), random.randint(0, screen_height)
        pyautogui.moveTo(x, y, duration=0.5)
        time.sleep(3)  # Adjust timing based on screen loading time
        
        # Use screencapture command to capture the screen with the cursor
        screenshot_file = os.path.join(data_dir, f'screenshot_{index}_{x}_{y}.png')
        subprocess.run(["screencapture", "-C", "-x", screenshot_file])
        
        index += 1
    return index

def main():
    website_lists = ["https://www.berkeley.edu", "https://www.amazon.com", "https://www.stanford.edu", "https://www.wikipedia.org", "https://www.khanacademy.org",
                     "https://twitter.com", "https://www.linkedin.com", "https://www.netflix.com", "https://www.spotify.com", "https://www.google.com"]

    index = 0

    for website in website_lists:
        driver = change_screen_content(website)
        index = capture_screenshots(driver, index, 5)
        driver.quit()

if __name__ == "__main__":
    main()