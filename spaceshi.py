from space_objects import Player, Ally, Bullet, TurretEnemy, Enemy
import pygame
import sys
import math
import random
import time
import subprocess

PLAYER_RADIUS = 20
PLAYER_SPEED = 5
BULLET_RADIUS = 5
BULLET_SPEED = 10
ENEMY_RADIUS = 18
ENEMY_SPEED = 3
ENEMY_FIRE_INTERVAL = 2
ENEMY_BULLET_RADIUS = 5
ENEMY_BULLET_SPEED = 8
ENEMY_BULLET_COLOR = (255, 50, 50)
TURRET_RADIUS = 22
TURRET_SPEED = 3
TURRET_STOP_Y = 135
ALLY_RADIUS = 16
ALLY_SPEED = 5
ALLY_RELOAD_TIME = 0.5
WAVE_SIZE = 1
RELOAD_TIME = 0
MISSION_TIME = 64
NEXT_MISSION_FILE = "spaceshi2.py"

def main():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    infoObject = pygame.display.Info()
    WIDTH, HEIGHT = infoObject.current_w, infoObject.current_h
    STOP_Y = HEIGHT - HEIGHT // 4

    font = pygame.font.SysFont(None, 36)
    big_font = pygame.font.SysFont(None, 72)

    player = Player(WIDTH // 2, HEIGHT - 80)
    allies = [Ally(-80), Ally(80)]
    bullets = []
    enemy_bullets = []
    enemies = []
    turrets = []
    score = 0
    game_over = False
    mission_complete = False
    next_wave_time = time.time() + random.uniform(2, 5)
    mission_start_time = time.time()
    mission_duration = MISSION_TIME

    story_text = [
        "Mission 1: Defend the Homeland",
        "Commander: Get a hang of the controls cadet!",
        "Commander: Its not everyday that your planet gets invaded by some fools.",
        "Commander: Use the A and D keys to move, and LMB to fire at your cursor.",
        "Commander: Two allies are going to be helping you",
        "Commander: Cadet, the Union cheers you on!"
    ]
    story_time = 4.5

    def show_story():
        clock = pygame.time.Clock()
        for line in story_text:
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
        restart_text = font.render("Press R to restart", True, (200, 200, 200))
        screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT - 80))
        return next_btn_rect, quit_btn_rect

    show_story()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        mx, my = pygame.mouse.get_pos()
        now = time.time()

        time_left = max(0, int(mission_duration - (now - mission_start_time)))
        if not mission_complete and time_left == 0:
            mission_complete = True

        if not game_over and not mission_complete:
            player.update(keys, STOP_Y=STOP_Y, WIDTH=WIDTH, HEIGHT=HEIGHT)
            for ally in allies:
                ally.update(player)

            if mouse_pressed:
                bullet = player.fire(mx, my)
                if bullet:
                    bullets.append(bullet)

            targets = enemies + turrets
            for ally in allies:
                if ally.alive and targets:
                    nearest = min(targets, key=lambda e: math.hypot(ally.x - e.x, ally.y - e.y))
                    bullet = ally.fire(nearest.x, nearest.y)
                    if bullet:
                        bullets.append(bullet)

            if player.stopped and now >= next_wave_time:
                for _ in range(WAVE_SIZE):
                    x = random.randint(ENEMY_RADIUS, WIDTH - ENEMY_RADIUS)
                    if random.random() < 0.5:
                        turrets.append(TurretEnemy(x))
                        turrets[-1].TURRET_STOP_Y = TURRET_STOP_Y
                    else:
                        enemies.append(Enemy(x))
                next_wave_time = now + random.uniform(2, 5)

            for enemy in enemies[:]:
                enemy.update(STOP_Y=HEIGHT//2, WIDTH=WIDTH, HEIGHT=HEIGHT)
                if not enemy.on_screen(WIDTH=WIDTH, HEIGHT=HEIGHT):
                    enemies.remove(enemy)
                else:
                    alive_targets = [player] + [ally for ally in allies if ally.alive]
                    if alive_targets:
                        nearest = min(alive_targets, key=lambda t: math.hypot(enemy.x - t.x, enemy.y - t.y))
                        ebullet = enemy.fire(nearest.x, nearest.y)
                        if ebullet:
                            enemy_bullets.append(ebullet)

            for turret in turrets[:]:
                turret.update()
                if not turret.on_screen(WIDTH=WIDTH, HEIGHT=HEIGHT):
                    turrets.remove(turret)
                else:
                    new_bullets = turret.fire(player.x, player.y)
                    enemy_bullets.extend(new_bullets)

            for bullet in bullets[:]:
                bullet.update()
                if not bullet.on_screen(WIDTH=WIDTH, HEIGHT=HEIGHT):
                    bullets.remove(bullet)
                    continue
                for enemy in enemies[:]:
                    if bullet.collide(enemy):
                        bullets.remove(bullet)
                        enemies.remove(enemy)
                        score += 1
                        break
                for turret in turrets[:]:
                    if bullet.collide(turret):
                        bullets.remove(bullet)
                        turrets.remove(turret)
                        score += 5
                        break

            for ebullet in enemy_bullets[:]:
                ebullet.update()
                if not ebullet.on_screen(WIDTH=WIDTH, HEIGHT=HEIGHT):
                    enemy_bullets.remove(ebullet)
                    continue
                if ebullet.collide(player):
                    game_over = True
                    break
                for ally in allies:
                    if ally.alive and ebullet.collide(ally):
                        enemy_bullets.remove(ebullet)
                        ally.alive = False
                        break

            for enemy in enemies:
                if enemy.collide(player):
                    game_over = True
                    break
            for turret in turrets:
                if turret.collide(player):
                    game_over = True
                    break

        # Dynamic background with subtle movement
 

        screen.fill((15,10,30))
    
        # Draw starfield effect
        for i in range(50):
            star_x = (i * 37) % WIDTH
            star_y = (i * 73 + int(now * 20)) % HEIGHT
            star_brightness = max(0, min(255, int(128 + 127 * math.sin(now * 2 + i))))
            pygame.draw.circle(screen, (star_brightness, star_brightness, star_brightness), 
                              (star_x, star_y), 1)
    
        player.draw(screen)
        for ally in allies:
            ally.draw(screen)
        for bullet in bullets:
            bullet.draw(screen)
        for enemy in enemies:
            enemy.draw(screen)
        for turret in turrets:
            turret.draw(screen)
        for ebullet in enemy_bullets:
            ebullet.draw(screen)
        
        score_text = font.render(f"Score: {score}", True, (255,255,255))
        screen.blit(score_text, (10, 10))

        alive_count = sum(ally.alive for ally in allies)
        ally_text = font.render(f"Allies left: {alive_count}", True, (0,255,128))
        screen.blit(ally_text, (10, 50))

        if not mission_complete:
            # Enhanced timer with visual effects
            timer_color = (255, 230, 100)
            if time_left <= 10:  # Warning colors for last 10 seconds
                timer_color = (255, 100, 100) if int(now * 2) % 2 == 0 else (255, 200, 100)
            
            timer_text = big_font.render(f"Survive for {time_left} seconds", True, timer_color)
            screen.blit(timer_text, (WIDTH//2 - timer_text.get_width()//2, 32))
            
            # Progress bar
            progress_width = 400
            progress_height = 8
            progress_x = WIDTH//2 - progress_width//2
            progress_y = 80
            progress_ratio = time_left / MISSION_TIME
            
            # Background bar
            pygame.draw.rect(screen, (60, 60, 60), (progress_x, progress_y, progress_width, progress_height))
            # Progress bar
            pygame.draw.rect(screen, timer_color, (progress_x, progress_y, int(progress_width * progress_ratio), progress_height))

        if game_over:
            # Enhanced game over screen
            over_text = big_font.render("MISSION FAILED!", True, (255, 50, 50))
            screen.blit(over_text, (WIDTH//2 - over_text.get_width()//2, HEIGHT//2 - 50))
            
            # Subtitle
            sub_text = font.render("Press R to restart the mission", True, (200, 200, 200))
            screen.blit(sub_text, (WIDTH//2 - sub_text.get_width()//2, HEIGHT//2 + 20))
            
            # Final score
            final_score = font.render(f"Final Score: {score}", True, (255, 255, 100))
            screen.blit(final_score, (WIDTH//2 - final_score.get_width()//2, HEIGHT//2 + 60))

        if mission_complete:
            next_btn_rect, quit_btn_rect = draw_popup(score)
            if mouse_pressed:
                if next_btn_rect.collidepoint(mx, my):
                    subprocess.Popen([sys.executable, NEXT_MISSION_FILE])
                    pygame.quit()
                    sys.exit()
                elif quit_btn_rect.collidepoint(mx, my):
                    pygame.quit()
                    sys.exit()

        pygame.display.flip()
        pygame.time.Clock().tick(60)

        if (game_over or mission_complete) and keys[pygame.K_r]:
            player = Player(WIDTH // 2, HEIGHT - 80)
            allies = [Ally(-80), Ally(80)]
            bullets = []
            enemy_bullets = []
            enemies = []
            turrets = []
            score = 0
            game_over = False
            mission_complete = False
            next_wave_time = time.time() + random.uniform(2, 5)
            mission_start_time = time.time()
            show_story()

if __name__ == '__main__':

    main()
