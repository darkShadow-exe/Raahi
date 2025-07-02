import os
import sys
from city_generator import CityGenerator
from city_visualizer import CityVisualizer
from route_finder import RouteFinder
import random

def get_next_city_dir():
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Find next city number
    city_num = 1
    while os.path.exists(os.path.join(data_dir, f"city_{city_num}")):
        city_num += 1
    
    city_dir = os.path.join(data_dir, f"city_{city_num}")
    os.makedirs(city_dir)
    return city_dir

def check_dependencies():
    try:
        import matplotlib
        import pandas
        import numpy
        print("All dependencies available")
        return True
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install matplotlib pandas numpy")
        return False

def generate_city(grid_size=15, num_stops=50):
    print("Generating city...")
    city_dir = get_next_city_dir()
    generator = CityGenerator(grid_size=grid_size)
    generator.set_output_dir(city_dir)
    generator.generate_city()
    print(f"City generated in {city_dir}")
    return generator, city_dir

def visualize_city(city_dir=None):
    if city_dir is None:
        # Find latest city
        data_dir = "data"
        if not os.path.exists(data_dir):
            print("No data directory found. Generate city first.")
            return False
        
        cities = [d for d in os.listdir(data_dir) if d.startswith("city_")]
        if not cities:
            print("No cities found. Generate city first.")
            return False
        
        city_dir = os.path.join(data_dir, max(cities))
    
    required_files = ['stops.csv', 'routes.csv', 'walking.csv', 'zones.csv']
    if not all(os.path.exists(os.path.join(city_dir, f)) for f in required_files):
        print("Data files not found. Generate city first.")
        return False
    
    print("Creating visualization...")
    visualizer = CityVisualizer()
    visualizer.load_data(city_dir)
    visualizer.plot_city(os.path.join(city_dir, 'city_map.png'))
    visualizer.print_stats()
    print("Visualization created!")
    return True

def demo_routing(city_dir=None):
    if city_dir is None:
        # Find latest city
        data_dir = "data"
        if not os.path.exists(data_dir):
            print("No data directory found. Generate city first.")
            return False
        
        cities = [d for d in os.listdir(data_dir) if d.startswith("city_")]
        if not cities:
            print("No cities found. Generate city first.")
            return False
        
        city_dir = os.path.join(data_dir, max(cities))
    
    required_files = ['stops.csv', 'routes.csv', 'walking.csv']
    if not all(os.path.exists(os.path.join(city_dir, f)) for f in required_files):
        print("Data files not found. Generate city first.")
        return False
    
    print("Testing route finding...")
    finder = RouteFinder()
    finder.load_data(city_dir)
    
    # Demo with random stops
    stops = finder.stops_df['stop_id'].tolist()
    if len(stops) >= 2:
        origin = random.choice(stops)
        destination = random.choice([s for s in stops if s != origin])
        
        print(f"Finding routes from {origin} to {destination}...")
        routes = finder.find_multiple_routes(origin, destination)
        
        for optimize_type, journey in routes.items():
            print(f"\n{'='*40}")
            print(f"ROUTE OPTIMIZED FOR: {optimize_type.upper()}")
            finder.print_journey(journey)
    
    print("Route finding demo completed!")
    return True

def interactive_route_finder(city_dir=None):
    if city_dir is None:
        # Find latest city
        data_dir = "data"
        if not os.path.exists(data_dir):
            print("No data directory found. Generate city first.")
            return False
        
        cities = [d for d in os.listdir(data_dir) if d.startswith("city_")]
        if not cities:
            print("No cities found. Generate city first.")
            return False
        
        city_dir = os.path.join(data_dir, max(cities))
    
    required_files = ['stops.csv', 'routes.csv', 'walking.csv']
    if not all(os.path.exists(os.path.join(city_dir, f)) for f in required_files):
        print("Data files not found. Generate city first.")
        return False
    
    finder = RouteFinder()
    finder.load_data(city_dir)
    
    print("Interactive Route Finder")
    print("Available stops:")
    
    stops_by_zone = finder.stops_df.groupby('zone')
    for zone, group in stops_by_zone:
        print(f"\n{zone.upper()}:")
        for _, stop in group.head(5).iterrows():
            print(f"  {stop['stop_id']} - {stop['name']}")
    
    print("\nEnter stop IDs (or 'q' to quit):")
    
    while True:
        origin = input("Origin stop: ").strip()
        if origin.lower() == 'q':
            break
        
        destination = input("Destination stop: ").strip()
        if destination.lower() == 'q':
            break
        
        if origin not in finder.stops_df['stop_id'].values:
            print("Origin stop not found!")
            continue
        
        if destination not in finder.stops_df['stop_id'].values:
            print("Destination stop not found!")
            continue
        
        print(f"Finding routes from {origin} to {destination}...")
        routes = finder.find_multiple_routes(origin, destination)
        
        if not routes:
            print("No routes found!")
            continue
        
        for optimize_type, journey in routes.items():
            print(f"\n{'='*50}")
            print(f"ROUTE OPTIMIZED FOR: {optimize_type.upper()}")
            finder.print_journey(journey)
        
        print("\n" + "="*50)

def main():
    print("RAAHI - City Transit System Generator")
    print("="*50)
    
    if not check_dependencies():
        return
    
    while True:
        print("\nChoose an option:")
        print("1. Generate new city")
        print("2. Visualize existing city")
        print("3. Demo route finding")
        print("4. Interactive route finder")
        print("5. Generate & visualize (complete workflow)")
        print("6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == '1':
            grid_size = int(input("Grid size (default 15): ") or "15")
            num_stops = int(input("Number of stops (default 50): ") or "50")
            generator, city_dir = generate_city(grid_size, num_stops)
        
        elif choice == '2':
            visualize_city()
        
        elif choice == '3':
            demo_routing()
        
        elif choice == '4':
            interactive_route_finder()
        
        elif choice == '5':
            # Complete workflow
            grid_size = int(input("Grid size (default 15): ") or "15")
            num_stops = int(input("Number of stops (default 50): ") or "50")
            
            generator, city_dir = generate_city(grid_size, num_stops)
            visualize_city(city_dir)
            demo_routing(city_dir)
        
        elif choice == '6':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()
