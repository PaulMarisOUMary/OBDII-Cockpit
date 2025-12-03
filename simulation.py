from math import sin
import random


class Simulator:
    def __init__(self):
        self.rpm = 800.0
        self.speed = 0.0
        self.state = "IDLE"
        self.timer = 0.0
        
    def update(self, dt):
        self.timer += dt
        
        if self.state == "IDLE":
            self.rpm = 800 + (sin(self.timer * 5) * 20)
            if self.timer > 2.0:
                self.state = "GEAR_1"
                self.timer = 0
                
        # --- ACCELERATION PHASE (1 -> 2 -> 3 -> 4) ---
        
        elif self.state == "GEAR_1":
            # 0 -> 40 km/h
            self.rpm += 3000 * dt  # Rev up
            self.speed += 40 * dt
            # User shifts at 3k-4k when brutal
            if self.rpm > 3800:
                self.state = "SHIFT_1_2"
                
        elif self.state == "SHIFT_1_2":
            self.rpm -= 6000 * dt # Fast drop
            self.speed += 0.5 * dt  # Momentum
            if self.rpm < 2200:
                self.rpm = 2200
                self.state = "GEAR_2"
                
        elif self.state == "GEAR_2":
            # 40 -> 80 km/h
            self.rpm += 2000 * dt
            self.speed += 45 * dt
            if self.rpm > 3600:
                self.state = "SHIFT_2_3"
                
        elif self.state == "SHIFT_2_3":
            self.rpm -= 5000 * dt
            self.speed += 0.5 * dt
            if self.rpm < 2200:
                self.rpm = 2200
                self.state = "GEAR_3"
                
        elif self.state == "GEAR_3":
            # 80 -> 110 km/h
            self.rpm += 1500 * dt
            self.speed += 40 * dt
            if self.rpm > 3400:
                self.state = "SHIFT_3_4"
                
        elif self.state == "SHIFT_3_4":
            self.rpm -= 4000 * dt
            self.speed += 0.2 * dt
            if self.rpm < 2200:
                self.rpm = 2200
                self.state = "GEAR_4"
                
        elif self.state == "GEAR_4":
            # 110 -> 130 km/h
            self.rpm += 800 * dt
            self.speed += 15 * dt
            
            # Safety cap to prevent 10k RPM (Redline 5500)
            if self.rpm > 5500:
                self.rpm = 5500
                
            if self.speed > 130:
                self.state = "CRUISE"
                self.timer = 0
                
        elif self.state == "CRUISE":
            self.rpm = 4500 + (sin(self.timer * 3) * 30)
            self.speed = 130 + (sin(self.timer * 1) * 1)
            if self.timer > 2.0:
                self.state = "BRAKE_4"
                
        # --- DECELERATION PHASE (4 -> Brake -> 2 -> Neutral) ---
        
        elif self.state == "BRAKE_4":
            # Braking in 4th gear
            self.speed -= 40 * dt
            self.rpm -= 1500 * dt # RPM drops with speed
            if self.speed < 60:
                self.state = "DOWNSHIFT_4_2"
                
        elif self.state == "DOWNSHIFT_4_2":
            # Rev match / Blip for 2nd gear
            # At 60km/h, 2nd gear is high RPM (~4500)
            self.rpm += 8000 * dt # Huge blip
            if self.rpm > 3500:
                self.state = "BRAKE_2"
                
        elif self.state == "BRAKE_2":
            # Braking in 2nd gear (Engine braking)
            self.speed -= 50 * dt
            self.rpm -= 3000 * dt
            if self.speed < 10:
                self.state = "NEUTRAL"
                
        elif self.state == "NEUTRAL":
            self.speed -= 10 * dt
            self.rpm -= 2000 * dt
            if self.rpm < 800:
                self.rpm = 800
            if self.speed < 0:
                self.speed = 0
                self.state = "IDLE"
                self.timer = 0
                
        result = {"ENGINE_SPEED": self.rpm, "VEHICLE_SPEED": self.speed}

        # --- FAULT INJECTION ---
        # 1% chance to return 0 values (simulating bad read interpreted as 0)
        if random.random() < 0.5:
             result["ENGINE_SPEED"] = 0
             result["VEHICLE_SPEED"] = 0
        
        # 1% chance to return None (simulating missing data)
        elif random.random() < 0.5:
             result["ENGINE_SPEED"] = None
             result["VEHICLE_SPEED"] = None

        return result
