import pyglet
from pyglet.window import key
import random
import math

screen_num = 0
screens = pyglet.canvas.Display().get_screens()
screen = screens[screen_num]

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
PLAYER_SPEED = 300
MONSTER_SPEED = 100
PLAYER_IMAGE = pyglet.image.load("PNG/playerShip1_blue.png")
PLAYER_IMAGE.anchor_x = PLAYER_IMAGE.width // 2
PLAYER_IMAGE.anchor_y = PLAYER_IMAGE.height // 2

MONSTER_IMAGE = pyglet.image.load("PNG/Meteors/meteorBrown_big1.png")
MONSTER_IMAGE.anchor_x = MONSTER_IMAGE.width // 2
MONSTER_IMAGE.anchor_y = MONSTER_IMAGE.height // 2

WEAPON_IMAGE = pyglet.image.load("PNG/Parts/gun03.png")
WEAPON_IMAGE.anchor_x = WEAPON_IMAGE.width // 2
WEAPON_IMAGE.anchor_y = WEAPON_IMAGE.height // 2

PLAYER_MAX_HEALTH = 100
MONSTER_DAMAGE = 1
MONSTER_PUSH_FORCE = 50
SPAWN_INTERVAL = 1

class SpaceSurvivor(pyglet.window.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keys = key.KeyStateHandler()
        self.push_handlers(self.keys)
        self.player = Player(self.keys, self)
        self.player.game = self
        self.monsters = []
        self.bullets = []
        self.spawn_timer = 0
        self.score = 0
        self.player_health = PLAYER_MAX_HEALTH
        self.score_label = pyglet.text.Label('Score: {}'.format(self.score),
                                              font_name='Arial',
                                              font_size=12,
                                              x=10, y=self.height - 20,
                                              anchor_x='left', anchor_y='top')
        self.health_label = pyglet.text.Label('Health: {}'.format(self.player_health),
                                               font_name='Arial',
                                               font_size=12,
                                               x=10, y=self.height - 40,
                                               anchor_x='left', anchor_y='top')
        self.game_over_label = pyglet.text.Label('Game Over',
                                         font_name='Arial',
                                         font_size=36,
                                         x=self.width // 2,
                                         y=self.height // 2,
                                         anchor_x='center',
                                         anchor_y='center',
                                         color=(255, 0, 0, 255))
    
        self.center_on_screen()
    
    def center_on_screen(self):
        left = screen.width // 2 - self.width // 2
        top = screen.height // 2 - self.height // 2
        self.set_location(left, top)

    def update(self, dt):
        self.player.update(dt)
        for monster in self.monsters:
            monster.update(dt)

        self.monsters = [monster for monster in self.monsters if not monster.dead]
        self.bullets = [bullet for bullet in self.bullets if not bullet.dead]

        self.spawn_timer += dt
        if self.spawn_timer >= SPAWN_INTERVAL:
            self.spawn_timer = 0
            self.spawn_monster()

        for bullet in self.bullets:
            bullet.update(dt)
        
        if self.player.dead:
            self.game_over()

    def spawn_monster(self):
        new_monster = Monster(self.player)
        self.monsters.append(new_monster)

    def on_draw(self):
        self.clear()
        self.player.draw()
        for monster in self.monsters:
            monster.draw()
        for bullet in self.bullets:
            bullet.draw()

        self.score_label.text = 'Score: {}'.format(self.score)
        self.health_label.text = 'Health: {}'.format(self.player.health)
        self.score_label.draw()
        self.health_label.draw()
        if self.player.dead:
            self.game_over_label.draw()
    
    def game_over(self):
        pyglet.clock.unschedule(self.update)
        self.game_over_label.text = "Game Over Score: {}".format(self.score)
        self.game_over_label.x = self.width // 2
        self.game_over_label.y = self.height // 2


class GameObject(pyglet.sprite.Sprite):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dead = False

    def collides_with(self, other):
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)


class Player(GameObject):
    def __init__(self, keys, window, *args, **kwargs):
        super().__init__(img=PLAYER_IMAGE, *args, **kwargs)
        self.keys = keys
        self.game = window
        self.health = PLAYER_MAX_HEALTH
        self.x = WINDOW_WIDTH / 2
        self.y = WINDOW_HEIGHT / 2
        self.rotation = 0
        self.weapons = [Weapon(self, self.game)]

    def update(self, dt):
        dx = 0
        dy = 0
        if self.keys[key.A]:
            dx -= PLAYER_SPEED * dt
        if self.keys[key.D]:
            dx += PLAYER_SPEED * dt
        if self.keys[key.W]:
            dy += PLAYER_SPEED * dt
        if self.keys[key.S]:
            dy -= PLAYER_SPEED * dt

        if dx != 0 or dy != 0:
            angle_rad = math.atan2(dy, dx)
            self.rotation = 90 - math.degrees(angle_rad)

        self.x += dx
        self.y += dy

        if self.x > (WINDOW_WIDTH - self.width//2):
            self.x = WINDOW_WIDTH - self.width//2
        if self.y > (WINDOW_HEIGHT - self.width//2):
            self.y = WINDOW_HEIGHT - self.width//2
        if self.x < self.width//2:
            self.x = self.width//2
        if self.y < self.width//2:
            self.y = self.width//2

        for monster in self.game.monsters:
            if self.collides_with(monster):
                self.health -= MONSTER_DAMAGE
                if self.health <= 0:
                    self.dead = True
            if monster.dead:
                self.game.score += 10

        for weapon in self.weapons:
            weapon.update(dt)


class Monster(GameObject):
    def __init__(self, player, *args, **kwargs):
        super().__init__(img=MONSTER_IMAGE, *args, **kwargs)
        self.player = player
        self.x = random.randint(-WINDOW_WIDTH, 2 * WINDOW_WIDTH)
        self.y = random.randint(-WINDOW_HEIGHT, 2 * WINDOW_HEIGHT)

        if self.x < 0:
            self.x -= self.width
        if self.x > WINDOW_WIDTH:
            self.x += self.width
        if self.y < 0:
            self.y -= self.height
        if self.y > WINDOW_HEIGHT:
            self.y += self.height

        self.attack_cooldown = 0
        self.attack_damage = 10

    def update(self, dt):
        dx = self.player.x - self.x
        dy = self.player.y - self.y
        angle = math.atan2(dy, dx)
        self.x += math.cos(angle) * MONSTER_SPEED * dt
        self.y += math.sin(angle) * MONSTER_SPEED * dt

        self.attack_cooldown -= dt

        if self.collides_with(self.player) and self.attack_cooldown <= 0:
            self.player.health -= self.attack_damage
            self.attack_cooldown = 1000


class Weapon(GameObject):
    def __init__(self, player, window, *args, **kwargs):
        super().__init__(img=WEAPON_IMAGE, *args, **kwargs)
        self.player = player
        self.window = window
        self.cooldown = 0

    def update(self, dt):
        self.cooldown -= dt
        while self.cooldown <= 0:
            self.cooldown = 0
            self.fire()

    def fire(self):
        bullet_x = self.player.x
        bullet_y = self.player.y
        bullet = Bullet(bullet_x, bullet_y, self.player.rotation, self.player)
        self.player.game.bullets.append(bullet)
        self.cooldown = 0.5


class Bullet(GameObject):
    def __init__(self, x, y, rotation, player, *args, **kwargs):
        image = pyglet.image.load("PNG/Lasers/laserBlue02.png")
        super().__init__(img=image, x=x, y=y, *args, **kwargs)
        self.player = player
        self.rotation = rotation
        self.speed = 500
        self.dx =  self.speed * math.sin(math.radians(rotation))
        self.dy =  self.speed * math.cos(math.radians(rotation))

    def update(self, dt):
        self.x += self.dx * dt
        self.y += self.dy * dt

        for monster in self.player.game.monsters:
            if self.collides_with(monster):
                monster.dead = True
                self.dead = True
                break


window = SpaceSurvivor(WINDOW_WIDTH, WINDOW_HEIGHT, "Space Survivor")
pyglet.clock.schedule_interval(window.update, 1 / 60.0)
pyglet.app.run()