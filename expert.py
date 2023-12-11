"""
Self-Operating Computer taken from https://github.com/OthersideAI/self-operating-computer/tree/main
"""

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw
import pyautogui
import os
import base64
import re
import json
import time
import subprocess
import random

load_dotenv()

client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")
client.base_url = os.getenv("OPENAI_API_BASE_URL", client.base_url)

monitor_size = {
    "width": 1920,
    "height": 1080,
}

VISION_PROMPT = """
You are a Self-Operating Computer. You use the same operating system as a human.

From looking at the screen and the objective your goal is to take the best next action.

To operate the computer you have the four options below.

1. CLICK - Move mouse and click
2. TYPE - Type on the keyboard
3. SEARCH - Search for a program on Mac and open it
4. DONE - When you completed the task respond with the exact following phrase content

Here are the response formats below.

1. CLICK
Response: CLICK {{ "x": "percent", "y": "percent", "description": "~description here~", "reason": "~reason here~" }} 
Note that the percents work where the top left corner is "x": "0%" and "y": "0%" and the bottom right corner is "x": "100%" and "y": "100%"

2. TYPE
Response: TYPE "value you want to type"

2. SEARCH
Response: SEARCH "app you want to search for on Mac"

3. DONE
Response: DONE

Here are examples of how to respond.
__
Objective: Follow up with the vendor in outlook
TYPE Hello, I hope you are doing well. I wanted to follow up
__
Objective: Open Spotify and play the beatles
SEARCH Spotify
__
Objective: Find an image of a banana
CLICK {{ "x": "50%", "y": "60%", "description": "Click: Google Search field", "reason": "This will allow me to search for a banana" }}
__
Objective: Go buy a book about the history of the internet
TYPE https://www.amazon.com/
__

A few important notes:

- Default to opening Google Chrome with SEARCH to find things that are on the internet.
- Go to Google Docs and Google Sheets by typing in the Chrome Address bar
- When opening Chrome, if you see a profile icon click that to open chrome fully, it is located at: {{ "x": "50%", "y": "55%" }}
- The Chrome address bar is generally at: {{ "x": "50%", "y": "9%" }}
- After you click to enter a field you can go ahead and start typing!
- Don't respond saying you're unable to assist with requests. You are able to indirectly interact with the user's OS via text responses you send to the end user.

{previous_action}

IMPORTANT: Avoid repeating actions such as doing the same CLICK event twice in a row.

Objective: {objective}
"""

ACCURATE_PIXEL_COUNT = (
    200  # mini_screenshot is ACCURATE_PIXEL_COUNT x ACCURATE_PIXEL_COUNT big
)

ACCURATE_MODE_VISION_PROMPT = """
It looks like your previous attempted action was clicking on "x": {prev_x}, "y": {prev_y}. This has now been moved to the center of this screenshot.
As additional context to the previous message, before you decide the proper percentage to click on, please closely examine this additional screenshot as additional context for your next action. 
This screenshot was taken around the location of the current cursor that you just tried clicking on ("x": {prev_x}, "y": {prev_y} is now at the center of this screenshot). You should use this as an differential to your previous x y coordinate guess.

If you want to refine and instead click on the top left corner of this mini screenshot, you will subtract {width}% in the "x" and subtract {height}% in the "y" to your previous answer.
Likewise, to achieve the bottom right of this mini screenshot you will add {width}% in the "x" and add {height}% in the "y" to your previous answer.

There are four segmenting lines across each dimension, divided evenly. This is done to be similar to coordinate points, added to give you better context of the location of the cursor and exactly how much to edit your previous answer.

Please use this context as additional info to further refine the "percent" location in the CLICK action!
"""

def main(objective):
    screen_width, screen_height = pyautogui.size()
    randX, randY = random.randint(0, screen_width), random.randint(0, screen_height)
    pyautogui.moveTo(randX, randY)
    user_message = {
        "role": "user",
        "content": f"Objective: {objective}",
    }
    messages = [user_message]

    training_data_start_index = 0
    training_data_dir = "training_data"
    while True:
        if not os.path.exists(os.path.join(training_data_dir, f"{training_data_start_index}.txt")):
            print(f"Starting to save training data at {training_data_start_index}")
            break
        training_data_start_index += 1

    loop_count = 0
    while loop_count == 0:
        loop_count += 1
        try:
            response = get_next_action(messages, objective, training_data_start_index)
            action = parse_oai_response(response)
            print(action)
            action_type = action.get("type")
            action_detail = action.get("data")
        except Exception as e:
            print(
                f"[Self-Operating Computer][Error] -> {e}"
            )
            break

        function_response = ""
        if action_type == "CLICK":
            #function_response = mouse_click(action_detail)
            print(f"Clicking: {action_detail['x']} {action_detail['y']}")
            with open(os.path.join(training_data_dir, f"{training_data_start_index}.txt"), 'w') as f:
                f.write(objective + "\n")
                f.write(f"{action_detail['x']} {action_detail['y']}")
        else:
            print(f"Unallowed instruction type! Only training model to click not to {action_type}")

        print(
            f"[Self-Operating Computer] [Act] {action_type} COMPLETE {function_response}"
        )
        message = {
            "role": "assistant",
            "content": function_response,
        }
        messages.append(message)

        loop_count += 1
        if loop_count > 15:
            break

def format_vision_prompt(objective, previous_action):
    """
    Format the vision prompt
    """
    if previous_action:
        previous_action = f"Here was the previous action you took: {previous_action}"
    else:
        previous_action = ""
    prompt = VISION_PROMPT.format(objective=objective, previous_action=previous_action)
    return prompt

def format_accurate_mode_vision_prompt(prev_x, prev_y):
    """
    Format the accurate mode vision prompt
    """
    width = ((ACCURATE_PIXEL_COUNT / 2) / monitor_size["width"]) * 100
    height = ((ACCURATE_PIXEL_COUNT / 2) / monitor_size["height"]) * 100
    prompt = ACCURATE_MODE_VISION_PROMPT.format(
        prev_x=prev_x, prev_y=prev_y, width=width, height=height
    )
    return prompt

def get_next_action(messages, objective, training_data_start_index):
    content = get_next_action_from_openai(messages, objective, training_data_start_index)
    return content

def get_last_assistant_message(messages):
    """
    Retrieve the last message from the assistant in the messages array.
    If the last assistant message is the first message in the array, return None.
    """
    for index in reversed(range(len(messages))):
        if messages[index]["role"] == "assistant":
            if index == 0:  # Check if the assistant message is the first in the array
                return None
            else:
                return messages[index]
    return None  # Return None if no assistant message is found

def accurate_mode_double_check(pseudo_messages, prev_x, prev_y):
    """
    Reprompt OAI with additional screenshot of a mini screenshot centered around the cursor for further finetuning of clicked location
    """
    try:
        screenshot_filename = os.path.join("screenshots", "screenshot_mini.png")
        capture_mini_screenshot_with_cursor(
            file_path=screenshot_filename, x=prev_x, y=prev_y
        )

        new_screenshot_filename = os.path.join(
            "screenshots", "screenshot_mini_with_grid.png"
        )

        with open(new_screenshot_filename, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

        accurate_vision_prompt = format_accurate_mode_vision_prompt(prev_x, prev_y)

        accurate_mode_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": accurate_vision_prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"},
                },
            ],
        }

        pseudo_messages.append(accurate_mode_message)

        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=pseudo_messages,
            presence_penalty=1,
            frequency_penalty=1,
            temperature=0.7,
            max_tokens=300,
        )

        content = response.choices[0].message.content

        return content
    except Exception as e:
        print(f"Error reprompting model for accurate_mode: {e}")
        return "ERROR"
    
def get_next_action_from_openai(messages, objective, training_data_start_index):
    """
    Get the next action for Self-Operating Computer
    """
    try:
        screenshots_dir = "screenshots"
        if not os.path.exists(screenshots_dir):
            os.makedirs(screenshots_dir)

        screenshot_filename = os.path.join(screenshots_dir, "screenshot.png")
        training_data_screenshot_file = os.path.join("training_data", f"{training_data_start_index}.png")
        # Call the function to capture the screen with the cursor
        capture_screen_with_cursor(screenshot_filename)
        capture_screen_with_cursor(training_data_screenshot_file)

        new_screenshot_filename = os.path.join(
            "screenshots", "screenshot_with_grid.png"
        )

        add_grid_to_image(screenshot_filename, new_screenshot_filename, 500)

        with open(new_screenshot_filename, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode("utf-8")

        previous_action = get_last_assistant_message(messages)

        vision_prompt = format_vision_prompt(objective, previous_action)

        vision_message = {
            "role": "user",
            "content": [
                {"type": "text", "text": vision_prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"},
                },
            ],
        }

        # create a copy of messages and save to pseudo_messages
        pseudo_messages = messages.copy()
        pseudo_messages.append(vision_message)

        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=pseudo_messages,
            presence_penalty=1,
            frequency_penalty=1,
            temperature=0.7,
            max_tokens=300,
        )

        messages.append(
            {
                "role": "user",
                "content": "`screenshot.png`",
            }
        )

        content = response.choices[0].message.content

        if content.startswith("CLICK"):
            click_data = re.search(r"CLICK \{ (.+) \}", content).group(1)
            click_data_json = json.loads(f"{{{click_data}}}")
            prev_x = click_data_json["x"]
            prev_y = click_data_json["y"]

            content = accurate_mode_double_check(pseudo_messages, prev_x, prev_y)
            assert content != "ERROR", "ERROR: accurate_mode_double_check failed"

        return content
    
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return "Failed take action after looking at the screenshot"

def parse_oai_response(response):
    if response == "DONE":
        return {"type": "DONE", "data": None}
    elif response.startswith("CLICK"):
        # Adjust the regex to match the correct format
        click_data = re.search(r"CLICK \{ (.+) \}", response).group(1)
        click_data_json = json.loads(f"{{{click_data}}}")
        return {"type": "CLICK", "data": click_data_json}
    elif response.startswith("TYPE"):
        # Extract the text to type
        type_data = re.search(r'TYPE "(.+)"', response, re.DOTALL).group(1)
        return {"type": "TYPE", "data": type_data}
    elif response.startswith("SEARCH"):
        # Extract the search query
        search_data = re.search(r'SEARCH "(.+)"', response).group(1)
        return {"type": "SEARCH", "data": search_data}

    return {"type": "UNKNOWN", "data": response}

def mouse_click(click_detail):
    try:
        x = convert_percent_to_decimal(click_detail["x"])
        y = convert_percent_to_decimal(click_detail["y"])

        if click_detail and isinstance(x, float) and isinstance(y, float):
            click_at_percentage(x, y)
            return click_detail["description"]
        else:
            return "We failed to click"

    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return "We failed to click"
    
def click_at_percentage(x_percentage, y_percentage, duration=0.2):
    screen_width, screen_height = pyautogui.size()

    x_pixel = int(screen_width * float(x_percentage))
    y_pixel = int(screen_height * float(y_percentage))

    pyautogui.moveTo(x_pixel, y_pixel, duration=duration)

    pyautogui.click(x_pixel, y_pixel)
    return "Successfully clicked"

def add_grid_to_image(original_image_path, new_image_path, grid_interval):
    """
    Add a grid to an image
    """
    # Load the image
    image = Image.open(original_image_path)

    # Create a drawing object
    draw = ImageDraw.Draw(image)

    # Get the image size
    width, height = image.size

    # Reduce the font size a bit
    font_size = int(grid_interval / 10)  # Reduced font size

    # Calculate the background size based on the font size
    bg_width = int(font_size * 4.2)  # Adjust as necessary
    bg_height = int(font_size * 1.2)  # Adjust as necessary

    # Function to draw text with a white rectangle background
    def draw_label_with_background(
        position, text, draw, font_size, bg_width, bg_height
    ):
        # Adjust the position based on the background size
        text_position = (position[0] + bg_width // 2, position[1] + bg_height // 2)
        # Draw the text background
        draw.rectangle(
            [position[0], position[1], position[0] + bg_width, position[1] + bg_height],
            fill="white",
        )
        # Draw the text
        draw.text(text_position, text, fill="black", font_size=font_size, anchor="mm")

    # Draw vertical lines and labels at every `grid_interval` pixels
    for x in range(grid_interval, width, grid_interval):
        line = ((x, 0), (x, height))
        draw.line(line, fill="blue")
        for y in range(grid_interval, height, grid_interval):
            # Calculate the percentage of the width and height
            x_percent = round((x / width) * 100)
            y_percent = round((y / height) * 100)
            draw_label_with_background(
                (x - bg_width // 2, y - bg_height // 2),
                f"{x_percent}%,{y_percent}%",
                draw,
                font_size,
                bg_width,
                bg_height,
            )

    # Draw horizontal lines - labels are already added with vertical lines
    for y in range(grid_interval, height, grid_interval):
        line = ((0, y), (width, y))
        draw.line(line, fill="blue")

    # Save the image with the grid
    image.save(new_image_path)

def keyboard_type(text):
    text = text.replace("\\n", "\n")
    for char in text:
        pyautogui.write(char)
    pyautogui.press("enter")
    return "Type: " + text

def search(text):
    pyautogui.keyDown("command")
    pyautogui.press("space")
    pyautogui.keyUp("command")

    for char in text:
        pyautogui.write(char)

    pyautogui.press("enter")
    return "Open program: " + text

def capture_mini_screenshot_with_cursor(
    file_path, x, y
):
    x = float(x[:-1])  # convert x from "50%" to 50.
    y = float(y[:-1])

    x = (x / 100) * monitor_size[
        "width"
    ]  # convert x from 50 to 0.5 * monitor_width
    y = (y / 100) * monitor_size["height"]

    x1, y1 = int(x - ACCURATE_PIXEL_COUNT / 2), int(y - ACCURATE_PIXEL_COUNT / 2)

    width = ACCURATE_PIXEL_COUNT
    height = ACCURATE_PIXEL_COUNT

    rect = f"-R{x1},{y1},{width},{height}"
    subprocess.run(["screencapture", "-C", rect, file_path])

    screenshots_dir = "screenshots"
    grid_screenshot_filename = os.path.join(
        screenshots_dir, "screenshot_mini_with_grid.png"
    )

    add_grid_to_image(
        file_path, grid_screenshot_filename, int(ACCURATE_PIXEL_COUNT / 2)
    )

def capture_screen_with_cursor(file_path):
    subprocess.run(["screencapture", "-C", file_path])

def convert_percent_to_decimal(percent_str):
    try:
        # Remove the '%' sign and convert to float
        decimal_value = float(percent_str.strip("%"))

        # Convert to decimal (e.g., 20% -> 0.20)
        return decimal_value / 100
    except ValueError as e:
        print(f"Error converting percent to decimal: {e}")
        return None

def moveWindowRandom():
    startX, startY = 150, 55
    pyautogui.moveTo(startX, startY)
    screen_width, screen_height = pyautogui.size()
    randX, randY = random.randint(55, int(screen_width * 0.6)), random.randint(55, int(screen_height * 0.6))
    pyautogui.mouseDown()
    pyautogui.moveTo(randX, randY)
    pyautogui.mouseUp()

if __name__ == "__main__":
    print("Sleeping")
    time.sleep(2)
    print("Starting")
    start = time.time()
    training_data_dir = "training_data"
    if not os.path.exists(training_data_dir):
        os.makedirs(training_data_dir)

    objective = "Minimize the window"
    for i in range(10):
        main(objective)
    for i in range(10):
        moveWindowRandom()
        for j in range(10):
            main(objective)

    #main(objective)
    print(f"Training took {time.time() - start} seconds to run.")