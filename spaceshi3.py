import pygame
import sys
import math
import random
import time
import subprocess

from space_objects import Bullet, Ally, TurretEnemy, Enemy
from space_objects import Player as BasePlayer

# -----------------------------------------------------------------------------
# Final Boss: The AI Overmind
# -----------------------------------------------------------------------------
class FinalBoss:
    def __init__(self, x, y, health=200):
        self.x = x
        self.y = y
        self.radius = 50
        self.health = health
        self.phase = 1
        self.last_fire = time.time()
        # Load boss sprites for different phases
        self.sprites = {
            1: pygame.image.load("sprites/boss_phase1.png").convert_alpha(),
            2: pygame.image.load("sprites/boss_phase1.png").convert_alpha(),
            3: pygame.image.load("sprites/boss_phase2.png").convert_alpha()
        }
        for k, img in self.sprites.items():
            self.sprites[k] = pygame.transform.scale(img, (128, 128))


    def update(self):
        # Horizontal oscillation
        if self.phase == 1:
            self.x += math.sin(time.time() * 0.5) * 2
        elif self.phase == 2:
            self.x += math.sin(time.time() * 0.7) * 3
        elif self.phase == 3:
            self.x += math.sin(time.time() * 1.0) * 5  # ← Phase 3: faster & wider

    def draw(self, screen, WIDTH):
        # Draw boss body
        # Draw boss sprite based on phase
        sprite = self.sprites[self.phase]
        rect = sprite.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(sprite, rect)
        # Draw health bar
        bar_w, bar_h = 300, 20
        bar_x = WIDTH // 2 - bar_w // 2
        bar_y = 20
        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        hp_ratio = max(self.health, 0) / 200
        pygame.draw.rect(screen, (0, 220, 0), (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))

    def fire(self, target_x, target_y):
        now = time.time()
        # Fire interval by phase
        interval = {1: 2.0, 2: 1.0, 3: 0.8}[self.phase]
        if now - self.last_fire >= interval:
            self.last_fire = now
            angle = math.atan2(target_y - self.y, target_x - self.x)
            bullets = [Bullet(self.x, self.y, angle, speed=8,
                              color=(255,100,100), radius=8, owner='boss')]
            if self.phase == 2:
                # Two-shot spread
                spread = math.radians(15)
                bullets.append(Bullet(self.x, self.y, angle + spread, speed=8,
                                      color=(255,100,100), radius=8, owner='boss'))
                bullets.append(Bullet(self.x, self.y, angle - spread, speed=8,
                                      color=(255,100,100), radius=8, owner='boss'))
            elif self.phase == 3:
                # Tight bullet storm
                for off in (-0.3, 0.0, 0.3):
                    bullets.append(Bullet(self.x, self.y, angle + off, speed=10,
                                          color=(255,200,0), radius=6, owner='boss'))
            return bullets
        return []

    def collide(self, player):
        dist = math.hypot(self.x - player.x, self.y - player.y)
        return dist < self.radius + player.radius

# -----------------------------------------------------------------------------
# Extended Player: 4-way movement + Phase 3 lives/invincibility
# -----------------------------------------------------------------------------
class Player3(BasePlayer):
    def __init__(self, x, y, speed=4, reload_time=0.5):
        super().__init__(x, y, reload_time=reload_time, speed=speed)
        self.lives = 1
        self.invincible = False
        self.invincibility_start = 0.0


    def update(self, keys, bounds):
        left, right, top, bottom = bounds
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.x -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.x += self.speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.y -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.y += self.speed

        # Clamp inside play zone
        self.x = max(self.radius, min(right - self.radius, self.x))
        self.y = max(top + self.radius, min(bottom - self.radius, self.y))

        # End invincibility after 5s
        if self.invincible and time.time() - self.invincibility_start >= 5.0:
            self.invincible = False

    def draw_invincibility(self, screen):
        # Blink effect when invincible
        if self.invincible and (int(time.time() * 5) % 2 == 0):
            pygame.draw.circle(screen, (255,255,0),
                               (int(self.x), int(self.y)),
                               self.radius + 4, 3)
    


# -----------------------------------------------------------------------------
# Main: Final Mission
# -----------------------------------------------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    info = pygame.display.Info()
    WIDTH, HEIGHT = info.current_w, info.current_h
    clock = pygame.time.Clock()

    # Play zone
    TOP_BOUND = int(HEIGHT * 3 / 8)
    BOTTOM_BOUND = HEIGHT - 80
    X_LEFT, X_RIGHT = 0, WIDTH

    font      = pygame.font.SysFont(None, 40)
    big_font  = pygame.font.SysFont(None, 80)

    # Opening dialogue
    intro_lines = [
        "Commander: We've reached the heart of the Empire's network.",
        "You: Their AI Overmind is controlling every defense.",
        "Commander: This is our final stand. Good luck, pilot."
    ]

    # Post-Phase 2 twist
    twist_lines = [
        "You: It's over... finally.",
        "Commander: Wait... something's not right.",
        "You: We won... or did we?"
    ]

    def show_intro(lines):
        for line in lines:
            skipped = False
            start = time.time()
            while True:
                screen.fill((10, 10, 30))
                # Dialogue text
                text = font.render(line, True, (230, 230, 255))
                screen.blit(text, (WIDTH//2 - text.get_width()//2,
                                   HEIGHT//2 - text.get_height()//2))
                # Skip hint
                hint = font.render("Press ENTER to skip", True, (180, 180, 200))
                screen.blit(hint, (WIDTH//2 - hint.get_width()//2,
                                   HEIGHT//2 + 60))
                pygame.display.flip()

                for evt in pygame.event.get():
                    if evt.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if evt.type == pygame.KEYDOWN and evt.key == pygame.K_RETURN:
                        skipped = True

                if skipped or time.time() - start >= 2:
                    break
                clock.tick(60)

    # Show opening briefing
    show_intro(intro_lines)

    # Initialize game objects
    player        = Player3(WIDTH // 2, BOTTOM_BOUND, speed=4, reload_time=0.5)
    allies        = [Ally(-100), Ally(100)]
    bullets       = []
    enemy_bullets = []
    enemies       = []
    turrets       = []
    boss          = None
    boss_spawned  = False
    score         = 0
    game_over     = False
    victory       = False
    
    # Load background image
    try:
        background = pygame.image.load("sprites//background.png").convert()
        # Scale background to fit screen while maintaining aspect ratio
        bg_width, bg_height = background.get_size()
        scale_x = WIDTH / bg_width
        scale_y = HEIGHT / bg_height
        scale = max(scale_x, scale_y)  # Use larger scale to cover entire screen
        new_width = int(bg_width * scale)
        new_height = int(bg_height * scale)
        background = pygame.transform.scale(background, (new_width, new_height))
        # Center the background
        bg_x = (WIDTH - new_width) // 2
        bg_y = (HEIGHT - new_height) // 2
    except:
        background = None
        bg_x = bg_y = 0
    


    battle_start     = time.time()
    BOSS_TRIGGER_TIME = 13  # seconds until boss arrival

    while True:
        now = time.time()
        dt  = clock.tick(60) / 1000.0

        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys          = pygame.key.get_pressed()
        mx, my        = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        # Spawn normal waves until boss arrives
        if not boss_spawned:
            if random.randint(0, 60) == 0:
                x = random.randint(50, WIDTH - 50)
                if random.random() < 0.5:
                    enemies.append(Enemy(x))
                else:
                    t = TurretEnemy(x)
                    t.TURRET_STOP_Y = HEIGHT // 6
                    turrets.append(t)

            if now - battle_start >= BOSS_TRIGGER_TIME:
                boss = FinalBoss(WIDTH // 2, HEIGHT // 5)
                boss_spawned = True

        # Gameplay updates
        if not game_over and not victory:
            # Phase transitions
            if boss_spawned and boss:
                # Phase 2 trigger
                if boss.health <= 60 and boss.phase == 1:
                    boss.phase = 2

                # Phase 3 trigger + twist
                elif boss.health <= 30 and boss.phase == 2:
                    show_intro(twist_lines)
                    boss.phase = 3
                    # Grant extra lives and upgrades
                    player.lives += 2
                    player.speed *= 1.5
                    player.invincible = True
                    player.invincibility_start = time.time()

            # Player & ally updates
            player.update(keys, (X_LEFT, X_RIGHT, TOP_BOUND, BOTTOM_BOUND))
            for ally in allies:
                ally.update(player)

            # Firing
            if mouse_pressed:
                b = player.fire(mx, my)
                if b:
                    bullets.append(b)

            targets = enemies + turrets + ([boss] if boss_spawned else [])
            for ally in allies:
                if ally.alive and targets:
                    nearest = min(targets,
                                  key=lambda e: math.hypot(ally.x - e.x, ally.y - e.y))
                    b = ally.fire(nearest.x, nearest.y)
                    if b:
                        bullets.append(b)

            # Update enemies
            for e in enemies[:]:
                e.update(STOP_Y=HEIGHT//2, WIDTH=WIDTH, HEIGHT=HEIGHT)
                if not e.on_screen(WIDTH, HEIGHT):
                    enemies.remove(e)
                else:
                    eb = e.fire(player.x, player.y)
                    if eb:
                        enemy_bullets.append(eb)

            # Update turrets
            for t in turrets[:]:
                t.update()
                if not t.on_screen(WIDTH, HEIGHT):
                    turrets.remove(t)
                else:
                    enemy_bullets.extend(t.fire(player.x, player.y))

            # Update boss
            if boss_spawned and boss and boss.health > 0:
                boss.update()
                enemy_bullets.extend(boss.fire(player.x, player.y))

            # Update player bullets & collisions
            for b in bullets[:]:
                b.update()
                if not b.on_screen(WIDTH, HEIGHT):
                    bullets.remove(b)
                    continue
                # Hit normal enemies
                for e in enemies[:]:
                    if b.collide(e):
                        bullets.remove(b)
                        enemies.remove(e)
                        score += 1
                        break
                # Hit turrets
                for t in turrets[:]:
                    if b.collide(t):
                        bullets.remove(b)
                        turrets.remove(t)
                        score += 2
                        break
                # Hit boss
                if boss_spawned and boss and b.collide(boss):
                    bullets.remove(b)
                    boss.health -= 5
                    if boss.health <= 0:
                        victory = True
                    break

            # Update enemy bullets & handle collisions
            for eb in enemy_bullets[:]:
                eb.update()
                if not eb.on_screen(WIDTH, HEIGHT):
                    enemy_bullets.remove(eb)
                    continue

                # Boss bullet hits player
                if eb.collide(player) and not player.invincible:
                    # In Phase 3 allies sacrifice first
                    if boss_spawned and boss and boss.phase == 3 \
                       and any(a.alive for a in allies):
                        for a in allies:
                            if a.alive:
                                a.alive = False
                                break
                    else:
                        player.lives -= 1
                        player.invincible = True
                        player.invincibility_start = time.time()
                        if player.lives <= 0:
                            game_over = True
                    enemy_bullets.remove(eb)
                    continue

                # Bullet hits an ally
                for a in allies:
                    if a.alive and eb.collide(a):
                        enemy_bullets.remove(eb)
                        a.alive = False
                        break

            # Direct collisions (enemies/turrets/boss → player)
            if not player.invincible:
                if any(e.collide(player) for e in enemies):
                    game_over = True
                if any(t.collide(player) for t in turrets):
                    game_over = True
                if boss_spawned and boss and boss.collide(player):
                    game_over = True

        # DRAW
        if background:
            screen.blit(background, (bg_x, bg_y))
        else:
            screen.fill((15, 10, 30))
        player.draw(screen)
        player.draw_invincibility(screen)

        for ally in allies:
            ally.draw(screen)
        for b in bullets:
            b.draw(screen)
        for e in enemies:
            e.draw(screen)
        for t in turrets:
            t.draw(screen)
        for eb in enemy_bullets:
            eb.draw(screen)
        if boss_spawned and boss and boss.health > 0:
            boss.draw(screen, WIDTH)

        # HUD
        score_txt = font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_txt, (10, 10))
        lives_txt = font.render(f"Lives: {player.lives}", True, (255, 200, 0))
        screen.blit(lives_txt, (10, 50))

        # Game Over screen
        if game_over:
            over = big_font.render("MISSION FAILED!", True, (255, 50, 50))
            screen.blit(over, (WIDTH//2 - over.get_width()//2, HEIGHT//2))
            sub = font.render("Press ENTER to quit", True, (200, 200, 200))
            screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 80))
            pygame.display.flip()
            if keys[pygame.K_RETURN]:
                pygame.quit()
                sys.exit()
            continue

        # Victory screen
        if victory:
            win = big_font.render("VICTORY!", True, (50, 255, 50))
            screen.blit(win, (WIDTH//2 - win.get_width()//2, HEIGHT//2))
            msg = font.render("The AI Overmind has been defeated.", True, (200, 200, 255))
            screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2 + 60))
            sub = font.render("Press ENTER to quit", True, (200, 200, 200))
            screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 120))
            pygame.display.flip()
            if keys[pygame.K_RETURN]:
                pygame.quit()
                sys.exit()
            continue

        pygame.display.flip()

if __name__ == "__main__":
    main()