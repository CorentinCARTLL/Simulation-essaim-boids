import sys
import random
import pygame
from pygame.math import Vector2

# PARAMÈTRES GLOBAUX
WIDTH, HEIGHT = 1000, 720
NUM_BOIDS = 60

MAX_SPEED = 3.0      # vitesse maximale d'un boid
MAX_FORCE = 0.05     # force (accélération) maximale

NEIGHBOR_RADIUS = 70     # rayon de perception pour alignement / cohésion
SEPARATION_RADIUS = 30   # distance minimale avant "repoussoir"

W_ALIGNMENT = 1.0
W_COHESION = 0.7
W_SEPARATION = 1.5

BACKGROUND_COLOR = (10, 10, 30)
BOID_COLOR = (230, 230, 255)

# FONCTIONS UTILITAIRES
def limit_vector(vec: Vector2, max_value: float) -> Vector2:
    """Limite la norme d'un vecteur à max_value."""
    if vec.length() > max_value:
        vec = vec.normalize() * max_value
    return vec



# CLASSE BOID
class Boid:
    def __init__(self, x=None, y=None):
        if x is None:
            x = random.uniform(0, WIDTH)
        if y is None:
            y = random.uniform(0, HEIGHT)

        self.position = Vector2(x, y)
        # Vitesse initiale : direction aléatoire, norme entre 1 et MAX_SPEED
        angle = random.uniform(0, 360)
        self.velocity = Vector2(1, 0).rotate(angle) * random.uniform(1, MAX_SPEED)
        self.acceleration = Vector2(0, 0)

    def edges(self):
        #Gestion des bords : on fait un 'wrap-around' (tore).
        if self.position.x < 0:
            self.position.x = WIDTH
        elif self.position.x > WIDTH:
            self.position.x = 0

        if self.position.y < 0:
            self.position.y = HEIGHT
        elif self.position.y > HEIGHT:
            self.position.y = 0

    def update(self):
        # Met à jour la vitesse et la position du boid.
        # Appliquer l'accélération à la vitesse
        self.velocity += self.acceleration
        self.velocity = limit_vector(self.velocity, MAX_SPEED)

        # Mettre à jour la position
        self.position += self.velocity

        # Réinitialiser l'accélération pour la frame suivante
        self.acceleration = Vector2(0, 0)

    def apply_force(self, force: Vector2):
        #Ajoute une force à l'accélération.
        self.acceleration += force

    # COMPORTEMENTS DES BOIDS
    def apply_behaviors(self, boids):
        #Calcule et applique les forces de séparation, alignement et cohésion.
        sep = self.separation(boids) * W_SEPARATION
        ali = self.alignment(boids) * W_ALIGNMENT
        coh = self.cohesion(boids) * W_COHESION

        self.apply_force(sep)
        self.apply_force(ali)
        self.apply_force(coh)

    def separation(self, boids):
        #Évite les collisions avec les voisins trop proches.
        steer = Vector2(0, 0)
        total = 0

        for other in boids:
            if other is self:
                continue
            distance = self.position.distance_to(other.position)
            if 0 < distance < SEPARATION_RADIUS:
                # Vecteur qui pointe loin du voisin
                diff = self.position - other.position
                if distance > 0:
                    diff /= distance  # plus fort si plus proche
                steer += diff
                total += 1

        if total > 0:
            steer /= total

        if steer.length() > 0:
            steer = steer.normalize() * MAX_SPEED - self.velocity
            steer = limit_vector(steer, MAX_FORCE)

        return steer

    def alignment(self, boids):
        #S'aligne sur la vitesse moyenne des voisins.
        avg_velocity = Vector2(0, 0)
        total = 0

        for other in boids:
            if other is self:
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
        #Se dirige vers le centre de masse de ses voisins.
        center_of_mass = Vector2(0, 0)
        total = 0

        for other in boids:
            if other is self:
                continue
            distance = self.position.distance_to(other.position)
            if distance < NEIGHBOR_RADIUS:
                center_of_mass += other.position
                total += 1

        if total > 0:
            center_of_mass /= total
            # 'seek' vers le centre de masse
            desired = center_of_mass - self.position
            if desired.length() > 0:
                desired = desired.normalize() * MAX_SPEED
                steer = desired - self.velocity
                steer = limit_vector(steer, MAX_FORCE)
                return steer

        return Vector2(0, 0)

    # AFFICHAGE
    def draw(self, surface):
        #Dessine le boid comme un petit triangle orienté.
        # Angle de la vitesse par rapport à l'axe x
        angle = self.velocity.angle_to(Vector2(1, 0))
        size = 8

        # Triangle en coordonnées locales
        # Pointe vers la direction +x, qu'on va ensuite faire tourner
        points = [
            Vector2(size, 0),           # pointe
            Vector2(-size, size / 2),   # arrière bas
            Vector2(-size, -size / 2),  # arrière haut
        ]

        # Rotation + translation vers la position du boid
        rotated_points = [
            self.position + p.rotate(-angle) for p in points
        ]

        pygame.draw.polygon(surface, BOID_COLOR, rotated_points)


# FONCTION PRINCIPALE
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Swarm / Boids Simulation")
    clock = pygame.time.Clock()

    # Création des boids
    boids = [Boid() for _ in range(NUM_BOIDS)]

    running = True
    while running:
        clock.tick(60)  # 60 FPS

        # Gestion des événements 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Logique de la simulation
        for boid in boids:
            boid.apply_behaviors(boids)

        for boid in boids:
            boid.update()
            boid.edges()

        # Rendu graphique
        screen.fill(BACKGROUND_COLOR)
        for boid in boids:
            boid.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
