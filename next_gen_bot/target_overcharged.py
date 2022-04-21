charged = {}
ei = {}

def read_map(md, energy_info):
    global ei

    ei = energy_info

def handle_events(events):
    global charged

    for ev in events:
        if isinstance(ev, FoodTileActiveEvent):
            charged[ev.pos] = ev.num_ticks
        elif isinstance(ev, FoodTileDeactivateEvent):
            charged[ev.pos].pop()

    # Decrement count of overcharged food tiles
    for k in charged.keys():
        charged[k] -= 1

def get_possible_food():
    fs = []
    for i in range(len(food)):
        if food_workers[food[i]] <= food_workers_limit[food[i]]:
            fs.append(i)

    if len(fs) == 0:
        return 0

    best_i = (0, 0)
    for f in fs:
        if food[f] in charged:
            if ei[food[f]] * 2 > best_i[1]:
                best_i = f, ei[food[f]] * 2 

    return best_i[0]

def get_patrol_location():
    i = get_possible_food()
    return food[i]

def send_worker_ant(ant_id=None):
    global food_workers, my_energy
    i = get_possible_food()

    food_workers[food[i]] += 1
    if ant_id == None:
        my_energy -= stats.ants.Worker.COST
        return SpawnRequest(AntTypes.WORKER, id=None, color=None, goal=food[i])
    else:
        dead_workers[ant_id] = food[i]
        return GoalRequest(ant_id, position=food[i])
