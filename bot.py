# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
from tilthenightends import Levelup, LevelupOptions, Vector, Team, Towards


RNG = np.random.default_rng(seed=12)


class Leader:
    def __init__(self, hero: str):
        self.hero = hero
        self.next_turn = 5.0
        self.vector = Vector(1, 1)

    def run(self, t, dt, monsters, players, pickups) -> Vector | Towards | None:
        if t > self.next_turn:
            self.vector = Vector(*RNG.random(2) * 2 - 1)
            self.next_turn += 5.0
        return self.vector


class Follower:
    def __init__(self, hero: str, following: str):
        self.hero = hero
        self.following = following

    def run(self, t, dt, monsters, players, pickups) -> Vector | Towards | None:
        for name, player in players.items():
            if name == self.following:
                return Towards(player.x, player.y)
        return None


class Brain:
    def __init__(self):
        pass

    def levelup(self, t: float, info: dict, players: dict) -> Levelup:
        # A very random choice
        hero = RNG.choice(list(players.keys()))
        what = RNG.choice(list(LevelupOptions))
        return Levelup(hero, what)


team = Team(
    players=[
        Leader(hero="alaric"),
        Follower(hero="kaelen", following="alaric"),
        Follower(hero="garron", following="alaric"),
        Follower(hero="isolde", following="alaric"),
        Follower(hero="lyra", following="alaric"),
    ],
    strategist=Brain(),
)
