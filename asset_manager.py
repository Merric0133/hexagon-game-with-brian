import pygame

class Assets:
    def __init__(self):
        # We use a dictionary to cache fonts so we don't reload them every frame
        self.fonts = {}

    def get_font(self, name, size):
        # Create a unique key for this font size
        key = f"{name}_{size}"
        if key not in self.fonts:
            # Fallback to system Arial if a specific file isn't found
            self.fonts[key] = pygame.font.SysFont("Arial", size)
        return self.fonts[key]

    def get_image(self, name):
        # Return a blank surface if you don't have actual PNG files yet
        return pygame.Surface((32, 32), pygame.SRCALPHA)

# Global singleton
assets = Assets()