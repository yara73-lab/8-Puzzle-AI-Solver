import math

BOARD_SIZE=3
class Heuristics:
    @staticmethod
    def manhattan(state,goal) -> int:
        res=0
        for i in range(len(state)):
            if state[i]==0:
                continue
            state_x, state_y = divmod(i, BOARD_SIZE)
            g = goal.index(state[i])
            goal_x, goal_y = divmod(g, BOARD_SIZE)
            res+=abs(state_x - goal_x) + abs(state_y - goal_y)
        return res
    @staticmethod    
    def euclidean(state,goal) -> float:
        res=0.0
        for i in range(len(state)):
            if state[i]==0:
                continue
            state_x, state_y = divmod(i, BOARD_SIZE)
            g = goal.index(state[i])
            goal_x, goal_y = divmod(g, BOARD_SIZE)
            res+=math.sqrt((state_x-goal_x)**2 + (state_y-goal_y)**2)
        return res 
