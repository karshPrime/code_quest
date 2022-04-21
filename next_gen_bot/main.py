from random import Random, random
from codequest22.server.ant import AntTypes
import codequest22.stats as stats
from codequest22.server.events import DepositEvent, DieEvent, ProductionEvent, SpawnEvent, QueenAttackEvent, ZoneActiveEvent, ZoneDeactivateEvent, MoveEvent
from codequest22.server.requests import GoalRequest, SpawnRequest
from collections import defaultdict

FIGHTER_RADIUS_MULT = 10

fighters = defaultdict(list)
fighter_id = 10000

def get_team_name():
    return f"nEXT_GEN"

my_index = None
def read_index(player_index, n_players):
    global my_index
    my_index = player_index

my_energy = stats.general.STARTING_ENERGY
map_data = {}
spawns = [None]*4
food = []
food_workers = {}
food_workers_limit = {}
distance = {}
closest_site = None
total_ants = 0
dead_workers = {}
STRATEGY = {
    "Early_game": [80,20,0],
    "Attacked": [20, 80,0],
    "Far_hill": [40, 40,20],
    "Close_hill": [20,40,40],
    "Rush": [20,80,0],
    "Econ_And_Harass": [60,40,0]
}
curr_strat = "Early_game"

hill_active = False
first_hill_active = False
curr_hill = (0,0)
enemy_cords = [None]*3

def read_map(md, energy_info):
    global map_data, spawns, food, distance, closest_site, food_workers, food_workers_limit, enemy_cords
    map_data = md
    for y in range(len(map_data)):
        for x in range(len(map_data[0])):
            if map_data[y][x] == "F":
                food.append((x, y))
                food_workers[(x,y)] = 0
            if map_data[y][x] in "RBYG":
                spawns["RBYG".index(map_data[y][x])] = (x, y)
    # Read map is called after read_index
    startpoint = spawns[my_index]
    # Dijkstra's Algorithm: Find the shortest path from your spawn to each food zone.
    # Step 1: Generate edges - for this we will just use orthogonally connected cells.
    adj = {}
    h, w = len(map_data), len(map_data[0])
    # A list of all points in the grid
    points = []
    # Mapping every point to a number
    idx = {}
    counter = 0
    for y in range(h):
        for x in range(w):
            adj[(x, y)] = []
            if map_data[y][x] == "W": continue
            points.append((x, y))
            idx[(x, y)] = counter
            counter += 1
    for x, y in points:
        for a, b in [(y+1, x), (y-1, x), (y, x+1), (y, x-1)]:
            if 0 <= a < h and 0 <= b < w and map_data[a][b] != "W":
                adj[(x, y)].append((b, a, 1))
    # Step 2: Run Dijkstra's
    import heapq
    # What nodes have we already looked at?
    expanded = [False] * len(points)
    # What nodes are we currently looking at?
    queue = []
    # What is the distance to the startpoint from every other point?
    heapq.heappush(queue, (0, startpoint))
    while queue:
        d, (a, b) = heapq.heappop(queue)
        if expanded[idx[(a, b)]]: continue
        # If we haven't already looked at this point, put it in expanded and update the distance.
        expanded[idx[(a, b)]] = True
        distance[(a, b)] = d
        # Look at all neighbours
        for j, k, d2 in adj[(a, b)]:
            if not expanded[idx[(j, k)]]:
                heapq.heappush(queue, (
                    d + d2,
                    (j, k)
                ))
    # Now I can calculate the closest food site.
    food = list(sorted(food, key=lambda prod: distance[prod]))
    closest_site = food[0]
    for food_place in food:
        food_workers_limit[food_place] = stats.energy.PER_TICK + (distance[food_place]/stats.ants.Worker.SPEED / stats.energy.DELAY)
    enemy_cords = [x for x in spawns if x != spawns[my_index]]

def handle_failed_requests(requests):
    global my_energy
    for req in requests:
        if req.player_index == my_index:
            print(f"Request {req.__class__.__name__} failed. Reason: {req.reason}.")

def handle_events(events):
    global food_workers, my_energy, total_ants, dead_workers, hill_active, first_hill_active, curr_strat, curr_hill, fighters, fighter_id
    requests = []
    new_fighters = []


    print ("\n"+str(my_energy)+"\n")
    queen_ant_attacked = False

    for ev in events:
        if isinstance(ev, DepositEvent):
            if ev.player_index == my_index:
                # One of my worker ants just made it back to the Queen! Let's send them back to the food site.
                requests.append(send_worker_ant(ev.ant_id))
                # Additionally, let's update how much energy I've got.
                my_energy = ev.total_energy
        elif isinstance(ev, ProductionEvent):
            if ev.player_index == my_index:
                # One of my worker ants just made it to the food site! Let's send them back to the Queen.
                food_location = (round((ev.ant_str['info']['position'][1])), round((ev.ant_str['info']['position'][0])))

                food_workers[food_location] -= 1

                requests.append(GoalRequest(ev.ant_id, spawns[my_index]))
        elif isinstance(ev, DieEvent):
            if ev.player_index == my_index:
                # One of my workers just died :(
                total_ants -= 1
                try:
                    food_workers[dead_workers[ev.ant_id]] -= 1
                except:
                    pass
            if ev.ant_id in fighters:
                # Set fighters to new target
                fs = fighters.pop(ev.ant_id)
                if len(fighters) == 0:
                    # No targets left, just go home
                    for f in fs:
                        requests.append(GoalRequest(f, spawns[my_index]))
                else:
                    fighters[list(fighters.keys())[0]] += fs    
                
        elif isinstance(ev, QueenAttackEvent):
            if ev.queen_player_index == my_index:
                queen_ant_attacked = True
        elif isinstance(ev, ZoneActiveEvent):
            first_hill_active = True
            curr_hill = ev.points
            hill_active = True
        elif isinstance(ev, ZoneDeactivateEvent):
            hill_active = False
            
        elif isinstance(ev, MoveEvent):
            if ev.player_index != my_index:
                if ev.ant_id in fighters:
                    # Adjust fighter positions
                    for f in fighters[ev.ant_id]:
                        requests.append(GoalRequest(f, ev.position))
                    continue

                if ev.ant_str['classname'] != 'FighterAnt':
                    continue

                x, y = spawns[my_index]
                e_x, e_y = ev.position
                d = (x - e_x)**2 + (y - e_y)**2

                if d < (stats.ants.Fighter.RANGE * FIGHTER_RADIUS_MULT)**2:
                    # Track this fighter ant 
                    new_fighters.append((ev.ant_id, fighter_id, ev.position))
                    fighter_id += 1

    strategic_location = (0,0)

    if queen_ant_attacked:
        strategic_location = spawns[my_index]
        curr_strat = "Attacked"
    elif hill_active:
        strategic_location = curr_hill[0]
        curr_strat = "Close_hill"
    elif (
        my_energy >= stats.general.MAX_ENERGY_STORED - 50 or
        (curr_strat == "Rush" and my_energy >= 100)
    ):
        strategic_location = enemy_cords[0]
        print ("Rush")
        curr_strat = "Rush"
    elif not first_hill_active:
        strategic_location = enemy_cords[0]        
        curr_strat = "Early_game"
    else:
        strategic_location = enemy_cords[0]
        curr_strat = "Econ_And_Harass"

    worker_to_spawn_this_tick = int(STRATEGY[curr_strat][0] * stats.general.MAX_SPAWNS_PER_TICK/100)
    fighter_to_spawn_this_tick = int(STRATEGY[curr_strat][1] * stats.general.MAX_SPAWNS_PER_TICK/100)
    settler_to_spawn_this_tick = int(STRATEGY[curr_strat][2] * stats.general.MAX_SPAWNS_PER_TICK/100)
    # Can I spawn ants?
    i = 0
    while (
        i < len(new_fighters) and
        total_ants < stats.general.MAX_ANTS_PER_PLAYER and 
        my_energy >= stats.ants.Fighter.COST and
        fighter_to_spawn_this_tick > 0
    ):
        ant_id, fighter_id, ant_pos = new_fighters[i]
        fighters[ant_id].append(fighter_id)
        requests.append(SpawnRequest(AntTypes.FIGHTER, id=fighter_id, color=None, goal=ant_pos))

        my_energy -= stats.ants.Fighter.COST        
        i += 1
        fighter_to_spawn_this_tick -= 1
        total_ants += 1
    while (
        total_ants < stats.general.MAX_ANTS_PER_PLAYER and 
        my_energy >= stats.ants.Worker.COST and
        worker_to_spawn_this_tick > 0
    ):
        worker_to_spawn_this_tick -= 1
        total_ants += 1
        # Spawn an ant, give it some id, no color, and send it to the closest site.
        # I will pay the base cost for this ant, so cost=None.
        requests.append(send_worker_ant())

    while (
        total_ants < stats.general.MAX_ANTS_PER_PLAYER and 
        my_energy >= stats.ants.Settler.COST and
        settler_to_spawn_this_tick > 0
    ):
        settler_to_spawn_this_tick -= 1
        total_ants += 1
        # Spawn an ant, give it some id, no color, and send it to the closest site.
        # I will pay the base cost for this ant, so cost=None.
        requests.append(SpawnRequest(AntTypes.SETTLER, color=(14, 255, 255), goal=strategic_location))
        print("Settling: " + str(strategic_location))

        my_energy -= stats.ants.Settler.COST


    return requests

def get_patrol_location():
    i = 0
    while (i < len(food) and food_workers[food[i]] > food_workers_limit[food[i]]):
        i += 1
    if (i == len(food)):
        i = 0
    return food[i]

def send_worker_ant(ant_id=None):
    global food_workers, my_energy
    i = 0
    while (i < len(food) and food_workers[food[i]] > food_workers_limit[food[i]]):
        i += 1
    if (i == len(food)):
        i = 0

    food_workers[food[i]] += 1
    if ant_id == None:
        my_energy -= stats.ants.Worker.COST
        return SpawnRequest(AntTypes.WORKER, id=None, color=None, goal=food[i])
    else:
        dead_workers[ant_id] = food[i]
        return GoalRequest(ant_id, position=food[i])