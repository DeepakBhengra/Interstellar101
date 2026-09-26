
from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import (
    WindowProperties,
    AmbientLight,
    DirectionalLight,
    Vec4,
    Vec3,
    TextNode,
)
import random


class InterstellarGame(ShowBase):

    def __init__(self):
        super().__init__()

        # Window setup
        props = WindowProperties()
        props.setTitle("INTERSTELLAR - Space Cockpit")
        props.setSize(1280, 720)
        self.win.requestProperties(props)

        self.setBackgroundColor(0.002, 0.004, 0.02, 1)
        
      

        # Game variables
        self.speed = 0.0
        self.max_speed = 100.0
        self.hyperdrive = False

        # First-person camera
        self.disableMouse()
        self.camera.setPos(0, 0, 0)
        self.camera.setHpr(0, 0, 0)

        # Lighting
        ambient = AmbientLight("ambient")
        ambient.setColor(Vec4(0.4, 0.4, 0.6, 1))
        ambient_node = self.render.attachNewNode(ambient)
        self.render.setLight(ambient_node)

        directional = DirectionalLight("directional")
        directional.setColor(Vec4(0.7, 0.8, 1, 1))
        directional_node = self.render.attachNewNode(directional)
        directional_node.setHpr(-30, -45, 0)
        self.render.setLight(directional_node)

        # Create starfield
        self.stars = []
        self.create_stars(500)

        # Cockpit HUD
        self.hud = OnscreenText(
            text="INTERSTELLAR EXPLORER",
            pos=(0, 0.9),
            scale=0.055,
            fg=(0.1, 0.9, 1, 1),
            align=TextNode.ACenter,
            mayChange=True
        )

        self.status = OnscreenText(
            text="SYSTEM: ONLINE",
            pos=(-1.25, 0.85),
            scale=0.045,
            fg=(0.2, 1, 0.7, 1),
            align=TextNode.ALeft,
            mayChange=True
        )

        self.speed_display = OnscreenText(
            text="SPEED: 0",
            pos=(1.0, 0.85),
            scale=0.05,
            fg=(0.1, 0.9, 1, 1),
            align=TextNode.ARight,
            mayChange=True
        )

        self.destination = OnscreenText(
            text="DESTINATION: ALPHA CENTAURI",
            pos=(-1.25, -0.9),
            scale=0.04,
            fg=(0.1, 0.9, 1, 1),
            align=TextNode.ALeft
        )

        self.controls = OnscreenText(
            text="W/S: Thrust | A/D: Turn | "
                 "Q/E: Pitch | SPACE: Hyperdrive",
            pos=(0, -0.95),
            scale=0.04,
            fg=(0.7, 0.8, 1, 1),
            align=TextNode.ACenter
        )

        # Keyboard controls
        self.keys = {}
        for key in ["w", "s", "a", "d", "q", "e", "space"]:
            self.keys[key] = False
            self.accept(key, self.set_key, [key, True])
            self.accept(key + "-up", self.set_key, [key, False])

        self.accept("escape", self.userExit)

        # Main game loop
        self.taskMgr.add(self.update_game, "update_game")

    def create_stars(self, count):
        for _ in range(count):
            star = self.render.attachNewNode(
                "star"
            )

            x = random.uniform(-150, 150)
            y = random.uniform(20, 300)
            z = random.uniform(-100, 100)

            star.setPos(x, y, z)
            star.setScale(random.uniform(0.05, 0.18))

            star.setColor(
                random.uniform(0.5, 1),
                random.uniform(0.7, 1),
                1,
                1
            )

            # Small glowing point
            star.setLightOff()
            star.setTwoSided(True)

            from panda3d.core import CardMaker
            cm = CardMaker("star")
            cm.setFrame(-1, 1, -1, 1)
            card = star.attachNewNode(cm.generate())
            card.setBillboardPointEye()
            card.setColor(0.5, 0.85, 1, 1)

            self.stars.append(star)

    def set_key(self, key, value):
        self.keys[key] = value

    def update_game(self, task):
        dt = min(globalClock.getDt(), 0.05)

        # Acceleration and braking
        if self.keys["w"]:
            self.speed += 30 * dt

        if self.keys["s"]:
            self.speed -= 40 * dt

        self.speed = max(0, min(self.speed, self.max_speed))

        # Turn the ship
        if self.keys["a"]:
            self.camera.setH(self.camera.getH() + 60 * dt)

        if self.keys["d"]:
            self.camera.setH(self.camera.getH() - 60 * dt)

        if self.keys["q"]:
            self.camera.setP(self.camera.getP() + 40 * dt)

        if self.keys["e"]:
            self.camera.setP(self.camera.getP() - 40 * dt)

        # Hyperdrive
        if self.keys["space"]:
            self.hyperdrive = True
            self.speed = min(100, self.speed + 80 * dt)
        else:
            self.hyperdrive = False

        # Move stars toward the cockpit
        for star in self.stars:
            star.setY(
                star.getY() - self.speed * dt
            )

            if star.getY() < 2:
                star.setY(random.uniform(150, 300))
                star.setX(random.uniform(-150, 150))
                star.setZ(random.uniform(-100, 100))

        # Update HUD
        self.speed_display.setText(
            f"SPEED: {int(self.speed)}"
        )

        if self.hyperdrive:
            self.status.setText("HYPERDRIVE: ENGAGED")
            self.hud.setFg((1, 0.4, 0.1, 1))
        else:
            self.status.setText("SYSTEM: ONLINE")
            self.hud.setFg((0.1, 0.9, 1, 1))

        return task.cont


game = InterstellarGame()
game.run()