"""INTERSTELLAR — fly a cockpit through real NASA / Hubble imagery."""

from __future__ import annotations

from panda3d.core import WindowProperties, loadPrcFileData

loadPrcFileData("", "window-title INTERSTELLAR - Space Cockpit")
loadPrcFileData("", "win-size 1280 720")
loadPrcFileData("", "audio-library-name null")
loadPrcFileData("", "sync-video #t")

from direct.showbase.ShowBase import ShowBase

from cockpit import CockpitHUD
from world import build_world, update_world


class InterstellarGame(ShowBase):
    def __init__(self):
        super().__init__()

        if self.win is not None and hasattr(self.win, "request_properties"):
            props = WindowProperties()
            props.set_title("INTERSTELLAR - Space Cockpit")
            props.set_size(1280, 720)
            self.win.request_properties(props)

        self.set_background_color(0.002, 0.003, 0.015, 1)
        self.disable_mouse()
        self.camLens.set_near_far(0.08, 22000)
        self.camLens.set_fov(62)

        self.camera.set_pos(0, -38, 7)
        self.camera.look_at(10, 105, -3)

        self.speed = 12.0
        self.cruise_max = 70.0
        self.hyper_max = 210.0
        self.hyperdrive = False
        self.base_fov = 62.0

        self.world = build_world(self)
        self.hud = CockpitHUD(self)
        self.targets = list(self.world.bodies)
        self.target_index = next(i for i, b in enumerate(self.targets) if b.name == "Earth")

        self.keys = {}
        for key in ("w", "s", "a", "d", "q", "e", "z", "c", "space"):
            self.keys[key] = False
            self.accept(key, self.set_key, [key, True])
            self.accept(f"{key}-up", self.set_key, [key, False])
        self.accept("tab", self.cycle_target)
        self.accept("f", self.face_target)
        self.accept("escape", self.userExit)
        self.accept("r", self.reset_ship)

        self.taskMgr.add(self.update_game, "update_game")

    def set_key(self, key, value):
        self.keys[key] = value

    def cycle_target(self):
        self.target_index = (self.target_index + 1) % len(self.targets)

    def current_target(self):
        return self.targets[self.target_index]

    def face_target(self):
        target = self.current_target()
        self.camera.look_at(target.node.get_pos(self.render))

    def reset_ship(self):
        self.camera.set_pos(0, -38, 7)
        self.camera.look_at(10, 105, -3)
        self.speed = 12.0

    def nearest_visual(self):
        cam = self.camera.get_pos(self.render)
        forward = self.camera.get_quat(self.render).get_forward()
        best = None
        best_score = -1.0
        best_dist = 0.0
        for body in self.world.bodies:
            delta = body.node.get_pos(self.render) - cam
            dist = delta.length() - body.radius
            if dist <= 1:
                continue
            align = delta.normalized().dot(forward)
            if align < 0.62:
                continue
            score = align * 180.0 / max(dist, 8.0)
            if score > best_score:
                best_score = score
                best = body
                best_dist = dist
        if best is None:
            return "DEEP SPACE", 0.0
        return best.name, best_dist

    def update_game(self, task):
        dt = min(globalClock.get_dt(), 0.05)

        if self.keys["w"]:
            self.speed += 28 * dt
        if self.keys["s"]:
            self.speed -= 36 * dt

        self.hyperdrive = self.keys["space"]
        max_speed = self.hyper_max if self.hyperdrive else self.cruise_max
        if self.hyperdrive:
            self.speed += 90 * dt
        self.speed = max(0.0, min(self.speed, max_speed))
        if not self.hyperdrive and self.speed > self.cruise_max:
            self.speed -= 50 * dt

        yaw = (self.keys["a"] - self.keys["d"]) * 52
        pitch = (self.keys["q"] - self.keys["e"]) * 38
        roll = (self.keys["z"] - self.keys["c"]) * 40
        self.camera.set_h(self.camera.get_h() + yaw * dt)
        self.camera.set_p(max(-82, min(82, self.camera.get_p() + pitch * dt)))
        self.camera.set_r(self.camera.get_r() * (1.0 - 2.2 * dt) + roll * dt)

        forward = self.camera.get_quat(self.render).get_forward()
        self.camera.set_pos(self.camera.get_pos(self.render) + forward * self.speed * dt)

        target_fov = 84 if self.hyperdrive else self.base_fov
        current = self.camLens.get_fov()
        # get_fov can be a VBase2; use the X component
        try:
            current_x = float(current[0])
        except TypeError:
            current_x = float(current)
        self.camLens.set_fov(current_x + (target_fov - current_x) * min(1.0, 3.0 * dt))

        update_world(self.world, dt, self.camera.get_pos(self.render))

        target = self.current_target()
        dest_range = (target.node.get_pos(self.render) - self.camera.get_pos(self.render)).length()
        visual, _ = self.nearest_visual()
        self.hud.update(self.speed, self.hyperdrive, target.name, dest_range, visual)
        return task.cont


if __name__ == "__main__":
    InterstellarGame().run()
