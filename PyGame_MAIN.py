import pygame #ВИНОВНИК ТОРЖЕСТВА!
import os #нужен чтобы папка не потерялась внутри системы
import random
import math
import json
import heapq #для работы с большой структурой данных

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
#ЕСЛИ units.json сломался!:
units.setdefault("pauk", {
    "nazvanie": "Паук",
    "zdorovie": 240,
    "prohodimost": 2,
    "uron": 65,
    "bronya": 15,
    "odin": False,
    "razmer_na_karte": 40,
    "razmer_v_boyu": 36,
    "animatsii": {
        "pokoy": {"fps": 1},
        "hodba": {"fps": 8},
        "ataka": {"fps": 10},
        "smert": {"fps": 1}
    }
})
provintsii_json = os.path.join(data_dir, "tipy_provintsiy.json")
if os.path.exists(provintsii_json):
    with open(provintsii_json, "r", encoding="utf-8") as fail:
        tipy_provintsiy = json.load(fail)
else:
    #Если у кого-то нет файла с типами клеток:
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
font = pygame.font.SysFont("Russo One", 18) #Russo One для всего
font_smiles = pygame.font.SysFont("segoeuiemoji", 22) #для иконок и смайликов
shrifty = {18: font}


def poluchit_shrift(razmer):
    if razmer not in shrifty:
        shrifty[razmer] = pygame.font.SysFont("Russo One", razmer)
    return shrifty[razmer]


#Подготовка размера шрифта:
for razmer_shrifta in (12, 13, 16, 20, 21, 22, 26, 27, 29, 30, 42):
    poluchit_shrift(razmer_shrifta)

r_hex = 26
HEX_GRID_WIDTH, HEX_GRID_HEIGHT = screen.get_size()
HEX_GRID_RADIUS = r_hex


"""ДЕЛАЕМ ИЗ КАРТИНОК SURFACES:"""

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
    pygame.image.load(os.path.join(textures_dir, f"ant{i}.png")).convert_alpha()
    for i in range(1, 4)
]



"""КЛАССЫ:"""
#HUD
class HUD:
    def __init__(self, resource_manager, width_hud, height_hud, building_images, resource_emojis):
        self.resource_manager = resource_manager
        self.width_hud = width_hud
        self.height_hud = height_hud
        self.hud_colour = (26, 37, 29, 232)
        self.building_images = building_images
        self.selected_tile = None

        emoji_colors = {
            "wood": (205, 165, 118),
            "stone": (182, 190, 196)
        }
        self.resource_icons = {
            name: font_smiles.render(emoji, True, emoji_colors.get(name, (230, 224, 204)))
            for name, emoji in resource_emojis.items()
        }
        self.turn_icon = font_smiles.render("⏳", True, (226, 196, 122))
        self.unit_icon = font_smiles.render("🐜", True, (222, 226, 214))

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

        pygame.draw.line(screen, (96, 116, 90), (0, self.resources_rect.bottom), (self.width_hud, self.resources_rect.bottom), 1)
        pygame.draw.rect(screen, (96, 116, 90), self.build_rect, 1)
        pygame.draw.rect(screen, (96, 116, 90), self.select_rect, 1)

        mouse_pos = pygame.mouse.get_pos()
        for tile in self.tiles:
            slot_rect = tile["rect"].inflate(8, 8)
            is_selected = self.selected_tile is tile
            is_hovered = tile["rect"].collidepoint(mouse_pos)
            slot_bg = (52, 70, 54) if is_hovered or is_selected else (38, 52, 40)
            slot_border = (224, 192, 110) if is_selected else (88, 108, 84)
            pygame.draw.rect(screen, slot_bg, slot_rect, border_radius=3)
            pygame.draw.rect(screen, slot_border, slot_rect, 2 if is_selected else 1, border_radius=3)
            screen.blit(tile["icon"], tile["rect"].topleft)

        #Панель найма в Муравейнике:
        if selected_ant_house is not None:
            pygame.draw.rect(screen, (196, 172, 108), self.select_rect, 2)
            free_slots = max(0, max_units - unit_count)
            header = font.render(f"Муравейник  ·  Свободно ячеек: {free_slots}", True, (236, 234, 222))
            screen.blit(header, (self.select_rect.left + 16, self.select_rect.top + 14))

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
                    bg_color = (48, 52, 50)
                    border_color = (82, 86, 82)
                    cost_color = (205, 118, 110)
                elif not can_afford:
                    bg_color = (66, 48, 46)
                    border_color = (128, 78, 72)
                    cost_color = (218, 150, 142)
                else:
                    bg_color = (64, 92, 62) if hovered else (48, 70, 49)
                    border_color = (156, 184, 142) if hovered else (108, 134, 98)
                    cost_color = (218, 224, 198)

                pygame.draw.rect(screen, bg_color, rect, border_radius=4)
                pygame.draw.rect(screen, border_color, rect, 1, border_radius=4)

                title_surf = font.render(btn["title"], True, (238, 236, 224))
                screen.blit(title_surf, title_surf.get_rect(midtop=(rect.centerx, rect.top + 14)))

                unit_data = units[unit_type]
                stats_surf = font.render(
                    f"ХП: {unit_data['zdorovie']}  |  Урон: {unit_data['uron']}",
                    True, (186, 198, 178)
                )
                screen.blit(stats_surf, stats_surf.get_rect(center=(rect.centerx, rect.centery + 2)))

                cost_text = f"Дер: {cost['wood']}  |  Кам: {cost['stone']}" if has_slot else "Нет ячеек юнитов"
                cost_surf = font.render(cost_text, True, cost_color)
                screen.blit(cost_surf, cost_surf.get_rect(midbottom=(rect.centerx, rect.bottom - 12)))
        else:
            hint = font.render("Кликни по Муравейнику, чтобы нанять войнов", True, (164, 178, 158))
            screen.blit(hint, hint.get_rect(center=self.select_rect.center))

        #Верхняя панель:
        turn_icon_rect = self.turn_icon.get_rect(midleft=(20, self.resources_rect.centery))
        screen.blit(self.turn_icon, turn_icon_rect)
        turn_text = font.render(f"Ход: {turn_number}", True, (238, 236, 224))
        turn_rect = turn_text.get_rect(midleft=(turn_icon_rect.right + 8, self.resources_rect.centery))
        screen.blit(turn_text, turn_rect)
        unit_icon_rect = self.unit_icon.get_rect(midleft=(turn_rect.right + 28, self.resources_rect.centery))
        screen.blit(self.unit_icon, unit_icon_rect)
        units_text = font.render(f"Отряды: {unit_count}/{max_units}", True, (238, 236, 224))
        units_rect = units_text.get_rect(midleft=(unit_icon_rect.right + 8, self.resources_rect.centery))
        screen.blit(units_text, units_rect)

        #Ресурсы:
        resource_names = {"wood": "Дерево", "stone": "Камень"}
        pos = self.width_hud - 420
        for resource, resource_value in self.resource_manager.resources.items():
            if resource in self.resource_icons:
                icon = self.resource_icons[resource]
                icon_rect = icon.get_rect(midleft=(pos, self.resources_rect.centery))
                screen.blit(icon, icon_rect)
                text_x = icon_rect.right + 8
            else:
                text_x = pos

            label = resource_names.get(resource, resource)
            text_surface = font.render(f"{label}: {resource_value}", True, (238, 236, 224))
            text_rect = text_surface.get_rect(midleft=(text_x, self.resources_rect.centery))
            screen.blit(text_surface, text_rect)
            pos += 200


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


"""СТРОЕНИЯ:"""
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

#Кнопка для пропуска хода:
class EndTurnButton:
    def __init__(self, text, x_pos, y_pos, width, height):
        self.rect = pygame.Rect(x_pos, y_pos, width, height)
        self.text = text

    def is_hovered(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def handle_click(self, mouse_pos, b_enabled):
        return b_enabled and self.rect.collidepoint(mouse_pos)

    def draw(self, surface, turn_number, b_enabled, has_unused_moves):
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.is_hovered(mouse_pos)

        if not b_enabled:
            bg_color = (52, 58, 54)
            border_color = (82, 88, 84)
            text_color = (150, 156, 148)
            label = "Ожидание..."
        elif not has_unused_moves:
            bg_color = (82, 128, 76) if hovered else (66, 108, 62)
            border_color = (166, 202, 154)
            text_color = (240, 244, 236)
            label = f"{self.text} ({turn_number})"
        else:
            bg_color = (162, 126, 62) if hovered else (138, 106, 52)
            border_color = (212, 186, 122)
            text_color = (245, 240, 224)
            label = f"{self.text} ({turn_number})"

        pygame.draw.rect(surface, bg_color, self.rect, border_radius=4)
        pygame.draw.rect(surface, border_color, self.rect, 1, border_radius=4)

        text_surf = font.render(label, True, text_color)
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

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

        self.panel = pygame.Rect(470, 225, 660, 420)
        self.button_rect = pygame.Rect(self.panel.centerx - 140, self.panel.bottom - 76, 280, 50)
        self.dim_overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        self.dim_overlay.fill((8, 14, 22, 180))

        #Текст компоненты вынесены отдельно для более гармоничного вида:
        self.title_font = poluchit_shrift(26)
        self.body_font = pygame.font.SysFont("PT Sans", 20)
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
        surface.blit(self.dim_overlay, (0, 0))
        pygame.draw.rect(surface, (30, 42, 33), self.panel, border_radius=4)
        pygame.draw.rect(surface, (112, 132, 104), self.panel, 2, border_radius=4)

        header_rect = pygame.Rect(self.panel.left + 2, self.panel.top + 2, self.panel.width - 4, 84)
        pygame.draw.rect(surface, (41, 56, 44), header_rect)
        pygame.draw.line(surface, (84, 104, 80), (header_rect.left, header_rect.bottom), (header_rect.right, header_rect.bottom), 1)

        emoji_bg = pygame.Rect(self.panel.left + 24, self.panel.top + 16, 54, 54)
        pygame.draw.rect(surface, (26, 36, 28), emoji_bg, border_radius=4)
        pygame.draw.rect(surface, (92, 114, 88), emoji_bg, 1, border_radius=4)
        surface.blit(self.emoji_surface, self.emoji_surface.get_rect(center=emoji_bg.center))

        title_surf = self.title_font.render(self.title, True, (241, 243, 238))
        surface.blit(title_surf, title_surf.get_rect(midleft=(emoji_bg.right + 18, emoji_bg.centery)))

        y_pos = self.panel.top + 122
        for line in self.wrap_text(self.description, self.panel.width - 70):
            line_surf = self.body_font.render(line, True, (212, 222, 208))
            surface.blit(line_surf, line_surf.get_rect(midtop=(self.panel.centerx, y_pos)))
            y_pos += 30

        badge_box = pygame.Rect(self.panel.left + 45, self.panel.bottom - 148, self.panel.width - 90, 48)
        pygame.draw.rect(surface, (42, 57, 45), badge_box, border_radius=4)
        pygame.draw.rect(surface, (96, 118, 92), badge_box, 1, border_radius=4)
        badge_surf = self.badge_font.render(self.badge_text, True, (236, 218, 162))
        surface.blit(badge_surf, badge_surf.get_rect(center=badge_box.center))

        hovered = self.button_rect.collidepoint(pygame.mouse.get_pos())
        btn_color = (102, 134, 86) if hovered else (82, 110, 70)

        pygame.draw.rect(surface, btn_color, self.button_rect, border_radius=4)
        pygame.draw.rect(surface, (156, 182, 142), self.button_rect, 1, border_radius=4)
        btn_label = font.render(self.button_text, True, (242, 244, 238))
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
        if not dannye.get("tekstura"):
            kadr = kadry_muravya[0]
            trup = pygame.transform.rotate(kadr, 180)
            trup.fill((135, 135, 135, 255), special_flags=pygame.BLEND_RGBA_MULT)
            telo = {"pokoy": [kadr], "hodba": list(kadry_muravya),
                    "ataka": [kadr], "smert": [trup]}
            w, h = kadr.get_size()
        else:
            w, h = dannye["shirina_kadra"], dannye["vysota_kadra"]
            atlas = self.zagruzit_atlas(dannye["tekstura"], w, h)
            telo = {imya: [self.poluchit_kadr(atlas, w, h, koord)
                           for koord in opisanie["kadry"]]
                    for imya, opisanie in dannye["animatsii"].items()}

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
        self.tsel = None
        self.tsel_udara = None
        self.vremya_ataki = 0.0
        self.pauza = random.uniform(0, .25)
        self.udary = 0
        self.mesto_ataki = None
        self.perevybor = 0.0
        self.zaderzhka = random.uniform(0, .3)

    def povernut(self, napravlenie):
        if napravlenie.length_squared() > .001:
            self.ugol = math.degrees(math.atan2(-napravlenie.y, napravlenie.x)) - 90

    def umeret(self):
        self.zhiv = False
        self.tsel = None
        self.tsel_udara = None
        self.animatsiya.ustanovit("smert")

    def narisovat(self, poverhnost):
        kartinka = self.animatsiya.kartinka(self.ugol)
        pozitsiya = self.pozitsiya
        if not units[self.tip].get("tekstura") and self.tsel_udara is not None and self.zhiv:
            vektor = self.tsel_udara.pozitsiya - pozitsiya
            if vektor.length_squared() > .01:
                pozitsiya = pozitsiya + vektor.normalize() * 5 * math.sin(math.pi * min(1, self.vremya_ataki / self.animatsiya.dlitelnost_ataki()))
        poverhnost.blit(kartinka, kartinka.get_rect(center=(round(pozitsiya.x), round(pozitsiya.y))))


class BoevoyII:
    def __init__(self, arena, levyy, pravyy, itog):
        self.arena = arena
        self.boitsy = []
        self.po_storonam = [[], []]
        self.ostalos = [itog["do_levogo"], itog["do_pravogo"]]
        self.vyzhivet = [itog["posle_levogo"], itog["posle_pravogo"]]
        self.poteri = [self.ostalos[i] - self.vyzhivet[i] for i in range(2)]
        self.ostalos_po_tipam = [dict(levyy.sostav), dict(pravyy.sostav)]
        self.vyzhivet_po_tipam = [dict(itog["sostav_levogo"]), dict(itog["sostav_pravogo"])]
        self.vremya = 0.0
        self.nachalo_udarov = None
        self.zakonchen = False
        self.avarijno = False
        self.shag = 1/60
        self.nakopleno = 0.0
        for storona, gruppa in enumerate((levyy, pravyy)):
            self.sozdat_boytsov(gruppa, storona)

    def sozdat_boytsov(self, gruppa, storona):
        n = gruppa.kolichestvo
        stolbtsy = max(1, math.ceil(math.sqrt(n * 1.45)))
        ryady = math.ceil(n / stolbtsy)
        interval = min((self.arena.width * .37 - 18) / stolbtsy, (self.arena.height - 24) / ryady)
        tipy = [tip for tip, kol in gruppa.sostav.items() for _ in range(kol)]
        random.shuffle(tipy)
        max_razmer = max(units[tip].get("razmer_v_boyu", 36) for tip in tipy)
        razmer = min(max_razmer, max(5, int(interval * .92)))
        shag = min(interval, max(razmer * .95, 17))
        x = self.arena.left + 18 if storona == 0 else self.arena.right - 18
        znak = 1 if storona == 0 else -1
        for i in range(n):
            col, row = i % stolbtsy, i // stolbtsy
            p = (x + znak * (razmer/2 + col * shag), self.arena.centery + (row-(ryady-1)/2)*shag)
            tip = tipy[i]
            razmer_boytsa = max(5, round(units[tip].get("razmer_v_boyu", 36) * razmer / max_razmer))
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
        dostupnye = [vrag for vrag in vragi if self.mozhno_ubit(vrag)] or vragi
        return min(dostupnye, key=lambda vrag: boets.pozitsiya.distance_to(vrag.pozitsiya) + nagruzka.get(vrag, 0) * boets.radius * 1.4)

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
        #БЕЗ ПРОВЕРКИ ПАР НА АРЕНЕ!
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
        if not tsel.zhiv or not boets.zhiv:
            return
        if boets.pozitsiya.distance_to(tsel.pozitsiya) > boets.radius+tsel.radius+boets.dalnost+4:
            return
        if self.nachalo_udarov is None:
            self.nachalo_udarov = self.vremya
        tsel.animatsiya.vspyshka = .09
        tsel.udary += 1
        storona = tsel.storona
        if not self.mozhno_ubit(tsel):
            return
        proshlo = self.vremya - self.nachalo_udarov
        razresheno = min(self.poteri[storona], 1+int(self.poteri[storona]*proshlo/5.5))
        if self.poteri[storona] - (self.ostalos[storona]-self.vyzhivet[storona]) >= razresheno:
            return
        drugaya = 1-storona
        if self.poteri[drugaya]:
            pogiblo = self.poteri[storona] - (self.ostalos[storona]-self.vyzhivet[storona])
            pogiblo_drugih = self.poteri[drugaya] - (self.ostalos[drugaya]-self.vyzhivet[drugaya])
            dopusk = max(.06, 1/self.poteri[storona], 1/self.poteri[drugaya])
            if (pogiblo+1)/self.poteri[storona] > pogiblo_drugih/self.poteri[drugaya]+dopusk+.00001:
                return
        if self.ostalos[storona] == 1 and self.ostalos[drugaya] > self.vyzhivet[drugaya]:
            if self.vyzhivet == [0,0] and self.ostalos == [1,1]:
                self.ubit(boets)
            else:
                return
        self.ubit(tsel)

    def mozhno_ubit(self, boets):
        return (boets.zhiv and self.ostalos_po_tipam[boets.storona][boets.tip]
                > self.vyzhivet_po_tipam[boets.storona].get(boets.tip, 0))

    def ubit(self, boets):
        if self.mozhno_ubit(boets):
            boets.umeret()
            self.ostalos[boets.storona] -= 1
            self.ostalos_po_tipam[boets.storona][boets.tip] -= 1

    def obnovit(self, delta_time):
        self.nakopleno += delta_time
        while self.nakopleno >= self.shag and not self.zakonchen:
            self.nakopleno -= self.shag
            self.shag_boya(self.shag)

    def shag_boya(self, dt):
        self.vremya += dt
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
        for b in zhivye:
            b.animatsiya.obnovit(dt)
            b.pauza = max(0, b.pauza-dt)
            b.perevybor -= dt
            if self.vremya < b.zaderzhka or self.ostalos == self.vyzhivet:
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
            if (b.tsel is None or not b.tsel.zhiv
                    or (not self.mozhno_ubit(b.tsel) and any(self.mozhno_ubit(v) for v in vragi[1-b.storona]))):
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
            if napravlenie.length_squared() > .001:
                b.povernut(napravlenie)
                b.pozitsiya += napravlenie.normalize()*min(b.skorost*dt, napravlenie.length())
                self.ogranichit(b)
                b.animatsiya.ustanovit("hodba")
        self.rastolknut(zhivye)
        for b, tsel in udary:
            self.udar(b, tsel)
        if self.ostalos == self.vyzhivet and self.vremya >= 8:
            self.zakonchen = True
        elif self.vremya >= 18:
            self.avarijno = self.ostalos != self.vyzhivet
            for i in range(2):
                kandidaty = sorted((b for b in self.po_storonam[i] if b.zhiv), key=lambda b: -b.udary)
                for b in kandidaty:
                    self.ubit(b)
            self.zakonchen = True

    def narisovat(self, poverhnost):
        staryy_clip = poverhnost.get_clip()
        poverhnost.set_clip(self.arena)
        for b in sorted(self.boitsy, key=lambda b: (b.zhiv,b.pozitsiya.y)):
            b.narisovat(poverhnost)
        poverhnost.set_clip(staryy_clip)


def sila_sostava(sostav):
    return sum(kol * max(0, units[tip]["uron"]) * max(0, units[tip]["zdorovie"])
               / max(.05, 1-max(0, min(95, units[tip].get("bronya", 0)))/100)
               for tip, kol in sostav.items())


def yacheyki_sostava(sostav):
    return sum(kol * units[tip].get("yacheyki", 0) for tip, kol in sostav.items())


#Муравьи & Перемещение муравьёв:
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
        #Муравьи выход на арену:
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
        #Кол-во из состава ТОЛЬКО ИНАЧЕ НЕ ТЕ ЗНАЧЕНИЯ:
        pelmeshki.sostav = {tip: sostav[tip] for tip in units if sostav.get(tip, 0) > 0}
        pelmeshki.kolichestvo = sum(pelmeshki.sostav.values())
        if not pelmeshki.sostav:
            pelmeshki.zdorovie = 0
            return
        pelmeshki.tip = next(iter(pelmeshki.sostav))
        dannye = units[pelmeshki.tip]
        pelmeshki.odin = dannye.get("odin", False)
        pelmeshki.nazvanie = "Смешанный отряд" if len(pelmeshki.sostav) > 1 else dannye["nazvanie"]
        pelmeshki.zdorovie = pelmeshki.max_zdorovie = dannye["zdorovie"]
        pelmeshki.uron = dannye["uron"]
        pelmeshki.bronya = dannye.get("bronya", 0)
        pelmeshki.prohodimost = min(units[tip]["prohodimost"] for tip in pelmeshki.sostav)
        pelmeshki.ostalos_hodov = min(pelmeshki.ostalos_hodov, pelmeshki.prohodimost)
        #2 Малых спрайта вместо 1 спрайта:
        pelmeshki.animatsii = {
            tip: Animatsiya(tip, pelmeshki.komanda,
                           round(units[tip].get("razmer_na_karte", 40) * (.65 if len(pelmeshki.sostav) > 1 else 1)))
            for tip in pelmeshki.sostav
        }
        pelmeshki.animatsiya = pelmeshki.animatsii[pelmeshki.tip]

    def poluchit_silu(pelmeshki):
        return sila_sostava(pelmeshki.sostav)

    def poluchit_yacheyki(pelmeshki):
        return yacheyki_sostava(pelmeshki.sostav)

    def narisovat(pelmeshki, poverhnost):
        if pelmeshki.zdorovie <= 0:
            return

        mesto = None
        for i, animatsiya in enumerate(pelmeshki.animatsii.values()):
            kartinka = animatsiya.kartinka(pelmeshki.ugol)
            sdvig = (i-(len(pelmeshki.animatsii)-1)/2)*21
            rect = kartinka.get_rect(center=(round(pelmeshki.pozitsiya.x+sdvig),
                                              round(pelmeshki.pozitsiya.y)))
            poverhnost.blit(kartinka, rect)
            mesto = rect if mesto is None else mesto.union(rect)

        chislo = shrift_kolichestva.render(str(pelmeshki.kolichestvo), True, (255, 255, 255))
        podlozhka = chislo.get_rect(bottomright=(mesto.right + 4, mesto.bottom + 5))
        podlozhka.inflate_ip(7, 4)
        pygame.draw.rect(poverhnost, (18, 30, 35), podlozhka)
        poverhnost.blit(chislo, chislo.get_rect(center=podlozhka.center))

        if pelmeshki.odin:
            #Различаем одиноких врагов
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
        global pending_event_trigger #нужно для системы ивентов
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
            elif pelmeshki.komanda == "igrok" and sleduyushchaya.event: #как же удобно работать с Гошеным кодом :)
                pelmeshki.marshrut.clear()
                pending_event_trigger = (pelmeshki, sleduyushchaya)
        elif rasstoyanie > 0:
            pelmeshki.pozitsiya += napravlenie.normalize() * shag

    def umeret(pelmeshki):
        #Логика гибеля:
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


def rasschitat_boy(levyy, pravyy):
    #Победителя считаем заранее:
    sila_levogo = levyy.poluchit_silu()
    sila_pravogo = pravyy.poluchit_silu()
    kol_levogo = levyy.kolichestvo
    kol_pravogo = pravyy.kolichestvo

    if sila_levogo == sila_pravogo:
        vyzhilo_levogo = 0
        vyzhilo_pravogo = 0
        pobeditel = "nichya"
    else:
        pobeditel = "igrok" if sila_levogo > sila_pravogo else "vrag"
        pobedivshih = levyy if pobeditel == "igrok" else pravyy
        sila_pobedy = max(sila_levogo, sila_pravogo)
        sila_porazheniya = min(sila_levogo, sila_pravogo)

        dolya_poter = (sila_porazheniya / sila_pobedy) ** 1.5
        umerlo_u_pobeditelya = min(
            pobedivshih.kolichestvo - 1,
            round(pobedivshih.kolichestvo * dolya_poter)
        )
        vyzhilo = pobedivshih.kolichestvo - umerlo_u_pobeditelya
        vyzhilo_levogo = vyzhilo if pobeditel == "igrok" else 0
        vyzhilo_pravogo = vyzhilo if pobeditel == "vrag" else 0

    return {
        "sila_levogo": sila_levogo,
        "sila_pravogo": sila_pravogo,
        "do_levogo": kol_levogo,
        "do_pravogo": kol_pravogo,
        "posle_levogo": vyzhilo_levogo,
        "posle_pravogo": vyzhilo_pravogo,
        "pobeditel": pobeditel,
        "sostav_levogo": raspredelit_poteri(levyy.sostav, vyzhilo_levogo),
        "sostav_pravogo": raspredelit_poteri(pravyy.sostav, vyzhilo_pravogo)
    }


def raspredelit_poteri(sostav, vyzhilo):
    #Округляем потери так, чтобы лишний муравей не появился из-за дробных чисел:
    vsego = sum(sostav.values())
    if not vsego:
        return {}
    pogiblo = vsego-vyzhilo
    poteri = {tip: kol*pogiblo//vsego for tip, kol in sostav.items()}
    ostatok = pogiblo-sum(poteri.values())
    for tip in sorted(sostav, key=lambda tip: -(sostav[tip]*pogiblo % vsego))[:ostatok]:
        poteri[tip] += 1
    return {tip: kol-poteri[tip] for tip, kol in sostav.items() if kol > poteri[tip]}


class Avtoboy:
    def __init__(self, levyy, pravyy):
        self.levyy = levyy
        self.pravyy = pravyy
        self.itog = rasschitat_boy(levyy, pravyy)
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

        self.ii = BoevoyII(self.arena, levyy, pravyy, self.itog)

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
        if self.stadiya != "bitva":
            return
        self.ii.obnovit(delta_time)
        self.vremya = self.ii.vremya
        if self.ii.zakonchen:
            self.stadiya = "rezultat"

    def zavershit(self):
        #Только после экрана результата перенос потери на карту:
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
            f"{self.ii.ostalos[1]} из {self.itog['do_pravogo']}"
            if self.pravyy.odin
            else f"{self.ii.ostalos[1]} муравьёв"
        )
        self.tekst(
            poverhnost, kolichestvo_vraga,
            self.sh_obychniy, self.palette["osnovnoy_tekst"],
            (self.panel.right - 48, self.panel.top + 146), "midright"
        )

        pygame.draw.rect(poverhnost, self.palette["arena"], self.arena)
        self.ii.narisovat(poverhnost)

        self.tekst(
            poverhnost, f"Сила: {self.itog['sila_levogo']:,.0f}".replace(",", " "),
            self.sh_obychniy, self.palette["levaya_sila"],
            (self.arena.left + 20, self.arena.bottom + 30), "midleft"
        )
        self.tekst(
            poverhnost, f"Сила: {self.itog['sila_pravogo']:,.0f}".replace(",", " "),
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
        self.oformit_podlozhku(poverhnost)
        if self.stadiya == "bitva":
            self.narisovat_bitvu(poverhnost)
        else:
            self.narisovat_rezultat(poverhnost)



#HEX TOOL:

#HEX TOOL (MAIN HEX):
class Hex: #$\sqrt{\Delta x^2 + \Delta y^2}$)
    def __init__(self, row, col, hex_x, hex_y, hex_radius):
        self.building = None
        self.build_unlocked = False
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
        self.is_water = False

    def is_has_neighbor(self, other_hex): #Проверка если ли соседняя клетка рядом с ней
        if other_hex is None or other_hex == self:
            return False

        return self.center.distance_squared_to(other_hex.center) < self.neighbor_distance

    def draw(self, surface, color, thick):
        pygame.draw.polygon(surface, color, self.table_points, thick)

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
def hex_under_mouse(grid, mouse_pos=None):
    if mouse_pos is None:
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



#Все достижимые клетки:

def nayti_dostupnye_kletki(muravey, zapas=None):
    nachalo = (muravey.kletka.col, muravey.kletka.row)
    #Реальные затраты на клетку:
    ochered = [(0, nachalo)]
    rashody = {nachalo: 0}
    otkuda = {}

    zanyatye = {
        (drugoy.kletka.col, drugoy.kletka.row)
        for drugoy in muravi
        if drugoy is not muravey and drugoy.zdorovie > 0
    }
    zanyatye.update((k.col, k.row) for drugoy in muravi
                    if drugoy is not muravey and drugoy.zdorovie > 0 for k in drugoy.marshrut)
    if zapas is None:
        zapas = muravey.ostalos_hodov

    while ochered:
        rashod, koord = heapq.heappop(ochered)
        if rashod > rashody[koord]:
            continue

        #ВОДА = СМЕРТЬ
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
    #ФИКС НЕ ПОСТАВИТЬ ЗДАНИЕ ПОД НОГАМИ!
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

    return candidates[0] if candidates else None


def recruit_from_ant_house(ant_house, unit_type):
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

    resource_manager.apply_unit_cost(unit_type)
    muravi.append(Muravey(unit_type, spawn_tile, "igrok", 12))
    print(f"Нанят новый отряд: {units[unit_type].get('nazvanie', unit_type)}")
    return True


def create_random_event(event_type):
    if event_type == "enemy_ants":
        return {"type": "enemy_ants", "count": random.randint(3, 7)}
    if event_type == "spider":
        spider_count = 1 if units.get("pauk", {}).get("odin", False) else random.randint(2, 3)
        return {"type": "spider", "count": spider_count}
    if event_type == "tarantula":
        return {"type": "tarantula", "count": random.randint(1, 2)}
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
        if tile.center.y < 46 or hud.is_mouse_over(tile.center) or end_turn_button.is_hovered(tile.center): #НЕ СТАВИМ ивенты под HUD
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
        spawn_tile = find_free_neighbor(tile)
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
            border_color = (118, 206, 148) if tile.building is None else (210, 180, 102)
            pygame.draw.polygon(surface, border_color, tile.table_points, 2)

        if tile.event is not None:
            cx, cy = int(tile.center.x), int(tile.center.y)
            is_failed = tile.event_state == "failed_battle"
            color = (226, 82, 76) if is_failed else (238, 204, 82)
            symbol = "!" if is_failed else "?"

            shadow = marker_font.render(symbol, True, (18, 22, 20))
            mark = marker_font.render(symbol, True, color)
            surface.blit(shadow, shadow.get_rect(center=(cx + 1, cy + 1)))
            surface.blit(mark, mark.get_rect(center=(cx, cy)))


#СОСТАВ ОТРЯДА:

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
    sosed.ostalos_hodov = min(otryad.ostalos_hodov, sosed.ostalos_hodov)
    sosed.atakoval_v_etom_hodu = otryad.atakoval_v_etom_hodu or sosed.atakoval_v_etom_hodu
    sosed.obnovit_sostav(sostav)
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
        pygame.draw.rect(poverhnost, (41,56,44), p)
        nadpis_na_okne(poverhnost, "СОСТАВ ОТРЯДА", (p.left+24,p.top+24), 26)
        nadpis_na_okne(poverhnost, "×", self.krestik.center, 26, vyrovnyat="center")
        for i, (podpis, cifra) in enumerate((("Численность", otryad.kolichestvo),
                                               ("Сила", round(otryad.poluchit_silu())),
                                               ("Ячейки", otryad.poluchit_yacheyki()))):
            rect = pygame.Rect(p.left+24+i*218,p.top+77,206,75)
            pygame.draw.rect(poverhnost,(57,75,55),rect)
            nadpis_na_okne(poverhnost,podpis,(rect.left+12,rect.top+9),16,(198,211,192))
            nadpis_na_okne(poverhnost,f"{cifra:,}".replace(","," "),(rect.left+12,rect.top+32),27)
        for i,(tip,kol) in enumerate(otryad.sostav.items()):
            rect = pygame.Rect(p.left+24,p.top+165+i*98,p.width-48,88)
            pygame.draw.rect(poverhnost,(52,70,49),rect)
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
        cvet = (91,120,75) if aktivna else (70,76,67)
        if aktivna and self.knopka.collidepoint(pygame.mouse.get_pos()):
            cvet = (110,145,92)
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
        pygame.draw.rect(poverhnost,(41,56,44),p)
        nadpis_na_okne(poverhnost,"РАЗДЕЛЕНИЕ ОТРЯДА",(p.left+24,p.top+24),26)
        nadpis_na_okne(poverhnost,"×",self.krestik.center,26,vyrovnyat="center")
        nadpis_na_okne(poverhnost,f"{o.kolichestvo} муравьёв  ·  {o.poluchit_yacheyki()} занятых ячеек",(p.left+24,p.top+64),16,(198,211,192))
        for tip,rect in self.polzunki.items():
            n = self.vybrannyy_sostav[tip]
            vsego = o.sostav[tip]
            nadpis_na_okne(poverhnost,units[tip]["nazvanie"],(rect.left,rect.top-32),18)
            nadpis_na_okne(poverhnost,f"{n} / {vsego}",(rect.right,rect.top-32),20,vyrovnyat="topright")
            pygame.draw.rect(poverhnost,(70,86,67),pygame.Rect(rect.left,rect.centery-4,rect.width,8))
            x = round(rect.left+rect.width*n/vsego)
            pygame.draw.rect(poverhnost,(122,164,92),pygame.Rect(rect.left,rect.centery-4,x-rect.left,8))
            pygame.draw.rect(poverhnost,(217,231,207),pygame.Rect(x-7,rect.top,14,rect.height))
        ostatok = {tip:kol-self.vybrannyy_sostav[tip] for tip,kol in o.sostav.items()}
        for i,(podpis,sostav) in enumerate((("Остаётся",ostatok),("Отделяется",self.vybrannyy_sostav))):
            rect = pygame.Rect(p.left+24+i*326,p.top+250,316,180)
            pygame.draw.rect(poverhnost,(57,75,55),rect)
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


"""Инициализация карты: """

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

setka_sloy = pygame.Surface(screen.get_size(), pygame.SRCALPHA)

cveta_koloniy = {"igrok": (82, 125, 200), "vrag": (189, 77, 77)}
zagruzchik_atlasov = ZagruzchikAtlasov()

muravi = [
    Muravey("rabochiy", hex_grid[(4, 4)], "igrok", 12),
    Muravey("soldat", hex_grid[(6, 4)], "igrok", 12),
    Muravey("soldat", hex_grid[(10, 4)], "vrag", 9),
]
zanyatye_pri_spavne = {(m.kletka.col, m.kletka.row) for m in muravi}
kletka_pauka = min((k for koord, k in hex_grid.items()
                   if koord not in zanyatye_pri_spavne
                   and tipy_provintsiy[provintsii_kletok[koord]].get("prohodima", True)
                   and not tipy_provintsiy[provintsii_kletok[koord]].get("smertelna", False)),
                  key=lambda k: k.center.distance_squared_to(hex_grid[(18, 5)].center), default=None)
if kletka_pauka is not None:
    muravi.append(Muravey("pauk", kletka_pauka, "vrag", 1))

vybrannyy_muravey = None
selected_ant_house = None
tsel_ataki = None
avtoboy = None
event_popup = None
pending_event_trigger = None
active_event_battle = None
kontekstnoe_menu = None
okno_otryada = None
razdelenie = None
slivanie = None

marker_font = poluchit_shrift(17)
shrift_kolichestva = poluchit_shrift(13)
shrift_imen_vragov = poluchit_shrift(12)

effekty_smerti = []
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
buildings = []

resource_manager = ResourceManager()
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

turn_number = 1
end_turn_button = EndTurnButton(
    "Конец хода",
    int(1600 * 0.84),
    int(900 * 0.74) - 60,
    int(1600 * 0.15),
    50
)

generate_map_events()

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


#Главное меню работает отдельно от игрового цикла, пока игрок не нажмёт «Играть».
main_menu = MainMenu(screen, MenuBackground(screen.get_size(),
                                            None,
                                            zagruzchik_atlasov),
                     poluchit_shrift)
running = main_menu.run() == "play"
clock.tick(60)


while running:
    delta_time = max(0.001, min(0.1, clock.tick(60) / 1000))
    mouse_pos = pygame.mouse.get_pos()

    #Идёт автобой или открыто окно ивента = карта ждёт
    if avtoboy is not None:
        avtoboy.obnovit(delta_time)
    elif event_popup is None:
        x += 50 * delta_time
        for muravey in muravi:
            muravey.obnovit(delta_time)

        if slivanie is not None:
            otryad, sosed = slivanie
            if not otryad.marshrut:
                if obiedinit_otryady(otryad, sosed):
                    vybrannyy_muravey = sosed
                slivanie = None

        if pending_event_trigger is not None:
            triggered_ant, triggered_tile = pending_event_trigger
            pending_event_trigger = None
            if triggered_ant.zdorovie > 0 and triggered_tile.event is not None:
                vybrannyy_muravey = None
                tsel_ataki = None
                selected_ant_house = None
                kontekstnoe_menu = okno_otryada = razdelenie = None
                event_popup = trigger_hex_event(triggered_ant, triggered_tile)

        if event_popup is None:
            for muravey in muravi:
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

    b_enabled = (
        avtoboy is None
        and event_popup is None
        and okno_otryada is None
        and kontekstnoe_menu is None
        and razdelenie is None
        and slivanie is None
        and not redaktor
        and all(not muravey.marshrut and muravey.vrag_dlya_boya is None for muravey in muravi)
    )
    has_unused_moves = any(
        muravey.komanda == "igrok" and muravey.zdorovie > 0 and muravey.ostalos_hodov > 0
        for muravey in muravi
    )

    boy_zakryvalsya_v_etom_kadre = avtoboy is not None
    popup_otkryt_v_etom_kadre = event_popup is not None
    okno_zakryto_v_etom_kadre = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            continue

        if boy_zakryvalsya_v_etom_kadre:
            #ФИКС после клика «Вернуться» не пускаем на карту (если быстрый кадр):
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if avtoboy is not None and avtoboy.obrabotat_nazhatie(event.pos):
                    if active_event_battle is not None:
                        battle_tile = active_event_battle["tile"]
                        battle_enemy = active_event_battle["enemy"]
                        if avtoboy.itog["pobeditel"] == "igrok":
                            battle_tile.event = None
                            battle_tile.event_state = None
                        else:
                            #Отряд игрока погиб на этой клетке - меняем '?' на красный '!'
                            battle_tile.event_state = "failed_battle"
                            if battle_tile.event is not None:
                                battle_tile.event["count"] = max(1, battle_enemy.kolichestvo)
                        active_event_battle = None
                    avtoboy = None
                    vybrannyy_muravey = None
                    tsel_ataki = None
                    selected_ant_house = None
            continue

        if popup_otkryt_v_etom_kadre:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if event_popup is not None and event_popup.handle_click(event.pos):
                    battle_data = event_popup.battle_data
                    event_popup = None
                    if battle_data is not None:
                        event_enemy = Muravey(
                            battle_data["enemy_type"],
                            battle_data["tile"],
                            "vrag",
                            battle_data["count"]
                        )
                        if event_enemy.kolichestvo != battle_data["count"]:
                            event_enemy.obnovit_sostav({battle_data["enemy_type"]: battle_data["count"]})
                        active_event_battle = {
                            "tile": battle_data["tile"],
                            "enemy": event_enemy
                        }
                        avtoboy = Avtoboy(battle_data["player_ant"], event_enemy)
            continue

        #На время объединения не даём второму отряду уйти с клетки:
        if slivanie is not None or okno_zakryto_v_etom_kadre:
            continue

        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_n, pygame.K_F2):
            bylo_okno = okno_otryada is not None or kontekstnoe_menu is not None or razdelenie is not None
            kontekstnoe_menu = okno_otryada = razdelenie = None
            if event.key == pygame.K_ESCAPE and bylo_okno:
                okno_zakryto_v_etom_kadre = True
                continue

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
                if okno_otryada.knopka.collidepoint(event.pos) or okno_otryada.krestik.collidepoint(event.pos):
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
                    kletka = hex_under_mouse(hex_grid, event.pos)
                    if kletka is not None and razdelit_otryad(*razdelenie, kletka) is not None:
                        vybrannyy_muravey = razdelenie[0]
                        razdelenie = None
                        okno_zakryto_v_etom_kadre = True
            continue

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F2:
                redaktor = not redaktor
                hud.selected_tile = None
                selected_ant_house = None
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

            if event.key == pygame.K_n and b_enabled:
                next_turn()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                hud.selected_tile = None
                selected_ant_house = None
                vybrannyy_muravey = None
                tsel_ataki = None
                if not redaktor and not hud.is_mouse_over(event.pos):
                    otryad = nayti_otryad_na_kletke(hex_under_mouse(hex_grid, event.pos))
                    if otryad is not None and otryad.komanda == "igrok":
                        kontekstnoe_menu = KontekstnoeMenu(event.pos, otryad)
                continue

            if event.button == 1 and not redaktor:
                if end_turn_button.handle_click(event.pos, b_enabled):
                    next_turn()
                    continue

                if hud.is_mouse_over(event.pos):
                    if selected_ant_house is not None:
                        for btn in hud.recruit_buttons:
                            if btn["rect"].collidepoint(event.pos):
                                recruit_from_ant_house(selected_ant_house, btn["unit_type"])
                                break

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
                if hud.selected_tile is not None:
                    building_type = hud.selected_tile["name"]
                    if can_place_building(kletka, building_type):
                        building = BUILDING_CLASSES[building_type](kletka, resource_manager)
                        kletka.building = building
                        buildings.append(building)
                        hud.selected_tile = None
                        selected_ant_house = None
                    continue

                nazhatyy_muravey = None
                for muravey in muravi:
                    if muravey.kletka is kletka and muravey.zdorovie > 0:
                        nazhatyy_muravey = muravey
                        break

                if nazhatyy_muravey is not None:
                    selected_ant_house = None
                    if nazhatyy_muravey.komanda == "igrok":
                        tsel_ataki = None
                        if (vybrannyy_muravey is not None and vybrannyy_muravey is not nazhatyy_muravey
                                and mozhno_upravlyat(vybrannyy_muravey) and mozhno_upravlyat(nazhatyy_muravey)
                                and vybrannyy_muravey.kletka.is_has_neighbor(nazhatyy_muravey.kletka)):
                            kontekstnoe_menu = KontekstnoeMenu(event.pos, vybrannyy_muravey, nazhatyy_muravey)
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
                                vybrannyy_muravey.vrag_dlya_boya = nazhatyy_muravey
                                vybrannyy_muravey.atakoval_v_etom_hodu = True
                                vybrannyy_muravey = None
                            tsel_ataki = None
                elif kletka.building is not None and kletka.building.name == "ant_house":
                    selected_ant_house = kletka.building
                    vybrannyy_muravey = None
                    tsel_ataki = None
                else:
                    selected_ant_house = None
                    tsel_ataki = None
                    if vybrannyy_muravey is not None:
                        vybrannyy_muravey.peremestitsya(kletka)

    if (hud.is_mouse_over(mouse_pos)
            or end_turn_button.is_hovered(mouse_pos)
            or avtoboy is not None
            or event_popup is not None
            or okno_otryada is not None
            or kontekstnoe_menu is not None):
        hovered_tile = None
    else:
        hovered_tile = hex_under_mouse(hex_grid)

    if (avtoboy is None and event_popup is None and redaktor and hovered_tile is not None
            and pygame.mouse.get_pressed()[0]):
        koord = (hovered_tile.col, hovered_tile.row)
        provintsii_kletok[koord] = tip_kisti

    screen.fill((128, 128, 128))
    screen.blit(scaled_map_img, (0, 0))

    setka_sloy.fill((0, 0, 0, 0))
    if razdelenie is not None and avtoboy is None and event_popup is None:
        otryad, sostav = razdelenie
        dostupnye, _ = dostupnye_dlya_razdeleniya(otryad, sostav)
        for koord in dostupnye:
            pygame.draw.polygon(setka_sloy, (40, 200, 75, 85), hex_grid[koord].table_points)
        pygame.draw.polygon(setka_sloy, (255, 215, 0, 110), otryad.kletka.table_points)
    elif not redaktor and vybrannyy_muravey is not None and avtoboy is None and event_popup is None:
        if vybrannyy_muravey.zdorovie > 0 and not vybrannyy_muravey.marshrut:
            dostupnye = {}
            if vybrannyy_muravey.ostalos_hodov > 0:
                dostupnye, _ = nayti_dostupnye_kletki(vybrannyy_muravey)
                for koord in dostupnye:
                    pygame.draw.polygon(
                        setka_sloy, (40, 200, 75, 85), hex_grid[koord].table_points
                    )

            #Подсветка врагов:
            if not vybrannyy_muravey.atakoval_v_etom_hodu:
                for vrag in muravi:
                    if (vrag.komanda != vybrannyy_muravey.komanda
                            and vrag.zdorovie > 0
                            and nayti_podhod_k_vragu(
                                vybrannyy_muravey, vrag, dostupnye
                            ) is not None):
                        pygame.draw.polygon(
                            setka_sloy, (225, 45, 45, 85), vrag.kletka.table_points
                        )

            pygame.draw.polygon(
                setka_sloy, (255, 215, 0, 110),
                vybrannyy_muravey.kletka.table_points
            )

    if redaktor:
        for koord, tip in provintsii_kletok.items():
            if tip != "polya":
                pygame.draw.polygon(
                    setka_sloy, cveta_tipov[tip], hex_grid[koord].table_points
                )

    for tile in hex_grid.values():
        tile.draw(setka_sloy, color=(235, 228, 205, 42), thick=1)

    if hovered_tile is not None:
        hovered_tile.draw(setka_sloy, color=(238, 206, 112, 165), thick=3)

    screen.blit(setka_sloy, (0, 0))

    draw_tile_markers(screen)

    if selected_ant_house is not None:
        pygame.draw.polygon(screen, (224, 192, 110), selected_ant_house.tile.table_points, 2)

    for building in buildings:
        building.draw(screen)

    for muravey in muravi:
        muravey.narisovat(screen)

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
            kartinka.set_alpha(min(255, int(255 * (3.0 - vremya) / 1.6)))
            screen.blit(kartinka, kartinka.get_rect(center=effekt["pozitsiya"]))
            nadpis = tekst_smerti.copy()
            nadpis.set_alpha(alfa)
            mesto = nadpis.get_rect(center=effekt["pozitsiya"])
            screen.blit(nadpis, mesto)

    if hud.selected_tile is not None and hovered_tile is not None and not redaktor:
        building_type = hud.selected_tile["name"]
        preview_img = scale_building_image(
            building_textures[building_type],
            hovered_tile.radius * 1.8
        )
        preview_img.set_alpha(160)
        preview_rect = preview_img.get_rect(center=hovered_tile.center)
        screen.blit(preview_img, preview_rect)

        can_build = can_place_building(hovered_tile, building_type)
        border_color = (108, 198, 118) if can_build else (214, 82, 78)
        hovered_tile.draw(screen, color=border_color, thick=2)

    unit_count = sum(unit.poluchit_yacheyki() for unit in muravi if unit.komanda == "igrok" and unit.zdorovie > 0)
    max_units = sum(building.unit_slots for building in buildings)
    hud.draw(screen, unit_count, max_units, turn_number, selected_ant_house)

    if not redaktor:
        end_turn_button.draw(screen, turn_number, b_enabled, has_unused_moves)

    if razdelenie is not None:
        rect = pygame.Rect(0, 0, 650, 38)
        rect.midtop = (screen.get_width() // 2, 44)
        pygame.draw.rect(screen, (41, 56, 44), rect)
        nadpis_na_okne(screen, "Выберите клетку для отделённого отряда", rect.center, 18, vyrovnyat="center")
    if kontekstnoe_menu is not None:
        kontekstnoe_menu.narisovat(screen)
    if okno_otryada is not None:
        okno_otryada.narisovat(screen)

    #Окно битвы:
    if avtoboy is not None:
        avtoboy.narisovat(screen)

    #Окно ивента:
    if event_popup is not None:
        event_popup.draw(screen)

    pygame.display.update() #чтобы показывалось изображение

pygame.quit()
