from space_objects import Player, Ally, CrossedAlly, Bullet, TurretEnemy, Enemy, update_session
import pygame
import sys
import math
import random
import time
import os, sys, subprocess

clock=pygame.time.Clock()
class RunnerEnemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 20
        self.speed = 6

    def update(self, player):
        dx = player.x - self.x
        dy = player.y - self.y
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.x += self.speed * dx / dist
            self.y += self.speed * dy / dist

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 140, 0), (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (0,0,0), (int(self.x), int(self.y)), 7)

    def collide(self, player):
        dist = math.hypot(self.x - player.x, self.y - player.y)
        return dist < self.radius + player.radius

    def on_screen(self, WIDTH=1920, HEIGHT=1080):
        return -self.radius <= self.x <= WIDTH + self.radius and -self.radius <= self.y <= HEIGHT + self.radius

# --- Session upgrades ---
session = {
    'score': 0,
    'allies': 2,
    'max_allies': 4,
    'reload_speed': 0.5, # default reload speed
    'crossed_ally': False, # can only have 1 crossed ally
}

def main():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    infoObject = pygame.display.Info()
    WIDTH, HEIGHT = infoObject.current_w, infoObject.current_h
    font = pygame.font.SysFont(None, 36)
    big_font = pygame.font.SysFont(None, 72)


    planet_count = 5
    planet_icons = []
    planet_positions = []
    planet_sprites = []
    selected_planet = None


    # Load planet sprites
    try:
        planet_sprites = [
        pygame.image.load("sprites\\pulanets\\97166-1.png"),
        pygame.image.load("sprites\\pulanets\\97166-2.png"),
        pygame.image.load("sprites\\pulanets\\image11.png"),
        pygame.image.load("sprites\\pulanets\\image (10).png"),
        pygame.image.load("sprites\\pulanets\\FInalboss.png")
        ]
        for i in range(len(planet_sprites)):
            planet_sprites[i] = pygame.transform.scale(planet_sprites[i], (80, 80))
    except:
        planet_sprites = [None] * planet_count


    # Load planet backgrounds
    try:
        planet_backgrounds = [
        pygame.image.load("sprites\\pulanets\\1.png").convert_alpha(),
        pygame.image.load("sprites\\pulanets\\planet2.png").convert_alpha(),
        pygame.image.load("sprites\\pulanets\\5.png").convert_alpha(),
        None, # Planet 4 is dialogue-only
        pygame.image.load("sprites\\pulanets\\planet3.png").convert_alpha()
        ]
        planet_backgrounds = [pygame.transform.scale(bg, (WIDTH, HEIGHT)) if bg else None for bg in planet_backgrounds]
    except:
        planet_backgrounds = [None] * planet_count


    spacing = WIDTH // (planet_count + 1)
    for i in range(planet_count):
        x = spacing * (i + 1)
        y = HEIGHT // 2
        planet_icons.append(pygame.Rect(x - 40, y - 40, 80, 80))
        planet_positions.append((x, y))
    # --- Dialogue content ---
    # Planet 4 serious dialogue (mission-appropriate)
    planet4_dialogue_lines = [
        "Commander: Planet 4's defenses are disciplined and entrenched.",
        "You: Civilians are wary, but a strike here secures a corridor for our fleets.",
        "Commander: No, they can prove to be a potential ally.",
        "You: Alright, I shall establish communication now.",
        "Head: You are speaking to the head of defenses of planet 4, state your purpose.",
        "You: We request a military alliance against the Empire.",
        "Head: The Empire? They have taken many things from us, money, lives, freedom...",
        "You: Is that not enough to make up your mind? We can destroy them, once and for all.",
        "Head: Alright, we accept your alliance request."
    ]

    # Revisit messages
    revisit_lines_generic = "Oh you came back? Want to loot us now that you have destroyed our fleet?"
    revisit_line_p4 = "Allies are ready to be dispatched."

    def show_story():
        level2_story = [
            "Level 2: Behind Enemy Lines",
            "After holding out, you and your crew must gather intel for the Union.",
            "Navigate from planet to planet across enemy space.",
            "Scan for friendly civilizations who may help defeat the Empire.",
            "Beware of enemy patrols and hazards as you search for allies.",
            "The Union cheers you on!"
        ]
        story_time = 5
        for line in level2_story:
            clock = pygame.time.Clock()
            skipped = False
            start = time.time()

            while True:
                # — handle quit & skip —
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                        skipped = True

                # — draw the line and hint —
                screen.fill((15, 10, 30))
                txt_surf = font.render(line, True, (255, 255, 255))
                screen.blit(
                    txt_surf,
                    (WIDTH//2 - txt_surf.get_width()//2,
                     HEIGHT//2 - txt_surf.get_height()//2)
                )

                hint = font.render("Press ENTER to continue", True, (180, 180, 200))
                screen.blit(
                    hint,
                    (WIDTH//2 - hint.get_width()//2,
                     HEIGHT//2 + txt_surf.get_height())
                )

                pygame.display.flip()

                # — break when time’s up or ENTER pressed —
                if skipped or (time.time() - start) >= story_time:
                    break

                clock.tick(60)

    STATE_MENU = "menu"
    STATE_RECON = "recon"
    STATE_DIALOGUE = "dialogue"
    STATE_COMPLETE = "complete"
    STATE_SHOP = "shop"
    STATE_MESSAGE = "message"   # simple one-shot message pane
    state = STATE_MENU
    mission_complete = False 
    planet_done = [False] * planet_count
    current_planet = None
    dialogue_step = 0
    session['score'] = 0
    session['reload_speed'] = 0.5

    # Message state (for revisit/gating popups)
    message_queue = []
    def push_message(lines):
        nonlocal message_queue, state
        # lines: list[str] or single str
        if isinstance(lines, str):
            lines = [lines]
        message_queue = lines
        return

    def draw_message_and_wait_to_continue(lines):
        # returns True when SPACE pressed to close
        box = pygame.Rect(WIDTH//2 - 600, HEIGHT//2 - 140, 1200, 280)
        pygame.draw.rect(screen, (60, 60, 120), box, border_radius=14)
        y = box.top + 40
        for ln in lines:
            t = font.render(ln, True, (240, 240, 255))
            screen.blit(t, (box.left + 30, y))
            y += 38
        hint = font.render("Press SPACE to continue", True, (220,220,220))
        screen.blit(hint, (box.centerx - hint.get_width()//2, box.bottom - 50))
        keys = pygame.key.get_pressed()
        return keys[pygame.K_SPACE]

    def reset_on_death():
        session['score'] += 0
        session['reload_speed'] += 0
        session['allies'] = 0

    def start_recon(planet_idx):
        # Planet timers: 1–3 => 30s, 5 => 60s. (Planet 4 is dialogue-only in this structure)
        timer_by_planet = {0:30, 1:30, 2:30, 4:60}
        recon_time = timer_by_planet.get(planet_idx, 30)

        # Allies spawn based on session (plus bonus for Planet 5)
        x_offsets = [-150, -80, 80, 150, 0]  # supports up to 5 ships on screen neatly
        allies = []
        crossed_ally = None
        base_allies = session['allies']

        # Bonus ally on Planet 5 regardless of cap
        bonus_allies = 1 if planet_idx == 4 else 0
        total_allies_to_spawn = min(len(x_offsets), base_allies + bonus_allies)

        for i in range(total_allies_to_spawn):
            allies.append(Ally(x_offsets[i], reload_time=session['reload_speed']))
            
        # Add crossed ally if purchased (invincible and center positioned)
        if session['crossed_ally']:
            crossed_ally = CrossedAlly(reload_time=session['reload_speed'])

        r = {
            'player': Player(WIDTH // 2, HEIGHT - 80, reload_time=session['reload_speed']),
            'allies': allies,
            'crossed_ally': crossed_ally,
            'bullets': [],
            'enemy_bullets': [],
            'enemies': [],
            'turrets': [],
            'score': session['score'],
            'game_over': False,
            'planet_idx': planet_idx,
            'start_time': time.time(),
            'recon_time': recon_time,
            'briefing_shown': True,   # default true; Planet 5 will flip to False to show pre-brief
        }

        if planet_idx == 4:
            # Pre-brief for Planet 5 (Mission 2 note + reinforcement)
            r['briefing_shown'] = False
            r['brief_lines'] = [
                "Command: This was only Mission 2 in the grand conquest.",
                "Command: A greater battle awaits beyond this sector.",
                "Logistics: Our allies have sent over a ship to help.",
                "Note: Timer starts after this briefing."
            ]
        return r

    recon = None

    show_story()

    shop_btn_rect = pygame.Rect(30, HEIGHT - 110, 220, 70)
    def draw_shop_buttons():
        # Buy Ally button
        ally_btn = pygame.Rect(WIDTH//2 - 350, HEIGHT//2 + 100, 200, 70)
        pygame.draw.rect(screen, (0,200,0), ally_btn)
        ally_text = font.render(f"Ally ({session['allies']}/{session['max_allies']})-10p", True, (255,255,255))
        screen.blit(ally_text, (ally_btn.left + 8, ally_btn.centery - 16))
        
        # Buy Crossed Ally button
        crossed_btn = pygame.Rect(WIDTH//2 - 130, HEIGHT//2 + 100, 200, 70)
        crossed_color = (255,140,0) if not session['crossed_ally'] else (100,100,100)
        pygame.draw.rect(screen, crossed_color, crossed_btn)
        crossed_text = font.render(f"C. Ally {'✓' if session['crossed_ally'] else ''}-50p", True, (255,255,255))
        screen.blit(crossed_text, (crossed_btn.left + 8, crossed_btn.centery - 16))
        
        # Buy Fast Reload button
        reload_btn = pygame.Rect(WIDTH//2 + 90, HEIGHT//2 + 100, 200, 70)
        pygame.draw.rect(screen, (0,0,200), reload_btn)
        reload_text = font.render(f"Reload Sp({session['reload_speed']:.1f}s)-15p", True, (255,255,255))
        screen.blit(reload_text, (reload_btn.left + 8, reload_btn.centery - 16))
        return ally_btn, crossed_btn, reload_btn

    def draw_popup(score):
        # Animated background
        bg_alpha = max(0, min(255, int(25 + 15 * math.sin(time.time() * 2))))
        screen.fill((bg_alpha, 25, 30))
        # Draw celebration stars
        for i in range(20):
            star_x = (i * 53) % WIDTH
            star_y = (i * 71 + int(time.time() * 30)) % HEIGHT
            star_brightness = max(0, min(255, int(200 + 55 * math.sin(time.time() * 4 + i))))
            pygame.draw.circle(screen, (star_brightness, star_brightness, 255), 
                              (star_x, star_y), 2)
        
        # Mission completed text with glow effect
        mission_text = big_font.render(f"MISSION COMPLETED!", True, (100, 255, 100))
        text_rect = mission_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 200))
        
        # Draw glow effect
        for i in range(3):
            glow_surface = pygame.Surface((mission_text.get_width() + 20, mission_text.get_height() + 20), pygame.SRCALPHA)
            glow_color = (100, 255, 100, 100 - i * 30)
            glow_text = big_font.render(f"MISSION COMPLETED!", True, glow_color)
            glow_rect = glow_text.get_rect(center=(glow_surface.get_width()//2, glow_surface.get_height()//2))
            glow_surface.blit(glow_text, glow_rect)
            screen.blit(glow_surface, (text_rect.x - 10 + i*2, text_rect.y - 10 + i*2))
        
        screen.blit(mission_text, text_rect)
        
        # Score display
        score_text = font.render(f"Final Score: {score}", True, (255, 255, 100))
        screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2 - 150))
        
        # Performance rating
        if score >= 15:
            rating = "EXCELLENT"
            rating_color = (100, 255, 100)
        elif score >= 10:
            rating = "GOOD"
            rating_color = (255, 255, 100)
        elif score >= 5:
            rating = "FAIR"
            rating_color = (255, 200, 100)
        elif score >= 1:
            rating = "NEEDS IMPROVEMENT"
            rating_color = (255, 150, 100)
        else:
            rating = "NO SCORE"
            rating_color = (255, 100, 100)
        
        rating_text = font.render(f"Rating: {rating}", True, rating_color)
        screen.blit(rating_text, (WIDTH//2 - rating_text.get_width()//2, HEIGHT//2 - 120))

        # Enhanced buttons with hover effects
        btn_w, btn_h = 300, 80
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        next_btn_rect = pygame.Rect(WIDTH//2 - btn_w - 20, HEIGHT//2 - 30, btn_w, btn_h)
        next_color = (70, 220, 70) if next_btn_rect.collidepoint(mouse_x, mouse_y) else (70, 180, 70)
        pygame.draw.rect(screen, next_color, next_btn_rect, border_radius=10)
        pygame.draw.rect(screen, (50, 150, 50), next_btn_rect, 3, border_radius=10)
        next_text = font.render("Next Mission", True, (0, 0, 0))
        screen.blit(next_text, (next_btn_rect.centerx - next_text.get_width()//2, next_btn_rect.centery - next_text.get_height()//2))

        quit_btn_rect = pygame.Rect(WIDTH//2 + 20, HEIGHT//2 - 30, btn_w, btn_h)
        quit_color = (220, 70, 70) if quit_btn_rect.collidepoint(mouse_x, mouse_y) else (180, 70, 70)
        pygame.draw.rect(screen, quit_color, quit_btn_rect, border_radius=10)
        pygame.draw.rect(screen, (150, 50, 50), quit_btn_rect, 3, border_radius=10)
        quit_text = font.render("Quit", True, (0, 0, 0))
        screen.blit(quit_text, (quit_btn_rect.centerx - quit_text.get_width()//2, quit_btn_rect.centery - quit_text.get_height()//2))

        # Instructions
        restart_text = font.render("Press R to return to planet menu", True, (200, 200, 200))
        screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT - 80))
        return next_btn_rect, quit_btn_rect

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        mx, my = pygame.mouse.get_pos()
        if state == STATE_RECON and recon:
            bg = planet_backgrounds[recon['planet_idx']]
            if bg:
                screen.blit(bg, (0, 0))
            else:
                screen.fill((20, 20, 30))
        else:
            screen.fill((20, 20, 30))


        if state == STATE_MENU:
            menu_text = big_font.render("Select a Planet for Recon", True, (200,200,255))
            screen.blit(menu_text, (WIDTH//2 - menu_text.get_width()//2, 80))
            for i, rect in enumerate(planet_icons):
                # Draw planet sprite or fallback to colored ellipse
                if planet_sprites[i] is not None:
                    # Apply completion effect (darken if completed)
                    if planet_done[i]:
                        # Create a darkened version of the sprite
                        darkened_sprite = planet_sprites[i].copy()
                        dark_surface = pygame.Surface((80, 80), pygame.SRCALPHA)
                        dark_surface.fill((80, 80, 80, 128))  # Semi-transparent dark overlay
                        darkened_sprite.blit(dark_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                        screen.blit(darkened_sprite, rect)
                        
                        # Add completion checkmark
                        check_text = font.render("✓", True, (0, 255, 0))
                        screen.blit(check_text, (rect.right - 15, rect.top + 5))
                    else:
                        screen.blit(planet_sprites[i], rect)
                        
                        # Add small glow effect for available planets
                        glow_surface = pygame.Surface((80, 80), pygame.SRCALPHA)
                        glow_surface.fill((100, 180, 255, 30))  # Subtle blue glow
                        screen.blit(glow_surface, rect)
                else:
                    # Fallback to colored ellipse if sprite failed to load
                    color = (100, 180, 255) if not planet_done[i] else (80, 80, 80)
                    pygame.draw.ellipse(screen, color, rect)
                    
                    # Add completion checkmark for fallback
                    if planet_done[i]:
                        check_text = font.render("✓", True, (0, 255, 0))
                        screen.blit(check_text, (rect.right - 15, rect.top + 5))
                
                label = font.render(f"Planet {i+1}", True, (255,255,255))
                screen.blit(label, (rect.centerx - label.get_width()//2, rect.bottom + 10))

                # Allow clicking even if planet is done (for revisit messages 1-4)
                if rect.collidepoint(mx, my):
                    # Draw hover effect (yellow border)
                    if planet_sprites[i] is not None:
                        # Create a yellow border around the sprite
                        border_rect = rect.inflate(8, 8)
                        pygame.draw.rect(screen, (255, 255, 0), border_rect, 4, border_radius=8)
                    else:
                        pygame.draw.ellipse(screen, (255,255,0), rect, 4)
                    if mouse_pressed:
                        selected_planet = i
                        current_planet = i

                        # Gate Planet 5 (index 4): must beat planets 1–3 and visit/complete planet 4
                        if i == 4:
                            # Conditions: planets 0,1,2,3 must be True
                            if not (planet_done[0] and planet_done[1] and planet_done[2] and planet_done[3]):
                                push_message([
                                    "Access Denied: You cannot advance yet.",
                                    "Requirement: Beat Planets 1–3 and complete Planet 4 first."
                                ])
                                state = STATE_MESSAGE
                                time.sleep(0.15)
                                continue

                        # Revisit behavior for planets 1–4:
                        if planet_done[i] and i <= 3:
                            # Show revisit message only, then return to menu
                            if i == 3:
                                push_message([revisit_line_p4])
                            else:
                                push_message([revisit_lines_generic])
                            state = STATE_MESSAGE
                            time.sleep(0.15)
                            continue

                        # First-time behaviors:
                        if i == 3:
                            # Planet 4 dialogue scene (serious)
                            dialogue_step = 0
                            state = STATE_DIALOGUE
                        else:
                            recon = start_recon(i)
                            state = STATE_RECON
                        time.sleep(0.15)

            # SHOP BUTTON
            pygame.draw.rect(screen, (200, 180, 50), shop_btn_rect)
            shop_text = font.render("SHOP", True, (0,0,0))
            screen.blit(shop_text, (shop_btn_rect.centerx - shop_text.get_width()//2, shop_btn_rect.centery - shop_text.get_height()//2))
            if shop_btn_rect.collidepoint(mx, my) and mouse_pressed:
                state = STATE_SHOP

            score_text = font.render(f"Score: {session['score']}", True, (255,255,0))
            screen.blit(score_text, (30, HEIGHT - 170))

            if all(planet_done):
                done_text = big_font.render("All Recon Complete!", True, (0,255,0))
                screen.blit(done_text, (WIDTH//2 - done_text.get_width()//2, HEIGHT//2 + 120))

        elif state == STATE_SHOP:
            shop_title = big_font.render("SHOP", True, (255,255,100))
            screen.blit(shop_title, (WIDTH//2 - shop_title.get_width()//2, HEIGHT//2 - 120))
            score_text = font.render(f"Score: {session['score']}", True, (255,255,0))
            screen.blit(score_text, (WIDTH//2 - 60, HEIGHT//2 - 50))
            ally_btn, crossed_btn, reload_btn = draw_shop_buttons()
            back_btn_rect = pygame.Rect(WIDTH//2 - 80, HEIGHT - 90, 160, 60)
            pygame.draw.rect(screen, (80,80,80), back_btn_rect)
            back_text = font.render("BACK", True, (255,255,255))
            screen.blit(back_text, (back_btn_rect.centerx - back_text.get_width()//2, back_btn_rect.centery - back_text.get_height()//2))
            # Handle shop buttons
            if mouse_pressed:
                if ally_btn.collidepoint(mx, my):
                    if session['score'] >= 10 and session['allies'] < session['max_allies']:
                        session['score'] -= 10
                        session['allies'] += 1
                        time.sleep(0.15)
                if crossed_btn.collidepoint(mx, my):
                    if session['score'] >= 20 and not session['crossed_ally']:
                        session['score'] -= 20
                        session['crossed_ally'] = True
                        time.sleep(0.15)
                if reload_btn.collidepoint(mx, my):
                    if session['score'] >= 15 and session['reload_speed'] > 0.2:
                        session['score'] -= 15
                        session['reload_speed'] = max(0.2, session['reload_speed'] - 0.1)
                        time.sleep(0.15)
                if back_btn_rect.collidepoint(mx, my):
                    state = STATE_MENU
                    time.sleep(0.15)

        elif state == STATE_MESSAGE:
            # Simple pop-up; SPACE returns to menu (or prior state caller expects)
            if draw_message_and_wait_to_continue(message_queue):
                state = STATE_MENU
                message_queue = []

        elif state == STATE_RECON:
            r = recon

            # Planet 5 pre-briefing before timer starts
            if not r['briefing_shown']:
                if draw_message_and_wait_to_continue(r['brief_lines']):
                    r['briefing_shown'] = True
                    r['start_time'] = time.time()  # start timer now
                pygame.display.flip()
                clock.tick(60)
                continue

            tleft = max(0, int(r['recon_time'] - (time.time() - r['start_time'])))
            r['player'].draw(screen)  # Ensure player is visible!

            for ally in r['allies']:
                ally.draw(screen)
            
            # Draw crossed ally
            if r['crossed_ally']:
                r['crossed_ally'].draw(screen)

            for bullet in r['bullets']:
                bullet.draw(screen)

            for enemy in r['enemies']:
                enemy.draw(screen)
            for turret in r['turrets']:
                turret.draw(screen)
            for ebullet in r['enemy_bullets']:
                ebullet.draw(screen)

            score_text = font.render(f"Score: {r['score']}", True, (255,255,255))
            screen.blit(score_text, (10, 10))
            alive_count = sum(ally.alive for ally in r['allies'])
            ally_text = font.render(f"Allies left: {alive_count}", True, (0,255,128))
            screen.blit(ally_text, (10, 50))
            timer_text = big_font.render(f"Survive for {tleft} seconds", True, (255,230,100))
            screen.blit(timer_text, (WIDTH//2 - timer_text.get_width()//2, 32))

            # SPAWN LOGIC BY PLANET
            if not r['game_over']: 
                r['player'].update(keys)
                for ally in r['allies']:
                    ally.update(r['player'])
                
                # Update crossed ally (invincible, stays in center)
                if r['crossed_ally']:
                    r['crossed_ally'].update(r['player'], WIDTH, HEIGHT)

                if mouse_pressed:
                    mx, my = pygame.mouse.get_pos()
                    bullet = r['player'].fire(mx, my)
                    if bullet:
                        r['bullets'].append(bullet)

                targets = r['enemies'] + r['turrets']
                for ally in r['allies']:
                    if ally.alive and targets:
                        nearest = min(targets, key=lambda e: math.hypot(ally.x - e.x, ally.y - e.y))
                        bullet = ally.fire(nearest.x, nearest.y)
                        if bullet:
                            r['bullets'].append(bullet)
                
                # Crossed ally fires in cross pattern automatically
                if r['crossed_ally'] and targets:
                    cross_bullets = r['crossed_ally'].fire_cross_pattern()
                    r['bullets'].extend(cross_bullets)

                # ENEMY SPAWN LOGIC (per planet)
                if time.time() - r['start_time'] < r['recon_time']:
                    if random.randint(0, 60) == 0: # spawn
                        x = random.randint(40, WIDTH-40)
                        idx = r['planet_idx']
                        if idx in [0, 1]:
                            # PLANET 1 & 2: RED ENEMY ONLY
                            r['enemies'].append(Enemy(x))
                        elif idx == 2:
                            # PLANET 3: TURRET + RED ENEMY
                            if random.random() < 0.5:
                                r['enemies'].append(Enemy(x))
                            else:
                                r['turrets'].append(TurretEnemy(x))
                                r['turrets'][-1].TURRET_STOP_Y = HEIGHT // 8
                        elif idx == 3:
                            # PLANET 4: Dialogue planet (handled elsewhere)
                            pass
                        elif idx == 4:
                            # PLANET 5: all types
                            roll = random.random()
                            if roll < 0.33:
                                r['enemies'].append(Enemy(x))
                            elif roll < 0.66:
                                r['turrets'].append(TurretEnemy(x))
                                r['turrets'][-1].TURRET_STOP_Y = HEIGHT // 8
                            else:
                                y = random.randint(40, HEIGHT//2)
                                r['enemies'].append(RunnerEnemy(x, y))

                STOP_Y = HEIGHT - HEIGHT // 4
                player = r['player']
                player.update(keys, STOP_Y=STOP_Y, WIDTH=WIDTH, HEIGHT=HEIGHT)

                for turret in r['turrets']:
                    turret.update()
                    if turret.on_screen(WIDTH=WIDTH, HEIGHT=HEIGHT):
                        new_bullets = turret.fire(r['player'].x, r['player'].y)
                        r['enemy_bullets'].extend(new_bullets)
                for enemy in r['enemies']:
                    if isinstance(enemy, RunnerEnemy):
                        enemy.update(r['player'])
                    else:
                        enemy.update(STOP_Y=HEIGHT//2, WIDTH=WIDTH, HEIGHT=HEIGHT)
                for bullet in r['bullets'][:]:
                    bullet.update()
                    if not bullet.on_screen(WIDTH=WIDTH, HEIGHT=HEIGHT):
                        r['bullets'].remove(bullet)
                        continue
                    for enemy in r['enemies'][:]:
                        if bullet.collide(enemy):
                            r['bullets'].remove(bullet)
                            r['enemies'].remove(enemy)
                            r['score'] += 1
                            session['score'] = r['score']
                            break
                    for turret in r['turrets'][:]:
                        if bullet.collide(turret):
                            r['bullets'].remove(bullet)
                            r['turrets'].remove(turret)
                            r['score'] += 5
                            session['score'] = r['score']
                            break
                for ebullet in r['enemy_bullets'][:]:
                    ebullet.update()
                    if not ebullet.on_screen(WIDTH=WIDTH, HEIGHT=HEIGHT):
                        r['enemy_bullets'].remove(ebullet)
                        continue
                    if ebullet.collide(r['player']):
                        r['game_over'] = True
                        reset_on_death()
                        break
                    for ally in r['allies']:
                        if ally.alive and ebullet.collide(ally):
                            r['enemy_bullets'].remove(ebullet)
                            ally.alive = False
                            # session allies reflect persistent stock, bonus ally is mission-only
                            if r['planet_idx'] != 4:  # do not decrement persistent count for bonus-only planet
                                session['allies'] = max(0, session['allies'] - 1)
                            break
                for enemy in r['enemies']:
                    if isinstance(enemy, Enemy):
                        alive_targets = [r['player']] + [a for a in r['allies'] if a.alive]
                        if alive_targets:
                            nearest = min(alive_targets, key=lambda t: math.hypot(enemy.x - t.x, enemy.y - t.y))
                            ebullet = enemy.fire(nearest.x, nearest.y)
                            if ebullet:
                                r['enemy_bullets'].append(ebullet)
                    if enemy.collide(r['player']):
                        r['game_over'] = True
                        reset_on_death()
                        break
                for turret in r['turrets']:
                    if turret.collide(r['player']):
                        r['game_over'] = True
                        reset_on_death()
                        break

            if r['game_over']:
                over_text = font.render("MISSION FAILED! Press R to Return", True, (255,0,0))
                screen.blit(over_text, (WIDTH//2 - over_text.get_width()//2, HEIGHT//2))
                if keys[pygame.K_r]:
                    state = STATE_MENU
                    planet_done[current_planet] = False
            elif tleft == 0:
                done_text = big_font.render("Recon Success!", True, (0,255,0))
                screen.blit(done_text, (WIDTH//2 - done_text.get_width()//2, HEIGHT//2))
                finish_text = font.render("Press SPACE to return to menu", True, (200,255,200))
                screen.blit(finish_text, (WIDTH//2 - finish_text.get_width()//2, HEIGHT//2 + 60))
                if keys[pygame.K_SPACE]:
                    planet_done[current_planet] = True
                    session['score'] = r['score']
                    state = STATE_MENU

        elif state == STATE_DIALOGUE:
            # Planet 4 dialogue (serious tone)
            screen.fill((40, 30, 60))
            box = pygame.Rect(WIDTH//2 - 600, HEIGHT//2 - 140, 1200, 280)
            pygame.draw.rect(screen, (80,80,180), box, border_radius=14)
            lines = planet4_dialogue_lines
            # paginate by step
            if dialogue_step < len(lines):
                text = font.render(lines[dialogue_step], True, (255,255,255))
                screen.blit(text, (box.left + 40, box.top + 80))
                next_text = font.render("Press SPACE for next", True, (200,200,200))
                screen.blit(next_text, (box.left + 40, box.bottom - 50))
                if keys[pygame.K_SPACE]:
                    time.sleep(0.2)
                    dialogue_step += 1
            else:
                finish_text = font.render("Council aligned. Press SPACE to return", True, (0,255,0))
                screen.blit(finish_text, (box.left + 40, box.bottom - 50))
                if keys[pygame.K_SPACE]:
                    planet_done[current_planet] = True
                    state = STATE_MENU

        # -----------------------------
        # Enhanced Mission Complete Popup
        # Show the enhanced popup when all five planets are completed.
        # -----------------------------
        if all(planet_done):
            mission_complete = True
            update_session(session['score'], session['allies'], session['reload_speed'])
            
            next_btn_rect, quit_btn_rect = draw_popup(session['score'])
            if mouse_pressed:
                if next_btn_rect.collidepoint(mx, my):
                    pygame.quit()
                    subprocess.Popen([sys.executable, "spaceshi3.py"])
                    sys.exit()
                elif quit_btn_rect.collidepoint(mx, my):
                    pygame.quit()
                    sys.exit()

        pygame.display.flip()
        clock.tick(60)

        # Return to planet menu functionality
        if (keys[pygame.K_r] and (mission_complete or any(r and r.get('game_over', False) for r in [recon] if recon))):
            # Return to planet menu without resetting progress
            state = STATE_MENU
            mission_complete = False
            recon = None
            current_planet = None
            dialogue_step = 0
            # Keep session progress (score, allies, reload_speed) for roguelike progression

if __name__ == '__main__':
    main()
