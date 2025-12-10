# grid_engine.py
import simpy
import random
import math
import config

class Server:
    def __init__(self, env, id):
        self.env = env
        self.id = id
        self.load = 0 
        self.status = "SLEEP"
        self.memory = 10 
        self.temp = 35   

    def get_power_consumption(self):
        if self.status == "SLEEP": return 0 
        utilization = self.load / 100.0
        return config.IDLE_POWER + (config.MAX_POWER - config.IDLE_POWER) * utilization

    def update_stats(self):
        if self.load > 0:
            self.status = "ACTIVE"
            target_mem = 15 + (self.load * 0.8) + random.randint(-5, 5)
            self.memory = max(10, min(100, target_mem))
            target_temp = 35 + (self.load * 0.5) 
            self.temp = (self.temp * 0.7) + (target_temp * 0.3)
        else:
            self.status = "SLEEP"
            self.memory = 10 
            self.temp = (self.temp * 0.9) + (35 * 0.1) 

    def update_load(self, added_load):
        space_left = 100 - self.load
        accepted_load = min(added_load, space_left)
        self.load += accepted_load
        return added_load - accepted_load

    def process_tasks(self):
        if self.load > 0:
            base_speed = 10
            turbo_boost = int(self.load * 0.30) 
            completed = base_speed + turbo_boost
            self.load = max(0, self.load - completed)
            self.update_stats() 
        else:
            self.update_stats() 

class GridSimulation:
    def __init__(self):
        self.env = simpy.Environment()
        self.servers = [Server(self.env, i) for i in range(config.SERVER_COUNT)]
        self.current_carbon = config.CARBON_LOW
        self.last_incoming_load = 0
        
        # --- NEW STRESS TEST VARIABLES ---
        self.stress_load_amount = 0
        self.stress_ticks_remaining = 0

    def inject_load(self, amount):
        remaining = amount
        for s in self.servers:
            if remaining <= 0: break
            remaining = s.update_load(remaining)

    def remove_load(self, amount):
        remaining_to_remove = amount
        for s in reversed(self.servers):
            if remaining_to_remove <= 0: break
            if s.load > 0:
                can_remove = min(s.load, remaining_to_remove)
                s.load -= can_remove
                remaining_to_remove -= can_remove
                s.update_stats()

    # --- SIMPLIFIED TRIGGER ---
    def start_stress_test(self, amount, duration):
        """Just sets the variables. The main loop handles the rest."""
        self.stress_load_amount = amount
        self.stress_ticks_remaining = duration
    # --------------------------

    def transfer_load(self, from_id, to_id, amount):
        source = self.servers[from_id]
        dest = self.servers[to_id]
        real_amount = min(amount, source.load)
        space_in_dest = 100 - dest.load
        final_amount = min(real_amount, space_in_dest)
        
        if final_amount > 0:
            source.load -= final_amount
            dest.load += final_amount
            return True
        return False

    def workload_generator(self):
        while True:
            # 1. Drain Tasks
            for s in self.servers: s.process_tasks()

            # 2. Calculate Standard Traffic (Sine Wave)
            time_of_day = (self.env.now % 1440) / 60.0 
            base, amp = 40, 100
            cycle = math.sin((time_of_day - 14) * math.pi / 12)
            noise = random.randint(-10, 20)
            incoming = max(0, int(base + (amp * cycle) + noise))
            
            # --- 3. ADD STRESS TEST LOAD (IF ACTIVE) ---
            if self.stress_ticks_remaining > 0:
                incoming += self.stress_load_amount
                self.stress_ticks_remaining -= 1
            # -------------------------------------------
            
            self.last_incoming_load = incoming
            self.inject_load(incoming)
            
            yield self.env.timeout(1)

    def get_metrics(self):
        total_watts = sum(s.get_power_consumption() for s in self.servers)
        server_stats = []
        for s in self.servers:
            server_stats.append({
                "load": s.load,
                "memory": s.memory,
                "temp": s.temp,
                "status": s.status
            })

        return {
            "time": self.env.now,
            "total_power": total_watts,
            "servers": server_stats,
            "incoming_load": self.last_incoming_load
        }