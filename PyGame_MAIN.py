import pygame
import os #нужен чтобы папка не потерялась внутри системы
import random
import math
import json


pygame.init()

screen = pygame.display.set_mode((1600, 900)) #разрешение окна (16:9)

main_dir = os.path.dirname(os.path.abspath(__file__))
textures_dir = os.path.join(main_dir, "Textures") 
data_dir = os.path.join(main_dir, "Data")

#Оформление окна:
pygame.display.set_caption("Pygame ANTSBATTLER")
path_game_icon = os.path.join(textures_dir, "GAMEICONANT.png")
game_icon = pygame.image.load(path_game_icon)
pygame.display.set_icon(game_icon)

#JSON парсер:
muravi_json = os.path.join(data_dir, "muravi.json")
with open(muravi_json, "r", encoding="utf-8") as f:
    json_f = json.load(f)
print(json_f)

provintsii_json = os.path.join(data_dir, "tipy_provintsiy.json")

with open(provintsii_json, "r", encoding="utf-8") as fail:
    tipy_provintsiy = json.load(fail)

"""ВАЖНЫЕ ПЕРЕМЕННЫЕ:"""
running = True #нужно чтобы игра сразу не закрывалась
x = 1000
clock = pygame.time.Clock()
delta_time = 0.1
font = pygame.font.Font(None, 18) #Сюда загрузить шрифт
r_hex = 26
HEX_GRID_WIDTH, HEX_GRID_HEIGHT = screen.get_size()
HEX_GRID_RADIUS = r_hex

"""ДЕЛАЕМ ИЗ КАРТИНОК SURFACES:"""

path_stonewall1 = os.path.join(textures_dir, "stoneWall1.png")
stonewall1_img = pygame.image.load(path_stonewall1).convert_alpha()
hitbox_stonewall1 = pygame.Rect(x, 30, stonewall1_img.get_width(), stonewall1_img.get_height())

path_map_img = os.path.join(textures_dir, "MainMap.png")
map_img = pygame.image.load(path_map_img).convert_alpha()
scaled_map_img = pygame.transform.scale(map_img, screen.get_size())


target = pygame.Rect(300, 0, 160, 280)
collision = hitbox_stonewall1.colliderect(target)
pygame.draw.rect(screen, (255 * collision, 255, 0), target)

"""stonewall1_img = pygame.transform.scale(stonewall1_img,
                                        (stonewall1_img.get_width() * 2,
                                         stonewall1_img.get_height() * 2)) НЕОПТИМИЗИРОВАННЫЙ ВАРИАНТ ТОЛЬКО ЧТО-ТО ОЧЕНЬ ВАЖНОЕ"""


"""КЛАССЫ:"""
#Кнопка:
class TestButton:
    def __init__(self, text, x_pos, y_pos, b_enabled):
        self.text = text
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.b_enabled = b_enabled
        self.draw()

    def draw(self):
        button_text = font.render(self.text, True, "black")
        button_rect = pygame.rect.Rect((self.x_pos, self.y_pos), (150, 25)) #2 скобки значения поставить самому
        if self.b_enabled:
            if self.check_if_clicked():
                pygame.draw.rect(screen, "red", button_rect, 0, 5)
            else:
                pygame.draw.rect(screen, "blue", button_rect, 0, 5)
        else:
            pygame.draw.rect(screen, "black", button_rect, 0, 5)
        pygame.draw.rect(screen, "black", button_rect, 2, 5)
        screen.blit(button_text, (self.x_pos + 3, self.y_pos + 3))

    def check_if_clicked(self):
        mouse_pos = pygame.mouse.get_pos()
        left_click = pygame.mouse.get_pressed()
        button_rect = pygame.rect.Rect((self.x_pos, self.y_pos), (150, 25))
        if left_click and button_rect.collidepoint(mouse_pos) and self.b_enabled:
            return True
        else:
            return False
        

#class Муравьёв:
class Muravey:
    def __init__(pelmeshki, tip, kletka):
        dannye = json_f[tip]

        pelmeshki.nazvanie = dannye["nazvanie"]
        pelmeshki.zdorovie = dannye["zdorovie"]
        pelmeshki.prohodimost = dannye["prohodimost"]
        pelmeshki.uron = dannye["uron"]
        pelmeshki.bronya = dannye.get("bronya", 0)
        pelmeshki.kletka = kletka

    def narisovat(pelmeshki, poverhnost, kartinka):
        if pelmeshki.zdorovie <= 0:
            return

        mesto = kartinka.get_rect(center=pelmeshki.kletka.center)
        poverhnost.blit(kartinka, mesto)

    def peremestitsya(pelmeshki, novaya_kletka):
        if pelmeshki.zdorovie <= 0:
            return False

        if novaya_kletka is None:
            return False

        if not pelmeshki.kletka.is_has_neighbor(novaya_kletka):
            return False

        koord = (novaya_kletka.col, novaya_kletka.row)
        tip = provintsii_kletok[koord]
        svoystva = tipy_provintsiy[tip]

        if not svoystva.get("prohodima", True):
            return False

        pelmeshki.kletka = novaya_kletka

        if svoystva.get("smertelna", False):
            pelmeshki.zdorovie = 0

        return True

#Логика получения урона
def nanesti_uron(atakuyushiy, zashchitnik):
    fakt_uron = atakuyushiy.uron * (1 - zashchitnik.bronya / 100)
    zashchitnik.zdorovie = max(0,
    zashchitnik.zdorovie - fakt_uron)




#HEX TOOL:

#HEX TOOL (MAIN HEX):
class Hex: #$\sqrt{\Delta x^2 + \Delta y^2}$)
    def __init__(self, row, col, hex_x, hex_y, hex_radius):
        self.col = col
        self.row = row
        self.center = pygame.math.Vector2(hex_x, hex_y)
        self.neighbor_distance = (hex_radius * 2) ** 2
        self.radius = hex_radius
        
        self.table_points = []
        for i in range(6):
            radius_angle = math.radians(60 * i)
            px = hex_x + hex_radius * math.cos(radius_angle) #координата вершины по x
            py = hex_y + hex_radius * math.sin(radius_angle) #координата вершины по y
            self.table_points.append((px, py))
            
        self.event = None
        self.is_water = False
    
    def is_has_neighbor(self, other_hex): #Проверка если ли соседняя клетка рядом с ней
        if other_hex is None or other_hex == self:
            return False
        
        return self.center.distance_squared_to(other_hex.center) < self.neighbor_distance
    
    def draw(self, surface, color, thick):
        pygame.draw.polygon(surface, color, self.table_points, thick)
        #ЕСЛИ ТАМ ЕСТЬ ИВЕНТ:
        if self.event is not None:
            has_event = font.render("!", True, (255, 230, 0))
            event_rect = has_event.get_rect(center=(self.center.x, self.center.y))
            surface.blit(has_event, event_rect)
            
#HEX TOOL (Создаём саму сетку):
def create_hex_grid(hex_grid_width, hex_grid_height, hex_grid_radius):
    grid = {} #{(col, row): Hex}
    step_x = 1.5 * hex_grid_radius
    step_y = math.sqrt(3) * hex_grid_radius
    
    hex_colons = int(hex_grid_width // step_x) + 1
    hex_rows = int(hex_grid_height // step_y) + 1
    
    for col in range(hex_colons):
        for row in range(hex_rows):
            hex_grid_x = col * step_x + hex_grid_radius
            hex_grid_y = row * step_y + hex_grid_radius
            if col % 2 == 1:
                hex_grid_y += step_y / 2 #сдвигаем нечётный столбец вниз на половину
            if hex_grid_x < hex_grid_width and hex_grid_y < hex_grid_height: #не добавляем hexы за экраном
                grid[(col, row)] = Hex(row, col, hex_grid_x, hex_grid_y, hex_grid_radius)
                
    return grid

#HEX TOOL (Конкретная клетка под курсором мыши):
def hex_under_mouse(grid):
    mouse_pos = pygame.mouse.get_pos()
    m_vec = pygame.math.Vector2(mouse_pos)
    closest_hex = None
    min_dist = float("inf")

    for hex_tile in grid.values():
        dist = hex_tile.center.distance_to(m_vec)
        if dist < min_dist:
            min_dist = dist
            closest_hex = hex_tile
            
    if closest_hex and min_dist <= closest_hex.radius:
        return closest_hex
    return None

"""Инициализация:"""
hex_grid = create_hex_grid(HEX_GRID_WIDTH, HEX_GRID_HEIGHT, HEX_GRID_RADIUS)

provintsii_kletok = {
    koord: "polya" for koord in hex_grid
}

provintsii_kletok[(4, 4)] = "les"
provintsii_kletok[(5, 4)] = "voda"
provintsii_kletok[(6, 4)] = "pustynya"

setka_sloy = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

kartinka_muravya = pygame.image.load(
    os.path.join(textures_dir, "ant1.png")
).convert_alpha()

muravi = [
    Muravey("rabochiy", hex_grid[(4, 4)]),
    Muravey("soldat", hex_grid[(6, 4)])
]

vybrannyy_muravey = None

while running:
    screen.fill((128, 128, 128)) 
    screen.blit(stonewall1_img, (x, 500))
    screen.blit(scaled_map_img, (0,0))
    
    delta_time = clock.tick(60) / 1000 #кол-во фпс на рендеринг
    delta_time = max(0.001, min(0.1, delta_time)) #убираем терринг при проблемы с кол-во кадров если слишком много или мало
    hovered_tile = hex_under_mouse(hex_grid)

    setka_sloy.fill((0, 0, 0, 0))

    for tile in hex_grid.values():
        tile.draw(setka_sloy, color=(200, 200, 200, 90), thick=3)

    if hovered_tile is not None:
        hovered_tile.draw(setka_sloy, color=(255, 255, 0, 180), thick=6)

    screen.blit(setka_sloy, (0, 0))

    for muravey in muravi:
        muravey.narisovat(screen, kartinka_muravya)

    test_button = TestButton("КЛИК НА МЕНЯ", 250, 250, True)
    
    mouse_pos = pygame.mouse.get_pos()
    x += 50 * delta_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                kletka = hex_under_mouse(hex_grid)

                if kletka is not None:
                    nazhatyy_muravey = None

                    for muravey in muravi:
                        if muravey.kletka is kletka and muravey.zdorovie > 0:
                            nazhatyy_muravey = muravey
                            break

                    if nazhatyy_muravey is not None:
                        vybrannyy_muravey = nazhatyy_muravey

                    elif vybrannyy_muravey is not None:
                        vybrannyy_muravey.peremestitsya(kletka)

    """#МЫШКА:
        if event.type == pygame.MOUSEBUTTONDOWN:
            print("КЛИК")
        if event.type == pygame.MOUSEBUTTONUP:
            print("КЛИК КОНЧИЛСЯ")"""
    
    
    
    
    pygame.display.update() #чтобы показывалось изображение
    

pygame.quit()