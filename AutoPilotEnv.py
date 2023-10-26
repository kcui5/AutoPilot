import gym
from gym import spaces
import numpy as np
import pyautogui
import cv2
from PIL import ImageGrab
import matplotlib.pyplot as plt

class CommandExecutionEnv(gym.Env):
    """
    Custom Environment that executes a specific command using keyboard and mouse.
    """
    def __init__(self, command, true_actions):
        super(CommandExecutionEnv, self).__init__()

        self.command = command
        self.true_actions = true_actions
        self.current_action_index = 0  # To track the current true action

        # Action space: continuous for mouse (x, y) and discrete for keyboard and mouse clicks
        screen_width, screen_height = pyautogui.size()
        self.action_space = spaces.Box(low=np.array([0, 0]), high=np.array([screen_width, screen_height]), dtype=np.float32)

        # Observation space: capture the screen
        self.observation_space = spaces.Box(low=0, high=255, shape=(screen_height, screen_width, 3), dtype=np.uint8)

    def step(self, action):
        self._perform_action(action)

        new_state = self._capture_screen()

        reward = self._calculate_reward(action)

        done = self._is_command_complete()

        return new_state, reward, done, {}

    def reset(self):
        self.current_action_index = 0
        return self._capture_screen()

    def render(self, mode='human'):
        if mode == 'human':
            # For human-readable rendering, display the screen
            plt.imshow(self._capture_screen())
            plt.show()
        elif mode == 'rgb_array':
            # For machine-readable rendering, return the current screen as an RGB array
            return self._capture_screen()


    def _perform_action(self, action):
        x, y = action[0], action[1]
        pyautogui.moveTo(x, y)  

    def _capture_screen(self):
        screen = np.array(ImageGrab.grab())
        screen = cv2.cvtColor(screen, cv2.COLOR_BGR2RGB)
        return screen

    def _calculate_reward(self, action):
        if self.current_action_index < len(self.true_actions):
            expected_action = self.true_actions[self.current_action_index]
            
            # Use np.array_equal for comparing arrays
            reward = 1 if np.array_equal(action, expected_action) else 0

            # Increment the action index
            self.current_action_index += 1
            return reward
        return 0

    def _is_command_complete(self):
        return self.current_action_index >= len(self.true_actions)


def main():
    command = "Execute some actions"

    true_actions = [
    (100, 200),               
    "left_click",              
    (300, 400),                
    "right_click",             
    "keyboard_space",          
    (450, 600),                
    "left_click",              
    "keyboard_arrow_up",      
    "keyboard_arrow_down",     
    (200, 300),                
    "double_left_click",      
    "keyboard_ctrl_c",         
    (600, 700),                
    "left_click",              
    "keyboard_ctrl_v",        
    (100, 100),                
    "right_click"              
]

    env = CommandExecutionEnv(command, true_actions)

    state = env.reset()
    print("Initial State Captured (showing a portion due to size):")
    print(state[:2, :2, :]) 

    # Run a few steps
    for _ in range(10): 
        action = env.action_space.sample()  # Random action;
        state, reward, done, _ = env.step(action)
    
        print(f"Action Taken: {action}")
        print(f"Reward: {reward}")
        print("State Captured (showing a portion due to size):")
        print(state[:2, :2, :]) 

        if done:
            break

if __name__ == "__main__":
    main()