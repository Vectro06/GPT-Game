import math
import random
from functools import lru_cache

import pygame as pg

INK = "#192f34"
PAPER = "#fff2d3"
GOLD = "#ffd478"
MINT = "#98dfbe"
RED = "#e27665"
FRUIT = [RED, GOLD, "#af93d4", "#84ca92"]
NAMES = ["Orchard", "Twenty One", "Color Wheel"]
WHEEL = [0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,10,5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26]


@lru_cache(None)
def font(size):
    return pg.font.SysFont("dejavusans", size, bold=True)


def hand_value(hand):
    ranks = [card[0] for card in hand]
    total = sum(min(10, rank) for rank in ranks)
    return total + 10 if 1 in ranks and total <= 11 else total


class Arcade:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((900, 640))
        pg.display.set_caption("Clover House Arcade")
        self.score = 0
        self.page = 0
        self.buttons = []
        self.new_grid()
        self.deal()
        self.angle = 0
        self.speed = 0
        self.target = "Red"
        self.wheel_note = "Start the wheel, then stop it on the target color."

    def new_grid(self):
        self.grid = [random.randrange(4) for _ in range(30)]
        self.eaten = 0
        self.bird = None
        self.fruit_note = "Pick 3 or more touching fruits of one kind."

    def eat(self, index):
        group = {index}
        todo = [index]
        while todo:
            pos = todo.pop()
            for near in (pos-6, pos+6, pos-1, pos+1):
                if not 0 <= near < 30 or abs(near % 6 - pos % 6) > 1:
                    continue
                if near not in group and self.grid[near] == self.grid[index]:
                    group.add(near)
                    todo.append(near)
        if len(group) < 3:
            self.fruit_note = "Too small! Look for a group of at least three."
            return
        self.bird = index
        self.eaten += len(group)
        bonus = self.eaten // 10 * 10
        self.eaten %= 10
        self.score += len(group) + bonus
        self.fruit_note = f"Bird ate {len(group)} fruits!" + ("  Harvest bonus +10!" if bonus else "")
        for pos in group:
            self.grid[pos] = random.randrange(4)

    def deal(self):
        self.deck = [(r,s) for r in range(1,14) for s in "♠♥♦♣"]
        random.shuffle(self.deck)
        self.player = [self.deck.pop(), self.deck.pop()]
        self.house = [self.deck.pop(), self.deck.pop()]
        self.done = False
        self.card_note = "Reach 21 or finish closer than the dealer."
        if 21 in (hand_value(self.player), hand_value(self.house)):
            self.finish()

    def hit(self):
        self.player.append(self.deck.pop())
        if hand_value(self.player) >= 21:
            self.finish()

    def finish(self):
        p = hand_value(self.player)
        while p <= 21 and hand_value(self.house) < 17:
            self.house.append(self.deck.pop())
        h = hand_value(self.house)
        self.done = True
        if p > 21:
            self.card_note = "Bust! Try a new hand."
        elif h > 21 or p > h:
            self.score += 5
            self.card_note = "You win!  +5 points"
        else:
            self.card_note = "Push! A tie." if h == p else "Dealer wins this hand."

    def spin(self):
        if not self.speed:
            self.target = random.choice(["Red", "Black"])
            self.speed = random.uniform(1.4, 2.2)
            self.wheel_note = f"Stop when {self.target.lower()} reaches the gold pointer."
        else:
            self.speed = 0
            i = int((-math.pi/2-self.angle) % math.tau / math.tau * 37)
            color = "Green" if i == 0 else "Red" if i % 2 else "Black"
            win = color == self.target
            self.score += 3 * win
            self.wheel_note = f"{WHEEL[i]} · {color}    " + ("On target! +3" if win else "Try again!")

    def label(self, value, x, y, size=20, color=PAPER, center=False):
        img = font(size).render(str(value), True, color)
        rect = img.get_rect(center=(x,y)) if center else img.get_rect(topleft=(x,y))
        self.screen.blit(img, rect)

    def box(self, rect, color, radius=12):
        pg.draw.rect(self.screen, color, rect, border_radius=radius)

    def button(self, title, x, y, w, action, color=MINT):
        rect = pg.Rect(x,y,w,44)
        self.buttons.append((rect,action))
        self.box(rect, PAPER if rect.collidepoint(pg.mouse.get_pos()) else color)
        self.label(title,*rect.center,18,INK,True)

    def orchard(self):
        self.label(f"Harvest bonus   {self.eaten} / 10",555,225,22,GOLD)
        self.label("Feed ten fruits for +10.",555,270,18)
        self.button("Shuffle fruit",555,425,190,self.new_grid)
        for i, kind in enumerate(self.grid):
            x,y = 80+i%6*73,190+i//6*66
            r = pg.Rect(x,y,66,59)
            self.box(r,"#335353")
            self.buttons.append((r,lambda i=i:self.eat(i)))
            cx,cy = r.center
            pg.draw.circle(self.screen,FRUIT[kind],(cx,cy+4),[17,15,13,18][kind])
            pg.draw.ellipse(self.screen,MINT,(cx,cy-19,14,8))
            pg.draw.circle(self.screen,PAPER,(cx-6,cy),3)
            if i == self.bird:
                pg.draw.circle(self.screen,GOLD,(x+13,y+13),10)
                pg.draw.polygon(self.screen,RED,[(x+21,y+10),(x+29,y+15),(x+20,y+16)])
                pg.draw.circle(self.screen,INK,(x+16,y+11),2)
        return self.fruit_note

    def cards(self):
        for name, hand, y in [("Dealer",self.house,175),("You",self.player,350)]:
            hide = name == "Dealer" and not self.done
            self.label(name if hide else f"{name}   {hand_value(hand)}",85,y,20,GOLD)
            for i,(rank,suit) in enumerate(hand):
                x = 85+i*min(90,690//len(hand))
                back = hide and i == 1
                self.box((x,y+37,77,98),MINT if back else PAPER)
                self.label("✦" if back else {1:"A",11:"J",12:"Q",13:"K"}.get(rank,rank),x+12,y+42,24,INK)
                if not back:
                    self.label(suit,x+39,y+96,30,RED if suit in "♥♦" else INK,True)
        if self.done:
            self.button("New hand",610,490,170,self.deal)
        else:
            self.button("Hit",610,490,80,self.hit)
            self.button("Stand",705,490,95,self.finish)
        return self.card_note

    def wheel(self):
        cx,cy,r = 320,365,167
        for i,n in enumerate(WHEEL):
            a = self.angle + i*math.tau/37
            b = a + math.tau/37
            def point(t,rad):
                return cx+rad*math.cos(t),cy+rad*math.sin(t)
            pg.draw.polygon(self.screen,MINT if i==0 else RED if i%2 else INK,[(cx,cy),point(a,r),point(b,r)])
            self.label(n,*point((a+b)/2,r-19),13,PAPER,True)
        pg.draw.circle(self.screen,GOLD,(cx,cy),51)
        self.label("Clover",cx,cy,19,INK,True)
        pg.draw.polygon(self.screen,GOLD,[(cx-12,184),(cx+12,184),(cx,211)])
        self.label("TARGET COLOR",550,265,16,MINT)
        self.label(self.target,550,298,43)
        self.button("Stop wheel" if self.speed else "Start wheel",550,419,190,self.spin)
        return self.wheel_note

    def draw(self):
        self.buttons.clear()
        self.screen.fill(INK)
        self.label("Clover House",44,25,37,GOLD)
        self.label(f"{self.score} pts",770,36,21,MINT)
        for i,title in enumerate(NAMES):
            self.button(title,44+i*188,95,177,lambda i=i:setattr(self,"page",i),GOLD if i==self.page else MINT)
        self.box((44,156,812,398),"#244544",20)
        note = [self.orchard,self.cards,self.wheel][self.page]()
        self.label(note,52,578,19)
        pg.display.flip()

    def run(self):
        clock = pg.time.Clock()
        while True:
            dt = clock.tick(60)/1000
            self.angle = (self.angle+self.speed*dt) % math.tau
            self.draw()
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    return
                if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                    for rect, action in self.buttons:
                        if rect.collidepoint(event.pos):
                            action()
                            break
                    self.draw()


if __name__ == "__main__":
    Arcade().run()
