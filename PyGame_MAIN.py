import pygame
import os #нужен чтобы папка не потерялась внутри системы
import random
import math
import json
import heapq


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
font = pygame.font.SysFont("arial", 18) #arial для всего
font_smiles = pygame.font.SysFont("segoeuiemoji", 22) #для иконок и смайликов
r_hex = 26
HEX_GRID_WIDTH, HEX_GRID_HEIGHT = screen.get_size()
HEX_GRID_RADIUS = r_hex


"""ДЕЛАЕМ ИЗ КАРТИНОК SURFACES:"""

path_stonewall1 = os.path.join(textures_dir, "stoneWall1.png")
stonewall1_img = pygame.image.load(path_stonewall1).convert_alpha()
hitbox_stonewall1 = pygame.Rect(x, 30, stonewall1_img.get_width(), stonewall1_img.get_height())

path_ant_house = os.path.join(textures_dir, "muraveynik.png")
ant_house_img = pygame.image.load(path_ant_house).convert_alpha()

path_ferma = os.path.join(textures_dir, "ferma.png")
ferma_img = pygame.image.load(path_ferma).convert_alpha()

path_stone_farm = os.path.join(textures_dir, "kamenolomna.png")
stone_farm_img = pygame.image.load(path_stone_farm).convert_alpha()

path_map_img = os.path.join(textures_dir, "MainMap.png")
map_img = pygame.image.load(path_map_img).convert_alpha()
scaled_map_img = pygame.transform.scale(map_img, screen.get_size())


kadry_muravya = [
    pygame.image.load(
        os.path.join(textures_dir, f"ant{i}.png")
    ).convert_alpha()
    for i in range(1, 4)
]

target = pygame.Rect(300, 0, 160, 280)
collision = hitbox_stonewall1.colliderect(target)
pygame.draw.rect(screen, (255 * collision, 255, 0), target)

"""stonewall1_img = pygame.transform.scale(stonewall1_img,
                                        (stonewall1_img.get_width() * 2,
                                         stonewall1_img.get_height() * 2)) НЕОПТИМИЗИРОВАННЫЙ ВАРИАНТ ТОЛЬКО ЧТО-ТО ОЧЕНЬ ВАЖНОЕ"""


#ФУНКЦИЯ ДЛЯ ГРАМОТНОГО МАСШТАБИРОВАНИЯ ПОД РАЗМЕР HEXа
def scale_building_image(image, target_width):
    target_height = int(image.get_height() * (target_width / image.get_width()))
    return pygame.transform.scale(image, (int(target_width), target_height))



"""КЛАССЫ:"""
#HUD
class HUD:
    def __init__(self, resource_manager, width_hud, height_hud, building_images, resource_emojis):
        self.resource_manager = resource_manager
        self.width_hud = width_hud
        self.height_hud = height_hud
        self.hud_colour = (174, 219, 242, 240) #последнее прозрачность, пока так так как иначе видно hexы
        self.building_images = building_images
        self.selected_tile = None
        
        self.resource_icons = {
            name: font_smiles.render(emoji, True, (30, 30, 30))
            for name, emoji in resource_emojis.items()
        }
        
        #Панель ресурсов:
        self.resources_surface = pygame.Surface((width_hud, height_hud * 0.04), pygame.SRCALPHA)
        self.resources_surface.fill(self.hud_colour)
        
        #Панель строений:
        self.build_surface = pygame.Surface((width_hud * 0.15, height_hud * 0.25), pygame.SRCALPHA)
        self.build_surface.fill(self.hud_colour)
        
        #Выбрать HUD:
        self.select_surface = pygame.Surface((width_hud * 0.3, height_hud * 0.2), pygame.SRCALPHA)
        self.select_surface.fill(self.hud_colour)
        self.tiles = self.create_build_hud()
        
        self.resources_rect = self.resources_surface.get_rect(topleft=(0, 0))
        self.build_rect = self.build_surface.get_rect(topleft=(width_hud * 0.84, height_hud * 0.74))
        self.select_rect = self.select_surface.get_rect(topleft=(width_hud * 0.01, height_hud * 0.79))
    
    def create_build_hud(self):
        x_start = self.width_hud * 0.84 + 15
        render_pos = [x_start, self.height_hud * 0.74 + 15]
        tiles = []
        object_width = self.build_surface.get_width() // 3
        
        for name, image in self.building_images.items():
            icon = self.scale_image(image, w=object_width)
            rect = icon.get_rect(topleft = render_pos)
            
            tiles.append({
                "name": name,
                "icon": icon,
                "rect": rect
            })
            
            render_pos[0] += object_width + 15
            if render_pos[0] + object_width > self.width_hud * 0.99: #переносим на новую строчку вниз если вылазит за правый край экрана
                render_pos[0] = x_start
                render_pos[1] += icon.get_height() + 15
        return tiles
    
    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_action = pygame.mouse.get_pressed()
        
        if mouse_action[2]:
            self.selected_tile = None
        
        for tile in self.tiles:
            if tile["rect"].collidepoint(mouse_pos):
                if mouse_action[0]:
                    self.selected_tile = tile
    
    def draw(self, screen, unit_count = 0, max_units = 0):
        screen.blit(self.resources_surface, (0, 0))
        screen.blit(self.build_surface, (self.width_hud * 0.84, self.height_hud * 0.74))
        screen.blit(self.select_surface, (self.width_hud * 0.01, self.height_hud * 0.79))
        
        for tile in self.tiles:
            screen.blit(tile["icon"], tile["rect"].topleft)
        
        if self.selected_tile is not None:
            pygame.draw.rect(screen, (255, 255, 0), self.selected_tile["rect"], 3)
        
        #Прочее, текст и так далее:
        units_text = font.render(f"Ячейки юнитов: {unit_count}/{max_units}", True, (20, 20, 20))
        units_rect = units_text.get_rect(midleft=(20, self.resources_rect.centery))
        screen.blit(units_text, units_rect)

        
        #Ресурсы:
        pos = self.width_hud - 420
        for resource, resource_value in self.resource_manager.resources.items():
            if resource in self.resource_icons:
                icon = self.resource_icons[resource]
                icon_rect = icon.get_rect(midleft=(pos, self.resources_rect.centery))
                screen.blit(icon, icon_rect)
                text_x = icon_rect.right + 8
            else:
                text_x = pos
            
            text_surface = font.render(f"{resource}: {resource_value}", True, (20, 20, 20))
            text_rect = text_surface.get_rect(midleft=(text_x, self.resources_rect.centery))
            screen.blit(text_surface, text_rect)
            pos += 180
    
    
    def scale_image(self, image, w=None, h=None):
        if (w == None) and (h == None):
            pass
        elif h is None:
            scale = w / image.get_width()
            h = scale * image.get_height()
            image = pygame.transform.scale(image, (int(w), int(h)))
        elif w is None:
            scale = h / image.get_height()
            w = scale * image.get_width()
            image = pygame.transform.scale(image, (int(w), int(h)))
        else:
            image = pygame.transform.scale(image, (int(w), int(h)))
        
        return image
    
    def is_mouse_over(self, mouse_pos):
        return(
            self.resources_rect.collidepoint(mouse_pos)
            or self.build_rect.collidepoint(mouse_pos)
            or self.select_rect.collidepoint(mouse_pos)
        )


#Resource Manager
class ResourceManager:
    def __init__(self):
        #Ресурсы:
        self.resources = {
            "wood": 40,
            "stone": 40
        }
        
        #Стоимость постройки:
        self.costs = {
            "Stone_Farm": {"wood": 15, "stone": 3},
            "Wood_Farm": {"wood": 3, "stone": 15},
            "ant_house": {"wood": 20, "stone": 20}
        }
    
    def apply_cost_to_resource(self, building):
        for resource, cost in self.costs[building].items():
            self.resources[resource] -= cost
        
    def is_affordable(self, building):
        b_affordable = True
        for resource, cost in self.costs[building].items():
            if cost > self.resources[resource]:
                b_affordable = False
        return b_affordable


#СТРОЕНИЯ:
#Муравейник:
class Ant_House:
    def __init__(self, tile, resource_manager):
        self.tile = tile
        self.image = scale_building_image(ant_house_img, tile.radius * 1.8)
        self.name = "ant_house"
        self.rect = self.image.get_rect(center = tile.center)
        self.resource_manager = resource_manager
        self.resource_manager.apply_cost_to_resource(self.name)
        self.unit_slots = 5
        self.production = {"wood": 7, "stone": 7}
    
    def produce_per_turn(self):
        for resource, amount in self.production.items():
            self.resource_manager.resources[resource] += amount
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)

#Ферма:
class WoodFarm:
    def __init__(self, tile, resource_manager):
            self.tile = tile
            self.image = scale_building_image(ferma_img, tile.radius * 1.8)
            self.name = "Wood_Farm"
            self.rect = self.image.get_rect(center = tile.center)
            self.resource_manager = resource_manager
            self.resource_manager.apply_cost_to_resource(self.name)
            self.unit_slots = 0
            self.production = {"wood": 5}
    
    def produce_per_turn(self):
        for resource, amount in self.production.items():
            self.resource_manager.resources[resource] += amount
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)

#Каменоломня:
class StoneFarm:
    def __init__(self, tile, resource_manager):
            self.tile = tile
            self.image = scale_building_image(stone_farm_img, tile.radius * 1.8)
            self.name = "Stone_Farm"
            self.rect = self.image.get_rect(center = tile.center)
            self.resource_manager = resource_manager
            self.resource_manager.apply_cost_to_resource(self.name)
            self.unit_slots = 0
            self.production = {"stone": 5}
    
    def produce_per_turn(self):
        for resource, amount in self.production.items():
            self.resource_manager.resources[resource] += amount
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)

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
        pelmeshki.ostalos_hodov = pelmeshki.prohodimost
        pelmeshki.uron = dannye["uron"]
        pelmeshki.bronya = dannye.get("bronya", 0)
        pelmeshki.kletka = kletka
        pelmeshki.pozitsiya = pygame.math.Vector2(kletka.center)
        pelmeshki.marshrut = []
        pelmeshki.vremya_animatsii = 0.0
        pelmeshki.skorost_dvizheniya = 160
        pelmeshki.ugol = 0

    def narisovat(pelmeshki, poverhnost, kadry):
        if pelmeshki.zdorovie <= 0:
            return

        if pelmeshki.marshrut:
            nomer = int(pelmeshki.vremya_animatsii / 0.12) % len(kadry)
        else:
            nomer = 0

        kartinka = pygame.transform.rotate(
            kadry[nomer],
            pelmeshki.ugol
        )

        mesto = kartinka.get_rect(center=(
            round(pelmeshki.pozitsiya.x),
            round(pelmeshki.pozitsiya.y)
        ))

        poverhnost.blit(kartinka, mesto)

    def peremestitsya(pelmeshki, novaya_kletka):
        if pelmeshki.zdorovie <= 0 or pelmeshki.marshrut:
            return False

        if novaya_kletka is None:
            return False

        koord = (novaya_kletka.col, novaya_kletka.row)
        dostupnye, otkuda = nayti_dostupnye_kletki(pelmeshki)

        if koord not in dostupnye:
            return False

        stoimost = dostupnye[koord]
        nachalo = (pelmeshki.kletka.col, pelmeshki.kletka.row)

        put = []
        tekushchaya = koord

        while tekushchaya != nachalo:
            put.append(hex_grid[tekushchaya])
            tekushchaya = otkuda[tekushchaya]

        put.reverse()

        pelmeshki.ostalos_hodov -= stoimost
        pelmeshki.marshrut = put
        pelmeshki.vremya_animatsii = 0.0

        return True

    def obnovit(pelmeshki, delta_time):
        if pelmeshki.zdorovie <= 0 or not pelmeshki.marshrut:
            return

        pelmeshki.vremya_animatsii += delta_time

        sleduyushchaya = pelmeshki.marshrut[0]

        napravlenie = sleduyushchaya.center - pelmeshki.pozitsiya
        rasstoyanie = napravlenie.length()
        shag = pelmeshki.skorost_dvizheniya * delta_time

        if rasstoyanie > 0:
            pelmeshki.ugol = math.degrees(
                math.atan2(-napravlenie.y, napravlenie.x)
            ) - 90

        if rasstoyanie <= shag:
            pelmeshki.pozitsiya = sleduyushchaya.center.copy()
            pelmeshki.kletka = sleduyushchaya
            pelmeshki.marshrut.pop(0)

            koord = (sleduyushchaya.col, sleduyushchaya.row)
            tip = provintsii_kletok[koord]

            if tipy_provintsiy[tip].get("smertelna", False):
                pelmeshki.umeret()

        else:
            pelmeshki.pozitsiya += napravlenie.normalize() * shag

    def umeret(pelmeshki):
        if pelmeshki.zdorovie <= 0:
            return

        pelmeshki.zdorovie = 0
        pelmeshki.marshrut.clear()

        effekty_smerti.append({
            "pozitsiya": pelmeshki.pozitsiya.copy(),
            "vremya": 0.0
        })
#Логика получения урона

def nanesti_uron(atakuyushiy, zashchitnik):
    if atakuyushiy.zdorovie <= 0 or zashchitnik.zdorovie <= 0:
        return

    fakt_uron = max(
        0,
        atakuyushiy.uron * (1 - zashchitnik.bronya / 100)
    )

    if fakt_uron >= zashchitnik.zdorovie:
        zashchitnik.umeret()
    else:
        zashchitnik.zdorovie -= fakt_uron



#HEX TOOL:

#HEX TOOL (MAIN HEX):
class Hex: #$\sqrt{\Delta x^2 + \Delta y^2}$)
    def __init__(self, row, col, hex_x, hex_y, hex_radius):
        self.building = None
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

def nayti_sosedey(kletka, hex_grid):
    col = kletka.col
    row = kletka.row

    if col % 2 == 0:
        sdvigi = [-1, 0]
    else:
        sdvigi = [0, 1]

    koordinaty = [
        (col, row - 1),
        (col, row + 1),
        (col - 1, row + sdvigi[0]),
        (col - 1, row + sdvigi[1]),
        (col + 1, row + sdvigi[0]),
        (col + 1, row + sdvigi[1])
    ]

    return [
        hex_grid[koord]
        for koord in koordinaty
        if koord in hex_grid
    ]

def nayti_dostupnye_kletki(muravey):
    nachalo = (muravey.kletka.col, muravey.kletka.row)

    ochered = [(0, nachalo)]
    rashody = {nachalo: 0}
    otkuda = {}

    zanyatye = {
        (drugoy.kletka.col, drugoy.kletka.row)
        for drugoy in muravi
        if drugoy is not muravey and drugoy.zdorovie > 0
    }

    while ochered:
        rashod, koord = heapq.heappop(ochered)

        if rashod > rashody[koord]:
            continue

        if koord != nachalo:
            tip = provintsii_kletok[koord]
            if tipy_provintsiy[tip].get("smertelna", False):
                continue

        for sosed in nayti_sosedey(hex_grid[koord], hex_grid):
            novye_koord = (sosed.col, sosed.row)

            if novye_koord in zanyatye:
                continue

            tip = provintsii_kletok[novye_koord]
            svoystva = tipy_provintsiy[tip]

            if not svoystva.get("prohodima", True):
                continue

            cena = svoystva["stoimost"]

            if cena is None or cena < 0:
                continue

            novyy_rashod = rashod + cena

            if novyy_rashod > muravey.ostalos_hodov:
                continue

            if novyy_rashod < rashody.get(novye_koord, float("inf")):
                rashody[novye_koord] = novyy_rashod
                otkuda[novye_koord] = koord
                heapq.heappush(ochered, (novyy_rashod, novye_koord))

    rashody.pop(nachalo)
    return rashody, otkuda

"""Инициализация:"""
hex_grid = create_hex_grid(HEX_GRID_WIDTH, HEX_GRID_HEIGHT, HEX_GRID_RADIUS)

put_karty = os.path.join(data_dir, "karta_provintsiy.json")

provintsii_kletok = {
    koord: "polya" for koord in hex_grid
}

if os.path.exists(put_karty):
    with open(put_karty, "r", encoding="utf-8") as fail:
        sohranennye = json.load(fail)

    for koord, tip in sohranennye.items():
        col, row = map(int, koord.split(","))

        if (col, row) in hex_grid and tip in tipy_provintsiy:
            provintsii_kletok[(col, row)] = tip

setka_sloy = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

muravi = [
    Muravey("rabochiy", hex_grid[(4, 4)]),
    Muravey("soldat", hex_grid[(6, 4)])
]

vybrannyy_muravey = None



resource_emojis = {
    "wood": "🌲",
    "stone": "🪨",
}

resource_manager = ResourceManager()

building_textures = {
    "Stone_Farm": stone_farm_img,
    "Wood_Farm": ferma_img,
    "ant_house": ant_house_img,
}

BUILDING_CLASSES = {
    "Stone_Farm": StoneFarm,
    "Wood_Farm": WoodFarm,
    "ant_house": Ant_House,
}

buildings = []

hud = HUD(resource_manager, 1600, 900, building_textures, resource_emojis)

redaktor = False
tip_kisti = "les"

knopki_tipov = {
    pygame.K_1: "polya",
    pygame.K_2: "les",
    pygame.K_3: "gory",
    pygame.K_4: "pustynya",
    pygame.K_5: "plyazh",
    pygame.K_6: "voda"
}

cveta_tipov = {
    "polya": (120, 200, 100, 90),
    "les": (20, 110, 40, 110),
    "gory": (120, 120, 120, 110),
    "pustynya": (230, 180, 70, 110),
    "plyazh": (240, 220, 140, 110),
    "voda": (30, 100, 210, 110)
}

effekty_smerti = []

shrift_smerti = pygame.font.SysFont("arial", 12, bold=True)
tekst_smerti = shrift_smerti.render("Смерть", True, (255, 255, 255))

while running:
    
    hud.update()
    
    delta_time = clock.tick(60) / 1000 #кол-во фпс на рендеринг
    delta_time = max(0.001, min(0.1, delta_time)) #убираем терринг при проблемы с кол-во кадров если слишком много или мало

    for muravey in muravi:
        muravey.obnovit(delta_time)

    x += 50 * delta_time
    mouse_pos = pygame.mouse.get_pos()

    if vybrannyy_muravey is not None:
        if (vybrannyy_muravey.ostalos_hodov <= 0
                or vybrannyy_muravey.zdorovie <= 0):
            vybrannyy_muravey = None

    screen.fill((128, 128, 128)) 
    screen.blit(stonewall1_img, (x, 500))
    screen.blit(scaled_map_img, (0,0))
    
    if hud.is_mouse_over(mouse_pos):
        hovered_tile = None
    else:
        hovered_tile = hex_under_mouse(hex_grid)

    if redaktor and hovered_tile is not None:
        if pygame.mouse.get_pressed()[0]:
            koord = (hovered_tile.col, hovered_tile.row)
            provintsii_kletok[koord] = tip_kisti

    setka_sloy.fill((0, 0, 0, 0))

    if not redaktor and vybrannyy_muravey is not None:
        if vybrannyy_muravey.zdorovie > 0:
            dostupnye, otkuda = nayti_dostupnye_kletki(vybrannyy_muravey)

            for koord in dostupnye:
                kletka = hex_grid[koord]

                pygame.draw.polygon(
                    setka_sloy,
                    (40, 200, 75, 85),
                    kletka.table_points
                )

    if redaktor:
        for koord, tip in provintsii_kletok.items():
            if tip == "polya":
                continue

            kletka = hex_grid[koord]

            pygame.draw.polygon(
                setka_sloy,
                cveta_tipov[tip],
                kletka.table_points
            )

    for tile in hex_grid.values():
        tile.draw(setka_sloy, color=(200, 200, 200, 90), thick=3)

    if hovered_tile is not None:
        hovered_tile.draw(setka_sloy, color=(255, 255, 0, 180), thick=6)

    if not redaktor and vybrannyy_muravey is not None:
        if vybrannyy_muravey.zdorovie > 0:
            pygame.draw.polygon(
                setka_sloy,
                (255, 215, 0, 110),
                vybrannyy_muravey.kletka.table_points
            )

    screen.blit(setka_sloy, (0, 0))

    for building in buildings:
        building.draw(screen)

    for muravey in muravi:
        muravey.narisovat(screen, kadry_muravya)

    for effekt in effekty_smerti[:]:
        effekt["vremya"] += delta_time
        vremya = effekt["vremya"]

        if vremya >= 3.0:
            effekty_smerti.remove(effekt)
            continue

        if vremya < 0.8:
            alfa = int(255 * vremya / 0.8)
        elif vremya < 1.4:
            alfa = 255
        else:
            alfa = int(255 * (1 - (vremya - 1.4) / 1.6))

        nadpis = tekst_smerti.copy()
        nadpis.set_alpha(alfa)

        mesto = nadpis.get_rect(
            center=effekt["pozitsiya"]
        )

        screen.blit(nadpis, mesto)

    test_button = TestButton("КЛИК НА МЕНЯ", 250, 250, True)

    for event in pygame.event.get():
        if event.type == pygame.QUIT: #закрыть полностью игру при нажатие на крестик сверху
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F2:
                redaktor = not redaktor
                print("Редактор:", redaktor)

            if redaktor and event.key in knopki_tipov:
                tip_kisti = knopki_tipov[event.key]
                print("Кисть:", tip_kisti)

            if redaktor and event.key == pygame.K_F5:
                dannye_karty = {
                    f"{col},{row}": tip
                    for (col, row), tip in provintsii_kletok.items()
                    if tip != "polya"
                }

                with open(put_karty, "w", encoding="utf-8") as fail:
                    json.dump(
                        dannye_karty,
                        fail,
                        ensure_ascii=False,
                        indent=2
                    )

                print("Карта сохранена!")

            if event.key == pygame.K_n and not redaktor:
                for muravey in muravi:
                    if muravey.zdorovie > 0:
                        muravey.ostalos_hodov = muravey.prohodimost

                for building in buildings:
                    building.produce_per_turn()

                print("Новый ход!")

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                vybrannyy_muravey = None

            if event.button == 1 and not hud.is_mouse_over(mouse_pos) and not redaktor:
                clicked_tile = hex_under_mouse(hex_grid)

                if clicked_tile is not None:
                    if hud.selected_tile is not None:
                        building_type = hud.selected_tile["name"]
                        coords = (clicked_tile.col, clicked_tile.row)
                        province_type = provintsii_kletok[coords]
                        is_passable = tipy_provintsiy[province_type].get("prohodima", True)

                        if clicked_tile.building is None and is_passable:
                            if resource_manager.is_affordable(building_type):
                                new_building = BUILDING_CLASSES[building_type](clicked_tile, resource_manager)
                                clicked_tile.building = new_building
                                buildings.append(new_building)
                                hud.selected_tile = None
                            else:
                                print("Недостаточно ресурсов для постройки!")
                        else:
                            print("На этой клетке нельзя строить!")
                    else:
                        clicked_ant = None

                        for muravey in muravi:
                            if muravey.kletka is clicked_tile and muravey.zdorovie > 0:
                                clicked_ant = muravey
                                break

                        if clicked_ant is not None:
                            if clicked_ant.ostalos_hodov > 0:
                                vybrannyy_muravey = clicked_ant
                            else:
                                vybrannyy_muravey = None

                        elif vybrannyy_muravey is not None:
                            vybrannyy_muravey.peremestitsya(clicked_tile)

    if hud.selected_tile is not None and hovered_tile is not None and not redaktor:
        building_type = hud.selected_tile["name"]
        preview_img = scale_building_image(
            building_textures[building_type],
            hovered_tile.radius * 1.8
        )
        preview_img.set_alpha(160)
        preview_rect = preview_img.get_rect(center=hovered_tile.center)
        screen.blit(preview_img, preview_rect)

        coords = (hovered_tile.col, hovered_tile.row)
        is_passable = tipy_provintsiy[provintsii_kletok[coords]].get("prohodima", True)
        can_build = (
            hovered_tile.building is None
            and is_passable
            and resource_manager.is_affordable(building_type)
        )
        border_color = (50, 255, 50) if can_build else (255, 60, 60)
        hovered_tile.draw(screen, color=border_color, thick=4)

    unit_count = sum(1 for m in muravi if m.zdorovie > 0)
    max_units = sum(b.unit_slots for b in buildings)
    hud.draw(screen, unit_count, max_units)

    pygame.display.update() #чтобы показывалось изображение

pygame.quit()