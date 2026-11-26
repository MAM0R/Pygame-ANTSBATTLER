import pygame #ВИНОВНИК ТОРЖЕСТВА!
import os #нужен чтобы папка не потерялась внутри системы
import random
import math
import json
import heapq #для работы с большой структурой данных



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
    "odin": False
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
                has_slot = unit_count < max_units
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
            bg_color = (95, 100, 105)
            border_color = (60, 65, 70)
            text_color = (180, 180, 180)
            label = "Ожидание..."
        elif not has_unused_moves:
            bg_color = (85, 175, 95) if hovered else (65, 145, 75)
            border_color = (230, 255, 220)
            text_color = (255, 255, 255)
            label = f"{self.text} ({turn_number})"
        else:
            bg_color = (235, 180, 75) if hovered else (205, 160, 55)
            border_color = (255, 240, 180)
            text_color = (25, 20, 10)
            label = f"{self.text} ({turn_number})"
        
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=8)
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=8)

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
        self.title_font = pygame.font.SysFont("Russo One", 26)
        self.body_font = pygame.font.SysFont("PT Sans", 20)
        self.badge_font = pygame.font.SysFont("Russo One", 18)
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
        pygame.draw.rect(surface, (26, 33, 42), self.panel, border_radius=12)
        pygame.draw.rect(surface, self.accent_color, self.panel, 3, border_radius=12)
        
        header_rect = pygame.Rect(self.panel.left + 3, self.panel.top + 3, self.panel.width - 6, 86)
        pygame.draw.rect(surface, (36, 45, 56), header_rect, border_top_left_radius=9, border_top_right_radius=9)
        
        emoji_bg = pygame.Rect(self.panel.left + 26, self.panel.top + 18, 56, 56)
        pygame.draw.rect(surface, (22, 28, 36), emoji_bg, border_radius=10)
        surface.blit(self.emoji_surface, self.emoji_surface.get_rect(center = emoji_bg.center))
        
        title_surf = self.title_font.render(self.title, True, (245, 245, 245))
        surface.blit(title_surf, title_surf.get_rect(midleft=(emoji_bg.right + 18, emoji_bg.centery)))
        
        y_pos = self.panel.top + 122
        for line in self.wrap_text(self.description, self.panel.width - 70):
            line_surf = self.body_font.render(line, True, (218, 224, 230))
            surface.blit(line_surf, line_surf.get_rect(midtop=(self.panel.centerx, y_pos)))
            y_pos += 30
            
        badge_box = pygame.Rect(self.panel.left + 45, self.panel.bottom - 148, self.panel.width - 90, 48)
        pygame.draw.rect(surface, (34, 43, 54), badge_box, border_radius=10)
        pygame.draw.rect(surface, self.accent_color, badge_box, 1, border_radius=8)
        pygame.draw.rect(surface,self.accent_color, badge_box, 1, border_radius=10)
        badge_surf = self.badge_font.render(self.badge_text, True, self.accent_color)
        surface.blit(badge_surf, badge_surf.get_rect(center = badge_box.center))
        
        hovered = self.button_rect.collidepoint(pygame.mouse.get_pos())
        btn_color = ( #ЦВЕТ КНОПКИ
            min(255, self.accent_color[0] + 25),
            min(255, self.accent_color[1] + 25),
            min(255, self.accent_color[2] + 25),
        ) if hovered else self.accent_color
        
        pygame.draw.rect(surface, btn_color, self.button_rect, border_radius=8)
        pygame.draw.rect(surface, (240, 240, 240), self.button_rect, 2, border_radius=8)
        btn_label = font.render(self.button_text, True, (18, 22, 26))
        surface.blit(btn_label, btn_label.get_rect(center=self.button_rect.center))


#Муравьи и их перемещение:
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
        pelmeshki.vremya_animatsii = 0.0
        pelmeshki.skorost_dvizheniya = 160
        pelmeshki.ugol = 0
        pelmeshki.vrag_dlya_boya = None
        pelmeshki.atakoval_v_etom_hodu = False

    def narisovat(pelmeshki, poverhnost, kadry):
        if pelmeshki.zdorovie <= 0:
            return

        if pelmeshki.marshrut:
            nomer = int(pelmeshki.vremya_animatsii / 0.12) % len(kadry)
        else:
            nomer = 0

        kartinka = pygame.transform.rotate(kadry[nomer], pelmeshki.ugol)
        mesto = kartinka.get_rect(center=(
            round(pelmeshki.pozitsiya.x),
            round(pelmeshki.pozitsiya.y)
        ))
        poverhnost.blit(kartinka, mesto)

        chislo = shrift_kolichestva.render(str(pelmeshki.kolichestvo), True, (255, 255, 255))
        podlozhka = chislo.get_rect(bottomright=(mesto.right + 4, mesto.bottom + 5))
        podlozhka.inflate_ip(7, 4)
        pygame.draw.rect(poverhnost, (18, 30, 35), podlozhka, border_radius=5)
        poverhnost.blit(chislo, chislo.get_rect(center=podlozhka.center))

        if pelmeshki.odin:
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
        pelmeshki.vremya_animatsii = 0.0
        return True

    def obnovit(pelmeshki, delta_time):
        global pending_event_trigger #нужно для системы ивентов
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
        pelmeshki.marshrut.clear()
        pelmeshki.vrag_dlya_boya = None
        effekty_smerti.append({
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
    #Победитель известен ещё до анимации:
    def sila(gruppa):
        zaschita = max(0.05, 1 - max(0, min(95, gruppa.bronya)) / 100)
        return gruppa.kolichestvo * max(0, gruppa.uron) * max(0, gruppa.max_zdorovie) / zaschita

    sila_levogo = sila(levyy)
    sila_pravogo = sila(pravyy)
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

        #Чем больше силы - тем больше потери:
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
        "pobeditel": pobeditel
    }


class Avtoboy:
    def __init__(self, levyy, pravyy, kadry):
        self.levyy = levyy
        self.pravyy = pravyy
        self.kadry = kadry
        self.itog = rasschitat_boy(levyy, pravyy)
        self.vremya = 0.0
        self.stadiya = "bitva"

        self.panel = pygame.Rect(245, 80, 1110, 740)
        self.arena = pygame.Rect(287, 255, 1026, 355)
        self.knopka = pygame.Rect(630, 719, 340, 59)
        self.fon_zatemneniya = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        self.fon_zatemneniya.fill((9, 17, 25, 205))

        self.sh_zagolovok = pygame.font.SysFont("arial", 29, bold=True)
        self.sh_krupnyy = pygame.font.SysFont("arial", 42, bold=True)
        self.sh_obychniy = pygame.font.SysFont("arial", 22, bold=True)
        self.sh_malyy = pygame.font.SysFont("arial", 18)

        koord_zashchitnika = (pravyy.kletka.col, pravyy.kletka.row)
        tip_polya_boya = provintsii_kletok.get(koord_zashchitnika, "polya")
        self.palette = self.poluchit_paltru_boya(tip_polya_boya)

        #На больших отрядах меньше размер отдельных спрайтов:
        self.figury_levogo, size_l = self.sozdat_figury(
            self.itog["do_levogo"], self.itog["posle_levogo"], "levyy"
        )
        self.figury_pravogo, size_p = self.sozdat_figury(
            self.itog["do_pravogo"], self.itog["posle_pravogo"], "pravyy"
        )
        self.sprayty = {}
        for storona, razmer in (("levyy", size_l), ("pravyy", size_p)):
            razmer = max(8, razmer)
            if storona == "pravyy" and pravyy.tip in ("bogomol", "tarantul"):
                razmer = 62 if pravyy.tip == "bogomol" else 72
            self.sprayty[storona] = [
                pygame.transform.rotate(
                    pygame.transform.scale(kadr, (razmer, razmer)),
                    -90 if storona == "levyy" else 90
                )
                for kadr in kadry
            ]

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

    def sozdat_figury(self, kolichestvo, vyzhilo, storona):
        stolbtsy = max(1, min(17, math.ceil(math.sqrt(kolichestvo * 1.6))))
        ryady = math.ceil(kolichestvo / stolbtsy)
        interval = min(43, 330 / max(1, stolbtsy), 290 / max(1, ryady))
        razmer = max(8, int(min(35, interval * 0.80)))
        nachalnyy_x = self.arena.left + 165 if storona == "levyy" else self.arena.right - 165
        konechnyy_x = self.arena.centerx - 88 if storona == "levyy" else self.arena.centerx + 88
        tsentr_y = self.arena.centery + 23

        figury = []
        for i in range(kolichestvo):
            col = i % stolbtsy
            row = i // stolbtsy
            dx = (col - (stolbtsy - 1) / 2) * interval
            dy = (row - (ryady - 1) / 2) * interval
            figury.append({
                "start": (nachalnyy_x + dx, tsentr_y + dy),
                "konets": (konechnyy_x + dx, tsentr_y + dy),
                "smert": None,
                "otstup": (i % 3 - 1) * 2
            })

        #Кого именно убрать (всего 1раз):
        indeksi = list(range(kolichestvo))
        random.Random(kolichestvo * 97 + vyzhilo * 17).shuffle(indeksi)
        skolko_umerlo = kolichestvo - vyzhilo
        for poriadok, i in enumerate(indeksi[:skolko_umerlo]):
            figury[i]["smert"] = 2.8 + (poriadok + 1) / (skolko_umerlo + 1) * 4.8

        return figury, razmer

    def obnovit(self, delta_time):
        if self.stadiya != "bitva":
            return
        self.vremya += delta_time
        if self.vremya >= 8.2:
            self.vremya = 8.2
            self.stadiya = "rezultat"

    def zavershit(self):
        #Только после экрана результата перенос потери на карту:
        for gruppa, kluch in (
            (self.levyy, "posle_levogo"),
            (self.pravyy, "posle_pravogo")
        ):
            vyzhilo = self.itog[kluch]
            if vyzhilo <= 0:
                gruppa.umeret()
            else:
                gruppa.kolichestvo = vyzhilo
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

    def narisovat_figury(self, poverhnost, figury, storona):
        #Анимация:
        priblizhenie = max(0, min(1, (self.vremya - 0.65) / 1.7))
        priblizhenie = priblizhenie * priblizhenie * (3 - 2 * priblizhenie)
        kadr = int(self.vremya / 0.12) % len(self.sprayty[storona])
        if self.vremya < 0.65:
            kadr = 0
        for i, figura in enumerate(figury):
            smert = figura["smert"]
            if smert is not None and self.vremya >= smert + 0.34:
                continue
            alfa = 255
            if smert is not None and self.vremya >= smert:
                alfa = max(0, int(255 * (1 - (self.vremya - smert) / 0.34)))

            x1, y1 = figura["start"]
            x2, y2 = figura["konets"]
            x = x1 + (x2 - x1) * priblizhenie
            y = y1 + (y2 - y1) * priblizhenie
            if 2.35 < self.vremya < 7.7:
                storona_udara = 1 if storona == "levyy" else -1
                x += storona_udara * math.sin(self.vremya * 10 + i * 1.3) * 6
                y += math.sin(self.vremya * 7 + i * 0.8) * 3

            kartinka = self.sprayty[storona][kadr]
            if alfa != 255:
                kartinka = kartinka.copy()
                kartinka.set_alpha(alfa)
            rect = kartinka.get_rect(center=(round(x), round(y)))
            poverhnost.blit(kartinka, rect)

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

        def ostalos(figury):
            return sum(
                1 for figura in figury
                if figura["smert"] is None or figura["smert"] > self.vremya
            )

        self.tekst(
            poverhnost, f"{ostalos(self.figury_levogo)} муравьёв",
            self.sh_obychniy, self.palette["osnovnoy_tekst"],
            (self.panel.left + 48, self.panel.top + 146), "midleft"
        )
        kolichestvo_vraga = (
            f"{ostalos(self.figury_pravogo)} из {self.itog["do_pravogo"]}"
            if self.pravyy.odin
            else f"{ostalos(self.figury_pravogo)} муравьёв"
        )
        self.tekst(
            poverhnost, kolichestvo_vraga,
            self.sh_obychniy, self.palette["osnovnoy_tekst"],
            (self.panel.right - 48, self.panel.top + 146), "midright"
        )

        pygame.draw.rect(poverhnost, self.palette["arena"], self.arena)
        self.narisovat_figury(poverhnost, self.figury_levogo, "levyy")
        self.narisovat_figury(poverhnost, self.figury_pravogo, "pravyy")

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

def nayti_dostupnye_kletki(muravey):
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
            if novyy_rashod > muravey.ostalos_hodov:
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
    #ФИКС НЕ ПОСТАВИТЬ ЗДАНИЕ ПОД НОГАМИ
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
    unit_count = sum(1 for unit in muravi if unit.komanda == "igrok" and unit.zdorovie > 0)
    max_units = sum(building.unit_slots for building in buildings)

    if unit_count >= max_units:
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
        return {"type": "spider", "count": random.randint(2, 3)}
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
        current_units = sum(1 for u in muravi if u.komanda == "igrok" and u.zdorovie > 0)
        max_units = sum(b.unit_slots for b in buildings)
        tile.event = None
        tile.event_state = None

        if current_units >= max_units:
            return EventPopup(
                "Бродячие войны-муравьи",
                "К вам хотел присоединиться дружественный отряд, но в колонии не хватает свободных ячеек для юнитов!",
                f"Мест нет ({current_units}/{max_units}) — ивент пропущен",
                "🐜",
                (170, 175, 185),
                "Грустно, понятно)"
            )
        spawn_tile = find_free_neighbor(tile)
        new_type = event_data["unit_type"]
        new_count = event_data["count"]
        unit_title = units[new_type].get("nazvanie", new_type)

        if spawn_tile is not None:
            muravi.append(Muravey(new_type, spawn_tile, "igrok", new_count))
            badge = f"+1 отряд ({unit_title}, {new_count} шт.)"
        else:
            player_ant.kolichestvo += new_count
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
            border_color = (90, 235, 165) if tile.building is None else (235, 200, 95)
            pygame.draw.polygon(surface, border_color, tile.table_points, 3)

        if tile.event is not None:
            cx, cy = int(tile.center.x), int(tile.center.y)
            is_failed = tile.event_state == "failed_battle"
            color = (255, 65, 65) if is_failed else (255, 230, 0)
            symbol = "!" if is_failed else "?"

            shadow = marker_font.render(symbol, True, (15, 15, 20))
            mark = marker_font.render(symbol, True, color)
            surface.blit(shadow, shadow.get_rect(center=(cx + 1, cy + 1)))
            surface.blit(mark, mark.get_rect(center=(cx, cy)))


#Инициализация карты:
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

muravi = [
    Muravey("rabochiy", hex_grid[(4, 4)], "igrok", 12),
    Muravey("soldat", hex_grid[(6, 4)], "igrok", 12),
    Muravey("soldat", hex_grid[(10, 4)], "vrag", 9),
    Muravey("bogomol", hex_grid[(12, 4)], "vrag", 1),
    Muravey("tarantul", hex_grid[(16, 5)], "vrag", 1)
]

vybrannyy_muravey = None
selected_ant_house = None
tsel_ataki = None
avtoboy = None
event_popup = None
pending_event_trigger = None
active_event_battle = None
marker_font = pygame.font.SysFont("PT Sans", 17, bold=True)
shrift_kolichestva = pygame.font.SysFont("PT Sans", 13, bold=True)
shrift_imen_vragov = pygame.font.SysFont("PT Sans", 12, bold=True)

effekty_smerti = []
shrift_smerti = pygame.font.SysFont("PT Sans", 12, bold=True)
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

        if pending_event_trigger is not None:
            triggered_ant, triggered_tile = pending_event_trigger
            pending_event_trigger = None
            if triggered_ant.zdorovie > 0 and triggered_tile.event is not None:
                vybrannyy_muravey = None
                tsel_ataki = None
                selected_ant_house = None
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
                    avtoboy = Avtoboy(muravey, vrag, kadry_muravya)
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
        and not redaktor
        and all(not muravey.marshrut and muravey.vrag_dlya_boya is None for muravey in muravi)
    )
    has_unused_moves = any(
        muravey.komanda == "igrok" and muravey.zdorovie > 0 and muravey.ostalos_hodov > 0
        for muravey in muravi
    )

    boy_zakryvalsya_v_etom_kadre = avtoboy is not None
    popup_otkryt_v_etom_kadre = event_popup is not None
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
                            # Отряд игрока погиб на этой клетке — меняем '?' на красный '!'
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
                        event_enemy.kolichestvo = battle_data["count"]
                        active_event_battle = {
                            "tile": battle_data["tile"],
                            "enemy": event_enemy
                        }
                        avtoboy = Avtoboy(battle_data["player_ant"], event_enemy, kadry_muravya)
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
            or event_popup is not None):
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
    if not redaktor and vybrannyy_muravey is not None and avtoboy is None and event_popup is None:
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
        tile.draw(setka_sloy, color=(200, 200, 200, 90), thick=3)

    if hovered_tile is not None:
        hovered_tile.draw(setka_sloy, color=(255, 255, 0, 180), thick=6)

    screen.blit(setka_sloy, (0, 0))

    draw_tile_markers(screen)

    if selected_ant_house is not None:
        pygame.draw.polygon(screen, (255, 220, 80), selected_ant_house.tile.table_points, 3)

    for building in buildings:
        building.draw(screen)

    for muravey in muravi:
        muravey.narisovat(screen, kadry_muravya)

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
        border_color = (50, 255, 50) if can_build else (255, 60, 60)
        hovered_tile.draw(screen, color=border_color, thick=4)

    unit_count = sum(1 for unit in muravi if unit.komanda == "igrok" and unit.zdorovie > 0)
    max_units = sum(building.unit_slots for building in buildings)
    hud.draw(screen, unit_count, max_units, turn_number, selected_ant_house)

    if not redaktor:
        end_turn_button.draw(screen, turn_number, b_enabled, has_unused_moves)

    #Окно битвы:
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