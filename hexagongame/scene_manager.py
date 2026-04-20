# =============================================================================
# engine/scene_manager.py — Lightweight scene-stack manager
# =============================================================================
# Provides:
#   BaseScene   — base class every scene inherits from
#   SceneManager — holds the active scene, wires switching
#   manager     — global singleton imported throughout the project
# =============================================================================


class BaseScene:
    """
    Every game screen (menu, gameplay, codex …) inherits from this.

    Life-cycle:
        on_enter(**kwargs)  — called once when the scene becomes active
        on_exit()           — called once just before leaving the scene
        update(events, dt)  — called every frame while active
        draw(surface)       — called every frame after update
    """

    def __init__(self):
        # Assigned by SceneManager.register()
        self.manager: "SceneManager | None" = None

    # Override in subclasses as needed ----------------------------------

    def on_enter(self, **kwargs):
        """Called when this scene is switched to. kwargs come from switch()."""
        pass

    def on_exit(self):
        """Called just before switching away from this """
        pass

    def update(self, events: list, dt: float):
        """Process input and advance simulation. dt = seconds since last frame."""
        pass

    def draw(self, surface):
        """Render everything to surface."""
        pass


class SceneManager:
    """
    Manages a dictionary of named scenes and tracks which is active.

    Usage:
        manager.register("game", GameScene())
        manager.switch("game", score=0)   # kwargs forwarded to on_enter
        manager.update(events, dt)
        manager.draw(screen)
    """

    def __init__(self):
        self._scenes: dict[str, BaseScene] = {}
        self._active: BaseScene | None = None
        self._active_name: str = ""

    # ---------------------------------------------------------- Registration

    def register(self, name: str, scene: BaseScene):
        """Register a scene instance under a string key."""
        self._scenes[name] = scene
        scene.manager = self

    # ------------------------------------------------------------ Switching

    def switch(self, name: str, **kwargs):
        """
        Deactivate the current scene and activate the named one.
        Any extra keyword arguments are forwarded to the new scene's on_enter().
        """
        if self._active is not None:
            self._active.on_exit()

        if name not in self._scenes:
            raise KeyError(f"SceneManager: unknown scene '{name}'. "
                           f"Registered: {list(self._keys())}")

        self._active      = self._scenes[name]
        self._active_name = name
        self._active.on_enter(**kwargs)

    # ---------------------------------------------------------- Frame hooks

    def update(self, events: list, dt: float):
        """Forward update to the active """
        if self._active:
            self._active.update(events, dt)

    def draw(self, surface):
        """Forward draw to the active """
        if self._active:
            self._active.draw(surface)

    # ---------------------------------------------------------- Utility

    @property
    def current_name(self) -> str:
        return self._active_name


# Global singleton — import this everywhere
manager = SceneManager()
