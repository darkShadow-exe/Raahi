import random
import csv
import math
import os
from dataclasses import dataclass
from typing import List, Dict, Tuple
from enum import Enum

class ZoneType(Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    TRANSIT_HUB = "transit_hub"

class TransportMode(Enum):
    BUS = "bus"
    METRO = "metro"
    TRAIN = "train"
    WALK = "walk"

@dataclass
class Stop:
    id: str
    mode: TransportMode
    x: int
    y: int
    zone: ZoneType
    name: str

@dataclass
class Route:
    id: str
    mode: TransportMode
    stops: List[str]
    schedule: Dict[str, List[str]]  # stop_id -> [departure_times]
    fare: float

@dataclass
class WalkingConnection:
    from_stop: str
    to_stop: str
    time_minutes: int
    distance_meters: int

class CityGenerator:
    def __init__(self, grid_size=15):
        self.grid_size = grid_size
        self.grid = [[None for _ in range(grid_size)] for _ in range(grid_size)]
        self.stops = []
        self.routes = []
        self.walking_connections = []
        self.zones = {}
        self.output_dir = "."
        
        # Indian city place names
        self.residential_names = [
            "Greenview Colony", "Lal Chowk", "Gandhi Nagar", "Saket", "Vasant Kunj",
            "Rajouri Garden", "Pitampura", "Rohini", "Dwarka", "Janakpuri",
            "Preet Vihar", "Mayur Vihar", "Kalkaji", "Malviya Nagar", "Hauz Khas"
        ]
        
        self.commercial_names = [
            "Connaught Place", "Khan Market", "Karol Bagh", "Nehru Place", "Gaffar Market",
            "Palika Bazaar", "Sarojini Nagar", "Lajpat Nagar", "Central Market", "City Center"
        ]
        
        self.industrial_names = [
            "Tech Park", "Industrial Area", "Okhla", "Udyog Vihar", "Sector 18",
            "IT Hub", "Export Zone", "Manufacturing Belt", "Cyber City", "Phase 1"
        ]
        
    def set_output_dir(self, output_dir):
        self.output_dir = output_dir

    def define_zones(self):
        # Residential zones (corners and edges)
        res_areas = [
            (0, 0, 4, 4), (11, 0, 14, 4), (0, 11, 4, 14), (11, 11, 14, 14)
        ]
        
        # Commercial zones (center areas)
        com_areas = [(5, 5, 9, 9)]
        
        # Industrial zones
        ind_areas = [(0, 5, 4, 9), (11, 5, 14, 9)]
        
        # Transit hubs (scattered)
        hub_points = [(7, 7), (3, 7), (11, 7), (7, 3), (7, 11)]
        
        # Mark zones
        for x1, y1, x2, y2 in res_areas:
            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
                        self.zones[(x, y)] = ZoneType.RESIDENTIAL
        
        for x1, y1, x2, y2 in com_areas:
            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
                        self.zones[(x, y)] = ZoneType.COMMERCIAL
        
        for x1, y1, x2, y2 in ind_areas:
            for x in range(x1, x2 + 1):
                for y in range(y1, y2 + 1):
                    if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
                        self.zones[(x, y)] = ZoneType.INDUSTRIAL
        
        for x, y in hub_points:
            if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
                self.zones[(x, y)] = ZoneType.TRANSIT_HUB

    def place_stops(self, total_stops=50):
        placed = 0
        attempts = 0
        
        while placed < total_stops and attempts < 1000:
            x = random.randint(0, self.grid_size - 1)
            y = random.randint(0, self.grid_size - 1)
            
            # Skip if already occupied
            if self.grid[x][y] is not None:
                attempts += 1
                continue
            
            zone = self.zones.get((x, y), ZoneType.RESIDENTIAL)
            mode = self._choose_mode_for_zone(zone)
            name = self._get_name_for_zone(zone, placed)
            
            stop_id = f"S{placed + 1:03d}"
            stop = Stop(stop_id, mode, x, y, zone, name)
            
            self.stops.append(stop)
            self.grid[x][y] = stop
            placed += 1
            attempts += 1

    def _choose_mode_for_zone(self, zone):
        weights = {
            ZoneType.RESIDENTIAL: {TransportMode.BUS: 0.7, TransportMode.METRO: 0.3},
            ZoneType.COMMERCIAL: {TransportMode.BUS: 0.4, TransportMode.METRO: 0.6},
            ZoneType.INDUSTRIAL: {TransportMode.BUS: 0.6, TransportMode.TRAIN: 0.4},
            ZoneType.TRANSIT_HUB: {TransportMode.METRO: 0.5, TransportMode.TRAIN: 0.5}
        }
        
        zone_weights = weights.get(zone, {TransportMode.BUS: 1.0})
        return random.choices(list(zone_weights.keys()), 
                            weights=list(zone_weights.values()))[0]

    def _get_name_for_zone(self, zone, index):
        if zone == ZoneType.RESIDENTIAL:
            return random.choice(self.residential_names)
        elif zone == ZoneType.COMMERCIAL:
            return random.choice(self.commercial_names)
        elif zone == ZoneType.INDUSTRIAL:
            return random.choice(self.industrial_names)
        else:
            return f"Hub {index + 1}"

    def create_routes(self):
        bus_stops = [s for s in self.stops if s.mode == TransportMode.BUS]
        metro_stops = [s for s in self.stops if s.mode == TransportMode.METRO]
        train_stops = [s for s in self.stops if s.mode == TransportMode.TRAIN]
        
        # Create 10 bus routes
        self._create_mode_routes(bus_stops, TransportMode.BUS, 10, 4, 8)
        
        # Create 5 metro lines
        self._create_mode_routes(metro_stops, TransportMode.METRO, 5, 6, 12)
        
        # Create 2 train routes
        self._create_mode_routes(train_stops, TransportMode.TRAIN, 2, 8, 15)

    def _create_mode_routes(self, stops, mode, num_routes, min_stops, max_stops):
        for i in range(num_routes):
            if len(stops) < min_stops:
                break
                
            route_stops = random.sample(stops, 
                                      min(random.randint(min_stops, max_stops), len(stops)))
            
            # Sort by distance for logical routing
            route_stops = self._sort_stops_by_proximity(route_stops)
            
            route_id = f"{mode.value.upper()}{i + 1:02d}"
            schedule = self._generate_schedule(route_stops, mode)
            fare = self._calculate_fare(mode, len(route_stops))
            
            route = Route(route_id, mode, [s.id for s in route_stops], schedule, fare)
            self.routes.append(route)

    def _sort_stops_by_proximity(self, stops):
        if len(stops) <= 1:
            return stops
        
        sorted_stops = [stops[0]]
        remaining = stops[1:]
        
        while remaining:
            last_stop = sorted_stops[-1]
            nearest = min(remaining, 
                         key=lambda s: math.sqrt((s.x - last_stop.x)**2 + (s.y - last_stop.y)**2))
            sorted_stops.append(nearest)
            remaining.remove(nearest)
        
        return sorted_stops

    def _generate_schedule(self, stops, mode):
        # Base frequency in minutes
        frequency = {
            TransportMode.BUS: 10,
            TransportMode.METRO: 15,
            TransportMode.TRAIN: 30
        }[mode]
        
        # Generate departures from 6 AM to 11 PM
        schedule = {}
        
        for stop in stops:
            times = []
            current_time = 6 * 60  # 6 AM in minutes
            
            while current_time < 23 * 60:  # Until 11 PM
                hour = current_time // 60
                minute = current_time % 60
                times.append(f"{hour:02d}:{minute:02d}")
                current_time += frequency
            
            schedule[stop.id] = times
        
        return schedule

    def _calculate_fare(self, mode, num_stops):
        base_fares = {
            TransportMode.BUS: 10,
            TransportMode.METRO: 20,
            TransportMode.TRAIN: 40
        }
        
        return base_fares[mode] + (num_stops - 1) * 2

    def create_walking_connections(self, max_distance=500):
        for i, stop1 in enumerate(self.stops):
            for stop2 in self.stops[i + 1:]:
                if stop1.mode == stop2.mode:
                    continue
                
                distance = math.sqrt((stop1.x - stop2.x)**2 + (stop1.y - stop2.y)**2) * 100
                
                if distance <= max_distance:
                    walking_time = max(3, int(distance / 60))  # 60m/min walking speed
                    
                    connection = WalkingConnection(
                        stop1.id, stop2.id, walking_time, int(distance)
                    )
                    self.walking_connections.append(connection)

    def export_data(self):
        # Export stops
        with open(os.path.join(self.output_dir, 'stops.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['stop_id', 'mode', 'x', 'y', 'zone', 'name'])
            for stop in self.stops:
                writer.writerow([stop.id, stop.mode.value, stop.x, stop.y, 
                               stop.zone.value, stop.name])
        
        # Export routes
        with open(os.path.join(self.output_dir, 'routes.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['route_id', 'mode', 'stops', 'fare'])
            for route in self.routes:
                writer.writerow([route.id, route.mode.value, 
                               '|'.join(route.stops), route.fare])
        
        # Export walking connections
        with open(os.path.join(self.output_dir, 'walking.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['from_stop', 'to_stop', 'walking_time', 'distance_meters'])
            for conn in self.walking_connections:
                writer.writerow([conn.from_stop, conn.to_stop, 
                               conn.time_minutes, conn.distance_meters])
        
        # Export zones
        with open(os.path.join(self.output_dir, 'zones.csv'), 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['x', 'y', 'zone_type'])
            for (x, y), zone in self.zones.items():
                writer.writerow([x, y, zone.value])

    def generate_city(self):
        print("Defining zones...")
        self.define_zones()
        
        print("Placing transit stops...")
        self.place_stops()
        
        print("Creating routes...")
        self.create_routes()
        
        print("Creating walking connections...")
        self.create_walking_connections()
        
        print("Exporting data...")
        self.export_data()
        
        print(f"City generated with:")
        print(f"- {len(self.stops)} stops")
        print(f"- {len(self.routes)} routes")
        print(f"- {len(self.walking_connections)} walking connections")
        print(f"- {len(self.zones)} zone cells")

if __name__ == "__main__":
    random.seed(42)  # For reproducible results
    generator = CityGenerator(grid_size=15)
    generator.generate_city()
