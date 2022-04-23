from codequest22.server.ant import AntTypes
import codequest22.stats as stats
from codequest22.server.events import DepositEvent, DieEvent, ProductionEvent, SpawnEvent, QueenAttackEvent, ZoneActiveEvent, ZoneDeactivateEvent, MoveEvent, FoodTileDeactivateEvent, FoodTileActiveEvent, TeamDefeatedEvent, SettlerScoreEvent
from codequest22.server.requests import GoalRequest, SpawnRequest
from collections import defaultdict
from random import randint

DEFAULT_MAP = [['W', 'W', '.', '.', '.', '.', '.', 'W', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', 'W', '.', '.', '.', '.', '.', 'W', 'W'], ['W', '.', '.', '.', '.', 'F', '.', 'W', '.', '.', '.', '.', '.', '.', 'W', '.', '.', 'W', '.', '.', '.', '.', '.', '.', 'W', '.', 'F', '.', '.', '.', '.', 'W'], ['.', '.', '.', '.', '.', '.', '.', 'W', '.', '.', '.', '.', '.', 'W', '.', '.', '.', '.', 'W', '.', '.', '.', '.', '.', 'W', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', 'W', 'W', '.', '.', '.', '.', '.', 'W', '.', '.', 'F', 'F', '.', '.', 'W', '.', '.', '.', '.', '.', 'W', 'W', '.', '.', '.', '.', '.'], ['.', '.', 'R', '.', 'W', '.', '.', '.', '.', '.', '.', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', '.', '.', '.', '.', '.', '.', 'W', '.', 'Y', '.', '.'], ['.', '.', '.', '.', 'W', '.', '.', '.', '.', '.', '.', '.', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', '.', '.', '.', '.', '.', '.', '.', 'W', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', 'W', 'W', 'W', 'W', 'W', 'W', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', '.', '.', '.', '.', '.', '.', 'W', 'W', 'W', 'W', '.', '.', '.', '.', '.', '.', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'], ['Z', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', 'F', '.', '.', 'Z', 'Z', '.', '.', 'F', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', 'Z'], ['Z', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', 'F', '.', '.', 'Z', 'Z', '.', '.', 'F', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', 'Z'], ['W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', '.', '.', '.', '.', '.', '.', 'W', 'W', 'W', 'W', '.', '.', '.', '.', '.', '.', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W'], ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', 'W', 'W', 'W', 'W', 'W', 'W', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', 'W', '.', '.', '.', '.', '.', '.', '.', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', '.', '.', '.', '.', '.', '.', '.', 'W', '.', '.', '.', '.'], ['.', '.', 'G', '.', 'W', '.', '.', '.', '.', '.', '.', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', 'W', '.', '.', '.', '.', '.', '.', 'W', '.', 'B', '.', '.'], ['.', '.', '.', '.', '.', 'W', 'W', '.', '.', '.', '.', '.', 'W', '.', '.', 'F', 'F', '.', '.', 'W', '.', '.', '.', '.', '.', 'W', 'W', '.', '.', '.', '.', '.'], ['.', '.', '.', '.', '.', '.', '.', 'W', '.', '.', '.', '.', '.', 'W', '.', '.', '.', '.', 'W', '.', '.', '.', '.', '.', 'W', '.', '.', '.', '.', '.', '.', '.'], ['W', '.', '.', '.', '.', 'F', '.', 'W', '.', '.', '.', '.', '.', '.', 'W', '.', '.', 'W', '.', '.', '.', '.', '.', '.', 'W', '.', 'F', '.', '.', '.', '.', 'W'], ['W', 'W', '.', '.', '.', '.', '.', 'W', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', '.', 'W', '.', '.', '.', '.', '.', 'W', 'W']]

FIGHTER_RADIUS_MULT = 10
DEFAULT_MAP_DEFENDERS_COUNT = 5

fighters = defaultdict(set)
fighter_id = 10000

def get_team_name():
    return f"nEXT_GEN"

my_index = None
def read_index(player_index, n_players):
    global my_index
    my_index = player_index

on_default_map = False
default_map_corner = (0, 0)
default_map_defenders = {}
my_energy = stats.general.STARTING_ENERGY
map_data = {}
spawns = [None]*4
food = []
food_workers = {}
food_workers_limit = {}
distance = {}
closest_site = None
total_ants = 0
STRATEGY = {
    "Early_game": [80,20,0],
    "Attacked": [20, 80,0],
    "Far_hill": [40, 40,20],
    "Close_hill": [20,40,40],
    "Rush": [20,80,0],
    "Econ_And_Harass": [60,40,0],
    "Snipe": [40,60,0]
}
curr_strat = "Early_game"

hill_active = False
first_hill_active = False
curr_hill = (0,0)
time_hill_active = 0
enemy_cords = [None]*3
hill_points = {}
defeated = set()

charged = {}
ei = {}

snipe_target = []

snipe_squad = []

unreachable_enemies = []

CLOSE_HILL_THRESHOLD = 80
SNIPE_THRESHOLD = 25

def read_map(md, energy_info):
    global map_data, spawns, food, distance, closest_site, food_workers, food_workers_limit, enemy_cords, ei, on_default_map, default_map_corner, unreachable_enemies

    ei = energy_info
    map_data = md
    for y in range(len(map_data)):
        for x in range(len(map_data[0])):
            if map_data[y][x] == "F":
                food.append((x, y))
                food_workers[(x,y)] = []
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

    for i in range(4):
        if distance[spawns[i]] > stats.ants.Fighter.LIFESPAN * stats.ants.Fighter.SPEED:
            unreachable_enemies.append(i)

    print (unreachable_enemies)
    if md == DEFAULT_MAP:
        on_default_map = True 
        s_x, s_y = spawns[my_index]
        
        d_x = 2 if s_x == 2 else -2
        d_y = 2 if s_y == 4 else -2

        default_map_corner = (s_x + d_x, s_y + d_y)


def handle_failed_requests(requests):
    global my_energy
    for req in requests:
        if req.player_index == my_index:
            print(f"Medic: Request {req.__class__.__name__} failed. Reason: {req.reason}.")

def handle_events(events):
    global food_workers, my_energy, total_ants, hill_active, first_hill_active, curr_strat, curr_hill, fighters, fighter_id, ei, time_hill_active, snipe_target, snipe_squad, hill_points, defeated, default_map_defenders
    requests = []
    new_fighters = []
    to_send_home = set()
    dead_fighters = set()
    to_move = set()

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
                for location in food_workers:
                    if (ev.ant_id) in food_workers[location]:
                        food_workers[location].remove(ev.ant_id)


                requests.append(GoalRequest(ev.ant_id, spawns[my_index]))
        elif isinstance(ev, DieEvent):
            if ev.player_index == my_index:
                # One of my workers just died :(
                total_ants -= 1
                
                for location in food_workers:
                    if (ev.ant_id) in food_workers[location]:
                        food_workers[location].remove(ev.ant_id)

                if ev.ant_id in default_map_defenders:
                    default_map_defenders.pop(ev.ant_id)

                if ev.ant_id in to_send_home:
                    to_send_home.remove(ev.ant_id)

                if ev.ant_id in snipe_squad:
                    snipe_squad.remove(ev.ant_id)

                for k, v in fighters.items():
                    if ev.ant_id in v:
                        fighters[k].remove(ev.ant_id)
                        dead_fighters.add(ev.ant_id)

            if (ev.ant_id, ev.player_index) in fighters:
                # Set fighters to new target
                fs = fighters.pop((ev.ant_id, ev.player_index))
                if len(fighters) == 0:
                    # No targets left, just go home
                    for f in fs:
                        # We're not sure if our buddy is dead so lets wait till we have have seen all events before moving him
                        to_remove_move = []
                        for (ff, pos) in to_move:
                            if ff == f:
                                to_remove_move.append((ff, pos))
                        for ff in to_remove_move:
                            to_move.remove(ff)
                        to_send_home.add(f)
                else:
                    fighters[list(fighters.keys())[0]] = fighters[list(fighters.keys())[0]].union(fs)
                
        elif isinstance(ev, QueenAttackEvent):
            if ev.queen_player_index == my_index:
                queen_ant_attacked = True
            elif ev.queen_hp < stats.general.QUEEN_HEALTH * SNIPE_THRESHOLD / 100 and ev.queen_hp > 0 and not ev.queen_player_index in defeated and not ev.queen_player_index in unreachable_enemies:
                if not ev.queen_player_index in snipe_target:
                    snipe_target.append(ev.queen_player_index)

            if ev.queen_hp <= 0:
                if ev.queen_player_index in snipe_target:
                    snipe_target.remove(ev.queen_player_index)
                defeated.add(ev.queen_player_index)
        elif isinstance(ev, ZoneActiveEvent):
            first_hill_active = True
            curr_hill = ev.points[0]
            hill_active = True
            time_hill_active = ev.num_ticks
        elif isinstance(ev, ZoneDeactivateEvent):
            hill_active = False
            
        elif isinstance(ev, MoveEvent):
            if ev.player_index != my_index:
                if (ev.ant_id, ev.player_index) in fighters:
                    # Adjust fighter positions
                    for f in fighters[(ev.ant_id, ev.player_index)]:
                        # We also don't know if these guys are dead
                        to_move.add((f, ev.position))
                    continue

                if ev.ant_str['classname'] != 'FighterAnt':
                    continue

                x, y = spawns[my_index]
                e_x, e_y = ev.position
                d = (x - e_x)**2 + (y - e_y)**2

                if d < (stats.ants.Fighter.RANGE * FIGHTER_RADIUS_MULT)**2:
                    # Track this fighter ant 
                    new_fighters.append((ev.ant_id, ev.player_index, fighter_id, ev.position))
                    fighter_id += 1

        elif isinstance(ev, FoodTileActiveEvent):
            charged[ev.pos] = ev.num_ticks
        elif isinstance(ev, FoodTileDeactivateEvent):
            charged.pop(ev.pos)
        elif isinstance(ev, TeamDefeatedEvent):
            if ev.defeated_index in snipe_target:
                snipe_target.remove(ev.defeated_index)

            if ev.defeated_index in hill_points:
                hill_points.pop(ev.defeated_index)
            
            if ev.by_index != my_index:
                hill_points[ev.by_index] = ev.new_hill_score

            defeated.add(ev.defeated_index)
        elif isinstance(ev, SettlerScoreEvent):
            if ev.player_index != my_index:
                hill_points[ev.player_index] += ev.score_amount
        elif isinstance(ev, SpawnEvent):
            if ev.player_index != my_index:
                if ev.player_index not in hill_points and ev.player_index not in defeated:
                    hill_points[ev.player_index] = 0

    if on_default_map:
        if len(default_map_defenders) < DEFAULT_MAP_DEFENDERS_COUNT:
            default_map_defenders[fighter_id] = False
            fighter_id += 1

    # Send our wounded veterans home
    for t in to_send_home:
        requests.append(GoalRequest(t, spawns[my_index]))

    # Move fighters who have targets that have also moved
    for f, pos in to_move:
        if f not in dead_fighters and f not in to_send_home:
            requests.append(GoalRequest(f, pos))

    strategic_location = (0,0)

    enemy_to_attack = get_highest_score_index()

    if queen_ant_attacked:
        strategic_location = spawns[my_index]
        curr_strat = "Attacked"
    elif (
        len(snipe_target) > 0 and
        my_energy >= 100
    ):
        curr_strat = "Snipe"
        if len(food) == 1:
            strategic_location = food[0]
        else:
            strategic_location = food[1]
    elif hill_active:
        if (
            (distance[curr_hill]/stats.ants.Settler.SPEED) > stats.ants.Settler.LIFESPAN*CLOSE_HILL_THRESHOLD/100 or
            (distance[curr_hill]/stats.ants.Settler.SPEED) > time_hill_active*CLOSE_HILL_THRESHOLD/100
        ):
            if enemy_to_attack == None:
                strategic_location = food[-1]    
            else:
                strategic_location = spawns[get_highest_score_index()]
            curr_strat = "Econ_And_Harass"
        else:
            strategic_location = curr_hill
            curr_strat = "Close_hill"
    elif (
        my_energy >= stats.general.MAX_ENERGY_STORED - 50 or
        (curr_strat == "Rush" and my_energy >= 100)
    ):
        if enemy_to_attack == None:
            strategic_location = food[-1]
            curr_strat = "Econ_And_Harass"
        else:
            strategic_location = spawns[get_highest_score_index()]
            curr_strat = "Rush"
    elif not first_hill_active:
        if len(food) == 1:
            strategic_location = food[0] 
        else:
            strategic_location = food[randint(1, min(3, len(food) - 1))]      
        curr_strat = "Early_game"
    else:
        if enemy_to_attack == None:
            strategic_location = food[-1]
        else:
            strategic_location = spawns[get_highest_score_index()]

        curr_strat = "Econ_And_Harass"

    worker_to_spawn_this_tick = int(STRATEGY[curr_strat][0] * stats.general.MAX_SPAWNS_PER_TICK/100)
    fighter_to_spawn_this_tick = int(STRATEGY[curr_strat][1] * stats.general.MAX_SPAWNS_PER_TICK/100)
    settler_to_spawn_this_tick = int(STRATEGY[curr_strat][2] * stats.general.MAX_SPAWNS_PER_TICK/100)

    defenders_to_spawn = []
    if on_default_map and curr_strat == "Early_game":
        for k, v in default_map_defenders.items():
            if not v:
                defenders_to_spawn.append(k)
                break

    # Can I spawn ants?
    i = 0
    j = 0
    while (
        total_ants < stats.general.MAX_ANTS_PER_PLAYER and 
        (
            my_energy >= stats.ants.Fighter.COST + 100 or
            (len(new_fighters) > 0 and my_energy >= stats.ants.Fighter.COST) or
            (len(defenders_to_spawn) > 0 and my_energy >= stats.ants.Fighter.COST + stats.ants.Worker.COST)
        ) and
        fighter_to_spawn_this_tick > 0
    ):
        if j < len(defenders_to_spawn):
            default_map_defenders[defenders_to_spawn[j]] = True
            print("Spawning defender")
            requests.append(SpawnRequest(AntTypes.FIGHTER, id=defenders_to_spawn[j], color=None, goal=default_map_corner))
            j += 1
        elif i < len(new_fighters):
            ant_id, p_id, f_id, ant_pos = new_fighters[i]
            fighters[(ant_id, p_id)].add(f_id)
            requests.append(SpawnRequest(AntTypes.FIGHTER, id=f_id, color=None, goal=ant_pos))
            i += 1
        elif curr_strat=="Snipe":
            id = "Snipe-"+str(fighter_id)
            requests.append(SpawnRequest(AntTypes.FIGHTER, id=id))
            fighter_id+=1
            snipe_squad.append(id)
        else:
            requests.append(SpawnRequest(AntTypes.FIGHTER, color=None, goal=strategic_location))

        my_energy -= stats.ants.Fighter.COST        
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

        my_energy -= stats.ants.Settler.COST

    for snipers in snipe_squad:
        if (len(snipe_target)>0):
            requests.append(GoalRequest(snipers, spawns[snipe_target[0]]))
        else:
            requests.append(GoalRequest(snipers, strategic_location))
    
    for k in charged.keys():
        charged[k] -= 1

    if hill_active:
        time_hill_active -= 1

    return requests

def get_highest_score_index():
    if len(hill_points) == 0:
        neighbors = [i for i, x in enumerate(spawns) if i != my_index and i not in defeated and i not in unreachable_enemies]
        if len(neighbors) > 0:
            return neighbors[0]
        else:
            return None 

    have_points = [x for x in hill_points.values() if x > 0]
    if len(have_points) == 0:
        d = sorted([(distance[spawns[x]], x) for x in hill_points.keys() if x != my_index and x not in defeated and x not in unreachable_enemies], key=lambda k: k[0])

        if len(d) > 0:
            return d[0][1]
        else:
            return None

    hp_n = {k:v for k, v in hill_points.items() if k not in defeated and k not in unreachable_enemies}
    if len(hp_n) == 0:
        return None
    return max(hp_n, key=hp_n.get)

def get_possible_food():
    fs = []
    for i in range(len(food)):
        if len(food_workers[food[i]]) <= food_workers_limit[food[i]]:
            fs.append(i)

    if len(fs) == 0:
        return 0

    best_i = (0, 0)
    for i, f in enumerate(fs):
        if food[f] in charged:
            if ei[food[f]] * 2 > best_i[1]:
                best_i = i, ei[food[f]] * 2

    return fs[best_i[0]]

def get_patrol_location():
    i = get_possible_food()
    return food[i]

def send_worker_ant(ant_id=None):
    global food_workers, my_energy, fighter_id
    i = get_possible_food()

    if ant_id == None:
        id = "worker_" + str(fighter_id)
        food_workers[food[i]].append(id)
        fighter_id+=1
        my_energy -= stats.ants.Worker.COST
        return SpawnRequest(AntTypes.WORKER, id=id, color=None, goal=food[i])
    else:
        food_workers[food[i]].append(ant_id)
        return GoalRequest(ant_id, position=food[i])
