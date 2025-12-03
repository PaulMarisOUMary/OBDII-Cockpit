import time
import math
import random
from collections import deque
from typing import List, Any


class SignalFilter:
    def __init__(self, window_size: int = 3):
        self.window = deque(maxlen=window_size)

    def filter(self, new_value: float) -> float:
        self.window.append(new_value)
        return sum(self.window) / len(self.window)


class Interpolator:
    def __init__(self, initial_value: float = 0.0, smoothing_speed: float = 5.0):
        self.current_value = initial_value
        self.target_value = initial_value
        self.smoothing_speed = smoothing_speed  # Plus haut = plus rapide

    def set_target(self, target: float):
        self.target_value = target

    def update(self, dt: float) -> float:
        # Formule Lerp indépendante du framerate:
        # value = lerp(current, target, 1 - exp(-speed * dt))
        t = 1.0 - math.exp(-self.smoothing_speed * dt)
        self.current_value += (self.target_value - self.current_value) * t
        return self.current_value


class DeadReckoningPredictor:
    def __init__(self, max_prediction_time: float = 0.5):
        self.last_value = 0.0
        self.last_timestamp = time.time()
        self.velocity = 0.0  # Unités par seconde
        self.max_prediction_time = max_prediction_time # Ne pas prédire trop loin

    def push_update(self, new_value: float):
        now = time.time()
        dt = now - self.last_timestamp
        
        if dt > 0:
            # Calcul de la vélocité instantanée
            current_velocity = (new_value - self.last_value) / dt
            # Lissage de la vélocité pour éviter les sauts brusques
            self.velocity = (self.velocity * 0.5) + (current_velocity * 0.5)
            
        self.last_value = new_value
        self.last_timestamp = now

    def get_predicted_value(self) -> float:
        now = time.time()
        time_delta = now - self.last_timestamp
        
        # Sécurité: Si la donnée est trop vieille, on arrête de prédire (évite l'emballement)
        if time_delta > self.max_prediction_time:
            return self.last_value
            
        # Projection linéaire: x = x0 + v*t
        predicted = self.last_value + (self.velocity * time_delta)
        return predicted


class PriorityPollingManager:
    def __init__(self):
        self.high_freq_cmds = []   # Ex: RPM, SPEED (Chaque cycle)
        self.medium_freq_cmds = [] # Ex: COOLANT, LOAD (1 cycle sur 10)
        self.low_freq_cmds = []    # Ex: FUEL, VOLTAGE (1 cycle sur 100)
        
        self.cycle_counter = 0

    def register(self, command, priority: str):
        if priority == 'HIGH':
            self.high_freq_cmds.append(command)
        elif priority == 'MEDIUM':
            self.medium_freq_cmds.append(command)
        elif priority == 'LOW':
            self.low_freq_cmds.append(command)
        else:
            raise ValueError("Priority must be 'HIGH', 'MEDIUM', or 'LOW'")

    def get_commands_for_cycle(self) -> List[Any]:
        commands_to_run = []
        
        # Toujours inclure High Frequency
        commands_to_run.extend(self.high_freq_cmds)
        
        # Medium Frequency: 1 fois tous les 10 cycles
        if self.cycle_counter % 10 == 0:
            # On peut aussi étaler les requêtes medium pour ne pas faire de pic
            # Mais pour l'exemple simple, on prend tout le bloc
            commands_to_run.extend(self.medium_freq_cmds)
            
        # Low Frequency: 1 fois tous les 100 cycles
        if self.cycle_counter % 100 == 0:
            commands_to_run.extend(self.low_freq_cmds)
            
        self.cycle_counter += 1
        return commands_to_run


class SpringPhysics:
    def __init__(self, frequency: float = 2.5, damping: float = 0.6, initial_value: float = 0.0):
        self.current_value = initial_value
        self.target_value = initial_value
        self.velocity = 0.0
        
        # Configuration physique
        # frequency: Vitesse de réaction (Hz). Plus haut = plus nerveux.
        # damping: Amortissement (0.0 - 1.0). 1.0 = pas de rebond. 0.5 = rebond visible.
        self.kp = (2.0 * math.pi * frequency) ** 2
        self.kd = 2.0 * damping * (2.0 * math.pi * frequency)

    def set_target(self, target: float):
        self.target_value = target

    def update(self, dt: float) -> float:
        # Simulation Euler semi-implicite pour la stabilité
        
        # Calcul de l'erreur
        error = self.target_value - self.current_value
        
        # Accélération (F = ma, ici m=1)
        acceleration = (error * self.kp) - (self.velocity * self.kd)
        
        # Intégration
        self.velocity += acceleration * dt
        self.current_value += self.velocity * dt
        
        return self.current_value


class IdleSimulator:
    def __init__(self, intensity: float = 15.0, noise_speed: float = 10.0):
        self.intensity = intensity
        self.noise_speed = noise_speed
        self.time_offset = random.random() * 100.0

    def apply(self, value: float, dt: float) -> float:
        if value < 100:
            return value

        self.time_offset += dt * self.noise_speed
        noise = math.sin(self.time_offset) * self.intensity * (0.8 + 0.4 * random.random())
        
        return value + noise
