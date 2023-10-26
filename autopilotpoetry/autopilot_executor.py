import pyautogui
import json
from time import sleep

pyautogui.FAILSAFE = True

#Number of seconds to move to given location
MOUSE_SPEED = 1

instructions = []
with open('example.json', 'r') as file:
    instructions = json.loads(file.read())

print("INSTRUCTIONS: ", instructions)

def mouseCommand(args):
    if args[1] == "Left-click":
        print("Left clicking")
        pyautogui.click()
    elif args[1] == "Right-click":
        print("Right clicking")
        pyautogui.click(button="right")
    elif args[1] == "Move":
        if len(args) < 4:
            print("Unparseable instruction!")
            print(args)
            return
        try:
            x = int(args[2])
            y = int(args[3])
            print(f"Moving to {x} {y}")
            pyautogui.moveTo(x, y, MOUSE_SPEED)
        except:
            print("Unparseable instruction!")
            print(args)
    elif args[1] == "MoveRel":
        if len(args) < 4:
            print("Unparseable instruction!")
            print(args)
            return
        try:
            x = int(args[2])
            y = int(args[3])
            print(f"Moving relative to {x} {y}")
            pyautogui.moveRel(x, y, MOUSE_SPEED)
        except:
            print("Unparseable instruction!")
            print(args)
    else:
        print("Unparseable instruction!")
        print(args)
    

def keyboardCommand(args):
    for arg in args[1:]:
        if arg[0] == "\\":
            print(f"Keyboard button {arg[1:]}")
            pyautogui.typewrite([arg[1:]])
        else:
            print(f"Keyboard type {arg}")
            pyautogui.typewrite(arg + " ")
            #sleep(1)

for instruction in instructions:
    args = instruction.split()
    if not args:
        print("Empty instruction!")
        continue
    if len(args) <= 1:
        print("Unparseable instruction!")
        print(args)
        continue

    cmd = args[0]
    if cmd == "Mouse":
        mouseCommand(args)
    if cmd == "Keyboard":
        keyboardCommand(args)
    if cmd == "DoNothing":
        continue
    sleep(3)
