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
units_json = os.path.join(data_dir, "units.json")
with open(units_json, "r", encoding="utf-8") as fail:
    units = json.load(fail)

provintsii_json = os.path.join(data_dir, "tipy_provintsiy.json")

if os.path.exists(provintsii_json):
    with open(provintsii_json, "r", encoding="utf-8") as fail:
        tipy_provintsiy = json.load(fail)
else:
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
    pygame.image.load(os.path.join(textures_dir, f"ant{i}.png")).convert_alpha()
    for i in range(1, 4)
]

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
        if left_click[0] and button_rect.collidepoint(mouse_pos) and self.b_enabled:
            return True
        else:
            return False
        



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
            # Это пока затычка для богомола, отдельного атласа для него нет.
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
    def __init__(self, gruppa, pozitsiya, razmer, nomer, storona):
        self.tip = gruppa.tip
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
            # У старого спрайта удара нет, поэтому немного двигаем тело вперёд.
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
        razmer = min(units[gruppa.tip]["razmer_v_boyu"], max(5, int(interval * .92)))
        shag = min(interval, max(razmer * .95, 17))
        x = self.arena.left + 18 if storona == 0 else self.arena.right - 18
        znak = 1 if storona == 0 else -1
        for i in range(n):
            col, row = i % stolbtsy, i // stolbtsy
            p = (x + znak * (razmer/2 + col * shag), self.arena.centery + (row-(ryady-1)/2)*shag)
            boets = Boets(gruppa, p, razmer, len(self.boitsy), storona)
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
        if not tsel.zhiv or not boets.zhiv:
            return
        if boets.pozitsiya.distance_to(tsel.pozitsiya) > boets.radius+tsel.radius+boets.dalnost+4:
            return
        if self.nachalo_udarov is None:
            self.nachalo_udarov = self.vremya
        tsel.animatsiya.vspyshka = .09
        tsel.udary += 1
        storona = tsel.storona
        if self.ostalos[storona] <= self.vyzhivet[storona]:
            return
        # Потери считаются заранее, удар только решает, кто именно погибнет.
        proshlo = self.vremya - self.nachalo_udarov
        razresheno = min(self.poteri[storona], 1+int(self.poteri[storona]*proshlo/5.5))
        if self.poteri[storona] - (self.ostalos[storona]-self.vyzhivet[storona]) >= razresheno:
            return
        drugaya = 1-storona
        # Не даём одной армии исчезнуть слишком рано, иначе последнему бойцу
        # придётся в одиночку добивать десятки противников.
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

    def ubit(self, boets):
        if boets.zhiv:
            boets.umeret()
            self.ostalos[boets.storona] -= 1

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
            if b.tsel is None or not b.tsel.zhiv:
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
            # Если бойцы застряли, результат всё равно должен совпасть с расчётом.
            self.avarijno = self.ostalos != self.vyzhivet
            for i in range(2):
                kandidaty = sorted((b for b in self.po_storonam[i] if b.zhiv), key=lambda b: -b.udary)
                for b in kandidaty[:self.ostalos[i]-self.vyzhivet[i]]:
                    self.ubit(b)
            self.zakonchen = True

    def narisovat(self, poverhnost):
        staryy_clip = poverhnost.get_clip()
        poverhnost.set_clip(self.arena)
        for b in sorted(self.boitsy, key=lambda b: (b.zhiv,b.pozitsiya.y)):
            b.narisovat(poverhnost)
        poverhnost.set_clip(staryy_clip)


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
        pelmeshki.animatsiya = Animatsiya(tip, komanda, dannye["razmer_na_karte"])

    def narisovat(pelmeshki, poverhnost):
        if pelmeshki.zdorovie <= 0:
            return

        kartinka = pelmeshki.animatsiya.kartinka(pelmeshki.ugol)
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
        pelmeshki.animatsiya.ustanovit("hodba" if pelmeshki.marshrut else "pokoy")
        pelmeshki.animatsiya.obnovit(delta_time)
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
        elif rasstoyanie > 0:
            pelmeshki.pozitsiya += napravlenie.normalize() * shag

    def umeret(pelmeshki):
        # Сюда сводим любую гибель: и утопление, и проигрыш целой группы.
        if pelmeshki.zdorovie <= 0:
            return
        pelmeshki.zdorovie = 0
        pelmeshki.kolichestvo = 0
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
    # Победитель известен ещё до анимации. Иначе пришлось бы запускать ИИ для каждого муравья.
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

        # Чем ближе силы отрядов, тем больше потери. У победителя останется хотя бы один живой.
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

        self.sh_zagolovok = pygame.font.SysFont("arial", 29, bold=True)
        self.sh_krupnyy = pygame.font.SysFont("arial", 42, bold=True)
        self.sh_obychniy = pygame.font.SysFont("arial", 22, bold=True)
        self.sh_malyy = pygame.font.SysFont("arial", 18)

        koord_zashchitnika = (pravyy.kletka.col, pravyy.kletka.row)
        tip_polya_boya = provintsii_kletok.get(koord_zashchitnika, "polya")
        self.palette = self.poluchit_paltru_boya(tip_polya_boya)

        # На больших отрядах ужимаем отдельные спрайты, но не подменяем армию одной картинкой.
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
        # Только после экрана результата переносим потери на карту.
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



# Все достижимые клетки и предшественники маршрута

def nayti_dostupnye_kletki(muravey):
    nachalo = (muravey.kletka.col, muravey.kletka.row)
    # Тут считаем реальные затраты на клетки.
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
    # Проверяем ещё и маршрут юнита, чтобы не поставить здание прямо у него под ногами.
    is_occupied = any(
        unit.zdorovie > 0 and (unit.kletka is tile or tile in unit.marshrut)
        for unit in muravi
    )
    return (
        tile.building is None
        and terrain.get("prohodima", True)
        and not terrain.get("smertelna", False)
        and not is_occupied
        and resource_manager.is_affordable(building_type)
    )


# Инициализация карты
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
    Muravey("bogomol", hex_grid[(12, 4)], "vrag", 1),
    Muravey("tarantul", hex_grid[(16, 5)], "vrag", 1)
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
shrift_kolichestva = pygame.font.SysFont("arial", 13, bold=True)
shrift_imen_vragov = pygame.font.SysFont("arial", 12, bold=True)

effekty_smerti = []
shrift_smerti = pygame.font.SysFont("arial", 12, bold=True)
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

while running:
    delta_time = max(0.001, min(0.1, clock.tick(60) / 1000))
    mouse_pos = pygame.mouse.get_pos()

    # Пока идёт автобой, стратегическая карта полностью ждёт.
    if avtoboy is not None:
        avtoboy.obnovit(delta_time)
    else:
        x += 50 * delta_time
        for muravey in muravi:
            muravey.obnovit(delta_time)

        for muravey in muravi:
            vrag = muravey.vrag_dlya_boya
            if vrag is None or muravey.marshrut:
                continue
            muravey.vrag_dlya_boya = None
            if (muravey.zdorovie > 0 and vrag.zdorovie > 0
                    and muravey.kolichestvo > 0 and vrag.kolichestvo > 0
                    and muravey.kletka.is_has_neighbor(vrag.kletka)):
                avtoboy = Avtoboy(muravey, vrag)
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


    boy_zakryvalsya_v_etom_kadre = avtoboy is not None
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            continue

        if boy_zakryvalsya_v_etom_kadre:
            # Даже после клика «Вернуться» остатки событий этого кадра не пускаем на карту.
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if avtoboy is not None and avtoboy.obrabotat_nazhatie(event.pos):
                    avtoboy = None
                    vybrannyy_muravey = None
                    tsel_ataki = None
            continue

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F2:
                redaktor = not redaktor
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
                    for muravey in muravi:
                        if muravey.zdorovie > 0:
                            muravey.ostalos_hodov = muravey.prohodimost
                            muravey.atakoval_v_etom_hodu = False
                    vybrannyy_muravey = None
                    tsel_ataki = None
                    for building in buildings:
                        building.produce_per_turn()
                    print("Новый ход!")

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                hud.selected_tile = None
                vybrannyy_muravey = None
                tsel_ataki = None

            if event.button == 1 and not redaktor:
                if hud.is_mouse_over(event.pos):
                    for tile in hud.tiles:
                        if tile["rect"].collidepoint(event.pos):
                            hud.selected_tile = tile
                            vybrannyy_muravey = None
                            tsel_ataki = None
                            break
                    continue

                kletka = hex_under_mouse(hex_grid, event.pos)
                if kletka is None:
                    continue

                # Если выбрали постройку, этот клик уже не должен двигать муравья.
                if hud.selected_tile is not None:
                    building_type = hud.selected_tile["name"]
                    if can_place_building(kletka, building_type):
                        building = BUILDING_CLASSES[building_type](kletka, resource_manager)
                        kletka.building = building
                        buildings.append(building)
                        hud.selected_tile = None
                    continue

                nazhatyy_muravey = None
                for muravey in muravi:
                    if muravey.kletka is kletka and muravey.zdorovie > 0:
                        nazhatyy_muravey = muravey
                        break

                if nazhatyy_muravey is not None:
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
                                # Подход оплачиваем, а сама атака очки движения не забирает.
                                vybrannyy_muravey.vrag_dlya_boya = nazhatyy_muravey
                                vybrannyy_muravey.atakoval_v_etom_hodu = True
                                vybrannyy_muravey = None
                            tsel_ataki = None
                else:
                    tsel_ataki = None
                    if vybrannyy_muravey is not None:
                        vybrannyy_muravey.peremestitsya(kletka)

    if hud.is_mouse_over(mouse_pos) or avtoboy is not None:
        hovered_tile = None
    else:
        hovered_tile = hex_under_mouse(hex_grid)

    if (avtoboy is None and redaktor and hovered_tile is not None
            and pygame.mouse.get_pressed()[0]):
        koord = (hovered_tile.col, hovered_tile.row)
        provintsii_kletok[koord] = tip_kisti

    screen.fill((128, 128, 128))
    screen.blit(stonewall1_img, (x, 500))
    screen.blit(scaled_map_img, (0, 0))

    setka_sloy.fill((0, 0, 0, 0))
    if not redaktor and vybrannyy_muravey is not None and avtoboy is None:
        if vybrannyy_muravey.zdorovie > 0 and not vybrannyy_muravey.marshrut:
            dostupnye = {}
            if vybrannyy_muravey.ostalos_hodov > 0:
                dostupnye, _ = nayti_dostupnye_kletki(vybrannyy_muravey)
                for koord in dostupnye:
                    pygame.draw.polygon(
                        setka_sloy, (40, 200, 75, 85), hex_grid[koord].table_points
                    )

            # Враги подсвечиваются сами, если до них можно дойти и напасть.
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

    for building in buildings:
        building.draw(screen)

    for muravey in muravi:
        muravey.narisovat(screen)

    if avtoboy is None:
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
            screen.blit(kartinka, kartinka.get_rect(center=effekt["pozitsiya"]))
            nadpis = tekst_smerti.copy()
            nadpis.set_alpha(alfa)
            mesto = nadpis.get_rect(center=effekt["pozitsiya"])
            screen.blit(nadpis, mesto)

    test_button = TestButton("КЛИК НА МЕНЯ", 250, 250, True)

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
    hud.draw(screen, unit_count, max_units)

    # Окно битвы.
    if avtoboy is not None:
        avtoboy.narisovat(screen)

    """#МЫШКА:
        if event.type == pygame.MOUSEBUTTONDOWN:
            print("КЛИК")
        if event.type == pygame.MOUSEBUTTONUP:
            print("КЛИК КОНЧИЛСЯ")"""

    pygame.display.update() #чтобы показывалось изображение

pygame.quit()
