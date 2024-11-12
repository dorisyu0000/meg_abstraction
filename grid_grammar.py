import numpy as np 
import os 
import json
import random
#1=terminal, 2=south, 3=east, 4=north, 5=west
def complement(s):
    if s=='2':
        return '4'
    if s=='4':
        return '2'
    if s=='3':
        return '5'
    if s=='5':
        return '3'
    
def chain_production(grid,check=True,n=7):
    idxs=np.where(grid>1)
    possible_expansions_nodes=[]
    for i in range(len(idxs[0])):
        possible_expansions=[]
        curr=(idxs[0][i],idxs[1][i])
        val=str(grid[curr])
        if '2' in val and curr[0]+1<n and grid[curr[0]+1,curr[1]]==0:
            possible_expansions.append((curr[0]+1,curr[1],'2',curr))
        if '3' in val and curr[1]+1<n and grid[curr[0],curr[1]+1]==0:
            possible_expansions.append((curr[0],curr[1]+1,'3',curr))
        if '4' in val and curr[0]-1>=0 and grid[curr[0]-1,curr[1]]==0:
            possible_expansions.append((curr[0]-1,curr[1],'4',curr))
        if '5' in val and curr[1]-1>=0 and grid[curr[0],curr[1]-1]==0:
            possible_expansions.append((curr[0],curr[1]-1,'5',curr))
        possible_expansions_nodes.append(possible_expansions)
    if check:
        return len(possible_expansions_nodes)>0 and len(possible_expansions_nodes[0])>0
    else:
        expansions=possible_expansions_nodes[0]
        if len(expansions)>2:
            choice_idx2=np.random.choice(range(len(expansions)),size=2)
            expansion=[expansions[i] for i in choice_idx2]
            directions=[e[2] for e in expansion]
            while directions[0]!=complement(directions[1]):
                choice_idx2=np.random.choice(range(len(expansions)),size=2)
                expansion=[expansions[i] for i in choice_idx2]
                directions=[e[2] for e in expansion]
        else:
            choice_idx2=np.random.choice(range(len(expansions)),size=1)
            expansion=[expansions[i] for i in choice_idx2]

        for node in expansion:
            terminal=np.random.binomial(1,0.1)
            if terminal==1:
                grid[node[0],node[1]]=1
            else:
                grid[node[0],node[1]]=int(node[2])
            grid[node[3][0],node[3][1]]=1

    return grid


#1=terminal, 2=south, 3=east, 4=north, 5=west
def tree_production(grid,check=True,n=7):
    idxs=np.where(grid>1)
    possible_expansions_nodes=[]
    for i in range(len(idxs[0])):
        possible_expansions=[]
        curr=(idxs[0][i],idxs[1][i])
        val=str(grid[curr])
        if '2' in val and curr[0]+1<n-1 and grid[curr[0]+1,curr[1]]==0 and sum(grid[curr[0]+1,max(curr[1]-1,0):min(curr[1]+1,n-1)+1])==0:
            possible_expansions.append((curr[0]+1,curr[1],'2',curr))
        if '3' in val and curr[1]+1<n-1 and grid[curr[0],curr[1]+1]==0 and sum(grid[max(curr[0]-1,0):min(curr[0]+1,n-1)+1,curr[1]+1])==0:
            possible_expansions.append((curr[0],curr[1]+1,'3',curr))
        if '4' in val and curr[0]-1>=0 and grid[curr[0]-1,curr[1]]==0 and sum(grid[curr[0]-1,max(curr[1]-1,0):min(curr[1]+1,n-1)+1])==0:
            possible_expansions.append((curr[0]-1,curr[1],'4',curr))
        if '5' in val and curr[1]-1>=0 and grid[curr[0],curr[1]-1]==0 and sum(grid[max(curr[0]-1,0):min(curr[0]+1,n-1)+1,curr[1]-1])==0:
            possible_expansions.append((curr[0],curr[1]-1,'5',curr))
        if len(possible_expansions)>=2:
            possible_expansions_nodes.append(possible_expansions)
    #print(possible_expansions_nodes)
    if check:
        return len(possible_expansions_nodes)>0 and len(possible_expansions_nodes[0])>0
    else:
        choice_idx=np.random.choice(range(len(possible_expansions_nodes)),size=1)[0]
        expansions=possible_expansions_nodes[choice_idx]
        if len(expansions)>2:
            choice_idx2=np.random.choice(range(len(expansions)),size=2)
            expansion=[expansions[i] for i in choice_idx2]
            directions=[e[2] for e in expansion]
            while directions[0]==complement(directions[1]) or directions[0]==directions[1]:
                choice_idx2=np.random.choice(range(len(expansions)),size=2)
                expansion=[expansions[i] for i in choice_idx2]
                directions=[e[2] for e in expansion]
        else:
            expansion=expansions
        node0=(expansion[0][0],expansion[0][1],expansion[0][2]+complement(expansion[1][2]),expansion[0][3])
        node1=(expansion[1][0],expansion[1][1],expansion[1][2]+complement(expansion[0][2]),expansion[0][3])
        #print(expansions,expansion,node0,node1)
        expansion=[node0,node1]
        for i,node in enumerate(expansion):
            if len(str(grid[node[3][0],node[3][0]]))>1:
                terminal=0
            else:
                terminal=np.random.binomial(1,0.2)
            if terminal:
                grid[node[0],node[1]]=1
            else:
                grid[node[0],node[1]]=int(node[2])
            grid[node[3][0],node[3][1]]=1
    return grid

#1=terminal, 2=south, 3=east, 4=north, 5=west
def loop_production(grid, check=True, n=7):
    idxs = np.where(grid > 1)
    possible_expansions_nodes = []
    for i in range(len(idxs[0])):
        possible_expansions = []
        curr = (idxs[0][i], idxs[1][i])
        val = str(grid[curr])
        if '2' in val and curr[0] + 1 < n - 1 and grid[curr[0] + 1, curr[1]] == 0:
            possible_expansions.append((curr[0] + 1, curr[1], '2', curr))
        if '3' in val and curr[1] + 1 < n - 1 and grid[curr[0], curr[1] + 1] == 0:
            possible_expansions.append((curr[0], curr[1] + 1, '3', curr))
        if '4' in val and curr[0] - 1 >= 0 and grid[curr[0] - 1, curr[1]] == 0:
            possible_expansions.append((curr[0] - 1, curr[1], '4', curr))
        if '5' in val and curr[1] - 1 >= 0 and grid[curr[0], curr[1] - 1] == 0:
            possible_expansions.append((curr[0], curr[1] - 1, '5', curr))
        if len(possible_expansions) >= 2:
            possible_expansions_nodes.append(possible_expansions)
    if check:
        return len(possible_expansions_nodes) > 0 and len(possible_expansions_nodes[0]) > 0
    else:
        choice_idx = np.random.choice(range(len(possible_expansions_nodes)), size=1)[0]
        expansions = possible_expansions_nodes[choice_idx]
        if len(expansions) > 2:
            choice_idx2 = np.random.choice(range(len(expansions)), size=2)
            expansion = [expansions[i] for i in choice_idx2]
            directions = [e[2] for e in expansion]
            while directions[0] == complement(directions[1]) or directions[0] == directions[1]:
                choice_idx2 = np.random.choice(range(len(expansions)), size=2)
                expansion = [expansions[i] for i in choice_idx2]
                directions = [e[2] for e in expansion]
        else:
            expansion = expansions
        node0 = (expansion[0][0], expansion[0][1], expansion[0][2] + expansion[1][2], expansion[0][3])
        node1 = (expansion[1][0], expansion[1][1], expansion[1][2] + expansion[0][2], expansion[0][3])
        # print(expansions, expansion, node0, node1)
        expansion = [node0, node1]

        for i, node in enumerate(expansion):
            terminal = np.random.binomial(1, 0.5)
            if terminal:
                grid[node[0], node[1]] = 1
            else:
                grid[node[0], node[1]] = int(node[2])
            grid[node[3][0], node[3][1]] = 1
        grid[expansion[0][0], expansion[1][1]] = int(expansion[0][2])
        grid[expansion[1][0], expansion[0][1]] = int(expansion[1][2])

    return grid

def gkern(size=7,sigma=4,center=(0,3)):
    kernel=np.zeros((size,size))
    for i in range(size):
        for j in range(size):
            diff=np.sqrt((i-center[0])**2+(j-center[1])**2)
            kernel[i,j]=np.exp(-(diff**2)/(2*sigma**2))
    return kernel/np.sum(kernel)

def generate_grid_random(n=7):
    probs=np.zeros(13,)
    probs[0]=0.5
    for i in range(1,13):
        probs[i]=probs[i-1]*0.5
    probs=probs/probs.sum()
    number=np.random.choice(list(range(3,16)),p=probs)
    center=np.random.choice(list(range(7)),size=2,replace=True)
    chosen=np.random.choice(list(range(49)),size=number,replace=False,p=gkern(size=n,center=center,sigma=1.7463644200489674).flatten())
    vec=np.zeros((49,))
    vec[chosen]=1
    return vec.reshape((7,7))

def generate_grid(rules=None, trial_index=None, n=7): 
    rule = None 
    if rules == 'all':
        production = np.random.choice([chain_production, tree_production, loop_production])
    elif rules == 'chain':
        production = chain_production
        rule = 'chain'
    elif rules == 'tree':
        production = tree_production
        rule = 'tree'
    elif rules == 'loop':
        production = loop_production
        rule = 'loop'

    grid = np.zeros((n, n)).astype('int')
    start = np.random.choice(list(range(2, n-1)), size=2)
    print(start)
    grid[start[0], start[1]] = 2345 

    while np.sum(grid > 1) > 0:
        if production(grid, check=True, n=n):
            grid = production(grid, check=False, n=n)
        else:
            grid[grid > 1] = 1
    starts = generate_reveal(grid = grid, start = start.tolist(), n = n, reveal_n = 1)
    print(starts)
    return {"grid": grid.tolist(), "start": starts, "n": n, "rule": rule, "trial_number": trial_index}

def generate_locolizer(rules = None, reveal_n = 1, n=7):
    rule = None 
    if rules=='all':
        production=np.random.choice([chain_production,tree_production,loop_production])
    elif rules=='chain':
        production=chain_production
        rule = 'chain'
    elif rules=='tree':
        production=tree_production
        rule = 'tree'
    elif rules=='loop':
        production=loop_production
        rule = 'loop'

    grid = np.zeros((n,n))
    start = np.random.choice(list(range(2, n-1)), size=2)
    grid[start[0], start[1]] = 2345 

    while np.sum(grid > 1) > 0:
        if production(grid, check=True, n=n):
            grid = production(grid, check=False, n=n)
        else:
            grid[grid > 1] = 1


    starts = generate_reveal(grid = grid, start = start.tolist(), n = n, reveal_n = reveal_n)
    return {"grid": grid.tolist(), "start": starts,"n": n ,"rule": rule}

def generate_reveal(grid, start, reveal_n=3, n=7):
    if reveal_n == 1:
        return [start]
    
    starts = [start]
    possible_starts = []


    for i in range(max(0, start[0] - reveal_n + 1), min(n - reveal_n + 1, start[0] + 1)):
        for j in range(max(0, start[1] - reveal_n + 1), min(n - reveal_n + 1, start[1] + 1)):
            # Check if the start is within the reveal grid
            if i <= start[0] < i + reveal_n and j <= start[1] < j + reveal_n:
                possible_starts.append((i, j))

 
    if possible_starts:
        selected_start = random.choice(possible_starts)
        starts = [[selected_start[0] + x, selected_start[1] + y] for x in range(reveal_n) for y in range(reveal_n)]
    print(starts)
    return starts


def save_json(data, filename, folder_path):
    file_path = os.path.join(folder_path, f'{filename}.json')
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print(f'Data successfully saved to {file_path}')

if __name__=='__main__':
    n = 7
    kws = {'n': n}
    main = [] 
    practice = []
    trial_index = 1 

    main = [] 
    post_locolizer = []
    for rules in ['chain', 'tree', 'loop']:
        for _ in range(40):
            grid = generate_grid(rules=rules, trial_index=trial_index, n=n)
            trial_index += 1
            main.append(grid)

    trials = {
        'practice': practice,
        'main': main
    }

    localizer = generate_locolizer(rules = 'chain',reveal_n = 4, n = n)
    practice.append(localizer)

    for reveal_n in [5,3,2]:
        locolizer_bin = []
        for rules in ['chain', 'tree', 'loop']:
            for _ in range(15):
                locolizer = generate_locolizer(rules = rules,reveal_n = reveal_n, n = n)
                locolizer_bin.append(locolizer)
        random.shuffle(locolizer_bin)
        post_locolizer.extend(locolizer_bin)

    dest = "config/v2"
    os.makedirs(dest, exist_ok=True)

    # Generate and save other files without fixed seed
    for i in range(1, 11):  # Start from 1 because 0 is for sample.json
        random.shuffle(main) 
        rule_index = {'A':'tree', 'B':'loop', 'C':'chain'}
        trials = {
        'practice': practice,
        'main': main,
        'post': post_locolizer
        }
        with open(f"{dest}/{i}.json", "w", encoding='utf-8') as file:
            json.dump({ "rule_index": rule_index, "trials": trials}, file, ensure_ascii=False)



