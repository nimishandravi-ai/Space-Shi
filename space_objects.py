import math
import time
import random
import pygame

# Global session tracker
session_stats = {
    'score': 0,
    'allies': 2,
    'reload_speed': 0.5
}

def update_session(score=None, allies=None, reload_speed=None):
    if score is not None:
        session_stats['score'] = score
    if allies is not None:
        session_stats['allies'] = allies
    if reload_speed is not None:
        session_stats['reload_speed'] = reload_speed

def get_session():
    return session_stats.copy()

def load_animation_frames(folder_path, scale_size):
    import os, pygame
    frames = []
    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith(".png"):
            img = pygame.image.load(os.path.join(folder_path, filename)).convert_alpha()
            img = pygame.transform.scale(img, scale_size)
            frames.append(img)
    return frames

class Bullet:
    def __init__(self, x, y, angle, speed=10, color=(255, 150, 0), radius=5, owner=None):
        self.x = x
        self.y = y
        self.angle = angle
        self.radius = radius
        self.speed = speed
        self.color = color
        self.owner = owner


    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

    def draw(self, screen):
        # Draw glow effect (outer glow)
        glow_radius = self.radius + 3
        glow_color = (min(255, self.color[0] + 50), 
                     min(255, self.color[1] + 50), 
                     min(255, self.color[2] + 50))
        
        # Draw multiple glow layers for better effect
        for i in range(3, 0, -1):
            alpha = 100 - (i * 30)  # Decreasing alpha for outer layers
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*glow_color, alpha), (glow_radius, glow_radius), glow_radius - i)
            screen.blit(glow_surface, (int(self.x - glow_radius), int(self.y - glow_radius)))
        
        # Draw the main bullet
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        
        # Draw inner highlight for extra glow
        highlight_radius = max(1, self.radius // 3)
        highlight_color = (min(255, self.color[0] + 100), 
                         min(255, self.color[1] + 100), 
                         min(255, self.color[2] + 100))
        pygame.draw.circle(screen, highlight_color, (int(self.x), int(self.y)), highlight_radius)

    def on_screen(self, WIDTH=1920, HEIGHT=1080):
        return 0 <= self.x <= WIDTH and 0 <= self.y <= HEIGHT

    def collide(self, target):
        dist = math.hypot(self.x - target.x, self.y - target.y)
        return dist < self.radius + target.radius

class Player:
    def __init__(self, x, y, reload_time=0.5, radius=32, speed=5.5):
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = speed
        self.reload_time = reload_time
        self.last_shot = 0
        self.stopped = False
        self.frames = load_animation_frames("sprites\\Player", (radius*2, radius*2))
        self.frame_index = 0
        self.frame_timer = time.time()

    def draw(self, screen):
        now = time.time()
        if now - self.frame_timer > 0.1:  # Change frame every 0.1 seconds
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.frame_timer = now
        current_frame = self.frames[self.frame_index]
        rect = current_frame.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(current_frame, rect)

    def update(self, keys, STOP_Y=800, WIDTH=1920, HEIGHT=1080):
        if not self.stopped:
            self.y -= self.speed
            if self.y <= STOP_Y:
                self.y = STOP_Y
                self.stopped = True
        else:
            if keys[pygame.K_a]:
                self.x -= self.speed
            if keys[pygame.K_d]:
                self.x += self.speed
        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))

    def can_fire(self):
        now = time.time()
        return now - self.last_shot >= self.reload_time

    def fire(self, target_x, target_y):
        if self.can_fire():
            dx = target_x - self.x
            dy = target_y - self.y
            angle = math.atan2(dy, dx)
            self.last_shot = time.time()
            return Bullet(self.x, self.y, angle, owner='player')
        return None

    def set_reload_time(self, reload_time):
        self.reload_time = reload_time

class Ally:
    def __init__(self, x_offset, reload_time=0.5, radius=30, speed=5, is_temporary=False):
        self.x_offset = x_offset
        self.x = 0
        self.y = 0
        self.radius = radius
        self.speed = speed
        self.reload_time = reload_time
        self.last_shot = 0
        self.alive = True
        self.is_temporary = is_temporary
        self.frames = load_animation_frames("sprites\\Ally", (radius*2, radius*2))
        self.frame_index = 0
        self.frame_timer = time.time()

    def draw(self, screen):
        if self.alive:
            now = time.time()
            if now - self.frame_timer > 0.1:
                self.frame_index = (self.frame_index + 1) % len(self.frames)
                self.frame_timer = now
            frame = self.frames[self.frame_index]
            rect = frame.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(frame, rect)

    def update(self, player):
        if not self.alive:
            return
        target_x = player.x + self.x_offset
        if abs(self.x - target_x) > self.speed:
            self.x += self.speed if self.x < target_x else -self.speed
        else:
            self.x = target_x
        self.y = player.y

    def can_fire(self):
        if not self.alive:
            return False
        now = time.time()
        return now - self.last_shot >= self.reload_time

    def fire(self, target_x, target_y):
        if not self.alive:
            return None
        if self.can_fire():
            dx = target_x - self.x
            dy = target_y - self.y
            angle = math.atan2(dy, dx)
            self.last_shot = time.time()
            return Bullet(self.x, self.y, angle, owner='ally')
        return None

    def set_reload_time(self, reload_time):
        self.reload_time = reload_time

class CrossedAlly:
    def __init__(self, reload_time=0.5, radius=35):
        self.x = 0  # Will be set to screen center
        self.y = 0  # Will be set to screen center
        self.radius = radius
        self.reload_time = reload_time
        self.last_shot = 0
        self.alive = True  # Always stays alive (invincible)
        self.is_temporary = False
        # Try to load ally frames, but with different size for distinction
        try:
            self.frames = load_animation_frames("sprites\\Ally", (radius*2, radius*2))
        except:
            self.frames = []
        self.frame_index = 0
        self.frame_timer = time.time()

    def draw(self, screen):
        if self.alive and self.frames:
            now = time.time()
            if now - self.frame_timer > 0.1:
                self.frame_index = (self.frame_index + 1) % len(self.frames)
                self.frame_timer = now
            frame = self.frames[self.frame_index]
            rect = frame.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(frame, rect)
            
            # Draw cross pattern indicator
            cross_color = (255, 255, 0)  # Yellow cross
            pygame.draw.line(screen, cross_color, (self.x - 20, self.y), (self.x + 20, self.y), 2)
            pygame.draw.line(screen, cross_color, (self.x, self.y - 20), (self.x, self.y + 20), 2)
        elif self.alive:
            # Fallback if no frames
            pygame.draw.circle(screen, (255, 215, 0), (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 255, 0), (int(self.x), int(self.y)), self.radius - 5)
            # Draw cross pattern
            cross_color = (255, 0, 0)
            pygame.draw.line(screen, cross_color, (self.x - 20, self.y), (self.x + 20, self.y), 3)
            pygame.draw.line(screen, cross_color, (self.x, self.y - 20), (self.x, self.y + 20), 3)

    def update(self, player, WIDTH, HEIGHT):
        if not self.alive:
            return
        # Stay in the center of the screen
        self.x = WIDTH // 2
        self.y = HEIGHT // 2

    def can_fire(self):
        if not self.alive:
            return False
        now = time.time()
        return now - self.last_shot >= self.reload_time

    def fire_cross_pattern(self):
        """Fires bullets in all 4 cardinal directions (cross pattern)"""
        if not self.alive:
            return []
        if self.can_fire():
            self.last_shot = time.time()
            bullets = []
            # Fire in 4 directions: right, up, left, down
            angles = [0, -math.pi/2, math.pi, math.pi/2]  # 0°, 270°, 180°, 90°
            for angle in angles:
                bullet = Bullet(self.x, self.y, angle, owner='ally', color=(255, 255, 0))
                bullets.append(bullet)
            return bullets
        return []

    def set_reload_time(self, reload_time):
        self.reload_time = reload_time

class TurretEnemy:
    def __init__(self, x, radius=35, speed=3, fire_interval=2, sprite_path="sprites\\TurretEnemy\\Turret.png"):
        self.x = x
        self.y = -radius
        self.radius = radius
        self.speed = speed
        self.type = 'turret'
        self.stopped = False
        self.last_fire = time.time()
        self.TURRET_STOP_Y = 135  # default value, can be set in main game

        # --- Load sprite ---
        try:
            self.sprite = pygame.image.load(sprite_path).convert_alpha()
            scale_size = (radius * 2, radius * 2)  # scale to match radius
            self.sprite = pygame.transform.scale(self.sprite, scale_size)
        except:
            self.sprite = None  # fallback if sprite missing

    def update(self):
        if not self.stopped:
            self.y += self.speed
            if self.y >= self.TURRET_STOP_Y:
                self.y = self.TURRET_STOP_Y
                self.stopped = True

    def draw(self, screen):
        if self.sprite:
            rect = self.sprite.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(self.sprite, rect)
        else:
            # fallback to circle + line if sprite missing
            pygame.draw.circle(screen, (180, 100, 255), (int(self.x), int(self.y)), self.radius)
            pygame.draw.line(screen, (255,255,255), (int(self.x), int(self.y)), (int(self.x), int(self.y)-self.radius), 3)

    def fire(self, target_x, target_y, bullet_speed=8, bullet_radius=5):
        now = time.time()
        if now - self.last_fire >= 2 and self.stopped:
            dx = target_x - self.x
            dy = target_y - self.y
            angle = math.atan2(dy, dx)
            offset = math.radians(10)
            self.last_fire = now
            return [
                Bullet(self.x, self.y, angle, speed=bullet_speed, color=(255,150,150), radius=bullet_radius, owner='turret'),
                Bullet(self.x, self.y, angle + offset, speed=bullet_speed, color=(255,150,150), radius=bullet_radius, owner='turret')
            ]
        return []

    def collide(self, player):
        dist = math.hypot(self.x - player.x, self.y - player.y)
        return dist < self.radius + player.radius

    def on_screen(self, WIDTH=1920, HEIGHT=1080):
        return -self.radius <= self.y <= HEIGHT + self.radius


class Enemy:
    def __init__(self, x, radius=28, speed=3):
        self.x = x
        self.y = -radius
        self.radius = radius
        self.speed = speed
        self.type = 'normal'
        self.last_fire = time.time()
        self.stopped = False
        self.dodge_target_x = self.x
        self.dodge_timer = time.time() + random.uniform(0.8, 2.0)
        self.frames = load_animation_frames("sprites\\Enemy", (radius*2, radius*2))
        self.frame_index = 0
        self.frame_timer = time.time()

    def draw(self, screen):
        now = time.time()
        if now - self.frame_timer > 0.1:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.frame_timer = now
        frame = self.frames[self.frame_index]
        rect = frame.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(frame, rect)

    def update(self, STOP_Y=540, WIDTH=1920, HEIGHT=1080):
        if not self.stopped:
            self.y += self.speed
            if self.y >= STOP_Y:
                self.y = STOP_Y
                self.stopped = True
                self.dodge_target_x = self.x
        else:
            now = time.time()
            if abs(self.x - self.dodge_target_x) > 2:
                direction = 1 if self.x < self.dodge_target_x else -1
                self.x += direction * self.speed
            elif now >= self.dodge_timer:
                dodge_range = 50
                possible_left = max(self.radius, self.x - dodge_range)
                possible_right = min(WIDTH - self.radius, self.x + dodge_range)
                self.dodge_target_x = random.randint(int(possible_left), int(possible_right))
                self.dodge_timer = now + random.uniform(0.5, 1.2)
        self.x = max(self.radius, min(WIDTH - self.radius, self.x))

    def fire(self, target_x, target_y, bullet_speed=8, bullet_radius=5):
        # Fires at nearest target
        now = time.time()
        if now - self.last_fire >= 2:
            dx = target_x - self.x
            dy = target_y - self.y
            angle = math.atan2(dy, dx)
            self.last_fire = now
            return Bullet(self.x, self.y, angle, speed=bullet_speed, color=(255, 80, 80), radius=bullet_radius, owner='enemy')
        return None

    def collide(self, player):
        dist = math.hypot(self.x - player.x, self.y - player.y)
        return dist < self.radius + player.radius

    def on_screen(self, WIDTH=1920, HEIGHT=1080):
        return -self.radius <= self.y <= HEIGHT + self.radius
