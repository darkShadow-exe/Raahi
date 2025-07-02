import pandas as pd
import heapq
import os
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import math

@dataclass
class PathSegment:
    from_stop: str
    to_stop: str
    mode: str
    route_id: str
    departure_time: str
    arrival_time: str
    cost: float
    duration: int

@dataclass
class Journey:
    segments: List[PathSegment]
    total_cost: float
    total_time: int
    transfers: int
    walking_distance: int

class RouteFinder:
    def __init__(self):
        self.stops_df = None
        self.routes_df = None
        self.walking_df = None
        self.graph = {}
        
    def load_data(self, data_dir="."):
        self.stops_df = pd.read_csv(os.path.join(data_dir, 'stops.csv'))
        self.routes_df = pd.read_csv(os.path.join(data_dir, 'routes.csv'))
        self.walking_df = pd.read_csv(os.path.join(data_dir, 'walking.csv'))
        self._build_graph()
    
    def _build_graph(self):
        # Initialize graph
        for _, stop in self.stops_df.iterrows():
            self.graph[stop['stop_id']] = []
        
        # Add route connections
        for _, route in self.routes_df.iterrows():
            stops = route['stops'].split('|')
            mode = route['mode']
            route_id = route['route_id']
            fare = route['fare']
            
            # Connect consecutive stops
            for i in range(len(stops) - 1):
                from_stop = stops[i]
                to_stop = stops[i + 1]
                
                # Estimate travel time based on mode
                travel_time = self._estimate_travel_time(mode, from_stop, to_stop)
                
                connection = {
                    'to': to_stop,
                    'mode': mode,
                    'route_id': route_id,
                    'cost': fare / len(stops),  # Proportional fare
                    'time': travel_time,
                    'type': 'route'
                }
                
                self.graph[from_stop].append(connection)
        
        # Add walking connections
        for _, walk in self.walking_df.iterrows():
            from_stop = walk['from_stop']
            to_stop = walk['to_stop']
            time = walk['walking_time']
            distance = walk['distance_meters']
            
            # Bidirectional walking
            for start, end in [(from_stop, to_stop), (to_stop, from_stop)]:
                connection = {
                    'to': end,
                    'mode': 'walk',
                    'route_id': 'WALK',
                    'cost': 0,
                    'time': time,
                    'distance': distance,
                    'type': 'walk'
                }
                
                if start in self.graph:
                    self.graph[start].append(connection)
    
    def _estimate_travel_time(self, mode, from_stop, to_stop):
        # Get coordinates
        from_coords = self.stops_df[self.stops_df['stop_id'] == from_stop]
        to_coords = self.stops_df[self.stops_df['stop_id'] == to_stop]
        
        if from_coords.empty or to_coords.empty:
            return 10  # Default
        
        x1, y1 = from_coords.iloc[0]['x'], from_coords.iloc[0]['y']
        x2, y2 = to_coords.iloc[0]['x'], to_coords.iloc[0]['y']
        
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2) * 100  # meters
        
        # Speed by mode (m/min)
        speeds = {
            'bus': 300,      # 18 km/h
            'metro': 600,    # 36 km/h
            'train': 800     # 48 km/h
        }
        
        speed = speeds.get(mode, 300)
        return max(2, int(distance / speed))  # minimum 2 minutes
    
    def find_routes(self, origin: str, destination: str, optimize='time') -> List[Journey]:
        # Dijkstra's algorithm with optimization preference
        distances = {stop: float('inf') for stop in self.graph}
        distances[origin] = 0
        
        # Store path information
        previous = {stop: None for stop in self.graph}
        connections = {stop: None for stop in self.graph}
        
        pq = [(0, origin)]
        visited = set()
        
        while pq:
            current_cost, current_stop = heapq.heappop(pq)
            
            if current_stop in visited:
                continue
                
            visited.add(current_stop)
            
            if current_stop == destination:
                break
            
            for connection in self.graph[current_stop]:
                neighbor = connection['to']
                
                if neighbor in visited:
                    continue
                
                # Calculate cost based on optimization preference
                if optimize == 'time':
                    edge_cost = connection['time']
                elif optimize == 'cost':
                    edge_cost = connection['cost']
                elif optimize == 'transfers':
                    # Penalize mode changes
                    current_conn = connections.get(current_stop)
                    if current_conn and current_conn['mode'] != connection['mode']:
                        edge_cost = connection['time'] + 30  # Transfer penalty
                    else:
                        edge_cost = connection['time']
                else:  # balanced
                    edge_cost = connection['time'] + connection['cost'] * 2
                
                new_cost = current_cost + edge_cost
                
                if new_cost < distances[neighbor]:
                    distances[neighbor] = new_cost
                    previous[neighbor] = current_stop
                    connections[neighbor] = connection
                    heapq.heappush(pq, (new_cost, neighbor))
        
        # Reconstruct path
        if distances[destination] == float('inf'):
            return []  # No path found
        
        journey = self._reconstruct_journey(origin, destination, previous, connections)
        return [journey] if journey else []
    
    def _reconstruct_journey(self, origin, destination, previous, connections) -> Optional[Journey]:
        path = []
        current = destination
        
        while current != origin:
            prev = previous[current]
            if prev is None:
                return None
            
            connection = connections[current]
            if connection:
                segment = PathSegment(
                    from_stop=prev,
                    to_stop=current,
                    mode=connection['mode'],
                    route_id=connection['route_id'],
                    departure_time="--:--",  # Simplified
                    arrival_time="--:--",
                    cost=connection['cost'],
                    duration=connection['time']
                )
                path.append(segment)
            
            current = prev
        
        path.reverse()
        
        # Calculate journey metrics
        total_cost = sum(s.cost for s in path)
        total_time = sum(s.duration for s in path)
        transfers = len(set(s.route_id for s in path if s.mode != 'walk')) - 1
        walking_distance = sum(s.duration * 60 for s in path if s.mode == 'walk')  # Rough estimate
        
        return Journey(path, total_cost, total_time, transfers, walking_distance)
    
    def find_multiple_routes(self, origin: str, destination: str) -> Dict[str, Journey]:
        routes = {}
        
        for optimize in ['time', 'cost', 'transfers']:
            journeys = self.find_routes(origin, destination, optimize)
            if journeys:
                routes[optimize] = journeys[0]
        
        return routes
    
    def print_journey(self, journey: Journey):
        print(f"\n=== Journey Details ===")
        print(f"Total Cost: ₹{journey.total_cost:.2f}")
        print(f"Total Time: {journey.total_time} minutes")
        print(f"Transfers: {journey.transfers}")
        print(f"Walking Distance: ~{journey.walking_distance}m")
        
        print(f"\n=== Route Steps ===")
        for i, segment in enumerate(journey.segments, 1):
            if segment.mode == 'walk':
                print(f"{i}. Walk from {segment.from_stop} to {segment.to_stop} "
                      f"({segment.duration} min)")
            else:
                print(f"{i}. Take {segment.mode.upper()} {segment.route_id} "
                      f"from {segment.from_stop} to {segment.to_stop} "
                      f"({segment.duration} min, ₹{segment.cost:.2f})")

def demo_route_finder():
    finder = RouteFinder()
    finder.load_data()
    
    # Get some random stops for demo
    stops = finder.stops_df['stop_id'].tolist()
    if len(stops) >= 2:
        origin = stops[0]
        destination = stops[-1]
        
        print(f"Finding routes from {origin} to {destination}...")
        
        routes = finder.find_multiple_routes(origin, destination)
        
        for optimize_type, journey in routes.items():
            print(f"\n{'='*50}")
            print(f"OPTIMIZED FOR: {optimize_type.upper()}")
            finder.print_journey(journey)

if __name__ == "__main__":
    demo_route_finder()
