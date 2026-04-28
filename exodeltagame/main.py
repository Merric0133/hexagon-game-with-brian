import pygame
import sys
import ctypes
from core.game import Game

def main():
    pygame.init()
    pygame.mixer.init()
    
    # Get display info
    display_info = pygame.display.Info()
    screen_width = display_info.current_w
    screen_height = display_info.current_h
    
    # Create resizable window
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
    pygame.display.set_caption("EXODELTA")
    
    # Maximize the window using Windows API (for Windows)
    try:
        # Get the window handle
        hwnd = pygame.display.get_wm_info()['window']
        # Maximize window using Windows API
        ctypes.windll.user32.ShowWindow(hwnd, 3)  # 3 = SW_MAXIMIZE
    except:
        # If that fails, just use full screen size
        pass
    
    clock = pygame.time.Clock()
    game = Game(screen, clock)
    game.run()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
