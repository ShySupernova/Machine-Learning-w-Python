import pygame
import numpy as np

pygame.init()

#Background Colors (Halloween Theme)
PURPLE = (50,0,110)
DARK_PURPLE = (25,0,25)
BLACK = (0, 0, 0)

# Pumpkin-Pacman and candies
CANDY = (255,200,0)
CANDY_WRAP = (255,0,0)
ORANGE = (255,140,0)
DARK_ORANGE = (200,90,0)
STEM_GREEN = (120,90,0)
GLOW = (255,230, 80)

# Ghosts
SPOOKY_GHOST = (255,255,255)
SPOOKY_GREEN_GHOST = (0,255,0)

labyrinth = [
    "#############",
    "#.         .#",
    "#  ## . ##  #",
    "#  #.....#  #",
    "#  ...#...  #",
    "# ...###... #",
    "#  ...#...  #",
    "#  #.....#. #",
    "#  ## . ##  #",
    "#.         .#",
    "#############"
]

ORIGINAL = list(labyrinth) # Array which saves the layout of the bonbons as a list
DIRECTIONS = [(-1,0), (1,0), (0,-1), (0,1)] # Left, Right, Up, Down

CELL_SIZE = 40
ROWS = len(labyrinth)
COLS = len(labyrinth[0])

screen = pygame.display.set_mode((COLS * CELL_SIZE, ROWS * CELL_SIZE))
pygame.display.set_caption("Spooky Q-Learning 🎃")

def draw_labyrinth():
    for y, row in enumerate(labyrinth):
        for x, cell in enumerate(row):
            if cell == "#":
                rect = (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, PURPLE, rect)
                pygame.draw.rect(screen, BLACK, rect, 2)
            elif cell == ".":
                cx = x * CELL_SIZE + CELL_SIZE // 2
                cy = y * CELL_SIZE + CELL_SIZE // 2

                pygame.draw.polygon(screen, CANDY_WRAP, [(cx - 4, cy), (cx - 11, cy - 5), (cx - 11, cy + 5)])
                pygame.draw.polygon(screen, CANDY_WRAP, [(cx + 4, cy), (cx + 11, cy - 5), (cx + 11, cy + 5)])
                pygame.draw.circle(screen, CANDY, (cx, cy), 5)

class Pacman:
    def __init__(self, x, y): #Constructor. Position of pacman and count for flickering animation of face
        self.x = x
        self.y = y
        self.count = 0

    def move(self, dx, dy):
        new_x, new_y = self.x + dx, self.y + dy
        if labyrinth[new_y][new_x] != "#":
            self.x = new_x
            self.y = new_y

    def draw(self):
        cx = self.x * CELL_SIZE + CELL_SIZE // 2
        cy = self.y * CELL_SIZE + CELL_SIZE // 2 + 2
        r = CELL_SIZE // 2 - 5

        # Pumpkin body
        pygame.draw.ellipse(screen, DARK_ORANGE, (cx - r, cy - r + 3, 2 * r, 2 * r - 6))
        pygame.draw.ellipse(screen, ORANGE, (cx - r + 3, cy - r + 3, 2 * r - 6, 2 * r - 6))
        pygame.draw.ellipse(screen, DARK_ORANGE, (cx - 4, cy - r + 3, 8, 2 * r - 6), 1)

        # Stem
        pygame.draw.rect(screen, STEM_GREEN, (cx - 2, cy - r - 3, 5, 7))

        # Glowing animation of the face
        self.count += 1
        face = GLOW if self.count % 2 == 0 else BLACK

        # Triangle eyes
        pygame.draw.polygon(screen, face, [(cx - 8, cy - 1), (cx - 4, cy - 7), (cx - 1, cy - 1)])
        pygame.draw.polygon(screen, face, [(cx + 1, cy - 1), (cx + 4, cy - 7), (cx + 8, cy - 1)])

        # Mouth
        pygame.draw.polygon(screen, face, [
            (cx - 9, cy + 3), (cx + 9, cy + 3),
            (cx + 6, cy + 8), (cx + 3, cy + 6), (cx, cy + 9),
            (cx - 3, cy + 6), (cx - 6, cy + 8)
        ])

class Ghost:
    ghost_pixels = [
        " #### ",
        "######",
        "## # #",
        "######",
        "######",
        "# # # "
    ]

    GHOST_SPEED = 0.2

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.last = (0,0)

    def move_random(self):
        options = []
        for dx, dy in DIRECTIONS:
            if labyrinth[self.y + dy][self.x + dx] != "#":
                options.append((dx,dy))

        back = (-self.last[0],-self.last[1])
        if len(options) > 1 and back in options:
            options.remove(back)

        if options:
            dx, dy = options[np.random.randint(len(options))]
            self.x += dx
            self.y += dy
            self.last = (dx,dy)

    def move_towards_pacman(self, pacman):
        if self.x < pacman.x and labyrinth[self.y][self.x + 1] != "#":
            self.x += 1
        elif self.x > pacman.x and labyrinth[self.y][self.x - 1] != "#":
            self.x -= 1
        elif self.y < pacman.y and labyrinth[self.y + 1][self.x] != "#":
            self.y += 1
        elif self.y > pacman.y and labyrinth[self.y - 1][self.x] != "#":
            self.y -= 1

    def draw(self):
        pixel_size = CELL_SIZE // len(self.ghost_pixels)
        for row_idx, row in enumerate(self.ghost_pixels):
            for col_idx, pixel in enumerate(row):
                if pixel == "#":
                    pixel_x = self.x * CELL_SIZE + col_idx * pixel_size
                    pixel_y = self.y * CELL_SIZE + row_idx * pixel_size
                    pygame.draw.rect(screen, self.color, (pixel_x, pixel_y, pixel_size, pixel_size))

def nearest_candy(x,y):
    best = None
    for cy, row in enumerate(labyrinth):
        for cx, cell in enumerate(row):
            if cell == ".":
                d = abs(cx - x) + abs(cy - y)
                if best is None or d < best[0]:
                    best = (d, cx, cy)
    if best is None:
        return 0
    _, cx, cy = best
    if cx < x: return 0
    if cx > x: return 1
    if cy < y: return 2
    return 3

def ghost_info(pacman,ghost, ghost2):
    # Pick closest ghost
    d1 = abs(ghost.x - pacman.x) + abs(ghost.y - pacman.y)
    d2 = abs(ghost2.x - pacman.x) + abs(ghost2.y - pacman.y)
    g = ghost if d1 <= d2 else ghost2

    if   g.x < pacman.x: d = 0
    elif g.x > pacman.x: d = 1
    elif g.y < pacman.y: d = 2
    else:                d = 3
    # Case if ghost is closer than two fields
    near = 1 if abs(g.x - pacman.x) + abs(g.y - pacman.y) <= 2 else 0
    return d * 2 + near

def caught(pacman, ghost, ghost2):
    return (pacman.x == ghost.x and pacman.y == ghost.y) or \
        (pacman.x == ghost2.x and pacman.y == ghost2.y)

#Calculate position of Pacman and Ghosts on field
def get_state(pacman,ghost, ghost2):
    pos = pacman.y * COLS + pacman.x
    s = pos * 4 + nearest_candy(pacman.x, pacman.y)
    return s * 8 + ghost_info(pacman,ghost,ghost2)

# If there's a candy, Pacman eats it. Therefore the candy disappears and the now  empty space gets saved in the char-array.
def eat_candy(pacman):
    if labyrinth[pacman.y][pacman.x] == ".":
        labyrinth[pacman.y] = labyrinth[pacman.y][:pacman.x] + " " + labyrinth[pacman.y][pacman.x+1:]
        return True
    return False

# Q-Learning math
q = np.random.rand(ROWS * COLS * 4 * 8, 4) * 0.1 # Q-Table is filled with random numbers at the beginning.
alpha = 0.5 # Learning Rate - How much does the pumpkin use experience VS try random directions.
gamma = 0.9 #Discount Rate, closest way to reward (candy).
epsilon = 1.0 # Exploration Rate

def main():

    global epsilon
    clock = pygame.time.Clock()

    ghost_speed = Ghost.GHOST_SPEED

    EPISODES = 700

    for episode in range(EPISODES):
        labyrinth[:] = ORIGINAL
        pacman = Pacman(1,1)
        ghost = Ghost(COLS - 2, 1,SPOOKY_GHOST)
        ghost2 = Ghost(COLS - 2, ROWS - 2,SPOOKY_GREEN_GHOST)
        eat_candy(pacman)

        done = False # While loop
        steps = 0
        show = episode % 50 == 0 or episode >= EPISODES - 5

        while not done and steps < 1000:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            s = get_state(pacman,ghost,ghost2)

            if np.random.rand() < epsilon:
                a = np.random.randint(4)
            else:
                a = np.argmax(q[s])

            pacman.move(*DIRECTIONS[a])
            reward = -1

            if caught(pacman,ghost,ghost2):
                reward = -100
                done = True
            else:
                if eat_candy(pacman):
                    reward = 10
                if all("." not in row for row in labyrinth):
                    reward = 100
                    done = True

            if not done:
                if np.random.rand() < ghost_speed:
                    ghost.move_towards_pacman(pacman)
                if np.random.rand() < ghost_speed:
                    ghost2.move_random()
                if caught(pacman,ghost,ghost2):
                    reward = -100
                    done = True

            s_new = get_state(pacman,ghost,ghost2)
            if done:
                target = reward
            else:
                target = reward + gamma * np.max(q[s_new])
            q[s][a] += alpha * (target - q[s][a])

            steps += 1

            if show:
                screen.fill(DARK_PURPLE)
                draw_labyrinth()
                pacman.draw()
                ghost.draw()
                ghost2.draw()
                pygame.display.flip()
                clock.tick(10)

        #Exploration rate goes down as Pacman keeps learning during the episodes
        epsilon = max(0.0, epsilon * 0.995)

        eaten = sum(row.count(".") for row in ORIGINAL) - sum(row.count(".") for row in labyrinth)
        print("Episode:", episode, "Candies:",eaten,"Steps:", steps)

    pygame.quit()

if __name__=="__main__":
    main()
