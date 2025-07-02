import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np
import os
from matplotlib.colors import ListedColormap

class CityVisualizer:
    def __init__(self, grid_size=15):
        self.grid_size = grid_size
        self.zone_colors = {
            'residential': '#90EE90',    # Light green
            'commercial': '#FFB6C1',     # Light pink
            'industrial': '#D3D3D3',     # Light gray
            'transit_hub': '#FFD700'     # Gold
        }
        
        self.mode_colors = {
            'bus': '#FF4500',      # Orange red
            'metro': '#4169E1',    # Royal blue
            'train': '#32CD32'     # Lime green
        }

    def load_data(self, data_dir="."):
        self.stops_df = pd.read_csv(os.path.join(data_dir, 'stops.csv'))
        self.routes_df = pd.read_csv(os.path.join(data_dir, 'routes.csv'))
        self.walking_df = pd.read_csv(os.path.join(data_dir, 'walking.csv'))
        self.zones_df = pd.read_csv(os.path.join(data_dir, 'zones.csv'))

    def plot_city(self, save_path='city_map.png'):
        fig, ax = plt.subplots(figsize=(12, 12))
        
        # Plot zone backgrounds
        self._plot_zones(ax)
        
        # Plot walking connections
        self._plot_walking_connections(ax)
        
        # Plot routes
        self._plot_routes(ax)
        
        # Plot stops
        self._plot_stops(ax)
        
        # Formatting
        ax.set_xlim(-0.5, self.grid_size - 0.5)
        ax.set_ylim(-0.5, self.grid_size - 0.5)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_title('Generated City Transit System', fontsize=16, fontweight='bold')
        
        # Add legends
        self._add_legends(ax)
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()

    def _plot_zones(self, ax):
        # Create zone background
        zone_grid = np.full((self.grid_size, self.grid_size), 0, dtype=int)
        zone_types = ['residential', 'commercial', 'industrial', 'transit_hub']
        
        for _, row in self.zones_df.iterrows():
            x, y = int(row['x']), int(row['y'])
            zone_type = row['zone_type']
            zone_grid[y, x] = zone_types.index(zone_type) + 1
        
        # Plot zone colors
        for x in range(self.grid_size):
            for y in range(self.grid_size):
                if (x, y) in [(row['x'], row['y']) for _, row in self.zones_df.iterrows()]:
                    zone_row = self.zones_df[(self.zones_df['x'] == x) & (self.zones_df['y'] == y)]
                    if not zone_row.empty:
                        zone_type = zone_row.iloc[0]['zone_type']
                        color = self.zone_colors.get(zone_type, '#FFFFFF')
                        rect = patches.Rectangle((x-0.4, y-0.4), 0.8, 0.8, 
                                               facecolor=color, alpha=0.3, edgecolor='none')
                        ax.add_patch(rect)

    def _plot_stops(self, ax):
        for _, stop in self.stops_df.iterrows():
            x, y = stop['x'], stop['y']
            mode = stop['mode']
            color = self.mode_colors.get(mode, '#000000')
            
            # Different shapes for different modes
            if mode == 'bus':
                marker = 'o'
                size = 80
            elif mode == 'metro':
                marker = 's'
                size = 100
            else:  # train
                marker = '^'
                size = 120
            
            ax.scatter(x, y, c=color, marker=marker, s=size, 
                      edgecolors='black', linewidth=1, zorder=5)
            
            # Add stop labels
            ax.annotate(stop['stop_id'], (x, y), xytext=(5, 5), 
                       textcoords='offset points', fontsize=6, alpha=0.7)

    def _plot_routes(self, ax):
        for _, route in self.routes_df.iterrows():
            stops = route['stops'].split('|')
            mode = route['mode']
            
            # Get coordinates for route stops
            route_coords = []
            for stop_id in stops:
                stop_row = self.stops_df[self.stops_df['stop_id'] == stop_id]
                if not stop_row.empty:
                    route_coords.append((stop_row.iloc[0]['x'], stop_row.iloc[0]['y']))
            
            if len(route_coords) > 1:
                # Plot route line
                xs, ys = zip(*route_coords)
                color = self.mode_colors.get(mode, '#000000')
                
                line_style = '-'
                if mode == 'metro':
                    line_style = '--'
                elif mode == 'train':
                    line_style = '-.'
                
                ax.plot(xs, ys, color=color, linewidth=2, alpha=0.6, 
                       linestyle=line_style, zorder=2)

    def _plot_walking_connections(self, ax):
        for _, conn in self.walking_df.iterrows():
            from_stop = self.stops_df[self.stops_df['stop_id'] == conn['from_stop']]
            to_stop = self.stops_df[self.stops_df['stop_id'] == conn['to_stop']]
            
            if not from_stop.empty and not to_stop.empty:
                x1, y1 = from_stop.iloc[0]['x'], from_stop.iloc[0]['y']
                x2, y2 = to_stop.iloc[0]['x'], to_stop.iloc[0]['y']
                
                ax.plot([x1, x2], [y1, y2], color='gray', linewidth=1, 
                       alpha=0.3, linestyle=':', zorder=1)

    def _add_legends(self, ax):
        # Zone legend
        zone_handles = []
        for zone_type, color in self.zone_colors.items():
            handle = patches.Patch(color=color, alpha=0.3, label=zone_type.title())
            zone_handles.append(handle)
        
        zone_legend = ax.legend(handles=zone_handles, loc='upper left', 
                               bbox_to_anchor=(1.02, 1), title='Zones')
        
        # Transport mode legend
        mode_handles = []
        markers = {'bus': 'o', 'metro': 's', 'train': '^'}
        for mode, color in self.mode_colors.items():
            handle = ax.scatter([], [], c=color, marker=markers[mode], 
                              s=100, edgecolors='black', label=mode.title())
            mode_handles.append(handle)
        
        mode_legend = ax.legend(handles=mode_handles, loc='upper left', 
                               bbox_to_anchor=(1.02, 0.7), title='Transport Modes')
        
        # Add zone legend back
        ax.add_artist(zone_legend)

    def print_stats(self):
        print("\n=== City Statistics ===")
        print(f"Grid Size: {self.grid_size}x{self.grid_size}")
        print(f"Total Stops: {len(self.stops_df)}")
        print(f"Total Routes: {len(self.routes_df)}")
        print(f"Walking Connections: {len(self.walking_df)}")
        
        print("\nStops by Mode:")
        print(self.stops_df['mode'].value_counts())
        
        print("\nStops by Zone:")
        print(self.stops_df['zone'].value_counts())
        
        print("\nRoutes by Mode:")
        print(self.routes_df['mode'].value_counts())
        
        # Average route length
        route_lengths = []
        for _, route in self.routes_df.iterrows():
            stops = route['stops'].split('|')
            route_lengths.append(len(stops))
        
        print(f"\nAverage Route Length: {np.mean(route_lengths):.1f} stops")
        print(f"Average Walking Connection Distance: {self.walking_df['distance_meters'].mean():.0f}m")

if __name__ == "__main__":
    visualizer = CityVisualizer()
    visualizer.load_data()
    visualizer.plot_city()
    visualizer.print_stats()
