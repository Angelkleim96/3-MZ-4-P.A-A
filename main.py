import pygame
import random
import math
from collections import deque
import os
from datetime import datetime


pygame.init()


WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Ниндзя против зомби")

WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)
DARK_GRAY = (50, 50, 50)
GRID_COLOR = (70, 70, 70)
RED = (255, 0, 0)
LIGHT_BLUE = (100, 100, 255)
DARK_BLUE = (0, 0, 100)


font = pygame.font.SysFont('Arial', 36)
large_font = pygame.font.SysFont('Arial', 72)
small_font = pygame.font.SysFont('Arial', 24)

# Состояния игры
MENU = 0
LEVEL_SELECT = 1
GAME = 2
GAME_OVER = 3
LEADERBOARD = 4
game_state = MENU

current_level = None
zombies_killed = 0
game_start_time = 0
final_score = 0

# Настройки сетки
GRID_SIZE = 50  
show_grid = False  

# Класс для кнопок
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.scale = 1.0
        self.target_scale = 1.0

    def update(self):
       
        if abs(self.scale - self.target_scale) > 0.01:
            self.scale += (self.target_scale - self.scale) * 0.1
        else:
            self.scale = self.target_scale

    def draw(self, screen):
    
        color = self.hover_color if self.is_hovered else self.color
        width = int(self.rect.width * self.scale)
        height = int(self.rect.height * self.scale)
        x = self.rect.centerx - width // 2
        y = self.rect.centery - height // 2
        
        pygame.draw.rect(screen, color, (x, y, width, height), border_radius=10)
        pygame.draw.rect(screen, BLACK, (x, y, width, height), 2, border_radius=10)  # Обводка
        
        text_surf = font.render(self.text, True, BLACK if color == GREEN else WHITE)
        screen.blit(text_surf, (self.rect.centerx - text_surf.get_width() // 2, 
                               self.rect.centery - text_surf.get_height() // 2))

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        self.target_scale = 1.05 if self.is_hovered else 1.0

    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False

# Создание кнопок главного меню
start_button = Button(WIDTH // 2 - 150, HEIGHT // 2 - 60, 300, 60, "Начать игру", BLUE, GREEN)
scores_button = Button(WIDTH // 2 - 150, HEIGHT // 2 + 20, 300, 60, "Таблица рекордов", BLUE, GREEN)
quit_button = Button(WIDTH // 2 - 150, HEIGHT // 2 + 100, 300, 60, "Выход", BLUE, GREEN)
menu_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 160, 200, 50, "В меню", BLUE, GREEN)
next_level_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 40, 200, 50, "Продолжить", BLUE, GREEN)

# Кнопки выбора уровня
level1_button = Button(WIDTH // 4 - 100, HEIGHT // 2, 200, 100, "Уровень 1", BLUE, GREEN)
level2_button = Button(WIDTH // 2 - 100, HEIGHT // 2, 200, 100, "Уровень 2", BLUE, GREEN)
level3_button = Button(3 * WIDTH // 4 - 100, HEIGHT // 2, 200, 100, "Уровень 3", BLUE, GREEN)
back_button = Button(50, HEIGHT - 80, 100, 50, "Назад", BLUE, GREEN)

# Кнопки для таблицы рекордов
leaderboard_back_button = Button(WIDTH // 2 - 100, HEIGHT - 80, 200, 50, "Назад", BLUE, GREEN)
clear_button = Button(WIDTH - 150, HEIGHT - 80, 100, 50, "Очистить", RED, GREEN)

# Настройки уровней
class Level:
    def __init__(self, num, zombie_speed, zombies_to_kill, walls, coefficient):
        self.num = num
        self.zombie_speed = zombie_speed
        self.zombies_to_kill = zombies_to_kill
        self.walls = walls
        self.coefficient = coefficient
        self.time_limit = 300  # 5 минут в секундах

# Инициализация стен (пустой список по умолчанию)
walls = []

levels = [
    Level(1, 2, 10, [
        pygame.Rect(100, 100, 50, 200),
        pygame.Rect(300, 400, 200, 50),
        pygame.Rect(600, 200, 50, 300),
        pygame.Rect(200, 300, 100, 50)
    ], 1.0),
    Level(2, 3, 20, [
        pygame.Rect(100, 100, 50, 400),
        pygame.Rect(300, 150, 50, 300),
        pygame.Rect(500, 50, 50, 400),
        pygame.Rect(700, 200, 50, 300)
    ], 1.5),
    Level(3, 4, 30, [
        pygame.Rect(100, 100, 50, 400),
        pygame.Rect(200, 100, 400, 50),
        pygame.Rect(200, 450, 400, 50),
        pygame.Rect(650, 100, 50, 400),
        pygame.Rect(300, 250, 200, 50),
        pygame.Rect(400, 300, 50, 100)
    ], 2.0)
]

# Функция для загрузки и сохранения рекордов
def load_scores():
    if not os.path.exists('scores.txt'):
        return []
    
    with open('scores.txt', 'r') as f:
        lines = f.readlines()
    
    scores = []
    for line in lines:
        parts = line.strip().split('|')
        if len(parts) == 4:
            date = parts[0].strip()
            time = parts[1].strip()
            score = int(parts[2].strip())
            attempt = int(parts[3].strip().replace('#', ''))
            scores.append((date, time, score, attempt))
    
    return sorted(scores, key=lambda x: x[2], reverse=True)

def save_scores(scores):
    with open('scores.txt', 'w') as f:
        for score in scores:
            f.write(f"{score[0]} | {score[1]} | {score[2]} | #{score[3]}\n")

def add_score(date, time, score):
    scores = load_scores()
    attempt = len(scores) + 1
    scores.append((date, time, score, attempt))
    scores = sorted(scores, key=lambda x: x[2], reverse=True)
    save_scores(scores)

# Функция для создания стен по сетке
def create_wall(grid_x, grid_y, width_cells=1, height_cells=1):
    """Создает стену, занимающую указанное количество клеток сетки"""
    x = grid_x * GRID_SIZE
    y = grid_y * GRID_SIZE
    width = width_cells * GRID_SIZE
    height = height_cells * GRID_SIZE
    return pygame.Rect(x, y, width, height)

# Игровые переменные
player_pos = [WIDTH // 2, HEIGHT // 2]
player_direction = [0, 0]
player_scale = 20
player_speed = 4
player_health = 100

bullets = []
bullet_radius = 8
bullet_speed = 7
shoot_cooldown = 0
shoot_delay = 15

zombies = []
zombie_scale = 20
zombie_spawn_timer = 0
zombie_spawn_interval = 180
zombie_damage_cooldown = 0

coins = []
coin_radius = 10
coin_spawn_timer = 0
coin_spawn_interval = 500
coins_collected = 0

score = 0
game_over = False

def load_texture(path, size=None):
    try:
        texture = pygame.image.load(path)
        if size:
            texture = pygame.transform.scale(texture, size)
        return texture.convert_alpha()
    except:
        print(f"Ошибка загрузки текстуры: {path}")
        return None

# Загрузка текстур игрока для анимации
player_textures = {
    'idle_down': load_texture("img/ninja_down.png", (player_scale*1.5, player_scale*2)),
    'idle_up': load_texture("img/ninja_up.png", (player_scale*1.5, player_scale*2)),
    'idle_left': load_texture("img/ninja_left.png", (player_scale*1.5, player_scale*2)),
    'idle_right': load_texture("img/ninja_right.png", (player_scale*1.5, player_scale*2)),
    'walk_down': [
        load_texture("img/ninja_down.png", (player_scale*1.5, player_scale*2)),
        load_texture("img/ninja_down2.png", (player_scale*1.5, player_scale*2)),
        load_texture("img/ninja_down3.png", (player_scale*1.5, player_scale*2))
    ],
    'walk_up': [
        load_texture("img/ninja_up.png", (player_scale*1.5, player_scale*2)),
        load_texture("img/ninja_up2.png", (player_scale*1.5, player_scale*2)),
        load_texture("img/ninja_up3.png", (player_scale*1.5, player_scale*2))
    ],
    'walk_left': [
        load_texture("img/ninja_left.png", (player_scale*1.5, player_scale*2)),
        load_texture("img/ninja_left2.png", (player_scale*1.5, player_scale*2))
    ],
    'walk_right': [
        load_texture("img/ninja_right.png", (player_scale*1.5, player_scale*2)),
        load_texture("img/ninja_right2.png", (player_scale*1.5, player_scale*2))
    ]
}

# Загрузка текстур зомби для анимации
zombie_textures = {
    'down': [
        load_texture("img/zombie_down.png", (zombie_scale*1.5, zombie_scale*2)),
        load_texture("img/zombie_down2.png", (zombie_scale*1.5, zombie_scale*2)),
        load_texture("img/zombie_down2.png", (zombie_scale*1.5, zombie_scale*2))
    ],
    'up': [
        load_texture("img/zombie_up.png", (zombie_scale*1.5, zombie_scale*2)),
        load_texture("img/zombie_up2.png", (zombie_scale*1.5, zombie_scale*2)),
        load_texture("img/zombie_up3.png", (zombie_scale*1.5, zombie_scale*2))
    ],
    'left': [
        load_texture("img/zombie_left.png", (zombie_scale*1.5, zombie_scale*2)),
        load_texture("img/zombie_left2.png", (zombie_scale*1.5, zombie_scale*2))
    ],
    'right': [ 
        load_texture("img/zombie_right.png", (zombie_scale*1.5, zombie_scale*2)),
        load_texture("img/zombie_right2.png", (zombie_scale*1.5, zombie_scale*2))
    ]
}

# Исключения

for direction in ['down', 'up', 'left', 'right']:
    if not zombie_textures.get(direction) or not all(zombie_textures[direction]):
        frames = 3 if direction in ['down', 'up'] else 2
        zombie_textures[direction] = []
        for i in range(frames):
            surf = pygame.Surface((zombie_scale * 1.5, zombie_scale * 2), pygame.SRCALPHA)
            pygame.draw.rect(surf, RED, (0, 0, zombie_scale * 1.5, zombie_scale * 2))
            zombie_textures[direction].append(surf)


if not player_textures['idle_down']:
    player_textures['idle_down'] = pygame.Surface((player_scale * 1.5, player_scale * 2), pygame.SRCALPHA)
    pygame.draw.rect(player_textures['idle_down'], BLUE, (0, 0, player_scale * 1.5, player_scale * 2))

if not player_textures['idle_up']:
    player_textures['idle_up'] = pygame.Surface((player_scale * 1.5, player_scale * 2), pygame.SRCALPHA)
    pygame.draw.rect(player_textures['idle_up'], BLUE, (0, 0, player_scale * 1.5, player_scale * 2))

if not player_textures['idle_left']:
    player_textures['idle_left'] = pygame.Surface((player_scale * 1.5, player_scale * 2), pygame.SRCALPHA)
    pygame.draw.rect(player_textures['idle_left'], BLUE, (0, 0, player_scale * 1.5, player_scale * 2))

if not player_textures['idle_right']:
    player_textures['idle_right'] = pygame.Surface((player_scale * 1.5, player_scale * 2), pygame.SRCALPHA)
    pygame.draw.rect(player_textures['idle_right'], BLUE, (0, 0, player_scale * 1.5, player_scale * 2))


for direction in ['walk_down', 'walk_up', 'walk_left', 'walk_right']:
    if not player_textures.get(direction) or not all(player_textures[direction]):
        if direction == 'walk_down' or direction == 'walk_up':
            frames = 3
        else:
            frames = 2
            
        player_textures[direction] = []
        for i in range(frames):
            surf = pygame.Surface((player_scale * 1.5, player_scale * 2), pygame.SRCALPHA)
            pygame.draw.rect(surf, BLUE, (0, 0, player_scale * 1.5, player_scale * 2))
            player_textures[direction].append(surf)

# Загрузка остальных текстур
zombie_texture = load_texture("img/zombi_down.png", (zombie_scale*1.5, zombie_scale*2))
bullet_texture = load_texture("img/bullet.png", (bullet_radius*2, bullet_radius*2))
coin_texture = load_texture("img/coin.png", (coin_radius*2, coin_radius*2))
wall_texture = load_texture("img/wall.png")

if not zombie_texture:
    zombie_texture = pygame.Surface((zombie_scale * 2, zombie_scale * 2), pygame.SRCALPHA)
    pygame.draw.rect(zombie_texture, RED, (0, 0, zombie_scale * 2, zombie_scale * 2))

if not bullet_texture:
    bullet_texture = pygame.Surface((bullet_radius * 2, bullet_radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(bullet_texture, GREEN, (bullet_radius, bullet_radius), bullet_radius)

if not coin_texture:
    coin_texture = pygame.Surface((coin_radius * 2, coin_radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(coin_texture, YELLOW, (coin_radius, coin_radius), coin_radius)

font = pygame.font.SysFont(None, 36)
large_font = pygame.font.SysFont(None, 72)

# Кнопка рестарта
restart_button = Button(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50, "Рестарт", BLUE, GREEN)

# Анимация игрока
class PlayerAnimation:
    def __init__(self):
        self.current_direction = 'down'
        self.is_walking = False
        self.animation_frame = 0
        self.animation_speed = 0.2  # Скорость смены кадров
        self.last_direction = 'down'
    
    def update(self, dx, dy):
     
        if (dx != 0 or dy) != 0:
            self.is_walking = True
            
            
            if dx != 0:  
                if dx > 0:
                    self.current_direction = 'right'
                else:
                    self.current_direction = 'left'
            else:  
                if dy > 0:
                    self.current_direction = 'down'
                else:
                    self.current_direction = 'up'
            
            self.last_direction = self.current_direction
        else:
            self.is_walking = False
        
        # Обновляем кадр анимации
        if self.is_walking:
            self.animation_frame += self.animation_speed
            if self.current_direction in ['down', 'up']:
                if self.animation_frame >= len(player_textures[f'walk_{self.current_direction}']):
                    self.animation_frame = 0
            else:  
                if self.animation_frame >= len(player_textures[f'walk_{self.current_direction}']):
                    self.animation_frame = 0
    
    def get_current_frame(self):
        if self.is_walking:
            frame_index = int(self.animation_frame)
            return player_textures[f'walk_{self.current_direction}'][frame_index]
        else:
            return player_textures[f'idle_{self.last_direction}']

player_animation = PlayerAnimation()

# Карта проходимости для поиска пути
def create_pathfinding_grid():
    if not walls:  
        return [[1 for _ in range(HEIGHT // GRID_SIZE + 1)] for _ in range(WIDTH // GRID_SIZE + 1)]
    
    grid_width = WIDTH // GRID_SIZE + 1
    grid_height = HEIGHT // GRID_SIZE + 1
    grid = [[1 for _ in range(grid_height)] for _ in range(grid_width)]
    
   
    for wall in walls:
      
        start_x = wall.x // GRID_SIZE
        start_y = wall.y // GRID_SIZE
        end_x = (wall.x + wall.width) // GRID_SIZE
        end_y = (wall.y + wall.height) // GRID_SIZE
        
     
        end_x = min(end_x, grid_width - 1)
        end_y = min(end_y, grid_height - 1)
        
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                if 0 <= x < grid_width and 0 <= y < grid_height:
                    grid[x][y] = 0
    
    return grid

pathfinding_grid = create_pathfinding_grid()

# Поиск пути с помощью BFS
def find_path(start, end):
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
    diagonal_directions = [(1, 1), (-1, -1), (1, -1), (-1, 1)]
    queue = deque()
    queue.append((start, []))
    visited = set()
    visited.add(start)
    
    while queue:
        (x, y), path = queue.popleft()
        
        if (x, y) == end:
            return path
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            
            # Проверка границ и проходимости
            if not (0 <= nx < len(pathfinding_grid) and 0 <= ny < len(pathfinding_grid[0])):
                continue
            if pathfinding_grid[nx][ny] == 0:
                continue
            if (nx, ny) in visited:
                continue
            
            
            if (dx, dy) in diagonal_directions:
              
                if (pathfinding_grid[x + dx][y] == 0) or (pathfinding_grid[x][y + dy] == 0):
                    continue  
            
            visited.add((nx, ny))
            queue.append(((nx, ny), path + [(nx, ny)]))
    
    return []  # Если путь не найден

class Zombie:
    def __init__(self, x, y):
        self.grid_x = x
        self.grid_y = y
        self.x = x * GRID_SIZE + GRID_SIZE // 2
        self.y = y * GRID_SIZE + GRID_SIZE // 2
        self.path = []
        self.target_grid = current_player_grid
        self.is_moving_to_cell = False
        self.direction = 'down'
        self.last_dx = 0
        self.last_dy = 0
        self.animation_frame = 0
        self.animation_speed = 0.15
        self.speed = current_level.zombie_speed if current_level and hasattr(current_level, 'zombie_speed') else 2
        self.path_update_timer = 0
        self.path_update_interval = 30  # Обновлять путь каждые 30 кадров
    
    def update(self):
        """Обновление позиции и состояния зомби"""
        # Обновляем анимацию
        self.animation_frame += self.animation_speed
        if self.animation_frame >= len(zombie_textures[self.direction]):
            self.animation_frame = 0
        
        # Обновляем таймер обновления пути
        self.path_update_timer += 1
        
        # Если есть путь, двигаемся по нему
        if self.path:
            target_x, target_y = self.path[0]
            target_screen_x = target_x * GRID_SIZE + GRID_SIZE // 2
            target_screen_y = target_y * GRID_SIZE + GRID_SIZE // 2
            
            # Вычисляем направление движения
            dx = target_screen_x - self.x
            dy = target_screen_y - self.y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > 0:
                dx = dx / distance * self.speed
                dy = dy / distance * self.speed
                
                self.last_dx = dx
                self.last_dy = dy
                
                # Обновляем направление для анимации
                self.update_direction()
                
                # Двигаем зомби
                self.x += dx
                self.y += dy
            
            # Если достигли текущей целевой клетки, переходим к следующей
            if distance < self.speed:
                self.path.pop(0)
        
        # Обновляем путь к игроку, если:
        # 1. Путь закончился или его не было
        # 2. Игрок сменил клетку
        # 3. Прошло достаточно времени с последнего обновления
        current_grid = (int(self.x // GRID_SIZE), int(self.y // GRID_SIZE))
        if (not self.path or 
            current_player_grid != self.target_grid or 
            self.path_update_timer >= self.path_update_interval):
            
            self.target_grid = current_player_grid
            self.path = find_path(current_grid, current_player_grid)
            self.path_update_timer = 0
            if self.path:
                self.is_moving_to_cell = True
    
    def update_direction(self):
        """Обновляем направление с учетом диагонального движения"""
        # Если движение строго вертикальное
        if abs(self.last_dx) < 0.1:  # Пороговое значение для определения строго вертикального движения
            if self.last_dy > 0:
                self.direction = 'down'
            else:
                self.direction = 'up'
        # Если есть заметная горизонтальная составляющая
        else:
            if self.last_dx > 0:
                self.direction = 'right'
            else:
                self.direction = 'left'
    
    def get_rect(self):
        return pygame.Rect(self.x - zombie_scale, self.y - zombie_scale,
                         zombie_scale * 1.5, zombie_scale * 2)
    
    def draw(self, screen):
        if self.is_moving_to_cell:
            frame_index = int(self.animation_frame) % len(zombie_textures[self.direction])
            screen.blit(zombie_textures[self.direction][frame_index], 
                       (int(self.x - zombie_scale), int(self.y - zombie_scale)))
        else:
            
            screen.blit(zombie_textures[self.direction][0], 
                       (int(self.x - zombie_scale), int(self.y - zombie_scale)))

# Функция сброса игры
def reset_game():
    global player_pos, player_health, bullets, coins, coins_collected, score, game_over, zombies, zombies_killed, game_start_time, pathfinding_grid, current_player_grid
    player_pos = [WIDTH // 2, HEIGHT // 2]
    player_health = 100
    bullets = []
    coins = []
    zombies = []
    coins_collected = 0
    score = 0
    game_over = False
    zombies_killed = 0
    game_start_time = pygame.time.get_ticks()
    current_player_grid = (int(player_pos[0] // GRID_SIZE), int(player_pos[1] // GRID_SIZE))
    pathfinding_grid = create_pathfinding_grid()

# Функция для отрисовки главного меню
def draw_menu():
    # Анимированный фон (градиент)
    for y in range(HEIGHT):
        color = (
            int(50 + 50 * math.sin(y / 100 + pygame.time.get_ticks() / 2000)),
            int(50 + 50 * math.sin(y / 80 + pygame.time.get_ticks() / 3000)),
            int(100 + 50 * math.sin(y / 120 + pygame.time.get_ticks() / 4000))
        )
        pygame.draw.line(screen, color, (0, y), (WIDTH, y))
    
    # Заголовок
    title_text = large_font.render("Ниндзя против зомби", True, WHITE)
    shadow_text = large_font.render("Ниндзя против зомби", True, BLACK)
    
    # Тень текста
    screen.blit(shadow_text, (WIDTH // 2 - title_text.get_width() // 2 + 3, 
                            HEIGHT // 4 - title_text.get_height() // 2 + 3))
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 
                           HEIGHT // 4 - title_text.get_height() // 2))
    
    # Кнопки
    start_button.draw(screen)
    scores_button.draw(screen)
    quit_button.draw(screen)

# Функция для отрисовки выбора уровня
def draw_level_select():
    screen.fill(DARK_BLUE)
    
    title_text = large_font.render("Выберите уровень", True, WHITE)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 30))
    
    # Размеры и отступы для мини-карт
    map_width = 200
    map_height = 200
    map_padding = 30  # Отступ между картами
    total_maps_width = len(levels) * map_width + (len(levels) - 1) * map_padding
    start_x = (WIDTH - total_maps_width) // 2
    
    # Отрисовка мини-карт уровней с отступами
    for i, level in enumerate(levels):
        x = start_x + i * (map_width + map_padding)
        y = HEIGHT // 3 - 50
        
        # Рамка уровня
        pygame.draw.rect(screen, WHITE, (x - 5, y - 5, map_width + 10, map_height + 10), 2, border_radius=10)
        
        # Мини-карта
        pygame.draw.rect(screen, GRAY, (x, y, map_width, map_height))
        
        # Стены на мини-карте
        for wall in level.walls:
            scaled_wall = pygame.Rect(
                x + wall.x // 4,
                y + wall.y // 3,
                wall.width // 4,
                wall.height // 3
            )
            pygame.draw.rect(screen, DARK_GRAY, scaled_wall)
    
    # Параметры для кнопок
    button_width = 200
    button_height = 100
    button_padding = 30  
    total_buttons_width = len(levels) * button_width + (len(levels) - 1) * button_padding
    buttons_start_x = (WIDTH - total_buttons_width) // 2
    
    # Позиционирование кнопок
    level1_button.rect.x = buttons_start_x
    level1_button.rect.y = HEIGHT // 2 + 70
    level1_button.rect.width = button_width
    level1_button.rect.height = button_height
    
    level2_button.rect.x = buttons_start_x + button_width + button_padding
    level2_button.rect.y = HEIGHT // 2 + 70
    level2_button.rect.width = button_width
    level2_button.rect.height = button_height
    
    level3_button.rect.x = buttons_start_x + 2 * (button_width + button_padding)
    level3_button.rect.y = HEIGHT // 2 + 70
    level3_button.rect.width = button_width
    level3_button.rect.height = button_height

    back_button.rect.y = HEIGHT - 100
    
    # Отрисовка кнопок
    level1_button.draw(screen)
    level2_button.draw(screen)
    level3_button.draw(screen)
    back_button.draw(screen)

# Функция для отрисовки таблицы рекордов
def draw_leaderboard():
    screen.fill(DARK_BLUE)
    
    title_text = large_font.render("Таблица рекордов", True, WHITE)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 50))
    
    scores = load_scores()
    
    if not scores:
        no_scores_text = font.render("Нет сохраненных рекордов", True, WHITE)
        screen.blit(no_scores_text, (WIDTH // 2 - no_scores_text.get_width() // 2, HEIGHT // 2))
    else:
        for i, (date, time, score, attempt) in enumerate(scores[:10]):  # Показываем топ-10
            score_text = small_font.render(
                f"{i+1}. {date} | {time} | Очки: {score} | #{attempt}", 
                True, WHITE
            )
            screen.blit(score_text, (WIDTH // 2 - 250, 150 + i * 40))
    
    leaderboard_back_button.draw(screen)
    clear_button.draw(screen)

def move_player(dx, dy):
    
    # Сохраняем исходную позицию
    orig_x, orig_y = player_pos[0], player_pos[1]
    
    # Создаем прямоугольник игрока для проверки коллизий
    player_rect = pygame.Rect(
        orig_x - player_scale,
        orig_y - player_scale,
        player_scale * 1.5,
        player_scale * 2
    )
    
    # Движение по X
    new_rect_x = player_rect.copy()
    new_rect_x.x += dx
    
    # Проверка границ экрана по X
    if new_rect_x.left < 0:
        dx = -player_rect.left  # Корректируем движение до границы
    elif new_rect_x.right > WIDTH:
        dx = WIDTH - player_rect.right
    
    # Проверка столкновений со стенами по X
    collision_x = False
    for wall in walls:
        if new_rect_x.colliderect(wall):
            collision_x = True
            # Определяем направление коллизии
            if dx > 0:  # Движение вправо
                dx = wall.left - player_rect.right
            elif dx < 0:  # Движение влево
                dx = wall.right - player_rect.left
            break
    
    # Применяем движение по X
    player_rect.x += dx
    player_pos[0] = player_rect.x + player_scale
    
    # Движение по Y
    new_rect_y = player_rect.copy()
    new_rect_y.y += dy
    
    # Проверка границ экрана по Y
    if new_rect_y.top < 0:
        dy = -player_rect.top
    elif new_rect_y.bottom > HEIGHT:
        dy = HEIGHT - player_rect.bottom
    
    # Проверка столкновений со стенами по Y
    collision_y = False
    for wall in walls:
        if new_rect_y.colliderect(wall):
            collision_y = True
            # Определяем направление коллизии
            if dy > 0:  # Движение вниз
                dy = wall.top - player_rect.bottom
            elif dy < 0:  # Движение вверх
                dy = wall.bottom - player_rect.top
            break
    
    # Применяем движение по Y
    player_rect.y += dy
    player_pos[1] = player_rect.y + player_scale

def draw_grid():
    """Отрисовывает сетку на экране"""
    for x in range(0, WIDTH, GRID_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y), 1)

# Игровой цикл
clock = pygame.time.Clock()
running = True

while running:
    mouse_pos = pygame.mouse.get_pos()
    
    # Обновление кнопок
    if game_state == MENU:
        start_button.check_hover(mouse_pos)
        scores_button.check_hover(mouse_pos)
        quit_button.check_hover(mouse_pos)
    elif game_state == LEVEL_SELECT:
        level1_button.check_hover(mouse_pos)
        level2_button.check_hover(mouse_pos)
        level3_button.check_hover(mouse_pos)
        back_button.check_hover(mouse_pos)
    elif game_state == LEADERBOARD:
        leaderboard_back_button.check_hover(mouse_pos)
        clear_button.check_hover(mouse_pos)
    
    start_button.update()
    scores_button.update()
    quit_button.update()
    level1_button.update()
    level2_button.update()
    level3_button.update()
    back_button.update()
    leaderboard_back_button.update()
    clear_button.update()
    
    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == MENU:
                if start_button.is_clicked(mouse_pos, event):
                    game_state = LEVEL_SELECT
                elif scores_button.is_clicked(mouse_pos, event):
                    game_state = LEADERBOARD
                elif quit_button.is_clicked(mouse_pos, event):
                    running = False
            
            elif game_state == LEVEL_SELECT:
                if level1_button.is_clicked(mouse_pos, event):
                    current_level = levels[0]
                    walls = current_level.walls
                    zombie_speed = current_level.zombie_speed
                    reset_game()
                    pathfinding_grid = create_pathfinding_grid()  
                    game_state = GAME
                elif level2_button.is_clicked(mouse_pos, event):
                    current_level = levels[1]
                    walls = current_level.walls
                    zombie_speed = current_level.zombie_speed
                    reset_game()
                    pathfinding_grid = create_pathfinding_grid()  
                    game_state = GAME
                elif level3_button.is_clicked(mouse_pos, event):
                    current_level = levels[2]
                    walls = current_level.walls
                    zombie_speed = current_level.zombie_speed
                    reset_game()
                    pathfinding_grid = create_pathfinding_grid()  
                    game_state = GAME
                elif back_button.is_clicked(mouse_pos, event):
                    game_state = MENU
            
            elif game_state == LEADERBOARD:
                if leaderboard_back_button.is_clicked(mouse_pos, event):
                    game_state = MENU
                elif clear_button.is_clicked(mouse_pos, event):
                    open('scores.txt', 'w').close()  
            
            elif game_state == GAME_OVER:
                if restart_button.is_clicked(mouse_pos, event):
                    reset_game()
                    game_state = GAME
                elif menu_button.is_clicked(mouse_pos, event):
                    game_state = MENU
                elif next_level_button.is_clicked(mouse_pos, event) and current_level.num < len(levels): # type: ignore
                    # Переходим на следующий уровень
                    current_level = levels[current_level.num]  # Индекс равен номеру уровня (нумерация с 1) # type: ignore
                    walls = current_level.walls
                    zombie_speed = current_level.zombie_speed
                    reset_game()
                    pathfinding_grid = create_pathfinding_grid()
                    game_state = GAME

    # Отрисовка в зависимости от состояния игры
    if game_state == MENU:
        draw_menu()
    elif game_state == LEVEL_SELECT:
        draw_level_select()
    elif game_state == LEADERBOARD:
        draw_leaderboard()
    elif game_state == GAME:
        
        if not game_over:
            # Движение игрока
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            
            if keys[pygame.K_w]:
                dy -= player_speed
            if keys[pygame.K_s]:
                dy += player_speed
            if keys[pygame.K_a]:
                dx -= player_speed
            if keys[pygame.K_d]:
                dx += player_speed
        
           
            if dx != 0 or dy != 0:
                player_direction = [dx, dy]
            
            if dx != 0 and dy != 0:
                factor = player_speed / math.sqrt(dx * dx + dy * dy)
                dx *= factor
                dy *= factor
            
            if dx != 0 or dy != 0:
                move_player(dx, dy)
                current_player_grid = (int(player_pos[0] // GRID_SIZE), int(player_pos[1] // GRID_SIZE))
        
            # Обновляем анимацию игрока
            player_animation.update(dx, dy)
            
            # Стрельба
            if keys[pygame.K_SPACE] and shoot_cooldown <= 0 and (player_direction[0] != 0 or player_direction[1] != 0):
                
                dir_len = math.sqrt(player_direction[0] ** 2 + player_direction[1] ** 2)
                if dir_len > 0:
                    norm_dx = player_direction[0] / dir_len
                    norm_dy = player_direction[1] / dir_len
                    
                    bullet_x = player_pos[0] + norm_dx * player_scale
                    bullet_y = player_pos[1] + norm_dy * player_scale
                    bullets.append([bullet_x, bullet_y, norm_dx, norm_dy])
                    shoot_cooldown = shoot_delay
            
            if shoot_cooldown > 0:
                shoot_cooldown -= 1
            
            # Спавн монет
            coin_spawn_timer += 1
            if coin_spawn_timer >= coin_spawn_interval and len(coins) < 5:
                while True:
                    coin_x = random.randint(coin_radius, WIDTH - coin_radius)
                    coin_y = random.randint(coin_radius, HEIGHT - coin_radius)
                    coin_rect = pygame.Rect(coin_x - coin_radius, coin_y - coin_radius,
                                            coin_radius * 2, coin_radius * 2)
                    
                    valid_position = True
                    for wall in walls:
                        if wall.colliderect(coin_rect):
                            valid_position = False
                            break
                    
                    if valid_position:
                        coins.append([coin_x, coin_y])
                        break
                coin_spawn_timer = 0
            
            # Спавн зомби
            zombie_spawn_timer += 1
            if zombie_spawn_timer >= zombie_spawn_interval and len(zombies) < 10:  # Увеличил лимит зомби
                # Выбираем случайную сторону экрана (0-3: верх, право, низ, лево)
                side = random.randint(0, 3)
                
                if side == 0:  # Верх
                    grid_x = random.randint(0, WIDTH // GRID_SIZE - 1)
                    grid_y = -1
                elif side == 1:  # Право
                    grid_x = WIDTH // GRID_SIZE
                    grid_y = random.randint(0, HEIGHT // GRID_SIZE - 1)
                elif side == 2:  # Низ
                    grid_x = random.randint(0, WIDTH // GRID_SIZE - 1)
                    grid_y = HEIGHT // GRID_SIZE
                else:  # Лево
                    grid_x = -1
                    grid_y = random.randint(0, HEIGHT // GRID_SIZE - 1)
                
                # Создаем зомби и сразу задаем ему путь к игроку
                zombie = Zombie(grid_x, grid_y)
                zombie.path = find_path((grid_x, grid_y), current_player_grid) # type: ignore
                if zombie.path:  # Если путь найден - сразу начинаем движение
                    zombie.is_moving_to_cell = True
                zombies.append(zombie)
                zombie_spawn_timer = 0
            
            # Обновление зомби
            for zombie in zombies[:]:
                zombie.update()
                
                # Проверка столкновения с игроком (квадратные хитбоксы)
                player_rect = pygame.Rect(player_pos[0] - player_scale,
                                        player_pos[1] - player_scale,
                                        player_scale * 2, player_scale * 2)
                if player_rect.colliderect(zombie.get_rect()):
                    if zombie_damage_cooldown <= 0:
                        player_health -= 10
                        zombie_damage_cooldown = 60  # 1 секунда задержки
                        if player_health <= 0:
                            game_over = True
            
            if zombie_damage_cooldown > 0:
                zombie_damage_cooldown -= 1
            
            # Движение пуль
            for bullet in bullets[:]:
                bullet[0] += bullet[2] * bullet_speed
                bullet[1] += bullet[3] * bullet_speed
                
                if (bullet[0] < 0 or bullet[0] > WIDTH or
                        bullet[1] < 0 or bullet[1] > HEIGHT):
                    bullets.remove(bullet)
                    continue
                
                bullet_rect = pygame.Rect(bullet[0] - bullet_radius, bullet[1] - bullet_radius,
                                        bullet_radius * 2, bullet_radius * 2)
                
                # Проверка столкновения со стенами
                for wall in walls:
                    if wall.colliderect(bullet_rect):
                        bullets.remove(bullet)
                        break
                else:  # Если не было столкновения со стенами
                    # Проверка столкновения с зомби
                    for zombie in zombies[:]:
                        if bullet_rect.colliderect(zombie.get_rect()):
                            zombies_killed += 1  
                            if bullet in bullets:
                                bullets.remove(bullet)
                            if zombie in zombies:
                                zombies.remove(zombie)
                            score += 10
                            break
            
            # Отрисовка
            screen.fill(GRAY)
            
            if show_grid:
                draw_grid()
            
            for wall in walls:
                if wall_texture:
                    for x in range(wall.x, wall.x + wall.width, wall_texture.get_width()):
                        for y in range(wall.y, wall.y + wall.height, wall_texture.get_height()):
                            screen.blit(wall_texture, (x, y))
                else:
                    pygame.draw.rect(screen, DARK_GRAY, wall)
            
            if not game_over:
                # Отрисовка монет
                for coin in coins:
                    screen.blit(coin_texture, (int(coin[0] - coin_radius), int(coin[1] - coin_radius)))
                
                # Проверка сбора монет
                player_rect = pygame.Rect(player_pos[0] - player_scale, player_pos[1] - player_scale,
                                        player_scale * 2, player_scale * 2)
                for coin in coins[:]:
                    coin_rect = pygame.Rect(coin[0] - coin_radius, coin[1] - coin_radius,
                                            coin_radius * 2, coin_radius * 2)
                    if player_rect.colliderect(coin_rect):
                        coins.remove(coin)
                        coins_collected += 1
                
                # Отрисовка пуль
                for bullet in bullets:
                    screen.blit(bullet_texture, (int(bullet[0] - bullet_radius), int(bullet[1] - bullet_radius)))
                
                # Отрисовка зомби
                for zombie in zombies:
                    zombie.draw(screen)
                
                # Отрисовка игрока с текущей текстурой
                screen.blit(player_animation.get_current_frame(),
                            (int(player_pos[0] - player_scale), int(player_pos[1] - player_scale)))
            
            # Отрисовка здоровья
            health_text = font.render(f"Здоровье: {player_health}", True, WHITE)
            screen.blit(health_text, (10, 10))
            
            # Отрисовка счета
            score_text = font.render(f"Счет: {score}", True, WHITE)
            screen.blit(score_text, (10, 50))
            
            # Отрисовка собранных монет
            coins_text = font.render(f"Монеты: {coins_collected}", True, WHITE)
            screen.blit(coins_text, (10, 90))

            if current_level and zombies_killed >= current_level.zombies_to_kill:
                # Расчет итогового счета с учетом времени
                time_elapsed = (pygame.time.get_ticks() - game_start_time) / 1000  # в секундах
                time_bonus = max(0, current_level.time_limit - time_elapsed) / current_level.time_limit
                final_score = int(score * (current_level.coefficient + time_bonus))
                
                # Сохранение результата
                now = datetime.now()
                add_score(now.strftime("%d.%m.%Y"), now.strftime("%H:%M:%S"), final_score)
                
                game_state = GAME_OVER
        else:
            # Отрисовка экрана завершения игры
            game_over_text = large_font.render("Игра окончена", True, WHITE)
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 150))
            
            stats_text1 = font.render(f"Ваш счет: {score}", True, WHITE)
            screen.blit(stats_text1, (WIDTH // 2 - stats_text1.get_width() // 2, HEIGHT // 2 - 50))
            
            stats_text2 = font.render(f"Собрано монет: {coins_collected}", True, WHITE)
            screen.blit(stats_text2, (WIDTH // 2 - stats_text2.get_width() // 2, HEIGHT // 2))
            
            # Отрисовка кнопки рестарта
            restart_button.draw(screen)
            pass
    elif game_state == GAME_OVER:
        screen.fill(DARK_BLUE)
        
        game_over_text = large_font.render("Уровень пройден!", True, WHITE)
        screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, 100))
        
        # Статистика
        stats = [
            f"Уничтожено зомби: {zombies_killed}/{current_level.zombies_to_kill}", # type: ignore
            f"Базовый счет: {score}",
            f"Итоговый счет: {final_score}"
        ]
        
        for i, stat in enumerate(stats):
            text = font.render(stat, True, WHITE)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, 200 + i*40))
        
        # Показываем кнопку следующего уровня только если это не последний уровень
        if current_level.num < len(levels): # type: ignore
            next_level_button.draw(screen)
        restart_button.draw(screen)
        menu_button.draw(screen)

        pass
    
    if restart_button.is_clicked(mouse_pos, event): # type: ignore
        reset_game()
        game_state = GAME
    elif menu_button.is_clicked(mouse_pos, event): # type: ignore
        game_state = MENU
        
    pygame.display.flip()
    clock.tick(60)

pygame.quit()