from pynput import mouse
import time
import pyautogui
import numpy as np

clickNumber = 0
clicking = False

def on_click(x, y, button, pressed):
    if pressed:
        global clickNumber
        global clicking
        clicking = True
        print(f"Mouse clicked at ({x}, {y}) with {button}")
        now = time.time()
        timestamp = round(now - start, 2)
        
        #screenshot = pyautogui.screenshot()
        #screenshot.save(f'training_data/click_{clickNumber}.png')
        with open(f'training_data/{clickNumber}_{0}.txt', 'w') as f:
            f.write(f"{clickNumber},{timestamp},{x},{y}" + "\n")
        for i in range(1, 10):
            new_x, new_y = x+np.random.normal(loc=0, scale=7),y+np.random.normal(loc=0, scale=7)
            pyautogui.moveTo(new_x, new_y, 0)
            #screenshot = ImageGrab.grab()
            #screenshot = pyautogui.screenshot()
            #screenshot.save(f'training_data/{clickNumber}_{i}.png')
            with open(f'training_data/{clickNumber}_{i}.txt', 'w') as f:
                f.write(f"{clickNumber},{timestamp},{new_x},{new_y}" + "\n")
        clickNumber += 1
        clicking = False

    # To stop listener, you can return False from this function

start = time.time()
listener = mouse.Listener(on_click=on_click)
listener.start()

# Your main logic here
try:
    i = 0
    while True:
        #screenshot = ImageGrab.grab()
        if not clicking:
            screenshot = pyautogui.screenshot()
            screenshot.save(f'training_data/{i}.png')
            i += 1
        time.sleep(0.1)
except KeyboardInterrupt:
    listener.stop()
    print("Program terminated by user")

# Stop the listener when done
listener.stop()


"""import cv2
import numpy as np
import pyautogui

# Screen resolution
screen_size = pyautogui.size()

# Define the codec and create a VideoWriter object to write the video
fourcc = cv2.VideoWriter_fourcc(*"X264")
out = cv2.VideoWriter("output.mp4", fourcc, 20.0, (screen_size.width, screen_size.height))

for i in range(1000):
    # Take a screenshot using pyautogui
    img = pyautogui.screenshot()

    # Convert the screenshot to a numpy array format
    frame = np.array(img)

    # Convert it from BGR(Blue, Green, Red) to RGB(Red, Green, Blue)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Write the frame into the file 'output.avi'
    out.write(frame)

    # Optional: Display the recording screen
    cv2.imshow("Screen Recorder", frame)

    # Stop recording when 'q' is pressed
    if cv2.waitKey(1) == ord('q'):
        break

# Release the VideoWriter object and close all frames
out.release()
cv2.destroyAllWindows()"""
