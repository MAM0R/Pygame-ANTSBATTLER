import pygame #ВИНОВНИК ТОРЖЕСТВА!
import os #нужен чтобы папка не потерялась внутри системы
import random
import math
import json
import heapq #для работы с большой структурой данных
from collections import deque
from menu import MainMenu, MenuBackground



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
units_json = os.path.join(data_dir, "units.json")
with open(units_json, "r", encoding="utf-8") as fail:
    units = json.load(fail)

provintsii_json = os.path.join(data_dir, "tipy_provintsiy.json")

if os.path.exists(provintsii_json):
    with open(provintsii_json, "r", encoding="utf-8") as fail:
        tipy_provintsiy = json.load(fail)
else:
    #Если у кого-то нет файла с типами клеток:
    # Если у кого-то нет файла с типами клеток, игра хотя бы запустится на стандартных настройках.
    tipy_provintsiy = {
        "polya": {"stoimost": 1},
        "les": {"stoimost": 2},
        "gory": {"stoimost": 3},
        "pustynya": {"stoimost": 2},
        "plyazh": {"stoimost": 2},
        "voda": {"stoimost": 0, "smertelna": True}
    }

"""ВАЖНЫЕ ПЕРЕМЕННЫЕ:"""
running = True #нужно чтобы игра сразу не закрывалась
x = 1000
clock = pygame.time.Clock()
delta_time = 0.1
russo_one_path = os.path.join(main_dir, "Fonts", "RussoOne-Regular.ttf")
if not os.path.isfile(russo_one_path):
    russo_one_path = pygame.font.match_font("Russo One")


def zagruzit_russo_one(razmer):
    if russo_one_path:
        return pygame.font.Font(russo_one_path, razmer)
    return pygame.font.SysFont("Russo One", razmer)


font = zagruzit_russo_one(18) #Russo One для всего
font_smiles = pygame.font.SysFont("segoeuiemoji", 22) #для иконок и смайликов
font_count = pygame.font.SysFont("PT Sans", 10, bold=True)
if pygame.font.match_font("PT Sans") is None:
    print("Шрифт PT Sans не установлен, Pygame использует системную замену.")
if russo_one_path is None:
    print("Шрифт Russo One не установлен, Pygame использует системную замену.")
shrifty = {18: font}


def poluchit_shrift(razmer):
    if razmer not in shrifty:
        shrifty[razmer] = zagruzit_russo_one(razmer)
    return shrifty[razmer]


# Размеры шрифтов готовим сразу, а не каждый раз при открытии окна.
for razmer_shrifta in (12, 13, 16, 20, 21, 22, 26, 27, 29, 30, 42):
    poluchit_shrift(razmer_shrifta)

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

# Пол для автобоя загружаем один раз, текстуры не растягиваем.
tekstury_pola_boya = {}
for tip_pola, imya_faila in {
    "les": "battler_les.png",
    "pustynya": "battler_pustinya.png",
    "polya": "battler_polya.png",
    "gory": "battler_gori.png"
}.items():
    put_k_polu = os.path.join(textures_dir, imya_faila)
    if os.path.isfile(put_k_polu):
        tekstury_pola_boya[tip_pola] = pygame.image.load(put_k_polu).convert_alpha()
    else:
        print(f"Не найдена текстура пола автобоя: {imya_faila}")


target = pygame.Rect(300, 0, 160, 280)
collision = hitbox_stonewall1.colliderect(target)
pygame.draw.rect(screen, (255 * collision, 255, 0), target)

"""stonewall1_img = pygame.transform.scale(stonewall1_img,
                                        (stonewall1_img.get_width() * 2,
                                         stonewall1_img.get_height() * 2)) НЕОПТИМИЗИРОВАННЫЙ ВАРИАНТ ТОЛЬКО ЧТО-ТО ОЧЕНЬ ВАЖНОЕ"""


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
        self.turn_icon = font_smiles.render("⏳", True, (30, 30, 30))
        self.unit_icon = font_smiles.render("🐜", True, (30, 30, 30))
        
        
        #Панель ресурсов:
        self.resources_surface = pygame.Surface((width_hud, int(height_hud * 0.04)), pygame.SRCALPHA)
        self.resources_surface.fill(self.hud_colour)
        
        #Панель строений:
        self.build_surface = pygame.Surface((int(width_hud * 0.15), int(height_hud * 0.25)), pygame.SRCALPHA)
        self.build_surface.fill(self.hud_colour)
        
        #Выбрать HUD:
        self.select_surface = pygame.Surface((int(width_hud * 0.3), int(height_hud * 0.2)), pygame.SRCALPHA)
        self.select_surface.fill(self.hud_colour)
        self.tiles = self.create_build_hud()
        
        self.resources_rect = self.resources_surface.get_rect(topleft=(0, 0))
        self.build_rect = self.build_surface.get_rect(topleft=(width_hud * 0.84, height_hud * 0.74))
        self.select_rect = self.select_surface.get_rect(topleft=(width_hud * 0.01, height_hud * 0.79))

        self.recruit_buttons = [
            {
                "unit_type": "rabochiy",
                "title": "Рабочий (12)",
                "rect": pygame.Rect(self.select_rect.left + 16, self.select_rect.top + 52, 215, 110)
            },
            {
                "unit_type": "soldat",
                "title": "Солдат (12)",
                "rect": pygame.Rect(self.select_rect.left + 249, self.select_rect.top + 52, 215, 110)
            }
        ]

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
    
    def draw(self, screen, unit_count = 0, max_units = 0, turn_number=1, selected_ant_house=None):
        screen.blit(self.resources_surface, (0, 0))
        screen.blit(self.build_surface, (self.width_hud * 0.84, self.height_hud * 0.74))
        screen.blit(self.select_surface, (self.width_hud * 0.01, self.height_hud * 0.79))
        
        for tile in self.tiles:
            screen.blit(tile["icon"], tile["rect"].topleft)
        
        if self.selected_tile is not None:
            pygame.draw.rect(screen, (255, 255, 0), self.selected_tile["rect"], 3)

        #Панель найма в Муравейнике:
        if selected_ant_house is not None:
            pygame.draw.rect(screen, (255, 220, 80), self.select_rect, 2)
            free_slots = max(0, max_units - unit_count)
            header = font.render(f"Муравейник  |  Свободно ячеек: {free_slots}", True, (20, 20, 20))
            screen.blit(header, (self.select_rect.left + 16, self.select_rect.top + 14))

            mouse_pos = pygame.mouse.get_pos()
            for btn in self.recruit_buttons:
                unit_type = btn["unit_type"]
                rect = btn["rect"]
                cost = self.resource_manager.unit_costs[unit_type]
                can_afford = self.resource_manager.is_unit_affordable(unit_type)
                needed_slots = 12 * units[unit_type].get("yacheyki", 0)
                has_slot = max_units > 0 and (
                    unit_count + needed_slots <= max_units if needed_slots > 0 else unit_count < max_units
                )
                hovered = rect.collidepoint(mouse_pos)

                if not has_slot:
                    bg_color = (120, 125, 130)
                    border_color = (80, 85, 90)
                    cost_color = (220, 90, 90)
                elif not can_afford:
                    bg_color = (145, 110, 110)
                    border_color = (180, 70, 70)
                    cost_color = (255, 210, 210)
                else:
                    bg_color = (115, 200, 130) if hovered else (85, 175, 105)
                    border_color = (255, 255, 220)
                    cost_color = (20, 35, 20)

                pygame.draw.rect(screen, bg_color, rect, border_radius=8)
                pygame.draw.rect(screen, border_color, rect, 2, border_radius=8)

                title_surf = font.render(btn["title"], True, (15, 20, 15))
                screen.blit(title_surf, title_surf.get_rect(midtop=(rect.centerx, rect.top + 14)))

                unit_data = units[unit_type]
                stats_surf = font.render(
                    f"ХП: {unit_data['zdorovie']} | Урон: {unit_data['uron']}",
                    True, (30, 35, 30)
                )
                screen.blit(stats_surf, stats_surf.get_rect(center=(rect.centerx, rect.centery + 2)))

                cost_text = f"Дер: {cost['wood']}  |  Кам: {cost['stone']}" if has_slot else "Нет ячеек юнитов"
                cost_surf = font.render(cost_text, True, cost_color)
                screen.blit(cost_surf, cost_surf.get_rect(midbottom=(rect.centerx, rect.bottom - 12)))
        else:
            hint = font.render("Кликни по Муравейнику, чтобы нанять войнов", True, (35, 45, 55))
            screen.blit(hint, hint.get_rect(center=self.select_rect.center))
        
        #Прочее, текст и так далее:
        #Верхняя панель:
        turn_icon_rect = self.turn_icon.get_rect(midleft=(20, self.resources_rect.centery))
        screen.blit(self.turn_icon, turn_icon_rect)
        turn_text = font.render(f"Ход: {turn_number}", True, (20, 20, 20))
        turn_rect = turn_text.get_rect(midleft=(turn_icon_rect.right + 8, self.resources_rect.centery))
        screen.blit(turn_text, turn_rect)
        unit_icon_rect = self.unit_icon.get_rect(midleft=(turn_rect.right + 25, self.resources_rect.centery))
        screen.blit(self.unit_icon, unit_icon_rect)
        units_text = font.render(f"Ячейки юнитов: {unit_count}/{max_units}", True, (20, 20, 20))
        units_rect = units_text.get_rect(midleft=(unit_icon_rect.right + 8, self.resources_rect.centery))
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
#Resource Manager:
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

        #Стоимость найма войска:
        self.unit_costs = {
            "rabochiy": {"wood": 10, "stone": 5},
            "soldat": {"wood": 15, "stone": 15}
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
    
    def is_unit_affordable(self, unit_type):
        b_affordable_unit = True
        for resource, cost in self.unit_costs[unit_type].items():
            if cost > self.resources.get(resource, 0):
                b_affordable_unit = False
        return b_affordable_unit
    
    def apply_unit_cost(self, unit_type):
        for resource, cost in self.unit_costs[unit_type].items():
            self.resources[resource] -= cost


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
        self.unit_slots = 60
        self.production = {"wood": 7, "stone": 7}

    def produce_per_turn(self):
        for resource, amount in self.production.items():
            self.resource_manager.resources[resource] += amount

    def draw(self, surface):
        surface.blit(self.image, self.rect)

#Ферма:
#Лесопилка:
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
        if left_click[0] and button_rect.collidepoint(mouse_pos) and self.b_enabled:
            return True
        else:
            return False
        



#Кнопка для пропуска хода:
class EndTurnButton:
    def __init__(self, text, x_pos, y_pos, width, height):
        self.rect = pygame.Rect(x_pos, y_pos, width, height)
        self.text = text
        self.hover = 0.0
        self.pressed = 0.0
    
    def is_hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def handle_click(self, mouse_pos, b_enabled):
        return b_enabled and self.rect.collidepoint(mouse_pos)
    
    def draw(self, surface, turn_number, b_enabled, has_unused_moves):
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.is_hovered(mouse_pos)
        self.hover += ((1.0 if hovered else 0.0) - self.hover) * min(1, delta_time * 12)
        self.pressed = max(0, self.pressed - delta_time)
        bg_color = tuple(round(a + (b - a) * self.hover)
                         for a, b in zip((81, 125, 50), (101, 151, 66))) if b_enabled else (70, 76, 67)
        rect = self.rect if self.pressed <= 0 else pygame.Rect(self.rect.x, self.rect.y + 2, self.rect.width, self.rect.height - 2)
        pygame.draw.rect(surface, bg_color, rect)
        nadpis_na_okne(surface, self.text, rect.center, 18, (241, 235, 221), 'center')


"""ИВЕНТЫ!:"""
#Случайные ивенты, их окно, логика и прочее:
class EventPopup:
    def __init__(self, title, description, badge_text, emoji, accent_color, button_text="Продолжить", battle_data=None):
        self.title = title
        self.description = description
        self.badge_text = badge_text
        self.accent_color = accent_color
        self.button_text = button_text
        self.battle_data = battle_data
        
        self.panel = pygame.Rect(410, 210, 780, 480)
        self.button_rect = pygame.Rect(self.panel.left + 30, self.panel.bottom - 76, self.panel.width - 60, 50)
        self.fade = 0.0
        self.dim_overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        self.dim_overlay.fill((8, 14, 22, 180))
        
        #Текст компоненты вынесены отдельно для более гармоничного вида:
        self.title_font = poluchit_shrift(26)
        self.body_font = poluchit_shrift(20)
        self.badge_font = poluchit_shrift(18)
        self.emoji_surface = pygame.font.SysFont("segoeuiemoji", 44).render(emoji, True, accent_color)
    
    
    def wrap_text(self, text, max_width):
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if self.body_font.size(test_line)[0] <= max_width:
                current_line = test_line #помещаем строку в лимит, т.е. черновик
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    
    def handle_click(self, mouse_pos):
        return self.button_rect.collidepoint(mouse_pos)
    
    
    def draw(self, surface):
        self.fade = min(1.0, self.fade + delta_time / .18)
        self.dim_overlay.set_alpha(round(255 * self.fade))
        surface.blit(self.dim_overlay, (0, 0))
        pygame.draw.rect(surface, (32, 59, 39), self.panel)
        emoji_bg = pygame.Rect(self.panel.left + 26, self.panel.top + 18, 56, 56)
        pygame.draw.rect(surface, (52, 83, 42), emoji_bg)
        surface.blit(self.emoji_surface, self.emoji_surface.get_rect(center=emoji_bg.center))
        title_surf = self.title_font.render(self.title, True, self.accent_color)
        surface.blit(title_surf, title_surf.get_rect(midleft=(emoji_bg.right + 18, emoji_bg.centery)))
        y_pos = self.panel.top + 100
        for line in self.wrap_text(self.description, self.panel.width - 70):
            line_surf = self.body_font.render(line, True, (241, 235, 221))
            surface.blit(line_surf, line_surf.get_rect(midtop=(self.panel.centerx, y_pos)))
            y_pos += 28
        badge_box = pygame.Rect(self.panel.left + 30, self.panel.bottom - 148, self.panel.width - 60, 48)
        pygame.draw.rect(surface, (48, 75, 49), badge_box)
        badge_font = self.badge_font
        if badge_font.size(self.badge_text)[0] > badge_box.width - 16:
            badge_font = poluchit_shrift(14)
        badge_surf = badge_font.render(self.badge_text, True, self.accent_color)
        surface.blit(badge_surf, badge_surf.get_rect(center=badge_box.center))
        hovered = self.button_rect.collidepoint(pygame.mouse.get_pos())
        btn_color = (101, 151, 66) if hovered else (81, 125, 50) #ЦВЕТ КНОПКИ
        pygame.draw.rect(surface, btn_color, self.button_rect)
        btn_label = font.render(self.button_text, True, (241, 235, 221))
        surface.blit(btn_label, btn_label.get_rect(center=self.button_rect.center))


class ZagruzchikAtlasov:
    def __init__(self):
        self.atlasy = {}
        self.ishodnye = {}
        self.kesh = {}
        for tip in units:
            self.podgotovit_tip(tip)

    def zagruzit_atlas(self, imya, shirina, vysota):
        kluch = (imya, shirina, vysota)
        if kluch not in self.atlasy:
            atlas = pygame.image.load(os.path.join(textures_dir, "Units", imya)).convert_alpha()
            if atlas.get_width() % shirina or atlas.get_height() % vysota:
                raise ValueError(f"Неправильный размер атласа {imya}")
            self.atlasy[kluch] = atlas
        return self.atlasy[kluch]

    def poluchit_kadr(self, atlas, shirina, vysota, koordinaty):
        col, row = koordinaty
        return atlas.subsurface((col * shirina, row * vysota, shirina, vysota)).copy()

    def podgotovit_tip(self, tip):
        dannye = units[tip]
        w, h = dannye["shirina_kadra"], dannye["vysota_kadra"]
        atlas = self.zagruzit_atlas(dannye["tekstura"], w, h)
        telo = {imya: [self.poluchit_kadr(atlas, w, h, koord)
                       for koord in opisanie["kadry"]]
                for imya, opisanie in dannye["animatsii"].items()}

        # Центр у всех кадров один, в том числе у тела с усиками.
        razmer = (w * 2, h * 2)
        tsentr = (w, h)
        def polozhit(kadr, tocka):
            sloy = pygame.Surface(razmer, pygame.SRCALPHA)
            sloy.blit(kadr, kadr.get_rect(center=tocka))
            return sloy
        telo = {imya: [polozhit(kadr, tsentr) for kadr in kadry]
                for imya, kadry in telo.items()}
        usiki = []
        if dannye.get("usiki"):
            u = dannye["usiki"]
            atlas = self.zagruzit_atlas(u["tekstura"], u["shirina_kadra"], u["vysota_kadra"])
            for koord in u["kadry"]:
                kadr = self.poluchit_kadr(atlas, u["shirina_kadra"], u["vysota_kadra"], koord)
                kadr = pygame.transform.scale(kadr, (round(w * u["shirina"]), round(h * u["vysota"])))
                usiki.append(polozhit(kadr, (w, round(h + h * u["sdvig_y"]))))
        granitsy = [kadr.get_bounding_rect() for kadry in telo.values() for kadr in kadry] + [k.get_bounding_rect() for k in usiki]
        granitsy = [r for r in granitsy if r.width and r.height]
        rx = max(max(w - r.left, r.right - w) for r in granitsy)
        ry = max(max(h - r.top, r.bottom - h) for r in granitsy)
        oblast = pygame.Rect(w-rx, h-ry, rx*2, ry*2)
        self.ishodnye[tip] = ({imya: [k.subsurface(oblast).copy() for k in kadry]
                               for imya, kadry in telo.items()},
                              [k.subsurface(oblast).copy() for k in usiki])

    def poluchit_animatsiyu(self, tip, komanda, razmer):
        cvet = tuple(cveta_koloniy.get(komanda, (255, 255, 255))) if units[tip].get("okrashivanie") else (255, 255, 255)
        kluch = (tip, cvet, razmer)
        if kluch not in self.kesh:
            telo, usiki = self.ishodnye[tip]
            w, h = telo["pokoy"][0].get_size()
            koeff = razmer / max(w, h)
            razmery = (max(1, round(w*koeff)), max(1, round(h*koeff)))
            def obrabotat(kadr):
                kadr = pygame.transform.smoothscale(kadr, razmery)
                if cvet != (255, 255, 255):
                    kadr.fill((*cvet, 255), special_flags=pygame.BLEND_RGBA_MULT)
                return kadr
            self.kesh[kluch] = ({imya: [obrabotat(k) for k in kadry]
                                 for imya, kadry in telo.items()},
                                [obrabotat(k) for k in usiki])
        return self.kesh[kluch]


class Animatsiya:
    def __init__(self, tip, komanda, razmer):
        self.tip = tip
        self.kadry, self.usiki = zagruzchik_atlasov.poluchit_animatsiyu(tip, komanda, razmer)
        self.sostoyanie = "pokoy"
        self.vremya = random.random()
        self.vremya_usikov = random.random()
        parametry_usikov = units[tip].get("usiki") or {}
        self.skorost_usikov = random.uniform(parametry_usikov.get("fps_min", 8), parametry_usikov.get("fps_max", 16))
        self.vspyshka = 0.0

    def ustanovit(self, sostoyanie):
        if self.sostoyanie != sostoyanie:
            self.sostoyanie = sostoyanie
            self.vremya = random.random() if sostoyanie == "hodba" else 0.0

    def obnovit(self, delta_time):
        self.vremya += delta_time
        if self.usiki and self.sostoyanie != "smert":
            self.vremya_usikov += delta_time
            if self.vremya_usikov * self.skorost_usikov >= len(self.usiki):
                self.vremya_usikov %= len(self.usiki) / self.skorost_usikov
                parametry = units[self.tip]["usiki"]
                self.skorost_usikov = random.uniform(parametry["fps_min"], parametry["fps_max"])
        self.vspyshka = max(0, self.vspyshka - delta_time)

    def dlitelnost_ataki(self):
        return len(self.kadry["ataka"]) / units[self.tip]["animatsii"]["ataka"]["fps"]

    def kartinka(self, ugol):
        kadry = self.kadry[self.sostoyanie]
        fps = units[self.tip]["animatsii"][self.sostoyanie]["fps"]
        nomer = int(self.vremya * fps)
        nomer = min(nomer, len(kadry)-1) if self.sostoyanie == "ataka" else nomer % len(kadry)
        kadr = kadry[nomer]
        if self.usiki and self.sostoyanie != "smert":
            kadr = kadr.copy()
            kadr.blit(self.usiki[int(self.vremya_usikov*self.skorost_usikov) % len(self.usiki)], (0, 0))
        if self.vspyshka > 0 and self.sostoyanie != "smert":
            kadr = kadr.copy()
            kadr.fill((135, 135, 135), special_flags=pygame.BLEND_RGB_ADD)
        return pygame.transform.rotate(kadr, ugol)


class Boets:
    def __init__(self, gruppa, pozitsiya, razmer, nomer, storona, tip=None):
        self.tip = tip if tip is not None else gruppa.tip
        self.komanda = gruppa.komanda
        self.storona = storona
        self.nomer = nomer
        self.pozitsiya = pygame.math.Vector2(pozitsiya)
        self.ugol = -90 if storona == 0 else 90
        self.radius = razmer * units[self.tip].get("radius_boya", 0.28)
        self.dalnost = max(3, razmer * 0.20)
        self.skorost = units[self.tip].get("skorost_boya", 115) * random.uniform(.85, 1.15)
        self.animatsiya = Animatsiya(self.tip, self.komanda, razmer)
        self.zhiv = True
        self.max_zdorovie = self.zdorovie = units[self.tip]["zdorovie"]
        self.uron = units[self.tip]["uron"]
        self.bronya = units[self.tip].get("bronya", 0)
        self.tsel = None
        self.tsel_udara = None
        self.vremya_ataki = 0.0
        self.pauza = random.uniform(0, .25)
        self.udary = 0
        self.vremya_pokaza_hp = 0.0
        self.mesto_ataki = None
        self.perevybor = 0.0
        self.zaderzhka = random.uniform(0, .3)

    def povernut(self, napravlenie):
        if napravlenie.length_squared() > .001:
            self.ugol = math.degrees(math.atan2(-napravlenie.y, napravlenie.x)) - 90

    def umeret(self):
        self.zhiv = False
        self.zdorovie = 0
        self.tsel = None
        self.tsel_udara = None
        self.animatsiya.ustanovit("smert")

    def narisovat(self, poverhnost):
        kartinka = self.animatsiya.kartinka(self.ugol)
        pozitsiya = self.pozitsiya
        poverhnost.blit(kartinka, kartinka.get_rect(center=(round(pozitsiya.x), round(pozitsiya.y))))


class BoevoyII:
    def __init__(self, arena, levyy, pravyy):
        self.arena = arena
        self.boitsy = []
        self.po_storonam = [[], []]
        self.ostalos = [levyy.kolichestvo, pravyy.kolichestvo]
        self.ostalos_po_tipam = [dict(levyy.sostav), dict(pravyy.sostav)]
        self.vremya = 0.0
        self.posledniy_uron = 0.0
        self.konets_boya = None
        self.zakonchen = False
        self.prervan = False
        self.shag = 1/60
        self.nakopleno = 0.0
        self.effekty = VizualnyeEffekty()
        self.cvet_pyli = (185, 173, 129)
        self.sled_pyli = 0.0
        for storona, gruppa in enumerate((levyy, pravyy)):
            self.sozdat_boytsov(gruppa, storona)

    #Муравьи выход на арену:
    def sozdat_boytsov(self, gruppa, storona):
        n = gruppa.kolichestvo
        stolbtsy = max(1, math.ceil(math.sqrt(n * 1.45)))
        ryady = math.ceil(n / stolbtsy)
        interval = min((self.arena.width * .37 - 18) / stolbtsy, (self.arena.height - 24) / ryady)
        tipy = [tip for tip, kol in gruppa.sostav.items() for _ in range(kol)]
        random.shuffle(tipy)
        max_razmer = max(units[tip]["razmer_v_boyu"] for tip in tipy)
        razmer = min(max_razmer, max(5, int(interval * .92)))
        shag = min(interval, max(razmer * .95, 17))
        x = self.arena.left + 18 if storona == 0 else self.arena.right - 18
        znak = 1 if storona == 0 else -1
        for i in range(n):
            col, row = i % stolbtsy, i // stolbtsy
            p = (x + znak * (razmer/2 + col * shag), self.arena.centery + (row-(ryady-1)/2)*shag)
            tip = tipy[i]
            razmer_boytsa = max(5, round(units[tip]["razmer_v_boyu"] * razmer / max_razmer))
            boets = Boets(gruppa, p, razmer_boytsa, len(self.boitsy), storona, tip)
            self.boitsy.append(boets)
            self.po_storonam[storona].append(boets)
            self.ogranichit(boets)

    def ogranichit(self, boets):
        r = boets.radius
        boets.pozitsiya.x = max(self.arena.left+r, min(self.arena.right-r, boets.pozitsiya.x))
        boets.pozitsiya.y = max(self.arena.top+r, min(self.arena.bottom-r, boets.pozitsiya.y))

    def nayti_tsel(self, boets, vragi, nagruzka):
        if not vragi:
            return None
        return min(vragi, key=lambda vrag: boets.pozitsiya.distance_to(vrag.pozitsiya) + nagruzka.get(vrag, 0) * boets.radius * 1.4)

    def nayti_mesto_ataki(self, boets, tsel, zanyatye):
        radius = boets.radius + tsel.radius + boets.dalnost * .65
        vektor = boets.pozitsiya - tsel.pozitsiya
        ugol = math.atan2(vektor.y, vektor.x)
        varianty = []
        for i in range(16):
            a = ugol + i * math.tau / 16
            p = tsel.pozitsiya + pygame.math.Vector2(math.cos(a), math.sin(a)) * radius
            if not (self.arena.left+boets.radius <= p.x <= self.arena.right-boets.radius and self.arena.top+boets.radius <= p.y <= self.arena.bottom-boets.radius):
                continue
            tsena = boets.pozitsiya.distance_to(p)
            for drugoy, mesto in zanyatye:
                if drugoy is boets:
                    continue
                peresechenie = boets.radius + drugoy.radius - mesto.distance_to(p)
                if peresechenie > 0:
                    tsena += 5 * peresechenie + 12
            varianty.append((tsena, a))
        return min(varianty)[1] if varianty else ugol

    def rastolknut(self, zhivye):
        if not zhivye:
            return
        razmer_kletki = max(8, 2 * max(b.radius for b in zhivye))
        # В большой битве проверяем соседние клетки, а не все пары на арене.
        for _ in range(2):
            setka = {}
            for b in zhivye:
                koord = (int(b.pozitsiya.x//razmer_kletki), int(b.pozitsiya.y//razmer_kletki))
                setka.setdefault(koord, []).append(b)
            for (x,y), spisok in setka.items():
                for b in spisok:
                    for dx in (-1,0,1):
                        for dy in (-1,0,1):
                            for drugoy in setka.get((x+dx,y+dy), ()):
                                if drugoy.nomer <= b.nomer:
                                    continue
                                v = drugoy.pozitsiya-b.pozitsiya
                                min_dist = b.radius+drugoy.radius
                                kv = v.length_squared()
                                if kv >= min_dist*min_dist:
                                    continue
                                dist = math.sqrt(kv)
                                napravlenie = v/dist if dist > .0001 else pygame.math.Vector2(1,0).rotate(b.nomer*137)
                                sdvig = napravlenie * (min_dist-dist+.02)
                                massa_b, massa_d = b.radius**2, drugoy.radius**2
                                b.pozitsiya -= sdvig * (massa_d/(massa_b+massa_d))
                                drugoy.pozitsiya += sdvig * (massa_b/(massa_b+massa_d))
                                self.ogranichit(b)
                                self.ogranichit(drugoy)

    def udar(self, boets, tsel):
        if not tsel.zhiv or not boets.zhiv or boets.storona == tsel.storona:
            return 0
        if boets.pozitsiya.distance_to(tsel.pozitsiya) > boets.radius+tsel.radius+boets.dalnost+4:
            return 0
        bronya = max(0, min(100, tsel.bronya))
        return max(0, boets.uron * (1 - bronya / 100))

    def primenit_udary(self, udary):
        # Сначала собираем все удары за этот шаг, чтобы порядок бойцов в списке
        # не давал одной стороне преимущество при одновременной атаке.
        uron_po_tselyam = {}
        for boets, tsel in udary:
            uron = self.udar(boets, tsel)
            if uron > 0:
                uron_po_tselyam[tsel] = uron_po_tselyam.get(tsel, 0) + uron
                tsel.udary += 1
        for tsel, uron in uron_po_tselyam.items():
            tsel.animatsiya.vspyshka = .09
            tsel.vremya_pokaza_hp = self.vremya+.55
            # Цифры урона ограничиваем, чтобы на большой арене было видно сам бой.
            if sum(len(ch) == 5 for ch in self.effekty.chastitsy) < 8:
                self.effekty.udar(tsel.pozitsiya, uron)
                self.effekty.pyl(tsel.pozitsiya, self.cvet_pyli, 2)
            tsel.zdorovie = max(0, tsel.zdorovie - uron)
            self.posledniy_uron = self.vremya
            if tsel.zdorovie <= 0:
                self.ubit(tsel)

    def ubit(self, boets):
        if boets.zhiv:
            boets.umeret()
            self.ostalos[boets.storona] -= 1
            self.ostalos_po_tipam[boets.storona][boets.tip] -= 1

    def obnovit(self, delta_time):
        self.effekty.obnovit(delta_time)
        self.sled_pyli += delta_time
        if self.sled_pyli >= .16 and self.konets_boya is None:
            self.sled_pyli = 0.0
            for b in self.boitsy:
                if b.zhiv and b.animatsiya.sostoyanie == "hodba" and self.effekty.random.random() < .18:
                    self.effekty.pyl(b.pozitsiya, self.cvet_pyli, 1)
        self.nakopleno += delta_time
        while self.nakopleno >= self.shag and not self.zakonchen:
            self.nakopleno -= self.shag
            self.shag_boya(self.shag)

    def shag_boya(self, dt):
        self.vremya += dt
        if self.konets_boya is not None:
            if self.vremya - self.konets_boya >= .65:
                self.zakonchen = True
            return
        zhivye = [b for b in self.boitsy if b.zhiv]
        vragi = [[b for b in spisok if b.zhiv] for spisok in self.po_storonam]
        nagruzka = {}
        mesta = {}
        for b in zhivye:
            if b.tsel is not None and b.tsel.zhiv:
                nagruzka[b.tsel] = nagruzka.get(b.tsel, 0)+1
                if b.mesto_ataki is not None:
                    r = b.radius+b.tsel.radius+b.dalnost*.65
                    a = b.mesto_ataki
                    p = b.tsel.pozitsiya+pygame.math.Vector2(math.cos(a),math.sin(a))*r
                    mesta.setdefault(b.tsel, []).append((b,p))
        udary = []
        zastoy = self.vremya - self.posledniy_uron
        for b in zhivye:
            b.animatsiya.obnovit(dt)
            b.pauza = max(0, b.pauza-dt)
            b.perevybor -= dt
            if self.vremya < b.zaderzhka:
                b.animatsiya.ustanovit("pokoy")
                continue
            if b.tsel_udara is not None:
                staroe = b.vremya_ataki
                b.vremya_ataki += dt
                dlitelnost = b.animatsiya.dlitelnost_ataki()
                if staroe < dlitelnost*.5 <= b.vremya_ataki:
                    udary.append((b,b.tsel_udara))
                if b.vremya_ataki >= dlitelnost:
                    b.tsel_udara = None
                    b.pauza = random.uniform(.12,.35)
                    b.animatsiya.ustanovit("pokoy")
                continue
            if b.tsel is None or not b.tsel.zhiv or (zastoy > 5 and b.perevybor <= 0):
                b.tsel = self.nayti_tsel(b, vragi[1-b.storona], nagruzka)
                b.mesto_ataki = None
                if b.tsel is not None:
                    nagruzka[b.tsel] = nagruzka.get(b.tsel,0)+1
            tsel = b.tsel
            if tsel is None:
                b.animatsiya.ustanovit("pokoy")
                continue
            vektor = tsel.pozitsiya-b.pozitsiya
            dist = vektor.length()
            dalnost = b.radius+tsel.radius+b.dalnost
            if dist <= dalnost:
                b.povernut(vektor)
                b.animatsiya.ustanovit("pokoy")
                if b.pauza <= 0:
                    b.tsel_udara = tsel
                    b.vremya_ataki = 0.0
                    b.animatsiya.ustanovit("ataka")
                continue
            if b.mesto_ataki is None or b.perevybor <= 0:
                b.mesto_ataki = self.nayti_mesto_ataki(b, tsel, mesta.get(tsel, []))
                b.perevybor = random.uniform(.35,.65)
                a = b.mesto_ataki
                r = b.radius+tsel.radius+b.dalnost*.65
                mesta.setdefault(tsel,[]).append((b,tsel.pozitsiya+pygame.math.Vector2(math.cos(a),math.sin(a))*r))
            a = b.mesto_ataki
            r = b.radius+tsel.radius+b.dalnost*.65
            mesto = tsel.pozitsiya+pygame.math.Vector2(math.cos(a),math.sin(a))*r
            napravlenie = mesto-b.pozitsiya
            # Если вокруг цели никак не получается занять место, идём к ней напрямую.
            if zastoy > 8:
                napravlenie = vektor
            if napravlenie.length_squared() > .001:
                b.povernut(napravlenie)
                b.pozitsiya += napravlenie.normalize()*min(b.skorost*dt, napravlenie.length())
                self.ogranichit(b)
                b.animatsiya.ustanovit("hodba")
        self.rastolknut(zhivye)
        self.primenit_udary(udary)
        if 0 in self.ostalos:
            self.konets_boya = self.vremya
        elif self.vremya - self.posledniy_uron >= 30:
            # Если никто не может нанести урон, не убиваем бойцов искусственно.
            self.prervan = True
            self.konets_boya = self.vremya
        if self.konets_boya is not None:
            for b in self.boitsy:
                if b.zhiv:
                    b.tsel = b.tsel_udara = None
                    b.animatsiya.ustanovit("pokoy")

    def narisovat(self, poverhnost):
        staryy_clip = poverhnost.get_clip()
        poverhnost.set_clip(self.arena)
        for b in self.boitsy:
            if b.zhiv:
                narisovat_ten(poverhnost, tuple(b.pozitsiya), b.radius*3.1, b.radius*2.2)
        for b in sorted(self.boitsy, key=lambda b: (b.zhiv,b.pozitsiya.y)):
            b.narisovat(poverhnost)
        self.effekty.narisovat(poverhnost)
        for b in self.boitsy:
            if b.zhiv and 0 < b.zdorovie < b.max_zdorovie and b.vremya_pokaza_hp > self.vremya:
                w = max(10, round(b.radius*2.6))
                x, y = round(b.pozitsiya.x)-w//2, round(b.pozitsiya.y-b.radius*1.9)-6
                pygame.draw.rect(poverhnost,(28,33,27),(x,y,w,4))
                pygame.draw.rect(poverhnost,(155,211,113),(x,y,round(w*b.zdorovie/b.max_zdorovie),4))
        poverhnost.set_clip(staryy_clip)


def sila_sostava(sostav):
    return sum(kol * max(0, units[tip]["uron"]) * max(0, units[tip]["zdorovie"])
               / max(.05, 1-max(0, min(95, units[tip].get("bronya", 0)))/100)
               for tip, kol in sostav.items())


def yacheyki_sostava(sostav):
    return sum(kol * units[tip].get("yacheyki", 0) for tip, kol in sostav.items())


# Муравьи и их перемещение
class Muravey:
    def __init__(pelmeshki, tip, kletka, komanda="igrok", kolichestvo=None):
        dannye = units[tip]
        pelmeshki.tip = tip
        pelmeshki.odin = dannye.get("odin", False)
        pelmeshki.nazvanie = dannye.get("nazvanie", dannye.get("imya", tip))
        pelmeshki.zdorovie = dannye["zdorovie"]
        pelmeshki.max_zdorovie = dannye["zdorovie"]
        pelmeshki.prohodimost = dannye["prohodimost"]
        pelmeshki.ostalos_hodov = pelmeshki.prohodimost
        pelmeshki.uron = dannye["uron"]
        pelmeshki.bronya = dannye.get("bronya", 0)
        pelmeshki.kletka = kletka
        pelmeshki.komanda = komanda
        # Сколько тут бойцов — столько и выйдет на арену.
        pelmeshki.kolichestvo = 1 if pelmeshki.odin else max(1, int(
            kolichestvo if kolichestvo is not None else dannye.get("kolichestvo", 10)
        ))
        pelmeshki.pozitsiya = pygame.math.Vector2(kletka.center)
        pelmeshki.marshrut = []
        pelmeshki.skorost_dvizheniya = 160
        pelmeshki.ugol = 0
        pelmeshki.vrag_dlya_boya = None
        pelmeshki.atakoval_v_etom_hodu = False
        pelmeshki.sostav = {tip: pelmeshki.kolichestvo}
        pelmeshki.animatsii = {}
        pelmeshki.obnovit_sostav(pelmeshki.sostav)

    def obnovit_sostav(pelmeshki, sostav):
        # Количество берём из состава, иначе после разделения цифры могут разойтись.
        pelmeshki.sostav = {tip: sostav[tip] for tip in units if sostav.get(tip, 0) > 0}
        pelmeshki.kolichestvo = sum(pelmeshki.sostav.values())
        if not pelmeshki.sostav:
            pelmeshki.zdorovie = 0
            return
        # На карте показываем самого сильного бойца, а не два мелких спрайта.
        pelmeshki.tip = max(pelmeshki.sostav, key=lambda tip: sila_sostava({tip: 1}))
        dannye = units[pelmeshki.tip]
        pelmeshki.odin = dannye.get("odin", False)
        pelmeshki.nazvanie = "Смешанный отряд" if len(pelmeshki.sostav) > 1 else dannye["nazvanie"]
        pelmeshki.zdorovie = pelmeshki.max_zdorovie = dannye["zdorovie"]
        pelmeshki.uron = dannye["uron"]
        pelmeshki.bronya = dannye.get("bronya", 0)
        pelmeshki.prohodimost = min(units[tip]["prohodimost"] for tip in pelmeshki.sostav)
        pelmeshki.ostalos_hodov = min(pelmeshki.ostalos_hodov, pelmeshki.prohodimost)
        pelmeshki.animatsiya = Animatsiya(pelmeshki.tip, pelmeshki.komanda,
                                        units[pelmeshki.tip]["razmer_na_karte"])
        pelmeshki.animatsii = {pelmeshki.tip: pelmeshki.animatsiya}

    def poluchit_silu(pelmeshki):
        return sila_sostava(pelmeshki.sostav)

    def poluchit_yacheyki(pelmeshki):
        return yacheyki_sostava(pelmeshki.sostav)

    def narisovat(pelmeshki, poverhnost):
        if pelmeshki.zdorovie <= 0:
            return

        kartinka = pelmeshki.animatsiya.kartinka(pelmeshki.ugol)
        mesto = kartinka.get_rect(center=(round(pelmeshki.pozitsiya.x), round(pelmeshki.pozitsiya.y)))
        poverhnost.blit(kartinka, mesto)

        chislo = font_count.render(str(pelmeshki.kolichestvo), True, (255, 255, 255))

        # Плашку делаем поменьше и цепляем справа от спрайта,
        # чтобы большие числа не залезали на самого муравья.
        vnutr_otstup_x = 4
        vnutr_otstup_y = 2
        shirina_podlozhki = chislo.get_width() + vnutr_otstup_x * 2
        vysota_podlozhki = chislo.get_height() + vnutr_otstup_y * 2
        levyy_kray = mesto.right + 1
        verhniy_kray = mesto.bottom - vysota_podlozhki + 1
        srez = 3

        podlozhka_sloy = pygame.Surface((shirina_podlozhki, vysota_podlozhki), pygame.SRCALPHA)
        pygame.draw.polygon(
            podlozhka_sloy,
            (45, 50, 56, 170),
            [(srez, 0),
             (shirina_podlozhki - srez, 0),
             (shirina_podlozhki, srez),
             (shirina_podlozhki, vysota_podlozhki - srez),
             (shirina_podlozhki - srez, vysota_podlozhki),
             (srez, vysota_podlozhki),
             (0, vysota_podlozhki - srez),
             (0, srez)]
        )
        poverhnost.blit(podlozhka_sloy, (levyy_kray, verhniy_kray))
        poverhnost.blit(
            chislo,
            chislo.get_rect(center=(levyy_kray + shirina_podlozhki / 2,
                                    verhniy_kray + vysota_podlozhki / 2))
        )

        if pelmeshki.odin:
            # Подпись нужна, чтобы одиночных врагов было проще различать на карте.
            imya = shrift_imen_vragov.render(pelmeshki.nazvanie, True, (255, 235, 190))
            poverhnost.blit(imya, imya.get_rect(midbottom=(mesto.centerx, mesto.top - 3)))

    def peremestitsya(pelmeshki, novaya_kletka):
        if (pelmeshki.zdorovie <= 0 or pelmeshki.marshrut
                or pelmeshki.ostalos_hodov <= 0 or novaya_kletka is None):
            return False

        koord = (novaya_kletka.col, novaya_kletka.row)
        dostupnye, otkuda = nayti_dostupnye_kletki(pelmeshki)
        if koord not in dostupnye:
            return False

        nachalo = (pelmeshki.kletka.col, pelmeshki.kletka.row)
        put = []
        tekushchaya = koord
        while tekushchaya != nachalo:
            put.append(hex_grid[tekushchaya])
            tekushchaya = otkuda[tekushchaya]
        put.reverse()

        pelmeshki.ostalos_hodov -= dostupnye[koord]
        pelmeshki.marshrut = put
        return True

    def obnovit(pelmeshki, delta_time):
        if pelmeshki.zdorovie <= 0:
            return
        for animatsiya in pelmeshki.animatsii.values():
            animatsiya.ustanovit("hodba" if pelmeshki.marshrut else "pokoy")
            animatsiya.obnovit(delta_time)
        if not pelmeshki.marshrut:
            return

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
            elif pelmeshki.komanda == "igrok" and sleduyushchaya.event is not None: #как же удобно работать с Гошеным кодом :)


                vozvrat = sum((tipy_provintsiy[provintsii_kletok[(k.col, k.row)]]["stoimost"] or 0)
                              for k in pelmeshki.marshrut)
                pelmeshki.ostalos_hodov = min(pelmeshki.prohodimost, pelmeshki.ostalos_hodov + vozvrat)
                pelmeshki.marshrut.clear()
                if pelmeshki.vrag_dlya_boya is not None:
                    pelmeshki.atakoval_v_etom_hodu = False
                pelmeshki.vrag_dlya_boya = None
                pending_event_triggers.append((pelmeshki, sleduyushchaya)) #нужно для системы ивентов
        elif rasstoyanie > 0:
            pelmeshki.pozitsiya += napravlenie.normalize() * shag

    def umeret(pelmeshki):
        #Логика гибеля:
        # Сюда сводим любую гибель: и утопление, и проигрыш целой группы.
        if pelmeshki.zdorovie <= 0:
            return
        pelmeshki.zdorovie = 0
        pelmeshki.kolichestvo = 0
        pelmeshki.sostav.clear()
        pelmeshki.marshrut.clear()
        pelmeshki.vrag_dlya_boya = None
        pelmeshki.animatsiya.ustanovit("smert")
        effekty_smerti.append({
            "kartinka": pelmeshki.animatsiya.kartinka(pelmeshki.ugol),
            "pozitsiya": pelmeshki.pozitsiya.copy(),
            "vremya": 0.0
        })


def nanesti_uron(atakuyushiy, zashchitnik):
    if atakuyushiy.zdorovie <= 0 or zashchitnik.zdorovie <= 0:
        return 0
    bronya = max(0, min(100, zashchitnik.bronya))
    fakt_uron = max(0, atakuyushiy.uron * (1 - bronya / 100))
    fakt_uron = min(fakt_uron, zashchitnik.zdorovie)

    if fakt_uron >= zashchitnik.zdorovie:
        zashchitnik.umeret()
    else:
        zashchitnik.zdorovie -= fakt_uron
    return fakt_uron


def rasschitat_itog_boya(ii, do_boya):
    # Считаем тех, кто действительно выжил, а не назначаем потери заранее.
    sostavy = [{}, {}]
    for boets in ii.boitsy:
        if boets.zhiv:
            sostav = sostavy[boets.storona]
            sostav[boets.tip] = sostav.get(boets.tip, 0) + 1
    levyy, pravyy = map(lambda sostav: sum(sostav.values()), sostavy)
    if levyy and not pravyy:
        pobeditel = "igrok"
    elif pravyy and not levyy:
        pobeditel = "vrag"
    elif not levyy and not pravyy:
        pobeditel = "nichya"
    else:
        pobeditel = "prervan"
    return {"do_levogo": do_boya[0], "do_pravogo": do_boya[1],
            "posle_levogo": levyy, "posle_pravogo": pravyy,
            "pobeditel": pobeditel, "sostav_levogo": sostavy[0],
            "sostav_pravogo": sostavy[1]}


class Avtoboy:
    def __init__(self, levyy, pravyy):
        self.levyy = levyy
        self.pravyy = pravyy
        self.itog = None
        self.do_boya = (levyy.kolichestvo, pravyy.kolichestvo)
        self.vremya = 0.0
        self.stadiya = "bitva"

        self.panel = pygame.Rect(245, 80, 1110, 740)
        self.arena = pygame.Rect(287, 255, 1026, 355)
        self.knopka = pygame.Rect(630, 719, 340, 59)
        self.fon_zatemneniya = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        self.fon_zatemneniya.fill((9, 17, 25, 205))

        self.sh_zagolovok = poluchit_shrift(29)
        self.sh_krupnyy = poluchit_shrift(42)
        self.sh_obychniy = poluchit_shrift(22)
        self.sh_malyy = poluchit_shrift(18)

        koord_zashchitnika = (pravyy.kletka.col, pravyy.kletka.row)
        tip_polya_boya = provintsii_kletok.get(koord_zashchitnika, "polya")
        self.palette = self.poluchit_paltru_boya(tip_polya_boya)
        self.pol_boya = self.sozdat_pol_boya(tip_polya_boya)

        # На больших отрядах ужимаем отдельные спрайты, но не подменяем армию одной картинкой.
        self.ii = BoevoyII(self.arena, levyy, pravyy)
        self.ii.cvet_pyli = {"les":(125,110,78), "polya":(168,159,107),
                            "gory":(157,157,150), "pustynya":(218,184,121),
                            "plyazh":(221,203,152), "voda":(110,170,205)}.get(tip_polya_boya,(168,159,107))
        self.polosy = [1.0, 1.0]
        self.poyavlenie = 0.0
        self.poyavlenie_itoga = 0.0

    def sozdat_pol_boya(self, tip):
        pol = pygame.Surface(self.arena.size)
        pol.fill(self.palette["arena"])
        # Для пляжа пока используем песок пустыни, для воды оставляем старый фон.
        tekstura = tekstury_pola_boya.get("pustynya" if tip == "plyazh" else tip)
        if tekstura is None:
            return pol

        # Кладём текстуры рядом в исходном размере, лишнее за краями само обрежется.
        for y in range(0, self.arena.height, tekstura.get_height()):
            for x in range(0, self.arena.width, tekstura.get_width()):
                pol.blit(tekstura, (x, y))
        return pol

    def poluchit_paltru_boya(self, tip):
        palitry = {
            "polya": {
                "panel": (26, 39, 30),
                "arena": (74, 101, 69),
                "niz": (39, 55, 43),
                "kartochka": (39, 55, 43),
                "razdelitel": (157, 180, 149),
                "osnovnoy_tekst": (241, 243, 238),
                "vtorichnyy_tekst": (199, 214, 199),
                "levyy_tekst": (202, 233, 198),
                "pravyy_tekst": (242, 214, 188),
                "levaya_sila": (202, 233, 198),
                "pravaya_sila": (242, 214, 188),
                "vs": (245, 217, 151),
                "knopka": (84, 118, 76),
                "knopka_hover": (97, 136, 88)
            },
            "les": {
                "panel": (16, 29, 20),
                "arena": (50, 79, 54),
                "niz": (27, 42, 31),
                "kartochka": (27, 42, 31),
                "razdelitel": (126, 155, 126),
                "osnovnoy_tekst": (239, 243, 239),
                "vtorichnyy_tekst": (186, 206, 187),
                "levyy_tekst": (177, 223, 181),
                "pravyy_tekst": (233, 196, 180),
                "levaya_sila": (177, 223, 181),
                "pravaya_sila": (233, 196, 180),
                "vs": (241, 212, 146),
                "knopka": (55, 95, 60),
                "knopka_hover": (69, 112, 75)
            },
            "gory": {
                "panel": (32, 36, 40),
                "arena": (99, 104, 108),
                "niz": (45, 49, 55),
                "kartochka": (45, 49, 55),
                "razdelitel": (171, 177, 183),
                "osnovnoy_tekst": (243, 244, 245),
                "vtorichnyy_tekst": (206, 211, 215),
                "levyy_tekst": (194, 228, 211),
                "pravyy_tekst": (238, 206, 194),
                "levaya_sila": (194, 228, 211),
                "pravaya_sila": (238, 206, 194),
                "vs": (246, 219, 161),
                "knopka": (87, 97, 104),
                "knopka_hover": (104, 115, 123)
            },
            "pustynya": {
                "panel": (53, 41, 23),
                "arena": (154, 126, 74),
                "niz": (70, 56, 33),
                "kartochka": (70, 56, 33),
                "razdelitel": (216, 190, 133),
                "osnovnoy_tekst": (249, 244, 233),
                "vtorichnyy_tekst": (232, 217, 188),
                "levyy_tekst": (214, 235, 185),
                "pravyy_tekst": (249, 212, 183),
                "levaya_sila": (228, 232, 175),
                "pravaya_sila": (247, 214, 184),
                "vs": (255, 228, 159),
                "knopka": (124, 98, 55),
                "knopka_hover": (145, 116, 67)
            },
            "plyazh": {
                "panel": (48, 44, 31),
                "arena": (184, 170, 123),
                "niz": (65, 60, 43),
                "kartochka": (65, 60, 43),
                "razdelitel": (228, 214, 161),
                "osnovnoy_tekst": (247, 245, 236),
                "vtorichnyy_tekst": (226, 218, 189),
                "levyy_tekst": (208, 231, 190),
                "pravyy_tekst": (246, 209, 183),
                "levaya_sila": (208, 231, 190),
                "pravaya_sila": (246, 209, 183),
                "vs": (255, 228, 165),
                "knopka": (118, 109, 77),
                "knopka_hover": (139, 128, 92)
            },
            "voda": {
                "panel": (18, 32, 45),
                "arena": (54, 95, 130),
                "niz": (29, 48, 66),
                "kartochka": (29, 48, 66),
                "razdelitel": (142, 176, 205),
                "osnovnoy_tekst": (239, 244, 247),
                "vtorichnyy_tekst": (195, 213, 224),
                "levyy_tekst": (192, 227, 215),
                "pravyy_tekst": (240, 206, 197),
                "levaya_sila": (192, 227, 215),
                "pravaya_sila": (240, 206, 197),
                "vs": (247, 224, 165),
                "knopka": (50, 82, 108),
                "knopka_hover": (63, 101, 132)
            }
        }
        return palitry.get(tip, palitry["polya"])

    def obnovit(self, delta_time):
        self.poyavlenie = min(1.0,self.poyavlenie+delta_time/.2)
        if self.stadiya != "bitva":
            self.poyavlenie_itoga = min(1.0,self.poyavlenie_itoga+delta_time/.18)
            return
        self.ii.obnovit(delta_time)
        for i in range(2):
            dolya = self.ii.ostalos[i]/max(1,self.do_boya[i])
            self.polosy[i] += (dolya-self.polosy[i])*min(1,delta_time*10)
        self.vremya = self.ii.vremya
        if self.ii.zakonchen:
            self.itog = rasschitat_itog_boya(self.ii, self.do_boya)
            self.stadiya = "rezultat"

    def zavershit(self):
        #Только после экрана результата перенос потери на карту:
        # Только после экрана результата переносим потери на карту.
        if self.itog is None:
            return
        for gruppa, kluch in (
            (self.levyy, "sostav_levogo"),
            (self.pravyy, "sostav_pravogo")
        ):
            sostav = self.itog[kluch]
            if not sostav:
                gruppa.umeret()
            else:
                gruppa.obnovit_sostav(sostav)
            gruppa.vrag_dlya_boya = None

    def obrabotat_nazhatie(self, pozitsiya):
        if self.stadiya == "rezultat" and self.knopka.collidepoint(pozitsiya):
            self.zavershit()
            return True
        return False

    def tekst(self, poverhnost, fraza, shrift, cvet, tocka, vyrovnyat="center"):
        nadpis = shrift.render(str(fraza), True, cvet)
        rect = nadpis.get_rect()
        setattr(rect, vyrovnyat, tocka)
        poverhnost.blit(nadpis, rect)

    def oformit_podlozhku(self, poverhnost):
        poverhnost.blit(self.fon_zatemneniya, (0, 0))
        pygame.draw.rect(poverhnost, self.palette["panel"], self.panel)

    def narisovat_bitvu(self, poverhnost):
        self.tekst(
            poverhnost, "ВАША КОЛОНИЯ", self.sh_malyy,
            self.palette["levyy_tekst"], (self.panel.left + 48, self.panel.top + 116), "midleft"
        )
        nazvanie_vraga = self.pravyy.nazvanie.upper() if self.pravyy.odin else "ПРОТИВНИК"
        self.tekst(
            poverhnost, nazvanie_vraga, self.sh_malyy,
            self.palette["pravyy_tekst"], (self.panel.right - 48, self.panel.top + 116), "midright"
        )

        self.tekst(
            poverhnost, f"{self.ii.ostalos[0]} муравьёв",
            self.sh_obychniy, self.palette["osnovnoy_tekst"],
            (self.panel.left + 48, self.panel.top + 146), "midleft"
        )
        kolichestvo_vraga = (
            f"{self.ii.ostalos[1]} из 1"
            if self.pravyy.odin
            else f"{self.ii.ostalos[1]} муравьёв"
        )
        self.tekst(
            poverhnost, kolichestvo_vraga,
            self.sh_obychniy, self.palette["osnovnoy_tekst"],
            (self.panel.right - 48, self.panel.top + 146), "midright"
        )

        # Полоски показывают живых бойцов, а не заранее рассчитанный результат.
        for i in range(2):
            w = 390
            x = self.arena.left+6 if i == 0 else self.arena.right-w-6
            y = self.arena.top-13
            pygame.draw.rect(poverhnost,(20,26,21),(x,y,w,8))
            zapolnenie = round(w*self.polosy[i])
            pygame.draw.rect(poverhnost,cveta_koloniy["igrok" if i==0 else "vrag"],
                             (x if i==0 else x+w-zapolnenie,y,zapolnenie,8))
        poverhnost.blit(self.pol_boya, self.arena.topleft)
        self.ii.narisovat(poverhnost)

        self.tekst(
            poverhnost, f"Сила: {sila_sostava(self.ii.ostalos_po_tipam[0]):,.0f}".replace(",", " "),
            self.sh_obychniy, self.palette["levaya_sila"],
            (self.arena.left + 20, self.arena.bottom + 30), "midleft"
        )
        self.tekst(
            poverhnost, f"Сила: {sila_sostava(self.ii.ostalos_po_tipam[1]):,.0f}".replace(",", " "),
            self.sh_obychniy, self.palette["pravaya_sila"],
            (self.arena.right - 20, self.arena.bottom + 30), "midright"
        )

        pygame.draw.rect(
            poverhnost, self.palette["niz"],
            (self.panel.left + 42, self.panel.bottom - 95, self.panel.width - 84, 64)
        )
        self.tekst(
            poverhnost, "Бой идёт автоматически…", self.sh_obychniy,
            self.palette["vs"], (self.panel.centerx, self.panel.bottom - 72)
        )
        self.tekst(
            poverhnost, "Результаты появятся после окончания сражения",
            self.sh_malyy, self.palette["vtorichnyy_tekst"],
            (self.panel.centerx, self.panel.bottom - 46)
        )

    def narisovat_rezultat(self, poverhnost):
        pobeditel = self.itog["pobeditel"]
        if pobeditel == "igrok":
            zagolovok = "ПОБЕДА"
            cvet_zagolovka = (137, 225, 169)
            podzagolovok = "Ваша группа выиграла сражение"
        elif pobeditel == "vrag":
            zagolovok = "ПОРАЖЕНИЕ"
            cvet_zagolovka = (240, 139, 128)
            podzagolovok = "Победила вражеская группа"
        elif pobeditel == "prervan":
            zagolovok = "БОЙ ПРЕРВАН"
            cvet_zagolovka = (249, 216, 157)
            podzagolovok = "Бойцы не смогли продолжить сражение"
        else:
            zagolovok = "НИЧЬЯ"
            cvet_zagolovka = (249, 216, 157)
            podzagolovok = "Обе группы уничтожены"

        self.tekst(
            poverhnost, zagolovok, self.sh_krupnyy, cvet_zagolovka,
            (self.panel.centerx, self.panel.top + 125)
        )
        self.tekst(
            poverhnost, podzagolovok, self.sh_obychniy, self.palette["vtorichnyy_tekst"],
            (self.panel.centerx, self.panel.top + 175)
        )

        for x, cifra, podpis, cvet in (
            (self.panel.left + 150, self.itog["posle_levogo"], "Выжило", (150, 231, 183)),
            (self.panel.left + 600, self.itog["do_levogo"] - self.itog["posle_levogo"],
             "Погибло", (247, 151, 142))
        ):
            kartochka = pygame.Rect(x, self.panel.top + 225, 360, 155)
            pygame.draw.rect(poverhnost, self.palette["kartochka"], kartochka)
            self.tekst(poverhnost, str(cifra), self.sh_krupnyy,
                       cvet, (kartochka.centerx, kartochka.top + 62))
            self.tekst(poverhnost, podpis, self.sh_obychniy,
                       self.palette["vtorichnyy_tekst"], (kartochka.centerx, kartochka.bottom - 36))

        stat = pygame.Rect(self.panel.left + 150, self.panel.top + 415, 810, 105)
        pygame.draw.rect(poverhnost, self.palette["kartochka"], stat)
        self.tekst(poverhnost, "Ваша группа", self.sh_obychniy, self.palette["osnovnoy_tekst"],
                   (stat.left + 28, stat.top + 32), "midleft")
        self.tekst(poverhnost, f"{self.itog['posle_levogo']} / {self.itog['do_levogo']}",
                   self.sh_obychniy, self.palette["osnovnoy_tekst"],
                   (stat.right - 28, stat.top + 32), "midright")
        self.tekst(poverhnost, "Вражеская группа", self.sh_obychniy,
                   self.palette["osnovnoy_tekst"], (stat.left + 28, stat.bottom - 30), "midleft")
        self.tekst(poverhnost, f"{self.itog['posle_pravogo']} / {self.itog['do_pravogo']}",
                   self.sh_obychniy, self.palette["osnovnoy_tekst"],
                   (stat.right - 28, stat.bottom - 30), "midright")

        mysh = pygame.mouse.get_pos()
        cvet = self.palette["knopka_hover"] if self.knopka.collidepoint(mysh) else self.palette["knopka"]
        pygame.draw.rect(poverhnost, cvet, self.knopka)
        self.tekst(
            poverhnost, "Вернуться на карту", self.sh_obychniy,
            self.palette["osnovnoy_tekst"], self.knopka.center
        )

    def narisovat(self, poverhnost):
        prozrachnost = self.poyavlenie if self.stadiya == "bitva" else self.poyavlenie_itoga
        if self.stadiya == "rezultat" and prozrachnost < 1:
            self.oformit_podlozhku(poverhnost)
            self.narisovat_bitvu(poverhnost)
        fon_do_okna = poverhnost.copy() if prozrachnost < 1 else None
        self.oformit_podlozhku(poverhnost)
        if self.stadiya == "bitva":
            self.narisovat_bitvu(poverhnost)
        else:
            self.narisovat_rezultat(poverhnost)
        if fon_do_okna is not None:
            fon_do_okna.set_alpha(round(255*(1-prozrachnost)))
            poverhnost.blit(fon_do_okna,(0,0))



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
        self.event_state = None
        self.build_unlocked = False
        self.is_water = False
    
    def is_has_neighbor(self, other_hex): #Проверка если ли соседняя клетка рядом с ней
        if other_hex is None or other_hex == self:
            return False
        
        return self.center.distance_squared_to(other_hex.center) < self.neighbor_distance
    
    def draw(self, surface, color, thick):
        pygame.draw.polygon(surface, color, self.table_points, thick)
        #ЕСЛИ ТАМ ЕСТЬ ИВЕНТ:
        if self.event is not None:
            has_event = font.render("!" if self.event_state == "failed_battle" else "?", True, (255, 65, 65) if self.event_state == "failed_battle" else (255, 230, 0))
            event_rect = has_event.get_rect(center=(self.center.x, self.center.y))
            surface.blit(has_event, event_rect)
            
#HEX TOOL (Создаём саму сетку):
def create_hex_grid(hex_grid_width, hex_grid_height, hex_grid_radius):
    grid = {} #{(col, row): Hex}
    step_x = 1.5 * hex_grid_radius
    step_y = math.sqrt(3) * hex_grid_radius
    hex_colons = int(hex_grid_width // step_x) + 1
    hex_rows = int(hex_grid_height // step_y) + 1

    # Подогнали сетку по границам леса, гор и берега на MainMap.png (1452 на 831).
    # Старые номера клеток оставляем, чтобы не потерять разметку провинций.
    sx, sy = hex_grid_width / 1452, hex_grid_height / 831
    shag_x, shag_y = 35.84 * sx, 42.08 * sy
    nachalo_x, nachalo_y = 19.81 * sx, 16.17 * sy
    radius_x, radius_y = shag_x / 1.5, shag_y / math.sqrt(3)

    for col in range(hex_colons):
        for row in range(hex_rows):
            hex_grid_x = col * step_x + hex_grid_radius
            hex_grid_y = row * step_y + hex_grid_radius
            if col % 2 == 1:
                hex_grid_y += step_y / 2 #сдвигаем нечётный столбец вниз на половину
            if hex_grid_x < hex_grid_width and hex_grid_y < hex_grid_height: #не добавляем hexы за экраном
                cx = nachalo_x + col * shag_x
                cy = nachalo_y + (row + (col % 2) / 2) * shag_y
                tile = Hex(row, col, cx, cy, hex_grid_radius)
                tile.table_points = [
                    (cx + radius_x * math.cos(math.radians(60*i)),
                     cy + radius_y * math.sin(math.radians(60*i)))
                    for i in range(6)
                ]
                grid[(col, row)] = tile
    return grid


class KameraKarty:
    def __init__(self, razmer):
        self.shirina, self.vysota = razmer
        self.sbrosit()

    def sbrosit(self):
        self.masshtab = 1.0
        self.x = self.y = 0.0
        self.peretaskivanie = False

    def oblast(self):
        w = max(1, round(self.shirina / self.masshtab))
        h = max(1, round(self.vysota / self.masshtab))
        return pygame.Rect(round(self.x), round(self.y), w, h)

    def ogranichit(self):
        oblast = self.oblast()
        self.x = max(0, min(self.x, self.shirina - oblast.width))
        self.y = max(0, min(self.y, self.vysota - oblast.height))

    def v_koordinaty_karty(self, pozitsiya):
        oblast = self.oblast()
        return (oblast.x + pozitsiya[0] * oblast.width / self.shirina,
                oblast.y + pozitsiya[1] * oblast.height / self.vysota)

    def izmenit_masshtab(self, shag, pozitsiya):
        # Приближаем именно ту часть карты, на которую смотрит курсор.
        x, y = self.v_koordinaty_karty(pozitsiya)
        self.masshtab = max(1.0, min(3.0, self.masshtab * 1.15 ** max(-20, min(20, shag))))
        oblast = self.oblast()
        self.x = x - pozitsiya[0] * oblast.width / self.shirina
        self.y = y - pozitsiya[1] * oblast.height / self.vysota
        self.ogranichit()

    def sdvinut(self, sdvig):
        oblast = self.oblast()
        self.x -= sdvig[0] * oblast.width / self.shirina
        self.y -= sdvig[1] * oblast.height / self.vysota
        self.ogranichit()

    def narisovat(self, poverhnost, karta):
        oblast = self.oblast()
        if self.masshtab == 1.0:
            poverhnost.blit(karta, (0, 0))
        else:
            poverhnost.blit(pygame.transform.smoothscale(karta.subsurface(oblast),
                                                        (self.shirina, self.vysota)), (0, 0))


#HEX TOOL (Конкретная клетка под курсором мыши):
def hex_under_mouse(grid, mouse_pos=None):
    if mouse_pos is None:
        mouse_pos = pygame.mouse.get_pos()
    x, y = kamera_karty.v_koordinaty_karty(mouse_pos)
    # Проверяем настоящий многоугольник, а не круг вокруг центра гекса.
    for hex_tile in grid.values():
        cx, cy = hex_tile.center.x, hex_tile.center.y
        rx = hex_tile.table_points[0][0] - cx
        hy = hex_tile.table_points[1][1] - cy
        dx, dy = abs(x-cx), abs(y-cy)
        if dy <= hy + 1e-8 and dx / rx + dy / (2*hy) <= 1 + 1e-8:
            return hex_tile
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



#Все достижимые клетки:
# Все достижимые клетки и предшественники маршрута

def nayti_dostupnye_kletki(muravey, zapas=None):
    nachalo = (muravey.kletka.col, muravey.kletka.row)
    #Реальные затраты на клетку:
    # Тут считаем реальные затраты на клетки.
    ochered = [(0, nachalo)]
    rashody = {nachalo: 0}
    otkuda = {}

    zanyatye = {
        (drugoy.kletka.col, drugoy.kletka.row)
        for drugoy in muravi
        if drugoy is not muravey and drugoy.zdorovie > 0
    }
    # Клетки чужого маршрута тоже заняты, иначе два отряда могут прийти в одну точку.
    zanyatye.update((k.col, k.row) for drugoy in muravi
                    if drugoy is not muravey and drugoy.zdorovie > 0 for k in drugoy.marshrut)
    if zapas is None:
        zapas = muravey.ostalos_hodov

    while ochered:
        rashod, koord = heapq.heappop(ochered)
        if rashod > rashody[koord]:
            continue

        #ВОДА = СМЕРТЬ
        # Вода допускается как конечная ловушка.
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
            if novyy_rashod > zapas:
                continue

            if novyy_rashod < rashody.get(novye_koord, float("inf")):
                rashody[novye_koord] = novyy_rashod
                otkuda[novye_koord] = koord
                heapq.heappush(ochered, (novyy_rashod, novye_koord))

    rashody.pop(nachalo, None)
    return rashody, otkuda


def nayti_podhod_k_vragu(muravey, vrag, dostupnye=None):
    if (muravey.zdorovie <= 0 or vrag.zdorovie <= 0
            or muravey.komanda == vrag.komanda
            or muravey.atakoval_v_etom_hodu or muravey.marshrut
            or vrag.marshrut):
        return None

    #В упор не тратим очки хода:
    # Если уже в упор, то на атаку очки движения не нужны.
    if muravey.kletka.is_has_neighbor(vrag.kletka):
        return muravey.kletka

    if muravey.ostalos_hodov <= 0:
        return None

    if dostupnye is None:
        dostupnye, _ = nayti_dostupnye_kletki(muravey)

    varianty = []
    for kletka in nayti_sosedey(vrag.kletka, hex_grid):
        koord = (kletka.col, kletka.row)
        if koord not in dostupnye:
            continue
        tip = provintsii_kletok[koord]
        if tipy_provintsiy[tip].get("smertelna", False):
            continue
        varianty.append((dostupnye[koord], kletka.col, kletka.row))

    if not varianty:
        return None

    _, col, row = min(varianty)
    return hex_grid[(col, row)]



def scale_building_image(image, size):
    scale = size / max(image.get_width(), image.get_height())
    width = max(1, round(image.get_width() * scale))
    height = max(1, round(image.get_height() * scale))
    return pygame.transform.scale(image, (width, height))


def can_place_building(tile, building_type):
    coords = (tile.col, tile.row)
    terrain = tipy_provintsiy[provintsii_kletok[coords]]
    #ФИКС НЕ ПОСТАВИТЬ ЗДАНИЕ ПОД НОГАМИ
    # Проверяем ещё и маршрут юнита, чтобы не поставить здание прямо у него под ногами.
    is_occupied = any(
        unit.zdorovie > 0 and (unit.kletka is tile or tile in unit.marshrut)
        for unit in muravi
    )
    return (
        tile.build_unlocked
        and tile.building is None
        and terrain.get("prohodima", True)
        and not terrain.get("smertelna", False)
        and not is_occupied
        and resource_manager.is_affordable(building_type)
    )


def find_free_neighbor(tile, avoid_events=False):
    candidates = []
    for neighbor in nayti_sosedey(tile, hex_grid):
        coords = (neighbor.col, neighbor.row)
        terrain = tipy_provintsiy[provintsii_kletok[coords]]
        if not terrain.get("prohodima", True) or terrain.get("smertelna", False):
            continue
        occupied = any(
            unit.zdorovie > 0 and (unit.kletka is neighbor or neighbor in unit.marshrut)
            for unit in muravi
        )
        if not occupied and neighbor.building is None:
            candidates.append(neighbor)

    if avoid_events:
        for candidate in candidates:
            if candidate.event is None:
                return candidate

    return None if avoid_events else (candidates[0] if candidates else None)


def recruit_from_ant_house(ant_house, unit_type):
    if ant_house not in buildings or ant_house.name != "ant_house" or unit_type not in resource_manager.unit_costs:
        return False
    unit_count = sum(unit.poluchit_yacheyki() for unit in muravi if unit.komanda == "igrok" and unit.zdorovie > 0)
    max_units = sum(building.unit_slots for building in buildings)
    needed_slots = 12 * units[unit_type].get("yacheyki", 0)
    has_slot = max_units > 0 and (
        unit_count + needed_slots <= max_units if needed_slots > 0 else unit_count < max_units
    )

    if not has_slot:
        print("Нет свободных ячеек юнитов! Постройте ещё Муравейник.")
        return False

    if not resource_manager.is_unit_affordable(unit_type):
        print("Недостаточно ресурсов для найма!")
        return False

    spawn_tile = find_free_neighbor(ant_house.tile, avoid_events=True)
    if spawn_tile is None:
        print("Вокруг Муравейника нет свободной клетки!")
        return False

    new_unit = Muravey(unit_type, spawn_tile, "igrok", 12)
    resource_manager.apply_unit_cost(unit_type)
    muravi.append(new_unit)
    print(f"Нанят новый отряд: {units[unit_type].get('nazvanie', unit_type)}")
    return True


def create_random_event(event_type):
    if event_type == "enemy_ants":
        return {"type": "enemy_ants", "count": random.randint(3, 7)}
    if event_type == "spider":
        spider_count = 1 if units.get("pauk", {}).get("odin", False) else random.randint(2, 3)
        return {"type": "spider", "count": spider_count}
    if event_type == "tarantula":
        return {"type": "tarantula", "count": 1}
    if event_type == "add_resources":
        return {
            "type": "add_resources",
            "wood": random.randint(8, 16),
            "stone": random.randint(6, 14)
        }
    if event_type == "add_units":
        return {
            "type": "add_units",
            "unit_type": random.choice(["rabochiy", "soldat"]),
            "count": random.randint(5, 8)
        }
    if event_type == "mom_pies":
        return {"type": "mom_pies"}
    if event_type == "unlock_build":
        return {"type": "unlock_build"}
    return None


def generate_map_events():
    occupied_tiles = {unit.kletka for unit in muravi}
    valid_tiles = []

    for tile in hex_grid.values():
        if tile in occupied_tiles:
            continue
        if tile.center.y < 46 or hud.is_mouse_over(tuple(tile.center)) or hud.select_rect.collidepoint(tuple(tile.center)): #НЕ СТАВИМ ивенты под HUD
            continue
        coords = (tile.col, tile.row)
        terrain = tipy_provintsiy[provintsii_kletok[coords]]
        if not terrain.get("prohodima", True) or terrain.get("smertelna", False):
            continue
        valid_tiles.append(tile)

    random.shuffle(valid_tiles)

    start_center = hex_grid[(4, 4)].center #Макс. 5 клеток для разблокировки постройки + 1 поближе будет к старту
    nearby_tiles = [
        t for t in valid_tiles
        if 45 < t.center.distance_to(start_center) < 190
    ]
    unlock_tiles = []
    if nearby_tiles:
        first_unlock = random.choice(nearby_tiles)
        unlock_tiles.append(first_unlock)
        valid_tiles.remove(first_unlock)

    for tile in valid_tiles[:]:
        if len(unlock_tiles) >= 5:
            break
        if all(tile.center.distance_to(u.center) > 220 for u in unlock_tiles): #Ставим место под постройку друг от друга подальше по всей карте
            unlock_tiles.append(tile)
            valid_tiles.remove(tile)

    for tile in unlock_tiles:
        tile.event = create_random_event("unlock_build")
        tile.event_state = "unvisited" #ещё не посетили

    event_pool = ["add_resources", "enemy_ants", "spider", "tarantula", "add_units", "mom_pies"]
    event_weights = [30, 26, 18, 8, 11, 7]

    target_count = int(len(valid_tiles) * 0.12) #Ивенты будут располагаться на 12% всей оставшихся проходимых клеток
    for tile in valid_tiles[:target_count]:
        chosen_type = random.choices(event_pool, weights=event_weights, k=1)[0]
        tile.event = create_random_event(chosen_type)
        tile.event_state = "unvisited"


def trigger_hex_event(player_ant, tile):
    event_data = tile.event
    if event_data is None:
        return None

    event_type = event_data["type"]

    if event_type == "mom_pies":
        lost_count = player_ant.kolichestvo
        player_ant.umeret()
        tile.event = None
        tile.event_state = None
        return EventPopup(
            "МАМА ЗОВЁТ!",
            "Войнов позвала мама поесть горячие пирожки. Отряд бросил всё, убежал домой и больше не вернулся...",
            f"Потеряно юнитов: -{lost_count} (весь отряд)",
            "🥧",
            (235, 95, 90),
            "Эх... Щас бы тоже пирожков..."
        )
    if event_type == "add_resources":
        wood_gain = event_data["wood"]
        stone_gain = event_data["stone"]
        resource_manager.resources["wood"] += wood_gain
        resource_manager.resources["stone"] += stone_gain
        tile.event = None
        tile.event_state = None
        return EventPopup(
            "Тайник ресурсов",
            "Войны нашли заброшенные запасы стройматериалов среди корней и камней, и прочего.",
            f"+{wood_gain} дерева   |   +{stone_gain} камня",
            "🪵",
            (235, 195, 70),
            "СЮДА ЛУТ!"
        )

    if event_type == "unlock_build":
        tile.build_unlocked = True
        tile.event = None
        tile.event_state = None
        return EventPopup(
            "Вот это земля!",
            "Почва здесь идеально подходит для строительства! Эта клетка навсегда отмечена как площадка для постройки зданий.",
            "Клетка разблокирована для строительства",
            "🏗️",
            (85, 220, 150),
            "Супер!"
        )

    if event_type == "add_units":
        current_units = sum(u.poluchit_yacheyki() for u in muravi if u.komanda == "igrok" and u.zdorovie > 0)
        max_units = sum(b.unit_slots for b in buildings)
        new_type = event_data["unit_type"]
        new_count = event_data["count"]
        needed_slots = new_count * units[new_type].get("yacheyki", 0)
        has_slot = max_units > 0 and (
            current_units + needed_slots <= max_units if needed_slots > 0 else current_units < max_units
        )
        tile.event = None
        tile.event_state = None

        if not has_slot:
            return EventPopup(
                "Бродячие войны-муравьи",
                "К вам хотел присоединиться дружественный отряд, но в колонии не хватает свободных ячеек для юнитов!",
                f"Мест нет ({current_units}/{max_units}) — ивент пропущен",
                "🐜",
                (170, 175, 185),
                "Грустно, понятно)"
            )
        spawn_tile = find_free_neighbor(tile, avoid_events=True)
        unit_title = units[new_type].get("nazvanie", new_type)

        if spawn_tile is not None:
            muravi.append(Muravey(new_type, spawn_tile, "igrok", new_count))
            badge = f"+1 отряд ({unit_title}, {new_count} шт.)"
        else:
            new_sostav = dict(player_ant.sostav)
            new_sostav[new_type] = new_sostav.get(new_type, 0) + new_count
            player_ant.obnovit_sostav(new_sostav)
            badge = f"+{new_count} бойцов в ваш отряд"

        return EventPopup(
            "Муравийное подкрепление!",
            "Заблудившийся отряд муравьёв с радостью примкнул к вашей армии!",
            badge,
            "🐜",
            (95, 210, 115),
            "В строй!"
        )

    if event_type in ("enemy_ants", "spider", "tarantula"):
        count = event_data["count"]
        if event_type == "enemy_ants":
            enemy_key = "soldat"
            title = "Враги!"
            desc = "На пути оказался отряд враждебных муравьёв-солдат. Они не пропустят вас без боя!"
            emoji = "⚔️"
        elif event_type == "spider":
            enemy_key = "pauk"
            title = "ПаУк!"
            desc = "Из-под листвы выбрались хищные пауки. Приготовьтесь к сражению!"
            emoji = "🕷️"
        else:
            enemy_key = "tarantul"
            title = "Логово тарантула!"
            desc = "Вы потревожили огромных тарантулов. Будет тяжёлая схватка!"
            emoji = "🦂"

        enemy_name = units[enemy_key].get("nazvanie", enemy_key)
        return EventPopup(
            title,
            desc,
            f"Противник: {enemy_name} ({count} шт.)",
            emoji,
            (235, 80, 75),
            "В бой!",
            battle_data={
                "player_ant": player_ant,
                "tile": tile,
                "enemy_type": enemy_key,
                "count": count
            }
        )
    return None


def draw_tile_markers(surface):
    for tile in hex_grid.values():
        if tile.build_unlocked:
            if tile.building is None:
                mark = marker_font.render("+", True, (177, 229, 135))
                surface.blit(mark, mark.get_rect(center=tuple(tile.center)))

        if tile.event is not None:
            cx, cy = int(tile.center.x), int(tile.center.y)
            is_failed = tile.event_state == "failed_battle"
            color = (255, 65, 65) if is_failed else (255, 230, 0)
            symbol = "!" if is_failed else "?"

            shadow = marker_font.render(symbol, True, (15, 15, 20))
            mark = marker_font.render(symbol, True, color)
            surface.blit(shadow, shadow.get_rect(center=(cx + 1, cy + 1)))
            surface.blit(mark, mark.get_rect(center=(cx, cy)))


def process_pending_events():
    global event_popup, vybrannyy_muravey, tsel_ataki, kontekstnoe_menu, okno_otryada, razdelenie, selected_ant_house
    while pending_event_triggers and event_popup is None:
        triggered_ant, triggered_tile = pending_event_triggers.popleft()
        if triggered_ant.zdorovie <= 0 or triggered_ant.kletka is not triggered_tile or triggered_tile.event is None:
            continue
        vybrannyy_muravey = tsel_ataki = kontekstnoe_menu = okno_otryada = razdelenie = None
        hud.selected_tile = None
        selected_ant_house = None
        kamera_karty.peretaskivanie = False
        event_popup = trigger_hex_event(triggered_ant, triggered_tile)


def start_event_battle(battle_data):
    global avtoboy, active_event_battle
    player = battle_data["player_ant"]
    tile = battle_data["tile"]
    if player.zdorovie <= 0 or tile.event is None:
        return
    enemy = Muravey(battle_data["enemy_type"], tile, "vrag", battle_data["count"])
    active_event_battle = {"tile": tile, "enemy": enemy}
    player.atakoval_v_etom_hodu = True
    avtoboy = Avtoboy(player, enemy)


def finish_event_battle():
    global active_event_battle
    if active_event_battle is None:
        return
    tile, enemy = active_event_battle["tile"], active_event_battle["enemy"]
    if enemy.kolichestvo <= 0:
        tile.event = tile.event_state = None
    elif tile.event is not None:
        tile.event["count"] = enemy.kolichestvo
        tile.event_state = "failed_battle"
    active_event_battle = None


# Управление составом отрядов

def nayti_otryad_na_kletke(kletka):
    return next((m for m in muravi if m.kletka is kletka and m.zdorovie > 0), None)


def mozhno_upravlyat(otryad):
    return (otryad in muravi and otryad.komanda == "igrok" and otryad.zdorovie > 0
            and not otryad.odin and not otryad.marshrut and otryad.vrag_dlya_boya is None)


def cena_obiedineniya(otryad, sosed):
    if (otryad is sosed or not mozhno_upravlyat(otryad) or not mozhno_upravlyat(sosed)
            or not otryad.kletka.is_has_neighbor(sosed.kletka) or otryad.ostalos_hodov <= 0):
        return None
    dannye = tipy_provintsiy[provintsii_kletok[(sosed.kletka.col, sosed.kletka.row)]]
    cena = dannye["stoimost"]
    if (not dannye.get("prohodima", True) or dannye.get("smertelna", False)
            or cena is None or cena < 0 or cena > otryad.ostalos_hodov):
        return None
    if any(sosed.kletka in m.marshrut for m in muravi if m.zdorovie > 0):
        return None
    return cena


def nachat_obiedinenie(otryad, sosed):
    cena = cena_obiedineniya(otryad, sosed)
    if cena is None:
        return False
    otryad.ostalos_hodov -= cena
    otryad.marshrut = [sosed.kletka]
    return True


def obiedinit_otryady(otryad, sosed):
    if (otryad is sosed or not mozhno_upravlyat(otryad) or not mozhno_upravlyat(sosed)
            or otryad.kletka is not sosed.kletka):
        return False
    sostav = dict(sosed.sostav)
    for tip, kol in otryad.sostav.items():
        sostav[tip] = sostav.get(tip, 0) + kol
    # Берём минимальный остаток, иначе можно будет восстанавливать очки объединением.
    sosed.ostalos_hodov = min(otryad.ostalos_hodov, sosed.ostalos_hodov)
    sosed.atakoval_v_etom_hodu = otryad.atakoval_v_etom_hodu or sosed.atakoval_v_etom_hodu
    sosed.obnovit_sostav(sostav)
    # Это объединение, а не смерть отряда, поэтому эффект смерти не запускаем.
    muravi.remove(otryad)
    otryad.sostav.clear()
    otryad.kolichestvo = otryad.zdorovie = 0
    return True


def dostupnye_dlya_razdeleniya(otryad, sostav):
    if not mozhno_upravlyat(otryad) or otryad.ostalos_hodov <= 0:
        return {}, {}
    if any(tip not in otryad.sostav or kol < 0 or kol > otryad.sostav[tip]
           for tip, kol in sostav.items()):
        return {}, {}
    sostav = {tip: kol for tip, kol in sostav.items() if kol > 0}
    if not sostav or sum(sostav.values()) >= otryad.kolichestvo:
        return {}, {}
    zapas = min(otryad.ostalos_hodov, *(units[tip]["prohodimost"] for tip in sostav))
    return nayti_dostupnye_kletki(otryad, zapas)


def razdelit_otryad(otryad, sostav, kletka):
    dostupnye, otkuda = dostupnye_dlya_razdeleniya(otryad, sostav)
    koord = (kletka.col, kletka.row)
    if koord not in dostupnye:
        return None
    sostav = {tip: kol for tip, kol in sostav.items() if kol > 0}
    tip = next(iter(sostav))
    novyy = Muravey(tip, otryad.kletka, otryad.komanda, sostav[tip])
    novyy.ostalos_hodov = otryad.ostalos_hodov
    novyy.atakoval_v_etom_hodu = otryad.atakoval_v_etom_hodu
    novyy.ugol = otryad.ugol
    novyy.obnovit_sostav(sostav)
    nachalo = (otryad.kletka.col, otryad.kletka.row)
    tekushchaya = koord
    while tekushchaya != nachalo:
        novyy.marshrut.append(hex_grid[tekushchaya])
        tekushchaya = otkuda[tekushchaya]
    novyy.marshrut.reverse()
    # Старый отряд никуда не идёт, поэтому очки у него остаются.
    novyy.ostalos_hodov -= dostupnye[koord]
    otryad.obnovit_sostav({tip: kol-sostav.get(tip, 0) for tip, kol in otryad.sostav.items()})
    muravi.append(novyy)
    return novyy


def nadpis_na_okne(poverhnost, fraza, tocka, razmer=18, cvet=(241, 243, 238), vyrovnyat="topleft"):
    kartinka = poluchit_shrift(razmer).render(str(fraza), True, cvet)
    rect = kartinka.get_rect()
    setattr(rect, vyrovnyat, tocka)
    poverhnost.blit(kartinka, rect)


class KontekstnoeMenu:
    def __init__(self, pozitsiya, otryad, sosed=None):
        self.otryad = otryad
        self.sosed = sosed
        self.punkty = ["Объединить"] if sosed is not None else ["Посмотреть состав", "Разделить"]
        shirina = max(font.size(punkt)[0] for punkt in self.punkty) + 32
        vysota = 34 * len(self.punkty)
        x = max(0, min(pozitsiya[0], screen.get_width()-shirina))
        y = max(0, min(pozitsiya[1], screen.get_height()-vysota))
        self.knopki = [pygame.Rect(x, y+i*34, shirina, 34) for i in range(len(self.punkty))]

    def aktivna(self, punkt):
        if punkt == "Объединить":
            return cena_obiedineniya(self.otryad, self.sosed) is not None
        if punkt == "Разделить":
            if not mozhno_upravlyat(self.otryad) or self.otryad.kolichestvo < 2 or self.otryad.ostalos_hodov <= 0:
                return False
            return bool(nayti_dostupnye_kletki(self.otryad)[0])
        return self.otryad.zdorovie > 0 and self.otryad in muravi

    def nazhatie(self, pozitsiya):
        for punkt, rect in zip(self.punkty, self.knopki):
            if rect.collidepoint(pozitsiya):
                return punkt if self.aktivna(punkt) else "neaktivna"
        return None

    def narisovat(self, poverhnost):
        for punkt, rect in zip(self.punkty, self.knopki):
            aktivna = self.aktivna(punkt)
            cvet = (217, 231, 245) if aktivna and rect.collidepoint(pygame.mouse.get_pos()) else (242, 242, 242)
            pygame.draw.rect(poverhnost, cvet, rect)
            nadpis_na_okne(poverhnost, punkt, (rect.left+16, rect.centery),
                           cvet=(32,32,32) if aktivna else (153,153,153), vyrovnyat="midleft")


class OknoSostava:
    def __init__(self, otryad):
        self.otryad = otryad
        self.panel = pygame.Rect(0, 0, 690, 555)
        self.panel.center = screen.get_rect().center
        self.knopka = pygame.Rect(0, 0, 290, 48)
        self.knopka.midbottom = (self.panel.centerx, self.panel.bottom-24)
        self.krestik = pygame.Rect(self.panel.right-48, self.panel.top+12, 36, 36)
        self.fon = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        self.fon.fill((9,17,25,170))

    def narisovat(self, poverhnost):
        otryad = self.otryad
        p = self.panel
        poverhnost.blit(self.fon, (0,0))
        pygame.draw.rect(poverhnost, (32,59,39), p)
        nadpis_na_okne(poverhnost, "СОСТАВ ОТРЯДА", (p.left+24,p.top+24), 26)
        for i, (podpis, cifra) in enumerate((("Численность", otryad.kolichestvo),
                                               ("Сила", round(otryad.poluchit_silu())),
                                               ("Ячейки", otryad.poluchit_yacheyki()))):
            rect = pygame.Rect(p.left+24+i*218,p.top+77,206,75)
            pygame.draw.rect(poverhnost,(52,83,42),rect)
            nadpis_na_okne(poverhnost,podpis,(rect.left+12,rect.top+9),16,(198,211,192))
            nadpis_na_okne(poverhnost,f"{cifra:,}".replace(","," "),(rect.left+12,rect.top+32),27)
        for i,(tip,kol) in enumerate(otryad.sostav.items()):
            rect = pygame.Rect(p.left+24,p.top+165+i*98,p.width-48,88)
            pygame.draw.rect(poverhnost,(48,75,49),rect)
            telo, usiki = zagruzchik_atlasov.poluchit_animatsiyu(tip,otryad.komanda,58)
            kartinka = telo["pokoy"][0].copy()
            if usiki:
                kartinka.blit(usiki[0],(0,0))
            poverhnost.blit(kartinka,kartinka.get_rect(center=(rect.left+42,rect.centery)))
            dannye = units[tip]
            nadpis_na_okne(poverhnost,dannye["nazvanie"],(rect.left+86,rect.top+10),21)
            nadpis_na_okne(poverhnost,f"Здоровье: {dannye['zdorovie']}   Урон: {dannye['uron']}",
                           (rect.left+86,rect.top+39),16,(198,211,192))
            nadpis_na_okne(poverhnost,f"Броня: {dannye.get('bronya',0)}%",(rect.left+86,rect.top+61),16,(198,211,192))
            nadpis_na_okne(poverhnost,kol,(rect.right-18,rect.centery),29,vyrovnyat="midright")
        nadpis_na_okne(poverhnost,f"Очки передвижения: {otryad.ostalos_hodov} / {otryad.prohodimost}",
                       (p.left+24,p.top+374))
        nadpis_na_okne(poverhnost,"Возможность атаки: " + ("Недоступна" if otryad.atakoval_v_etom_hodu else "Доступна"),
                       (p.left+24,p.top+407))
        self.narisovat_knopku(poverhnost,"ЗАКРЫТЬ",True)

    def narisovat_knopku(self, poverhnost, tekst, aktivna):
        cvet = (81,125,50) if aktivna else (70,76,67)
        if aktivna and self.knopka.collidepoint(pygame.mouse.get_pos()):
            cvet = (101,151,66)
        pygame.draw.rect(poverhnost,cvet,self.knopka)
        nadpis_na_okne(poverhnost,tekst,self.knopka.center,18,(255,255,255) if aktivna else (155,163,150),"center")


class OknoRazdeleniya(OknoSostava):
    def __init__(self, otryad):
        super().__init__(otryad)
        self.panel.height = 590
        self.panel.center = screen.get_rect().center
        self.krestik.topleft = (self.panel.right-48,self.panel.top+12)
        self.knopka.midbottom = (self.panel.centerx,self.panel.bottom-24)
        self.vybrannyy_sostav = {tip: 0 for tip in otryad.sostav}
        self.polzunki = {tip: pygame.Rect(self.panel.left+28,self.panel.top+128+i*84,self.panel.width-56,22)
                         for i,tip in enumerate(otryad.sostav)}
        self.peretaskivaem = None

    def sdvinut(self, tip, x):
        rect = self.polzunki[tip]
        dolya = max(0,min(1,(x-rect.left)/rect.width))
        self.vybrannyy_sostav[tip] = round(dolya*self.otryad.sostav[tip])

    def prichina(self):
        n = sum(self.vybrannyy_sostav.values())
        if not mozhno_upravlyat(self.otryad):
            return "Отряд сейчас недоступен"
        if self.otryad.ostalos_hodov <= 0:
            return "Недостаточно очков передвижения"
        if n <= 0:
            return "Выберите муравьёв"
        if n >= self.otryad.kolichestvo:
            return "В старом отряде должен остаться хотя бы один муравей"
        if not dostupnye_dlya_razdeleniya(self.otryad,self.vybrannyy_sostav)[0]:
            return "Нет доступных клеток"
        return None

    def obrabotat(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.krestik.collidepoint(event.pos):
                return "zakryt"
            if self.knopka.collidepoint(event.pos):
                return "razdelit" if self.prichina() is None else None
            for tip,rect in self.polzunki.items():
                if rect.inflate(12,14).collidepoint(event.pos):
                    self.peretaskivaem = tip
                    self.sdvinut(tip,event.pos[0])
                    break
        elif event.type == pygame.MOUSEMOTION and self.peretaskivaem is not None:
            self.sdvinut(self.peretaskivaem,event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.peretaskivaem = None
        return None

    def narisovat(self, poverhnost):
        p = self.panel
        o = self.otryad
        poverhnost.blit(self.fon,(0,0))
        pygame.draw.rect(poverhnost,(32,59,39),p)
        nadpis_na_okne(poverhnost,"РАЗДЕЛЕНИЕ ОТРЯДА",(p.left+24,p.top+24),26)
        nadpis_na_okne(poverhnost,"×",self.krestik.center,26,vyrovnyat="center")
        nadpis_na_okne(poverhnost,f"{o.kolichestvo} муравьёв  ·  {o.poluchit_yacheyki()} занятых ячеек",(p.left+24,p.top+64),16,(198,211,192))
        for tip,rect in self.polzunki.items():
            n = self.vybrannyy_sostav[tip]
            vsego = o.sostav[tip]
            nadpis_na_okne(poverhnost,units[tip]["nazvanie"],(rect.left,rect.top-32),18)
            nadpis_na_okne(poverhnost,f"{n} / {vsego}",(rect.right,rect.top-32),20,vyrovnyat="topright")
            pygame.draw.rect(poverhnost,(63,88,52),pygame.Rect(rect.left,rect.centery-4,rect.width,8))
            x = round(rect.left+rect.width*n/vsego)
            pygame.draw.rect(poverhnost,(122,164,92),pygame.Rect(rect.left,rect.centery-4,x-rect.left,8))
            pygame.draw.rect(poverhnost,(217,231,207),pygame.Rect(x-7,rect.top,14,rect.height))
        ostatok = {tip:kol-self.vybrannyy_sostav[tip] for tip,kol in o.sostav.items()}
        for i,(podpis,sostav) in enumerate((("Остаётся",ostatok),("Отделяется",self.vybrannyy_sostav))):
            rect = pygame.Rect(p.left+24+i*326,p.top+250,316,180)
            pygame.draw.rect(poverhnost,(52,83,42),rect)
            nadpis_na_okne(poverhnost,podpis,(rect.left+14,rect.top+10),18,(198,211,192))
            nadpis_na_okne(poverhnost,sum(sostav.values()),(rect.left+14,rect.top+35),30)
            for j,(tip,kol) in enumerate(sostav.items()):
                nadpis_na_okne(poverhnost,f"{units[tip]['nazvanie']}: {kol}",(rect.left+14,rect.top+77+j*22),16)
            sila = sila_sostava(sostav)
            yacheyki = yacheyki_sostava(sostav)
            nadpis_na_okne(poverhnost,f"Сила: {round(sila):,}".replace(","," "),(rect.left+14,rect.top+128),16)
            nadpis_na_okne(poverhnost,f"Ячейки: {yacheyki}",(rect.left+14,rect.top+151),16)
        nadpis_na_okne(poverhnost,f"Остаток очков передвижения: {o.ostalos_hodov}",(p.left+24,p.top+445),18)
        prichina = self.prichina()
        nadpis_na_okne(poverhnost,prichina or "После подтверждения выберите зелёную клетку",(p.left+24,p.top+475),16,
                       (236,169,160) if prichina else (198,211,192))
        self.narisovat_knopku(poverhnost,"РАЗДЕЛИТЬ",prichina is None)


# Графические эффекты отдельно от логики, чтобы они не влияли на результат боя.
class VizualnyeEffekty:
    def __init__(self):
        self.chastitsy = []
        self.random = random.Random(217)

    def pyl(self, pozitsiya, cvet, kol=3):
        for _ in range(kol):
            if len(self.chastitsy) >= 320:
                break
            ugol = self.random.uniform(0, math.tau)
            skorost = self.random.uniform(8, 24)
            self.chastitsy.append([pygame.math.Vector2(pozitsiya),
                                   pygame.math.Vector2(math.cos(ugol), math.sin(ugol))*skorost,
                                   self.random.uniform(.3, .65), cvet])

    def udar(self, pozitsiya, uron):
        if len(self.chastitsy) < 320:
            self.chastitsy.append([pygame.math.Vector2(pozitsiya), pygame.math.Vector2(0,-25),
                                   .65, (255, 227, 175), round(uron, 1)])

    def obnovit(self, dt):
        for ch in self.chastitsy:
            ch[0] += ch[1]*dt
            ch[2] -= dt
        self.chastitsy = [ch for ch in self.chastitsy if ch[2] > 0]

    def narisovat(self, poverhnost):
        for ch in self.chastitsy:
            p, _, vremya, cvet = ch[:4]
            alfa = min(255, int(vremya*390))
            if len(ch) == 5:
                kartinka = poluchit_shrift(12).render(f"−{ch[4]:g}", True, cvet)
                kartinka.set_alpha(alfa)
                poverhnost.blit(kartinka, kartinka.get_rect(center=(round(p.x),round(p.y)-12)))
                if vremya > .52:
                    pygame.draw.circle(poverhnost, (255, 235, 190), (round(p.x), round(p.y)), 2)
            else:
                radius = max(1, round(4-vremya*4))
                sloy = pygame.Surface((radius*2+2, radius*2+2), pygame.SRCALPHA)
                pygame.draw.circle(sloy, (*cvet, alfa//3), (radius+1,radius+1),radius)
                poverhnost.blit(sloy, (round(p.x)-radius,round(p.y)-radius))


teni = {}

def narisovat_ten(poverhnost, pozitsiya, shirina, vysota):
    kluch = (max(4, int(shirina)), max(4, int(vysota)))
    if kluch not in teni:
        w, h = kluch
        sloy = pygame.Surface(kluch, pygame.SRCALPHA)
        for i in range(8):
            otstup = i/16
            rect = pygame.Rect(round(w*otstup), round(h*otstup),
                               max(1, round(w*(1-2*otstup))), max(1,round(h*(1-2*otstup))))
            pygame.draw.ellipse(sloy, (12, 19, 12, (2+i*2 if w > 300 else 12+i*9)), rect)
        teni[kluch] = sloy
    sloy = teni[kluch]
    poverhnost.blit(sloy, sloy.get_rect(center=(round(pozitsiya[0])+2, round(pozitsiya[1])+3)))


teni_oblakov = {}


def narisovat_oblako(poverhnost, pozitsiya, shirina, vysota, variant):
    kluch = (shirina, vysota, variant)
    if kluch not in teni_oblakov:

        w, h = 180, 90
        sloy = pygame.Surface((w, h), pygame.SRCALPHA)
        rng = random.Random(900 + variant)
        pyatna = [(rng.randint(46, 134), rng.randint(29, 61), rng.randint(25, 43), rng.randint(18, 26)) for _ in range(8)]
        for i in range(12):
            scale = 1 - i * .058
            alfa = round(5 + 65 * (i / 11) ** 1.4)
            for cx, cy, rx, ry in pyatna:
                dx, dy = round(rx * scale), round(ry * scale)
                pygame.draw.ellipse(sloy, (10, 20, 10, alfa), (cx-dx, cy-dy, dx*2, dy*2))
        teni_oblakov[kluch] = pygame.transform.smoothscale(sloy, (shirina, vysota))
    sloy = teni_oblakov[kluch]
    poverhnost.blit(sloy, sloy.get_rect(center=pozitsiya))


def narisovat_marshrut(poverhnost, otryad, koord, dostupnye, otkuda):
    if koord not in dostupnye:
        return
    nachalo = (otryad.kletka.col, otryad.kletka.row)
    tochki = [hex_grid[koord].center]
    tek = koord
    while tek != nachalo:
        tek = otkuda[tek]
        tochki.append(hex_grid[tek].center)
    tochki.reverse()
    for a, b in zip(tochki, tochki[1:]):
        d = a.distance_to(b)
        for i in range(1, max(2, int(d/7))):
            p = a+(b-a)*(i/max(2,int(d/7)))
            pygame.draw.circle(poverhnost, (26,36,26), (round(p.x),round(p.y)), 3)
            pygame.draw.circle(poverhnost, (244,235,195), (round(p.x),round(p.y)), 2)
    p = tochki[-1]
    nadpis_na_okne(poverhnost, str(dostupnye[koord]), (round(p.x),round(p.y)-10), 16,
                   (255,248,218), 'center')


# Старый HUD оставляем как есть, меняем только то, что игрок видит и куда нажимает.
class VisualHUD(HUD):
    PANEL = (32, 59, 39)
    CARD = (52, 83, 42)
    TEXT = (241, 235, 221)
    MUTED = (189, 208, 182)
    ACCENT = (216, 187, 120)
    NAMES = {"Stone_Farm": "Каменоломня", "Wood_Farm": "Ферма", "ant_house": "Муравейник"}
    DETAILS = {"Stone_Farm": "+5 камня за ход", "Wood_Farm": "+5 дерева за ход",
               "ant_house": "+7 дерева и камня; +60 ячеек"}

    def __init__(self, resource_manager, width_hud, height_hud, building_images, resource_emojis):
        super().__init__(resource_manager,width_hud,height_hud,building_images,resource_emojis)
        w, h = width_hud, height_hud
        self.resources_rect = pygame.Rect(0,0,w,44)
        self.build_rect = pygame.Rect(w-332,h-146,320,84)
        self.select_rect = pygame.Rect(12,h-174,330,162)
        self.end_turn_button = EndTurnButton("ЗАВЕРШИТЬ ХОД  [N]", w-332, h-54, 320, 42)
        self.turn_rect = self.end_turn_button.rect
        self.selected_group = None
        self.recruit_rect = pygame.Rect(12,h-276,420,264)
        self.recruit_buttons = []
        self.recruit_icons = {unit_type: Animatsiya(unit_type, "igrok", 58).kartinka(0)
                              for unit_type in ("rabochiy", "soldat")}
        self.ready = True
        self.editor = False
        self.resource_changes = {}
        self.previous_resources = dict(resource_manager.resources)
        self.tiles = []
        self.resource_icons = {name:font_smiles.render(emoji,True,self.TEXT)
                               for name,emoji in resource_emojis.items()}

        wood = pygame.Surface((30,30),pygame.SRCALPHA)
        pygame.draw.rect(wood,(116,78,43),(12,17,6,12))
        for y,half in ((1,8),(8,11),(14,14)):
            pygame.draw.polygon(wood,(72,150,64),[(15,y),(15-half,y+12),(15+half,y+12)])
        stone = pygame.Surface((30,30),pygame.SRCALPHA)
        pygame.draw.polygon(stone,(151,160,151),[(2,20),(6,9),(16,4),(25,10),(28,22),(19,27),(8,26)])
        pygame.draw.polygon(stone,(198,204,190),[(6,9),(16,4),(25,10),(14,15)])
        pygame.draw.polygon(stone,(106,118,107),[(14,15),(25,10),(28,22),(19,27)])
        self.resource_icons = {"wood":wood,"stone":stone}
        for index,(name,image) in enumerate(building_images.items()):
            rect = pygame.Rect(self.build_rect.x+8+index*102,self.build_rect.y+8,100,68)
            scale = min(54/image.get_width(),40/image.get_height())
            icon = pygame.transform.smoothscale(image,(max(1,round(image.get_width()*scale)),max(1,round(image.get_height()*scale))))
            self.tiles.append({"name":name,"icon":icon,"rect":rect})

    def is_mouse_over(self, mouse_pos):
        return (self.resources_rect.collidepoint(mouse_pos) or self.build_rect.collidepoint(mouse_pos)
                or self.turn_rect.collidepoint(mouse_pos)
                or (selected_ant_house is not None and not redaktor and self.recruit_rect.collidepoint(mouse_pos))
                or (vybrannyy_muravey is not None and not redaktor and self.select_rect.collidepoint(mouse_pos)))


    def draw_recruitment(self, surface, unit_count, max_units):
        panel = self.recruit_rect
        pygame.draw.rect(surface, self.PANEL, panel)
        nadpis_na_okne(surface, "МУРАВЕЙНИК", (panel.x + 12, panel.y + 12), 20, self.ACCENT)
        free_slots = max(0, max_units - unit_count)
        nadpis_na_okne(surface, f"Свободно: {free_slots} ячеек", (panel.x + 12, panel.y + 42), 16, self.MUTED)
        self.recruit_buttons = []
        mouse_pos = pygame.mouse.get_pos()
        for index, (unit_type, title) in enumerate((("rabochiy", "Рабочие × 12"), ("soldat", "Солдаты × 12"))):
            rect = pygame.Rect(panel.x + 10 + index * 202, panel.y + 70, 198, 184)
            pygame.draw.rect(surface, self.CARD, rect)
            icon = self.recruit_icons[unit_type]
            surface.blit(icon, icon.get_rect(center=(rect.centerx, rect.y + 32)))
            nadpis_na_okne(surface, title, (rect.centerx, rect.y + 70), 18, self.TEXT, "center")
            unit_data = units[unit_type]
            nadpis_na_okne(surface, f"ХП: {unit_data['zdorovie']}  Урон: {unit_data['uron']}", (rect.centerx, rect.y + 94), 14, self.TEXT, "center")
            cost = self.resource_manager.unit_costs[unit_type]
            nadpis_na_okne(surface, f"Дер: {cost['wood']}   Кам: {cost['stone']}", (rect.centerx, rect.y + 118), 16, self.ACCENT, "center")
            button_rect = pygame.Rect(rect.x + 6, rect.bottom - 38, rect.width - 12, 32)
            needed_slots = 12 * unit_data.get("yacheyki", 0)
            has_slot = unit_count + needed_slots <= max_units
            can_afford = self.resource_manager.is_unit_affordable(unit_type)
            has_free_neighbor = find_free_neighbor(selected_ant_house.tile, avoid_events=True) is not None
            b_enabled = has_slot and can_afford and has_free_neighbor
            hovered = button_rect.collidepoint(mouse_pos)
            label = "НАНЯТЬ" if b_enabled else "НЕТ ЯЧЕЕК" if not has_slot else "НЕТ РЕСУРСОВ" if not can_afford else "НЕТ МЕСТА"
            bg_color = (101, 151, 66) if b_enabled and hovered else (81, 125, 50) if b_enabled else (65, 73, 61)
            pygame.draw.rect(surface, bg_color, button_rect)
            nadpis_na_okne(surface, label, button_rect.center, 14, self.TEXT if b_enabled else self.MUTED, "center")
            self.recruit_buttons.append({"unit_type": unit_type, "title": title, "rect": button_rect})

    def draw(self, screen, unit_count=0, max_units=0):
        mouse = pygame.mouse.get_pos()
        for rect in (self.resources_rect,self.build_rect,self.turn_rect):
            pygame.draw.rect(screen,self.PANEL,rect)
        nadpis_na_okne(screen,f"ХОД {turn_number}",(16,22),20,self.ACCENT,'midleft')
        nadpis_na_okne(screen,f"Ячейки юнитов: {unit_count}/{max_units}",(155,22),18,
                       (240,150,137) if unit_count>max_units else self.TEXT,'midleft')
        if self.editor:
            nadpis_na_okne(screen,"РЕДАКТОР · F5 — сохранить",(self.width_hud//2,22),18,self.ACCENT,'center')
        for i,(name,value) in enumerate(self.resource_manager.resources.items()):
            x = self.width_hud-430+i*210
            icon = self.resource_icons.get(name)
            if icon is not None:
                screen.blit(icon,icon.get_rect(midleft=(x,22)))
            nadpis_na_okne(screen,f"{'Дерево' if name == 'wood' else 'Камень'}: {value}",(x+34,22),18,self.TEXT,'midleft')
            old = self.previous_resources.get(name,value)
            if old != value:
                self.resource_changes[name] = (value-old,1.3)
            self.previous_resources[name] = value
            if name in self.resource_changes:
                change,t = self.resource_changes[name]
                nadpis_na_okne(screen,f"{change:+d}",(x+155,22),16,(166,214,139) if change>0 else (240,150,137),'midleft')
                self.resource_changes[name] = (change,t-delta_time)
                if t <= 0:
                    del self.resource_changes[name]
        hovered = None
        for tile in self.tiles:
            rect = tile['rect']
            active = self.selected_tile is tile
            over = rect.collidepoint(mouse)
            affordable = self.resource_manager.is_affordable(tile['name'])
            pygame.draw.rect(screen,(102,120,67) if active else (75,94,65) if over else self.CARD,rect)
            icon = tile['icon']
            screen.blit(icon,icon.get_rect(center=(rect.centerx,rect.top+23)))
            nadpis_na_okne(screen,self.NAMES[tile['name']],(rect.centerx,rect.bottom-12),12,self.TEXT if affordable else (212,154,141),'center')
            if over:
                hovered = tile['name']
        has_unused_moves = any(unit.komanda == "igrok" and unit.zdorovie > 0 and unit.ostalos_hodov > 0 for unit in muravi)
        self.end_turn_button.draw(screen, turn_number, self.ready, has_unused_moves)
        group = self.selected_group
        if selected_ant_house is not None and not self.editor:
            self.draw_recruitment(screen,unit_count,max_units)
        elif group is not None:
            p = self.select_rect
            pygame.draw.rect(screen,self.PANEL,p)
            nadpis_na_okne(screen,group.nazvanie.upper(),(p.x+12,p.y+12),18,self.ACCENT)
            nadpis_na_okne(screen,f"Численность: {group.kolichestvo}",(p.x+12,p.y+43),16,self.TEXT)
            nadpis_na_okne(screen,f"Сила: {round(group.poluchit_silu()):,}".replace(',',' '),(p.x+12,p.y+68),16,self.TEXT)
            nadpis_na_okne(screen,"Атака: " + ("использована" if group.atakoval_v_etom_hodu else "доступна"),(p.x+12,p.y+93),16,self.MUTED)
            for i in range(group.prohodimost):
                pygame.draw.rect(screen,(131,166,109) if i<group.ostalos_hodov else self.CARD,(p.x+12+i*24,p.y+129,20,12))
            nadpis_na_okne(screen,f"{group.ostalos_hodov}/{group.prohodimost}",(p.x+130,p.y+135),16,self.TEXT,'midleft')
        if hovered:
            rect = pygame.Rect(self.build_rect.x-30,self.build_rect.y-100,350,92)
            pygame.draw.rect(screen,self.PANEL,rect)
            cost = self.resource_manager.costs[hovered]
            nadpis_na_okne(screen,self.NAMES[hovered],(rect.x+12,rect.y+10),18,self.ACCENT)
            nadpis_na_okne(screen,f"Дерево: {cost['wood']}   Камень: {cost['stone']}",(rect.x+12,rect.y+37),16,self.TEXT)
            nadpis_na_okne(screen,self.DETAILS[hovered],(rect.x+12,rect.y+62),14,self.MUTED)


setka_sloy = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
karta_sloy = pygame.Surface(screen.get_size())
kamera_karty = KameraKarty(screen.get_size())

cveta_koloniy = {"igrok": (82, 125, 200), "vrag": (189, 77, 77)}
zagruzchik_atlasov = ZagruzchikAtlasov()

shrift_imen_vragov = poluchit_shrift(12)
marker_font = poluchit_shrift(22)

shrift_smerti = poluchit_shrift(12)
tekst_smerti = shrift_smerti.render("Смерть", True, (255, 255, 255))


resource_emojis = {
    "wood": "🌲",
    "stone": "🪨"
}

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

def next_turn():
    global turn_number, vybrannyy_muravey, tsel_ataki
    turn_number += 1
    for muravey in muravi:
        if muravey.zdorovie > 0:
            muravey.ostalos_hodov = muravey.prohodimost
            muravey.atakoval_v_etom_hodu = False
    vybrannyy_muravey = None
    tsel_ataki = None
    for building in buildings:
        building.produce_per_turn()
    print(f"Новый ход: {turn_number}")


# При выходе в меню начинаем с чистой карты и стартовых отрядов.
def sbrosit_igru():
    global hex_grid, put_karty, provintsii_kletok, muravi, vybrannyy_muravey
    global tsel_ataki, avtoboy, kontekstnoe_menu, okno_otryada, razdelenie, slivanie
    global effekty_smerti, buildings, resource_manager, hud, redaktor, tip_kisti
    global event_popup, pending_event_triggers, active_event_battle, selected_ant_house, turn_number, end_turn_button
    global x, delta_time, setka_obych, setka_redaktor, podsvetka_vremya, poslednee_vydelenie, vremya_okna, poslednee_okno, vremya_oblakov

    # Инициализация карты
    kamera_karty.sbrosit()
    hex_grid = create_hex_grid(HEX_GRID_WIDTH, HEX_GRID_HEIGHT, HEX_GRID_RADIUS)
    put_karty = os.path.join(data_dir, "karta_provintsiy.json")
    provintsii_kletok = {koord: "polya" for koord in hex_grid}

    if os.path.exists(put_karty):
        with open(put_karty, "r", encoding="utf-8") as fail:
            sohranennye = json.load(fail)
        for koord, tip in sohranennye.items():
            col, row = map(int, koord.split(","))
            if (col, row) in hex_grid and tip in tipy_provintsiy:
                provintsii_kletok[(col, row)] = tip


    muravi = [
        Muravey("rabochiy", hex_grid[(4, 4)], "igrok", 12),
        Muravey("soldat", hex_grid[(6, 4)], "igrok", 12),
        Muravey("soldat", hex_grid[(10, 4)], "vrag", 9),
        Muravey("tarantul", hex_grid[(12, 4)], "vrag", 1)
    ]
    # Если на своей карте кто-то залил точку появления паука водой, ищем ближайшую сухую клетку.
    zanyatye_pri_spavne = {(m.kletka.col, m.kletka.row) for m in muravi}
    kletka_pauka = min((k for koord, k in hex_grid.items()
                       if koord not in zanyatye_pri_spavne
                       and tipy_provintsiy[provintsii_kletok[koord]].get("prohodima", True)
                       and not tipy_provintsiy[provintsii_kletok[koord]].get("smertelna", False)),
                      key=lambda k: k.center.distance_squared_to(hex_grid[(18, 5)].center), default=None)
    if kletka_pauka is not None:
        muravi.append(Muravey("pauk", kletka_pauka, "vrag", 1))

    vybrannyy_muravey = None
    tsel_ataki = None
    avtoboy = None
    kontekstnoe_menu = None
    okno_otryada = None
    razdelenie = None
    slivanie = None
    effekty_smerti = []
    buildings = []
    resource_manager = ResourceManager()
    selected_ant_house = None
    turn_number = 1
    hud = VisualHUD(resource_manager, 1600, 900, building_textures, resource_emojis)
    end_turn_button = hud.end_turn_button
    setka_obych = pygame.Surface(screen.get_size(),pygame.SRCALPHA)
    setka_redaktor = pygame.Surface(screen.get_size(),pygame.SRCALPHA)
    for tile in hex_grid.values():
        pygame.draw.polygon(setka_obych,(30,44,28,52),tile.table_points,1)
        pygame.draw.polygon(setka_redaktor,(200,200,200,90),tile.table_points,3)
    podsvetka_vremya = 0.0
    poslednee_vydelenie = None
    vremya_okna = 0.0
    poslednee_okno = None
    vremya_oblakov = 0.0
    redaktor = False
    event_popup = None
    active_event_battle = None
    pending_event_triggers = deque()
    generate_map_events()
    tip_kisti = "les"
    x = 1000
    delta_time = 0.1


sbrosit_igru()

# Главное меню работает отдельно от игрового цикла, пока игрок не нажмёт «Играть».
main_menu = MainMenu(screen, MenuBackground(screen.get_size(),
                                            tekstury_pola_boya.get("polya"),
                                            zagruzchik_atlasov),
                     poluchit_shrift)
running = main_menu.run() == "play"
clock.tick(60)

while running:
    delta_time = max(0.001, min(0.1, clock.tick(60) / 1000))
    mouse_pos = pygame.mouse.get_pos()
    events = pygame.event.get()

    # Esc открывает меню даже во время боя. Пока меню открыто, игра стоит.
    if any(event.type == pygame.QUIT for event in events):
        running = False
        break
    if any(event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE for event in events):
        kamera_karty.peretaskivanie = False
        menu_action = main_menu.run("pause")
        if menu_action == "menu":
            sbrosit_igru()
            running = main_menu.run() == "play"
        elif menu_action == "quit":
            running = False
        clock.tick(60)
        continue

    # Пока идёт автобой, стратегическая карта полностью ждёт.
    #Идёт автобой или открыто окно ивента = карта ждёт
    if avtoboy is not None:
        avtoboy.obnovit(delta_time)
    elif event_popup is None:

        if not pending_event_triggers:
            x += 50 * delta_time
            for muravey in muravi:
                muravey.obnovit(delta_time)

        if slivanie is not None:
            otryad, sosed = slivanie
            if not otryad.marshrut:
                if obiedinit_otryady(otryad, sosed):
                    vybrannyy_muravey = sosed
                    pending_event_triggers = deque((sosed if m is otryad else m,k) for m,k in pending_event_triggers)
                slivanie = None

        process_pending_events()

        for muravey in muravi if event_popup is None else ():
            vrag = muravey.vrag_dlya_boya
            if vrag is None or muravey.marshrut:
                continue
            muravey.vrag_dlya_boya = None
            if (muravey.zdorovie > 0 and vrag.zdorovie > 0
                    and muravey.kolichestvo > 0 and vrag.kolichestvo > 0
                    and muravey.kletka.is_has_neighbor(vrag.kletka)):
                avtoboy = Avtoboy(muravey, vrag)
                kontekstnoe_menu = okno_otryada = razdelenie = None
                break

        if vybrannyy_muravey is not None:
            mozhet_atakovat_ryadom = (
                not vybrannyy_muravey.atakoval_v_etom_hodu
                and any(
                    drugoy.zdorovie > 0
                    and drugoy.komanda != vybrannyy_muravey.komanda
                    and vybrannyy_muravey.kletka.is_has_neighbor(drugoy.kletka)
                    for drugoy in muravi
                )
            )
            if (vybrannyy_muravey.zdorovie <= 0
                    or vybrannyy_muravey.marshrut
                    or (vybrannyy_muravey.ostalos_hodov <= 0
                        and not mozhet_atakovat_ryadom)):
                vybrannyy_muravey = None
                tsel_ataki = None

        if tsel_ataki is not None:
            if tsel_ataki.zdorovie <= 0 or vybrannyy_muravey is None:
                tsel_ataki = None


    hud.selected_group = vybrannyy_muravey if not redaktor else None
    hud.editor = redaktor
    hud.ready = (not redaktor and event_popup is None and not pending_event_triggers and avtoboy is None and slivanie is None and razdelenie is None
                 and okno_otryada is None and kontekstnoe_menu is None
                 and all(not m.marshrut and m.vrag_dlya_boya is None for m in muravi))
    # Кнопка вызывает тот же обработчик N, а не отдельную логику завершения хода.
    if hud.ready:
        for i,event in enumerate(events):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and end_turn_button.handle_click(event.pos, hud.ready):
                events[i] = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_n)
                end_turn_button.pressed = .12
    boy_zakryvalsya_v_etom_kadre = avtoboy is not None
    okno_zakryto_v_etom_kadre = False
    popup_otkryt_v_etom_kadre = event_popup is not None
    for event in events:
        if event.type == pygame.QUIT:
            running = False
            continue

        if boy_zakryvalsya_v_etom_kadre:
            #ФИКС после клика «Вернуться» не пускаем на карту (если быстрый кадр):
            # Даже после клика «Вернуться» остатки событий этого кадра не пускаем на карту.
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if avtoboy is not None and avtoboy.obrabotat_nazhatie(event.pos):
                    finish_event_battle()
                    avtoboy = None
                    vybrannyy_muravey = None
                    tsel_ataki = None
            continue

        if popup_otkryt_v_etom_kadre:
            if event_popup is not None and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if event_popup.handle_click(event.pos):
                    battle_data = event_popup.battle_data
                    event_popup = None
                    if battle_data is not None:
                        start_event_battle(battle_data)
            continue

        # Колёсико и средняя кнопка управляют только картой, HUD и окна остаются на месте.
        if event.type == pygame.MOUSEBUTTONUP and event.button == 2:
            kamera_karty.peretaskivanie = False
            continue
        kamera_dostupna = okno_otryada is None and kontekstnoe_menu is None
        if event.type == pygame.MOUSEWHEEL:
            if kamera_dostupna and not hud.is_mouse_over(mouse_pos):
                kamera_karty.izmenit_masshtab(event.y, mouse_pos)
            continue
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
            kamera_karty.peretaskivanie = kamera_dostupna and not hud.is_mouse_over(event.pos)
            continue
        if event.type == pygame.MOUSEMOTION and kamera_karty.peretaskivanie:
            if kamera_dostupna and event.buttons[1]:
                kamera_karty.sdvinut(event.rel)
            else:
                kamera_karty.peretaskivanie = False
            continue
        if event.type == pygame.KEYDOWN and event.key == pygame.K_HOME and kamera_dostupna:
            kamera_karty.sbrosit()
            continue

        # На время объединения не даём второму отряду уйти с клетки.
        if slivanie is not None or okno_zakryto_v_etom_kadre:
            continue

        if event.type == pygame.KEYDOWN and event.key in (pygame.K_n, pygame.K_F2):
            kontekstnoe_menu = okno_otryada = razdelenie = None

        # Клики в окнах не должны ещё и двигать отряд на карте.
        if okno_otryada is not None:
            if isinstance(okno_otryada, OknoRazdeleniya):
                deystvie = okno_otryada.obrabotat(event)
                if deystvie == "razdelit":
                    razdelenie = (okno_otryada.otryad, dict(okno_otryada.vybrannyy_sostav))
                    vybrannyy_muravey = okno_otryada.otryad
                    okno_otryada = None
                    okno_zakryto_v_etom_kadre = True
                elif deystvie == "zakryt":
                    okno_otryada = None
                    okno_zakryto_v_etom_kadre = True
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if okno_otryada.knopka.collidepoint(event.pos):
                    okno_otryada = None
                    okno_zakryto_v_etom_kadre = True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                okno_otryada = None
                okno_zakryto_v_etom_kadre = True
            continue

        if kontekstnoe_menu is not None:
            if event.type == pygame.MOUSEBUTTONDOWN:
                punkt = kontekstnoe_menu.nazhatie(event.pos) if event.button == 1 else None
                if punkt == "neaktivna":
                    continue
                if punkt == "Объединить":
                    otryad, sosed = kontekstnoe_menu.otryad, kontekstnoe_menu.sosed
                    if nachat_obiedinenie(otryad, sosed):
                        slivanie = (otryad, sosed)
                        vybrannyy_muravey = None
                elif punkt == "Посмотреть состав":
                    okno_otryada = OknoSostava(kontekstnoe_menu.otryad)
                elif punkt == "Разделить":
                    okno_otryada = OknoRazdeleniya(kontekstnoe_menu.otryad)
                kontekstnoe_menu = None
                okno_zakryto_v_etom_kadre = True
            continue

        if razdelenie is not None:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    razdelenie = None
                    okno_zakryto_v_etom_kadre = True
                elif event.button == 1 and not hud.is_mouse_over(event.pos):
                    kletka = hex_under_mouse(hex_grid,event.pos)
                    if kletka is not None and razdelit_otryad(*razdelenie,kletka) is not None:
                        vybrannyy_muravey = razdelenie[0]
                        razdelenie = None
                        okno_zakryto_v_etom_kadre = True
            continue

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F2:
                redaktor = not redaktor
                selected_ant_house = None
                hud.selected_tile = None
                vybrannyy_muravey = None
                tsel_ataki = None
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
                    json.dump(dannye_karty, fail, ensure_ascii=False, indent=2)
                print("Карта сохранена!")

            if event.key == pygame.K_n and not redaktor:
                if all(not muravey.marshrut and muravey.vrag_dlya_boya is None
                       for muravey in muravi):
                    next_turn()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                selected_ant_house = None
                hud.selected_tile = None
                vybrannyy_muravey = None
                tsel_ataki = None
                if not redaktor and not hud.is_mouse_over(event.pos):
                    otryad = nayti_otryad_na_kletke(hex_under_mouse(hex_grid,event.pos))
                    if otryad is not None and otryad.komanda == "igrok":
                        kontekstnoe_menu = KontekstnoeMenu(event.pos,otryad)
                continue

            if event.button == 1 and not redaktor:
                if hud.is_mouse_over(event.pos):
                    if selected_ant_house is not None and hud.recruit_rect.collidepoint(event.pos):
                        for btn in hud.recruit_buttons:
                            if btn["rect"].collidepoint(event.pos):
                                recruit_from_ant_house(selected_ant_house, btn["unit_type"])
                                break
                        continue
                    for tile in hud.tiles:
                        if tile["rect"].collidepoint(event.pos):
                            hud.selected_tile = tile
                            selected_ant_house = None
                            vybrannyy_muravey = None
                            tsel_ataki = None
                            break
                    continue

                kletka = hex_under_mouse(hex_grid, event.pos)
                if kletka is None:
                    selected_ant_house = None
                    continue

                #Выбрали постройку не дёргаем муравья:
                # Если выбрали постройку, этот клик уже не должен двигать муравья.
                if hud.selected_tile is not None:
                    building_type = hud.selected_tile["name"]
                    if can_place_building(kletka, building_type):
                        building = BUILDING_CLASSES[building_type](kletka, resource_manager)
                        kletka.building = building
                        buildings.append(building)
                        hud.selected_tile = None
                    continue

                selected_ant_house = None
                if isinstance(kletka.building, Ant_House) and nayti_otryad_na_kletke(kletka) is None:
                    selected_ant_house = kletka.building
                    vybrannyy_muravey = tsel_ataki = None
                    continue

                nazhatyy_muravey = None
                for muravey in muravi:
                    if muravey.kletka is kletka and muravey.zdorovie > 0:
                        nazhatyy_muravey = muravey
                        break

                if nazhatyy_muravey is not None:
                    if nazhatyy_muravey.komanda == "igrok":
                        if (kletka.event_state == "failed_battle" and not nazhatyy_muravey.marshrut
                                and not nazhatyy_muravey.atakoval_v_etom_hodu):
                            pending_event_triggers.append((nazhatyy_muravey,kletka))
                            process_pending_events()
                            popup_otkryt_v_etom_kadre = True
                            continue
                        tsel_ataki = None
                        if (vybrannyy_muravey is not None and vybrannyy_muravey is not nazhatyy_muravey
                                and mozhno_upravlyat(vybrannyy_muravey) and mozhno_upravlyat(nazhatyy_muravey)
                                and vybrannyy_muravey.kletka.is_has_neighbor(nazhatyy_muravey.kletka)):
                            kontekstnoe_menu = KontekstnoeMenu(event.pos,vybrannyy_muravey,nazhatyy_muravey)
                            continue
                        mozhet_atakovat = (
                            not nazhatyy_muravey.atakoval_v_etom_hodu
                            and any(
                                drugoy.zdorovie > 0
                                and drugoy.komanda != nazhatyy_muravey.komanda
                                and nazhatyy_muravey.kletka.is_has_neighbor(drugoy.kletka)
                                for drugoy in muravi
                            )
                        )
                        if (not nazhatyy_muravey.marshrut
                                and (nazhatyy_muravey.ostalos_hodov > 0
                                     or mozhet_atakovat)):
                            vybrannyy_muravey = nazhatyy_muravey
                        else:
                            vybrannyy_muravey = None

                    elif vybrannyy_muravey is not None:
                        kletka_podhoda = nayti_podhod_k_vragu(
                            vybrannyy_muravey, nazhatyy_muravey
                        )
                        if kletka_podhoda is None:
                            tsel_ataki = None
                            print("Враг недоступен для атаки в этом ходу")
                        elif tsel_ataki is not nazhatyy_muravey:
                            tsel_ataki = nazhatyy_muravey
                            print("Нажми ещё раз по врагу для подтверждения атаки")
                        else:
                            if kletka_podhoda is vybrannyy_muravey.kletka:
                                uspeshno = True
                            else:
                                uspeshno = vybrannyy_muravey.peremestitsya(
                                    kletka_podhoda
                                )
                            if uspeshno:
                                # Подход оплачиваем, а сама атака очки движения не забирает.
                                vybrannyy_muravey.vrag_dlya_boya = nazhatyy_muravey
                                vybrannyy_muravey.atakoval_v_etom_hodu = True
                                vybrannyy_muravey = None
                            tsel_ataki = None
                else:
                    tsel_ataki = None
                    if vybrannyy_muravey is not None:
                        vybrannyy_muravey.peremestitsya(kletka)

    hud.selected_group = vybrannyy_muravey if not redaktor else None
    if event_popup is not None or kamera_karty.peretaskivanie or hud.is_mouse_over(mouse_pos) or avtoboy is not None or okno_otryada is not None or kontekstnoe_menu is not None:
        hovered_tile = None
    else:
        hovered_tile = hex_under_mouse(hex_grid)

    if (avtoboy is None and event_popup is None and redaktor and hovered_tile is not None
            and pygame.mouse.get_pressed()[0]):
        koord = (hovered_tile.col, hovered_tile.row)
        provintsii_kletok[koord] = tip_kisti

    karta_sloy.fill((128, 128, 128))
    karta_sloy.blit(stonewall1_img, (x, 500))
    karta_sloy.blit(scaled_map_img, (0, 0))

    if avtoboy is None and event_popup is None:
        vremya_oblakov += delta_time

    for i,(w,h,speed,y) in enumerate(((620,260,11,190),(480,200,17,480),(710,280,8,740),(390,180,22,360))):
        px = ((vremya_oblakov*speed+250+i*540) % (karta_sloy.get_width()+w))-w//2
        narisovat_oblako(karta_sloy,(round(px),y),w,h,i)
    setka_sloy.fill((0, 0, 0, 0))
    for tile in hex_grid.values():
        if tile.build_unlocked and tile.building is None:
            pygame.draw.polygon(setka_sloy,(139,202,104,75),tile.table_points)
    marshrut_predprosmotra = None
    znachki_ataki = []
    tekuschee_vydelenie = (vybrannyy_muravey, razdelenie is not None)
    if tekuschee_vydelenie != poslednee_vydelenie:
        podsvetka_vremya = 0.0
        poslednee_vydelenie = tekuschee_vydelenie
    podsvetka_vremya = min(1,podsvetka_vremya+delta_time/.12)
    alfa_vydeleniya = podsvetka_vremya
    if razdelenie is not None and avtoboy is None:
        otryad, sostav = razdelenie
        dostupnye, otkuda = dostupnye_dlya_razdeleniya(otryad,sostav)
        if hovered_tile is not None:
            marshrut_predprosmotra = (otryad,(hovered_tile.col,hovered_tile.row),dostupnye,otkuda)
        for koord in dostupnye:
            pygame.draw.polygon(setka_sloy,(40,200,75,round(85*alfa_vydeleniya)),hex_grid[koord].table_points)
        pygame.draw.polygon(setka_sloy,(255,215,0,round(110*alfa_vydeleniya)),otryad.kletka.table_points)
    elif not redaktor and vybrannyy_muravey is not None and avtoboy is None:
        if vybrannyy_muravey.zdorovie > 0 and not vybrannyy_muravey.marshrut:
            dostupnye = {}
            otkuda = {}
            if vybrannyy_muravey.ostalos_hodov > 0:
                dostupnye, otkuda = nayti_dostupnye_kletki(vybrannyy_muravey)
                if hovered_tile is not None:
                    marshrut_predprosmotra = (vybrannyy_muravey,(hovered_tile.col,hovered_tile.row),dostupnye,otkuda)
                for koord in dostupnye:
                    pygame.draw.polygon(
                        setka_sloy, (40, 200, 75, round(85*alfa_vydeleniya)), hex_grid[koord].table_points
                    )

            #Подсветка врагов:
            # Враги подсвечиваются сами, если до них можно дойти и напасть.
            if not vybrannyy_muravey.atakoval_v_etom_hodu:
                for vrag in muravi:
                    if (vrag.komanda != vybrannyy_muravey.komanda
                            and vrag.zdorovie > 0
                            and nayti_podhod_k_vragu(
                                vybrannyy_muravey, vrag, dostupnye
                            ) is not None):
                        pygame.draw.polygon(
                            setka_sloy, (225, 45, 45, round(85*alfa_vydeleniya)), vrag.kletka.table_points
                        )
                        znachki_ataki.append(vrag.kletka.center)
                        if hovered_tile is vrag.kletka:
                            podhod = nayti_podhod_k_vragu(vybrannyy_muravey,vrag,dostupnye)
                            marshrut_predprosmotra = (vybrannyy_muravey,(podhod.col,podhod.row),dostupnye,otkuda)

            pygame.draw.polygon(
                setka_sloy, (255, 215, 0, round(110*alfa_vydeleniya)),
                vybrannyy_muravey.kletka.table_points
            )

    if redaktor:
        for koord, tip in provintsii_kletok.items():
            if tip != "polya":
                pygame.draw.polygon(
                    setka_sloy, cveta_tipov[tip], hex_grid[koord].table_points
                )

    karta_sloy.blit(setka_sloy, (0, 0))
    karta_sloy.blit(setka_redaktor if redaktor else setka_obych,(0,0))
    # Ивенты оставляем живыми, а саму сетку рисуем из кеша.
    draw_tile_markers(karta_sloy)
    if hovered_tile is not None:
        if redaktor:
            hovered_tile.draw(karta_sloy,color=(255,255,0),thick=3)
        else:
            setka_sloy.fill((0,0,0,0))
            pygame.draw.polygon(setka_sloy,(255,239,177,38),hovered_tile.table_points)
            karta_sloy.blit(setka_sloy,(0,0))
    for p in znachki_ataki:
        nadpis_na_okne(karta_sloy,"!",(round(p.x)-18,round(p.y)-14),14,(255,239,177),"center")
    if marshrut_predprosmotra is not None:
        narisovat_marshrut(karta_sloy,*marshrut_predprosmotra)
    for building in buildings:
        narisovat_ten(karta_sloy, building.rect.center, building.rect.width*1.25, building.rect.height*.8)
    for muravey in muravi:
        if muravey.zdorovie > 0:
            razmer = units[muravey.tip]["razmer_na_karte"]
            narisovat_ten(karta_sloy,tuple(muravey.pozitsiya),razmer*.9,razmer*.65)
    for building in buildings:
        building.draw(karta_sloy)

    for muravey in muravi:
        muravey.narisovat(karta_sloy)

    if avtoboy is None and event_popup is None:
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

            kartinka = effekt["kartinka"].copy()
            kartinka.set_alpha(min(255, int(255 * (3.0-vremya)/1.6)))
            karta_sloy.blit(kartinka, kartinka.get_rect(center=effekt["pozitsiya"]))
            nadpis = tekst_smerti.copy()
            nadpis.set_alpha(alfa)
            mesto = nadpis.get_rect(center=effekt["pozitsiya"])
            karta_sloy.blit(nadpis, mesto)

    test_button = TestButton("КЛИК НА МЕНЯ", 250, 250, True)

    if hud.selected_tile is not None and hovered_tile is not None and not redaktor:
        building_type = hud.selected_tile["name"]
        preview_img = scale_building_image(
            building_textures[building_type],
            hovered_tile.radius * 1.8
        )
        preview_img.set_alpha(160)
        preview_rect = preview_img.get_rect(center=hovered_tile.center)
        karta_sloy.blit(preview_img, preview_rect)

        can_build = can_place_building(hovered_tile, building_type)
        border_color = (50, 255, 50) if can_build else (255, 60, 60)
        hovered_tile.draw(karta_sloy, color=border_color, thick=1)

    kamera_karty.narisovat(screen, karta_sloy)

    unit_count = sum(unit.poluchit_yacheyki() for unit in muravi if unit.komanda == "igrok" and unit.zdorovie > 0)
    max_units = sum(building.unit_slots for building in buildings)
    hud.draw(screen, unit_count, max_units)

    if razdelenie is not None:
        rect = pygame.Rect(0,0,650,38)
        rect.midtop = (screen.get_width()//2,44)
        pygame.draw.rect(screen,(41,56,44),rect)
        nadpis_na_okne(screen,"Выберите клетку для отделённого отряда",rect.center,18,vyrovnyat="center")
    if kontekstnoe_menu is not None:
        kontekstnoe_menu.narisovat(screen)
    if okno_otryada is not poslednee_okno:
        vremya_okna = 0.0
        poslednee_okno = okno_otryada
    if okno_otryada is not None:
        vremya_okna = min(1,vremya_okna+delta_time/.12)
        fon_do_okna = screen.copy() if vremya_okna < 1 else None
        okno_otryada.narisovat(screen)
        if fon_do_okna is not None:
            fon_do_okna.set_alpha(round(255*(1-vremya_okna)))
            screen.blit(fon_do_okna,(0,0))

    #Окно битвы:
    # Окно битвы.
    if avtoboy is not None:
        avtoboy.narisovat(screen)
    #Окно ивента:
    if event_popup is not None:
        event_popup.draw(screen)

    """#МЫШКА:
        if event.type == pygame.MOUSEBUTTONDOWN:
            print("КЛИК")
        if event.type == pygame.MOUSEBUTTONUP:
            print("КЛИК КОНЧИЛСЯ")"""

    pygame.display.update() #чтобы показывалось изображение

pygame.quit()
