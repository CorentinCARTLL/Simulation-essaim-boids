import sys
import random
import pygame
from pygame.math import Vector2

# PARAMETRES GLOBAUX
WIDTH, HEIGHT = 1000, 720
NUM_BOIDS_TEAM1 = 30
NUM_BOIDS_TEAM2 = 30

NUM_PREDATORS = 3  # nombre de prédateurs

MAX_SPEED = 3.0
MAX_FORCE = 0.05

NEIGHBOR_RADIUS = 70
SEPARATION_RADIUS = 30

W_ALIGNMENT = 1.0
W_COHESION = 0.7
W_SEPARATION = 1.5
W_FLEE = 2.5

PREDATOR_SPEED = 4.5
PREDATOR_FORCE = 0.1
PREDATOR_RADIUS = 250
PREDATOR_COLOR = (255, 230, 50)

BACKGROUND_COLOR = (10, 10, 30)
COLOR_TEAM1 = (255, 90, 90)
COLOR_TEAM2 = (90, 140, 255)


def limit_vector(vec: Vector2, max_value: float) -> Vector2:
    if vec.length() > max_value:
        vec = vec.normalize() * max_value
    return vec


class Boid:
    def __init__(self, team):
        self.position = Vector2(random.uniform(0, WIDTH),
                                random.uniform(0, HEIGHT))
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

    def apply_force(self, force):
        self.acceleration += force

    def nearest_predator(self, predators):
        nearest = None
        min_dist = float("inf")

        for p in predators:
            d = self.position.distance_to(p.position)
            if d < min_dist:
                min_dist = d
                nearest = p

        return nearest

    def flee(self, predator):
        distance = self.position.distance_to(predator.position)

        if distance > 120:
            return Vector2(0, 0)

        diff = self.position - predator.position
        if distance > 0:
            diff /= distance

        desired = diff.normalize() * MAX_SPEED
        steer = desired - self.velocity
        steer = limit_vector(steer, MAX_FORCE)

        return steer

    def apply_behaviors(self, boids, predators):
        pred = self.nearest_predator(predators)
        flee_force = self.flee(pred) * W_FLEE

        if flee_force.length() > 0:
            self.apply_force(flee_force)
            return

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

            d = self.position.distance_to(other.position)

            if 0 < d < SEPARATION_RADIUS:
                diff = self.position - other.position
                if d > 0:
                    diff /= d
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

            d = self.position.distance_to(other.position)
            if d < NEIGHBOR_RADIUS:
                avg_velocity += other.velocity
                total += 1

        if total > 0:
            avg_velocity /= total
            if avg_velocity.length() > 0:
                desired = avg_velocity.normalize() * MAX_SPEED
                steer = desired - self.velocity
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

            d = self.position.distance_to(other.position)
            if d < NEIGHBOR_RADIUS:
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

        rotated = [self.position + p.rotate(-angle) for p in points]

        col = COLOR_TEAM1 if self.team == 1 else COLOR_TEAM2
        pygame.draw.polygon(surface, col, rotated)


class Predator:
    def __init__(self):
        self.position = Vector2(
            random.uniform(0, WIDTH),
            random.uniform(0, HEIGHT)
        )
        angle = random.uniform(0, 360)
        self.velocity = Vector2(1, 0).rotate(angle) * random.uniform(2, PREDATOR_SPEED)
        self.acceleration = Vector2(0, 0)

    def edges(self):
        if self.position.x < 0:
            self.position.x = WIDTH
        elif self.position.x > WIDTH:
            self.position.x = 0

        if self.position.y < 0:
            self.position.y = HEIGHT
        elif self.position.y > HEIGHT:
            self.position.y = 0

    def update(self, boids):
        target = None
        min_dist = float("inf")

        for b in boids:
            d = self.position.distance_to(b.position)
            if d < min_dist and d < PREDATOR_RADIUS:
                min_dist = d
                target = b

        if target is not None:
            desired = (target.position - self.position).normalize() * PREDATOR_SPEED
            steer = desired - self.velocity
            steer = limit_vector(steer, PREDATOR_FORCE)
            self.acceleration += steer

        self.velocity += self.acceleration
        self.velocity = limit_vector(self.velocity, PREDATOR_SPEED)
        self.position += self.velocity
        self.acceleration = Vector2(0, 0)

    def draw(self, surface):
        angle = self.velocity.angle_to(Vector2(1, 0))
        size = 20

        points = [
            Vector2(size, 0),
            Vector2(-size, size / 2),
            Vector2(-size, -size / 2),
        ]

        rotated = [self.position + p.rotate(-angle) for p in points]
        pygame.draw.polygon(surface, PREDATOR_COLOR, rotated)


def main():
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Boids multi-predateurs")
        clock = pygame.time.Clock()

        boids = []
        for _ in range(NUM_BOIDS_TEAM1):
            boids.append(Boid(1))
        for _ in range(NUM_BOIDS_TEAM2):
            boids.append(Boid(2))

        predators = [Predator() for _ in range(NUM_PREDATORS)]

        running = True
        while running:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            for p in predators:
                p.update(boids)
                p.edges()

            for b in boids:
                b.apply_behaviors(boids, predators)
                b.update()
                b.edges()

            screen.fill(BACKGROUND_COLOR)

            for b in boids:
                b.draw(screen)
            for p in predators:
                p.draw(screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
