import math
import random

import pygame

class MenuAnt:
    SPEED = 52.0
    MARGIN = 48

    def __init__(self, size, frames, rng):
        width, height = size
        self.frames = frames
        self.cache = {}
        angle = rng.uniform(0, math.tau)
        self.dx, self.dy = math.cos(angle), math.sin(angle)
        self.angle = math.degrees(math.atan2(-self.dx, -self.dy))
        x, y = rng.uniform(0, width), rng.uniform(0, height)

        # Like in the banner, each ant enters and leaves the screen off-camera.
        intervals = []
        for center, direction, low, high in (
            (x, self.dx, -self.MARGIN, width + self.MARGIN),
            (y, self.dy, -self.MARGIN, height + self.MARGIN),
        ):
            if abs(direction) > 1e-12:
                intervals.append(sorted(((low - center) / direction,
                                         (high - center) / direction)))
        entry = max(pair[0] for pair in intervals)
        exit_ = min(pair[1] for pair in intervals)
        self.x, self.y = x + entry * self.dx, y + entry * self.dy
        self.length = exit_ - entry
        self.period = self.length / self.SPEED + rng.uniform(0.5, 2.0)
        self.phase = rng.uniform(0, self.period)
        self.walk_phase = rng.randrange(len(frames[0]))
        self.antenna_phase = rng.randrange(len(frames[1]))

    def draw(self, surface, elapsed):
        distance = ((elapsed + self.phase) % self.period) * self.SPEED
        if distance > self.length:
            return
        x = self.x + distance * self.dx
        y = self.y + distance * self.dy
        bodies, antennae = self.frames
        walk = (int(elapsed * 16) + self.walk_phase) % len(bodies)
        feel = (int(elapsed * 8) + self.antenna_phase) % len(antennae)
        key = walk, feel
        if key not in self.cache:
            sprite = bodies[walk].copy()
            sprite.blit(antennae[feel], (0, 0))
            self.cache[key] = pygame.transform.rotate(sprite, self.angle)
        sprite = self.cache[key]
        surface.blit(sprite, sprite.get_rect(center=(round(x), round(y))))


class MenuBackground:
    COLORS = (
        (242, 98, 91), (97, 160, 255), (247, 215, 83),
        (108, 222, 119), (203, 141, 244), (255, 164, 83),
        (106, 221, 221), (240, 196, 221), (225, 225, 225),
    )

    def __init__(self, size, ground, atlas_loader):
        self.elapsed = 0.0
        self.ground = pygame.Surface(size)
        self.ground.fill((112, 68, 38))
        if ground is not None:
            # Keep the original 512 x 512 tiles, including at the screen edges.
            for y in range(0, size[1], ground.get_height()):
                for x in range(0, size[0], ground.get_width()):
                    self.ground.blit(ground, (x, y))
        self.overlay = pygame.Surface(size, pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 128))
        self.ants = []
        self.frames = {}
        rng = random.Random(93)
        count = max(27, round(27 * size[0] * size[1] / (1024 * 340)))
        for index in range(count):
            kind = "soldat" if index % 5 == 0 else "rabochiy"
            color = self.COLORS[index % len(self.COLORS)]
            sprite_size = rng.choice((40, 44, 46) if kind == "soldat" else (32, 36, 38))
            key = kind, sprite_size, color
            if key not in self.frames:
                self.frames[key] = self.prepare_frames(atlas_loader, *key)
            self.ants.append(MenuAnt(size, self.frames[key], rng))

    @staticmethod
    def prepare_frames(atlas_loader, kind, size, color):
        # Reuse the game's atlas geometry without touching its colony colors.
        bodies, antennae = atlas_loader.ishodnye[kind]
        width, height = bodies["hodba"][0].get_size()
        ratio = size / max(width, height)
        dimensions = max(1, round(width * ratio)), max(1, round(height * ratio))

        def prepare(frame):
            result = pygame.transform.smoothscale(frame, dimensions)
            result.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
            return result

        return ([prepare(frame) for frame in bodies["hodba"]],
                [prepare(frame) for frame in antennae])

    def update(self, dt):
        self.elapsed += dt

    def draw(self, surface):
        surface.blit(self.ground, (0, 0))
        for ant in self.ants:
            ant.draw(surface, self.elapsed)
        surface.blit(self.overlay, (0, 0))


class MenuButton:
    STYLES = {
        "primary": ((13, 155, 13), (50, 162, 50)),
        "secondary": ((22, 98, 162), (47, 113, 172)),
        "danger": ((155, 12, 12), (162, 32, 32)),
    }

    def __init__(self, text, action, rect, text_font, style="primary"):
        self.action = action
        self.rect = pygame.Rect(rect)
        self.normal, self.hover = self.STYLES[style]
        self.hover_progress = 0.0
        self.label = text_font.render(text, True, (255, 255, 255))
        self.shadow = pygame.Rect(self.rect.x + 3, self.rect.y + 3,
                                  self.rect.width, self.rect.height)

    def draw(self, surface, mouse_pos, pressed=False, dt=1/60):
        hovered = self.rect.collidepoint(mouse_pos)
        target = 1.0 if hovered or pressed else 0.0
        self.hover_progress += (target - self.hover_progress) * min(1.0, dt * 12)
        color = tuple(round(a + (b - a) * self.hover_progress)
                      for a, b in zip(self.normal, self.hover))
        rect = self.rect.move(0, 2) if pressed else self.rect
        pygame.draw.rect(surface, (0, 0, 0), self.shadow)
        pygame.draw.rect(surface, color, rect)
        surface.blit(self.label, self.label.get_rect(center=rect.center))


class MainMenu:
    def __init__(self, surface, background, font_factory):
        self.surface = surface
        self.background = background
        self.page = "main"
        self.pressed = None
        self.title_font = font_factory(76)
        self.button_font = font_factory(32)
        self.title = self.title_font.render("ANTSBATTLER", True, (255, 255, 255))
        self.buttons = []
        self.build_buttons()

    def build_buttons(self):
        width, height = self.surface.get_size()
        button_width = min(620, width - 80)
        if self.page == "main":
            items = (("Играть", "play", "primary"),
                     ("Выйти", "quit", "danger"))
        else:
            items = (("Выйти в меню", "menu", "secondary"),
                     ("Выйти", "quit", "danger"))
        self.buttons = []
        top = height // 2 - 35
        for index, (text, action, style) in enumerate(items):
            rect = ((width - button_width) // 2, top + index * 80,
                    button_width, 68)
            self.buttons.append(MenuButton(text, action, rect, self.button_font, style))

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            return "quit"
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.pressed = None
            return "resume" if self.page == "pause" else "quit"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.pressed = next((button.action for button in self.buttons
                                 if button.rect.collidepoint(event.pos)), None)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            action = next((button.action for button in self.buttons
                           if button.rect.collidepoint(event.pos)), None)
            pressed, self.pressed = self.pressed, None
            if action is not None and action == pressed:
                return action
        return None

    def draw(self, dt=1/60):
        self.background.draw(self.surface)
        width, height = self.surface.get_size()
        self.surface.blit(self.title, self.title.get_rect(center=(width // 2, height // 3)))
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.draw(self.surface, mouse_pos, self.pressed == button.action, dt)
        pygame.display.update()

    def run(self, page="main"):
        self.page = page
        self.pressed = None
        self.build_buttons()
        menu_clock = pygame.time.Clock()
        while True:
            dt = min(0.1, menu_clock.tick(60) / 1000)
            self.background.update(dt)
            events = pygame.event.get()
            if any(event.type == pygame.QUIT for event in events):
                return "quit"
            for event in events:
                action = self.handle_event(event)
                if action is not None:
                    return action
            self.draw(dt)
