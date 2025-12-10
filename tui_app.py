# tui_app.py
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Static, ProgressBar, Input, Label, RichLog
# --- NEW IMPORT ---
from textual_plotext import PlotextPlot 
# ------------------
import grid_engine 
import ml_predictor 
import optimizer
import config

class ServerWidget(Static):
    def __init__(self, server_index: int, **kwargs):
        super().__init__(**kwargs)
        self.idx = server_index

    def compose(self) -> ComposeResult:
        yield Label(f"Server {self.idx}", id=f"label_{self.idx}", classes="title_lbl")
        yield Label("CPU Load:", classes="sub_lbl")
        yield ProgressBar(total=100, show_percentage=True, id=f"bar_{self.idx}")
        with Horizontal(classes="details_box"):
            yield Label("RAM: 10%", id=f"mem_{self.idx}", classes="stat_lbl")
            yield Label("TEMP: 35°C", id=f"temp_{self.idx}", classes="stat_lbl")
        yield Label("STATUS: SLEEP", id=f"status_{self.idx}", classes="status_lbl")

class GreenGridApp(App):
    CSS = """
    Screen { align: center middle; }
    
    #stats_panel { 
        height: 5; dock: top; border: solid green; margin: 0 1; padding: 0 1; layout: horizontal; 
    }
    .stat_group { width: 1fr; height: 100%; align: center middle; }
    .stat_title { color: $text-muted; text-align: center; }
    .stat_value { text-style: bold; color: white; text-align: center; }
    
    #servers_panel { layout: grid; grid-size: 5; height: auto; align: center top; margin-top: 1; }
    
    ServerWidget { 
        border: round grey; height: auto; min-height: 20; margin: 1; padding: 1;
        background: $surface; color: grey;
    }
    ServerWidget.running { border: double green; background: $surface-lighten-1; color: white; }
    
    .title_lbl { text-style: bold; margin-bottom: 1; }
    .sub_lbl { color: $text-muted; text-align: left; margin-top: 1; }
    .status_lbl { width: 100%; text-align: center; margin-top: 1; padding-top: 1; border-top: solid #555555; }
    .details_box { height: auto; align: center middle; margin-top: 1; margin-bottom: 1; }
    .stat_lbl { width: 50%; text-align: center; }
    .active_text { color: green; text-style: bold; }
    .sleep_text { color: grey; }
    .hot_text { color: red; text-style: bold; }
    ProgressBar > .bar--complete { color: green; }
    
    .agent_off { color: red; text-style: bold; }
    .agent_on { color: cyan; text-style: bold; }
    #log_box { height: 8; border: solid white; margin: 1; background: $surface; }

    /* GRAPH STYLES */
    #graph_panel { 
        height: 15; /* Taller to fit axes */
        margin: 1; 
        border: solid blue; 
    }
    PlotextPlot {
        height: 100%;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Container(id="stats_panel"):
            with Vertical(classes="stat_group"):
                yield Label("Real-Time Power", classes="stat_title")
                yield Label("0.0 W", id="power_val", classes="stat_value")
            with Vertical(classes="stat_group"):
                yield Label("AI Forecast", classes="stat_title")
                yield Label("Gathering Data...", id="pred_val", classes="stat_value")
            with Vertical(classes="stat_group"):
                yield Label("Optimizer Agent", classes="stat_title")
                yield Label("OFF [Press 'O']", id="agent_status", classes="agent_off")
        
        with Container(id="servers_panel"):
            for i in range(config.SERVER_COUNT):
                yield ServerWidget(server_index=i, id=f"server_widget_{i}")

        # --- NEW REAL GRAPH ---
        with Container(id="graph_panel"):
            yield PlotextPlot(id="power_plot")
        # ----------------------
        
        yield Label("📝 Optimization Logs:")
        yield RichLog(id="log_box", highlight=True, markup=True)
        
        yield Label("⌨️  System Terminal (Type 'stress 100 50' to test):")
        yield Input(placeholder="Enter command...", id="cmd_input")
        yield Footer()

    def on_mount(self):
        self.simulation = grid_engine.GridSimulation()
        self.sim_generator = self.simulation.workload_generator()
        self.brain = ml_predictor.EnergyPredictor() 
        self.agent = optimizer.GreenAgent()
        self.agent_active = False 
        
        # --- SETUP GRAPH ---
        plt = self.query_one("#power_plot").plt
        plt.title("Live Power Consumption (Watts)")
        plt.xlabel("Time (Ticks)")
        plt.ylabel("Power (W)")
        plt.theme("dark") # Matches your dark mode
        plt.frame(True)
        plt.grid(True, True) # Show X and Y grid lines
        # -------------------
        
        self.set_interval(config.SIM_SPEED, self.update_system)

    def update_system(self):
        next(self.sim_generator)
        
        if self.agent_active:
            actions = self.agent.optimize(self.simulation)
            if actions:
                log = self.query_one("#log_box")
                for action in actions:
                    log.write(f"[cyan]🤖 {action}[/]")
        
        data = self.simulation.get_metrics()
        current_time = data['time']
        actual_power = data['total_power']
        total_active_load = sum(s['load'] for s in data['servers'])
        
        predicted_power = self.brain.predict_next(current_time + 1, total_active_load)
        current_pred = self.brain.predict_next(current_time, total_active_load)
        is_anomaly = self.brain.check_anomaly(actual_power, current_pred)
        self.brain.add_data(current_time, total_active_load, actual_power)

        self.query_one("#power_val").update(f"{actual_power:.1f} W")
        if self.brain.is_ready:
            self.query_one("#pred_val").update(f"{predicted_power:.1f} W")
            if is_anomaly:
                self.query_one("#pred_val").styles.color = "red"
            else:
                self.query_one("#pred_val").styles.color = "green"

        # --- UPDATE PLOT ---
        plot_widget = self.query_one("#power_plot")
        plt = plot_widget.plt
        plt.clear_data() # Clear old lines
        
        # Plot the history from the Brain's memory
        y_data = list(self.brain.history_y)
        # Create X axis (0, 1, 2, 3...)
        x_data = list(range(len(y_data)))
        
        plt.plot(x_data, y_data, label="Watts", color="green")
        plot_widget.refresh() # Force redraw
        # -------------------

        for i, stats in enumerate(data['servers']):
            widget = self.query_one(f"#server_widget_{i}")
            bar = self.query_one(f"#bar_{i}")
            status_lbl = self.query_one(f"#status_{i}")
            mem_lbl = self.query_one(f"#mem_{i}")
            temp_lbl = self.query_one(f"#temp_{i}")
            
            bar.update(progress=stats['load'])
            mem_lbl.update(f"RAM: {stats['memory']:.0f}%")
            temp_lbl.update(f"TEMP: {stats['temp']:.1f}°C")
            
            if stats['load'] > 0:
                widget.add_class("running")
                status_lbl.update(f"ACTIVE ({stats['load']:.0f}%)")
                status_lbl.classes = "active_text"
                if stats['temp'] > 75: temp_lbl.classes = "hot_text"
                else: temp_lbl.classes = ""
            else:
                widget.remove_class("running")
                status_lbl.update("SLEEP")
                status_lbl.classes = "sleep_text"
                temp_lbl.classes = ""

    def on_input_submitted(self, message: Input.Submitted) -> None:
        value = message.value.lower()
        if "toggle" in value:
            self.action_toggle_agent()
        elif "add" in value:
            try:
                amount = int(value.split()[1])
                self.simulation.inject_load(amount)
                self.notify(f"⚡ INJECTING {amount}% LOAD SPIKE!")
            except: pass
        elif "remove" in value or "kill" in value:
            try:
                amount = int(value.split()[1])
                self.simulation.remove_load(amount)
                self.notify(f"🗑️  REMOVED {amount}% LOAD FROM GRID!", severity="warning")
            except: pass
        elif "stress" in value:
            try:
                parts = value.split()
                amount = int(parts[1])
                duration = int(parts[2])
                self.simulation.start_stress_test(amount, duration)
                self.notify(f"🔥 STRESS TEST: {amount}% per tick for {duration} ticks!")
            except:
                self.notify("Error: Use 'stress 100 20'", severity="error")
            
        self.query_one("#cmd_input").value = ""
        self.set_focus(None)
    
    def key_o(self):
        self.action_toggle_agent()

    def action_toggle_agent(self):
        self.agent_active = not self.agent_active
        lbl = self.query_one("#agent_status")
        if self.agent_active:
            lbl.update("ON [Active]")
            lbl.classes = "agent_on"
            self.notify("🤖 GREEN AGENT ACTIVATED")
        else:
            lbl.update("OFF [Press 'O']")
            lbl.classes = "agent_off"
            self.notify("🛑 AGENT DEACTIVATED")

if __name__ == "__main__":
    app = GreenGridApp()
    app.run()