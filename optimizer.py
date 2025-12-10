# optimizer.py
import config

class GreenAgent:
    def __init__(self):
        self.cooldown = 0
    
    def optimize(self, simulation):
        """
        Logic:
        1. Find the least loaded active server (The Victim).
        2. Find the most loaded server that has space (The Target).
        3. Move load from Victim -> Target.
        4. If Victim reaches 0, it sleeps (Saving Power!).
        """
        # Don't optimize every single tick (simulates calculation time)
        if self.cooldown > 0:
            self.cooldown -= 1
            return None
            
        servers = simulation.servers
        actions = []
        
        # Filter for active servers
        active_indices = [s.id for s in servers if s.load > 0]
        
        if len(active_indices) < 2:
            return None # Can't consolidate if only 1 is running
            
        # Sort by load: [Least Loaded ... Most Loaded]
        active_indices.sort(key=lambda idx: servers[idx].load)
        
        victim_id = active_indices[0] # Smallest load (try to empty this one)
        
        # Try to find a target for the victim's load
        victim_load = servers[victim_id].load
        
        for target_id in reversed(active_indices):
            if target_id == victim_id: continue
            
            target = servers[target_id]
            space = 100 - target.load
            
            if space >= victim_load:
                # WE FOUND A MATCH! Move everything.
                success = simulation.transfer_load(victim_id, target_id, victim_load)
                if success:
                    actions.append(f"MIGRATED {victim_load:.0f}% from S{victim_id} -> S{target_id}")
                    actions.append(f"Server {victim_id} is entering SLEEP MODE.")
                    self.cooldown = 3 # Wait 3 ticks before next move
                    return actions
                    
        return None