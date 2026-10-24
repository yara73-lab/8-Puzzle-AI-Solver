import math

BOARD_SIZE=3
class Heuristics:
    @staticmethod
    def manhattan(state,goal_pos) -> int:
        # goal_pos is dict of the (x,y) for each tile's goal position - precomputed
        res=0
        for i,tile in enumerate(state):
            if state[i]==0:
                continue
            state_x, state_y = divmod(i, BOARD_SIZE)
            goal_x, goal_y = goal_pos[tile]
            res+=abs(state_x - goal_x) + abs(state_y - goal_y)
        return res
    
    @staticmethod    
    def euclidean(state,goal_pos) -> float:
        res=0.0
        for i,tile in enumerate(state):
            if state[i]==0:
                continue
            state_x, state_y = divmod(i, BOARD_SIZE)
            goal_x, goal_y = goal_pos[tile]
            res+=math.sqrt((state_x-goal_x)**2 + (state_y-goal_y)**2)
        return res 
