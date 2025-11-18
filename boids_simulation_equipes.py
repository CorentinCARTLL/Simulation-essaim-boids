import sys
import random
import pygame
from pygame.math import Vector2

# PARAMETRES GLOBAUX
WIDTH, HEIGHT = 1000, 720
NUM_BOIDS_TEAM1 = 30
NUM_BOIDS_TEAM2 = 30

MAX_SPEED = 3.0
MAX_FORCE = 0.05

NEIGHBOR_RADIUS = 120
SEPARATION_RADIUS = 40

W_ALIGNMENT = 1.0
W_COHESION = 0.7
W_SEPARATION = 1.5

BACKGROUND_COLOR = (10, 10, 30)
COLOR_TEAM1 = (255, 90, 90)
COLOR_TEAM2 = (90, 140, 255)


# FONCTION UTILITAIRE
def limit_vector(vec: Vector2, max_value: float) -> Vector2:
    if vec.length() > max_value:
        vec = vec.normalize() * max_value
    return vec


# CLASSE BOID
class Boid:
    def __init__(self, team, x=None, y=None):
        if x is None:
            x = random.uniform(0, WIDTH)
        if y is None:
            y = random.uniform(0, HEIGHT)

        self.position = Vector2(x, y)

        angle = random.uniform(0, 360)
        self.velocity = Vector2(1, 0).rotate(angle) * random.uniform(1, MAX_SPEED)
        self.acceleration = Vector2(0, 0)

        self.team = team

    def edges(self):
        if self.position.x < 0:
            self.position.x = WIDTH
        elif self.position.x > WIDTH:
            self.position.x = 0

        if self.position.y < 0:
            self.position.y = HEIGHT
        elif self.position.y > HEIGHT:
            self.position.y = 0

    def update(self):
        self.velocity += self.acceleration
        self.velocity = limit_vector(self.velocity, MAX_SPEED)

        self.position += self.velocity

        self.acceleration = Vector2(0, 0)

    def apply_force(self, force: Vector2):
        self.acceleration += force

    def apply_behaviors(self, boids):
        sep = self.separation(boids) * W_SEPARATION
        ali = self.alignment(boids) * W_ALIGNMENT
        coh = self.cohesion(boids) * W_COHESION

        self.apply_force(sep)
        self.apply_force(ali)
        self.apply_force(coh)

    def separation(self, boids):
        steer = Vector2(0, 0)
        total = 0

        for other in boids:
            if other is self:
                continue

            distance = self.position.distance_to(other.position)

            if 0 < distance < SEPARATION_RADIUS:
                diff = self.position - other.position
                if distance > 0:
                    diff /= distance
                steer += diff
                total += 1

        if total > 0:
            steer /= total

        if steer.length() > 0:
            steer = steer.normalize() * MAX_SPEED - self.velocity
            steer = limit_vector(steer, MAX_FORCE)

        return steer

    def alignment(self, boids):
        avg_velocity = Vector2(0, 0)
        total = 0

        for other in boids:
            if other is self:
                continue
            if other.team != self.team:
                continue

            distance = self.position.distance_to(other.position)

            if distance < NEIGHBOR_RADIUS:
                avg_velocity += other.velocity
                total += 1

        if total > 0:
            avg_velocity /= total

            if avg_velocity.length() > 0:
                avg_velocity = avg_velocity.normalize() * MAX_SPEED
                steer = avg_velocity - self.velocity
                steer = limit_vector(steer, MAX_FORCE)
                return steer

        return Vector2(0, 0)

    def cohesion(self, boids):
        center_of_mass = Vector2(0, 0)
        total = 0

        for other in boids:
            if other is self:
                continue
            if other.team != self.team:
                continue

            distance = self.position.distance_to(other.position)

            if distance < NEIGHBOR_RADIUS:
                center_of_mass += other.position
                total += 1

        if total > 0:
            center_of_mass /= total

            desired = center_of_mass - self.position

            if desired.length() > 0:
                desired = desired.normalize() * MAX_SPEED
                steer = desired - self.velocity
                steer = limit_vector(steer, MAX_FORCE)
                return steer

        return Vector2(0, 0)

    def draw(self, surface):
        angle = self.velocity.angle_to(Vector2(1, 0))
        size = 8

        points = [
            Vector2(size, 0),
            Vector2(-size, size / 2),
            Vector2(-size, -size / 2),
        ]

        rotated_points = [self.position + p.rotate(-angle) for p in points]

        if self.team == 1:
            color = COLOR_TEAM1
        else:
            color = COLOR_TEAM2

        pygame.draw.polygon(surface, color, rotated_points)


# FONCTION PRINCIPALE
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Boids multi equipes")
    clock = pygame.time.Clock()

    boids = []

    for _ in range(NUM_BOIDS_TEAM1):
        boids.append(Boid(team=1))

    for _ in range(NUM_BOIDS_TEAM2):
        boids.append(Boid(team=2))

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        for boid in boids:
            boid.apply_behaviors(boids)

        for boid in boids:
            boid.update()
            boid.edges()

        screen.fill(BACKGROUND_COLOR)
        for boid in boids:
            boid.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
