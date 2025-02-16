# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
from tilthenightends import Levelup, LevelupOptions, Vector, Team, Towards
from tilthenightends.player import PlayerInfo


RNG = np.random.default_rng(seed=12)
detection_angle = 3*np.pi/8
max_dodge_angle = np.pi/4
danger_distance = 800
critical_distance = 200
class Leader:
    def __init__(self, hero: str):
        self.hero = hero
        self.next_turn = 5.0
        self.vector = Vector(1, 0)
        self.dodge = False
    def run(self, t, dt, monsters, players, pickups) -> Vector | Towards | None:
        self.x = players[self.hero].x
        self.y = players[self.hero].y
        self.angle =np.arctan2(self.vector.y, self.vector.x)
        if t > self.next_turn:
            self.vector, self.dodge = self.choose_path(monsters)
            target_direction = self.treasure_nearby(pickups)
            self.next_turn += 5.0
            if self.dodge:
                return self.vector
            else:
                return target_direction
    def choose_path(self, monsters) -> Vector:
        monsters_near = self.monsters_ahead(monsters)
        critical_angles = []
        deviation_angle = 0
        dodge = False
        for monster in monsters_near:
            if monster[0] < critical_distance:
                critical_angles.append(monster[1]*(critical_distance-monster[0])/critical_distance)
            else:
                deviation_angle += -np.sign(monster[1])*detection_angle*(danger_distance-monster[0])/danger_distance
        if len(critical_angles) > 0:
            dodge = True
            if sum(critical_angles) > 0:
                return (self.rotate_vector(self.vector, -max_dodge_angle), dodge)
            else:
                return (self.rotate_vector(self.vector, max_dodge_angle), dodge)
        else:
            if deviation_angle > max_dodge_angle:
                deviation_angle = max_dodge_angle
            if deviation_angle < -max_dodge_angle:
                deviation_angle = -max_dodge_angle
            return (self.rotate_vector(self.vector, deviation_angle), dodge)
    def monsters_ahead(self, monsters) -> list:
        monsters_list = []
        for keys in monsters.keys():
            number_of_monsters = len(monsters[keys].x)
            for i in range(number_of_monsters):
                monster = monsters[keys]
                distance = np.linalg.norm([monster.x[i] - self.x, monster.y[i] - self.y])
                angle = np.arctan2(monster.y[i] - self.y, monster.x[i] - self.x)
                if distance < danger_distance and (angle - self.angle) < detection_angle and (angle - self.angle) > -detection_angle:
                    monsters_list.append((distance, angle-self.angle))
        return monsters_list
    def rotate_vector(self, vector, angle) -> Vector:
        x = vector.x * np.cos(angle) - vector.y * np.sin(angle)
        y = vector.x * np.sin(angle) + vector.y * np.cos(angle)
        return Vector(x, y)
    def treasure_nearby(self, pickups) -> Towards:
        nearest_pickup = 1000
        for keys in pickups.keys():
            number_of_pickups = len(pickups[keys].x)
            for i in range(number_of_pickups):
                pickup = pickups[keys]
                distance = np.linalg.norm([pickup.x[i] - self.x, pickup.y[i] - self.y])
                if distance < nearest_pickup:
                    direction = Towards(pickup.x[i], pickup.y[i])
                    nearest_pickup = distance
        if nearest_pickup == 1000:
            direction = self.vector
        return direction


class Follower:
    def __init__(self, hero: str, following: str):
        self.hero = hero
        self.following = following

    def run(self, t, dt, monsters, players, pickups) -> Vector | Towards | None:
        for name, player in players.items():
            if name == self.following:
                return Towards(players["garron"].x, players["garron"].y)
        return None

class Brain:
    def __init__(self):
        self.stats_lvlup = {
            "player_health":  "*1.05",
            "player_speed": "+1.0",
            "weapon_health": "*1.05",
            "weapon_speed": "+1.0",
            "weapon_damage": "*1.02",
            "weapon_cooldown": "*0.9",
            "weapon_size": "*1.10",
        }

    def calc_effective_dps(
            self, 
            pinfo: PlayerInfo, 
            weapon_size=None, 
            weapon_speed=None, 
            weapon_cooldown=None, 
            weapon_damage=None, 
            weapon_health=None,
            weapon_longevity=None,
            player_health=None,
            player_speed=None,
        ):
        

        health = (1 + weapon_health // 50) if weapon_health else pinfo.weapon.health
        size = weapon_size if weapon_size else pinfo.weapon.size
        long = weapon_longevity if weapon_longevity else pinfo.weapon.longevity
        cd = weapon_cooldown if weapon_cooldown else pinfo.weapon.cooldown
        dmg = weapon_damage if weapon_damage else pinfo.weapon.damage

        if cd < 0:
            cd = 1

        return size * dmg * health * long / cd


    def levelup(self, t: float, info: dict, players: dict[str, PlayerInfo]) -> Levelup:
        pds = ["garron", "weapon_cooldown", 1] # player, choice, dps_increase
        player: str
        pinfo: PlayerInfo

        # for player, pinfo in players.items():
        #     if pinfo.weapon.cooldown > 4.4:
        #         return Levelup(player, LevelupOptions.weapon_cooldown)

        for player, pinfo in players.items():
            lvl: dict[str, int] = pinfo.levels
            new_stats = {
                "weapon_health": pinfo.weapon.health * 1.05 /(1 + lvl.get("weapon_health", 1)) ,
                "weapon_speed": pinfo.weapon.speed + 1.0 /(1 + lvl.get("weapon_speed", 1)),
                "weapon_damage": 0.5 * pinfo.weapon.damage * 1.02 /(1 + lvl.get("weapon_damage", 1)),
                "weapon_cooldown": 0.8 * pinfo.weapon.cooldown * 0.9 * (1 + lvl.get("weapon_cooldown", 1)),
                "weapon_size": 1.05 * pinfo.weapon.size * 1.10 /(1 + lvl.get("weapon_size", 1)),
                "weapon_longevity": 1.1 * pinfo.weapon.longevity * 1.05 /(1 + lvl.get("weapon_longevity", 1)),
            }
            for lvlinfo, new_stat in new_stats.items():
                new_dps = self.calc_effective_dps(pinfo, **{lvlinfo:new_stat})
                dps_increase = new_dps / self.calc_effective_dps(pinfo)
                if dps_increase > pds[2] and pinfo.alive:
                    pds = [player, lvlinfo, dps_increase]

        return Levelup(pds[0], LevelupOptions[pds[1]])


team = Team(
    players=[
        Leader(hero="garron"),
        Follower(hero="cedric", following="garron"),
        Follower(hero="seraphina", following="garron"),
        Follower(hero="isolde", following="garron"),
        Follower(hero="evelyn", following="garron"),
    ],
    strategist=Brain(),
)
