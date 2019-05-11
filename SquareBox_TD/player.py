import numpy as np
import os
from copy import deepcopy
from random import choice
import sys


class GameState:

    def __init__(self):

        self.red = {
            'positions':[(-3,3), (-3,2), (-3,1), (-3,0)],
            'goals':{(3,-3), (3,-2), (3,-1), (3,0)},
            'eaten':0,
            'score':0
            }
        self.green = {
            'positions':[(0,-3), (1,-3), (2,-3), (3,-3)],
            'goals':{(-3,3), (-2,3), (-1,3), (0,3)},
            'eaten':0,
            'score':0
            }
        self.blue = {
            'positions':[(3,0),(2,1),(1,2),(0,3)],
            'goals':{(-3,0),(-2,-1),(-1,-2),(0,-3)},
            'eaten':0,
            'score':0
            }
        self.turns = 0
        self.last_move = []


    def getPlayer(self,colour):
        if colour == "red":
            return self.red
        elif colour == 'green':
            return self.green
        elif colour == 'blue':
            return self.blue
        else:
            return None

    def findTile(self,coor):
        for i in self.red['positions']:
            if i == coor:
                return "red"
        for i in self.green['positions']:
            if i == coor:
                return "green"
        for i in self.blue['positions']:
            if i == coor:
                return "blue"
        return None

    def getAllMoves(self):
        moves = []
        colours = ['red','green','blue']
        for colour in colours:
            for move in self.availableMoves(colour):
                moves.append((move,colour))
        return moves

    def availableMoves(self, colour):
        result = []
        for (x,y) in self.getPlayer(colour)['positions']:
            if (x,y) in self.getPlayer(colour)['goals']:
                result.append(("EXIT",(int(x),int(y))))
                continue

                # Range adapted from game.py
            ran = range(-3, +3+1)
            hexes = {(q,r) for q in ran for r in ran if -q-r in ran}
            directions = [(-1,0),(0,-1),(1,-1),(1,0),(0,1),(-1,1)]
            for (a,b) in directions:
                if (x+a,y+b) in hexes and not self.findTile((x+a,y+b)):
                    result.append(("MOVE",((x,y), (int(x+a),int(y+b)))))
                elif (x+2*a,y+2*b) in hexes and not self.findTile((x+2*a,y+2*b)):
                    result.append(("JUMP",((x,y), (int(x+2*a),int(y+2*b)))))

            if not any(result):
                result.append(("PASS",None))
        return result

    def winner(self):
        if self.red['score'] == 4:
            return "red"
        elif self.green['score'] == 4:
            return "green"
        elif self.blue['score'] == 4:
            return "blue"
        else:
            return None

    def undo(self):
        dic = self.last_move.pop()
        self.red['positions'] = dic['red']
        self.green['positions'] = dic['green']
        self.blue['positions'] = dic['blue']


    def updateState(self, colour, action):
        self.last_move.append({
            "red":deepcopy(self.red['positions']),
            "green":deepcopy(self.green['positions']),
            "blue":deepcopy(self.blue['positions'])
        })
        if action[0] == "MOVE":
            # Remove the original position and append the new position
            self.getPlayer(colour)['positions'].remove(action[1][0])
            self.getPlayer(colour)['positions'].append(action[1][1])

        if action[0] == "JUMP":
            # Check if there's a piece in between the jumps
            check = self.checkJumpOver(action[1])
            if check:
                # Check if the piece is an enemy piece
                if (check[0] != colour):
                    # Flip the piece
                    self.getPlayer(check[0])['positions'].remove(check[1])
                    self.getPlayer(colour)['positions'].append(check[1])
                    self.getPlayer(colour)['eaten'] += 1
                    self.getPlayer(check[0])['eaten'] -= 1
                # Update the jumped position
                self.getPlayer(colour)['positions'].remove(action[1][0])
                self.getPlayer(colour)['positions'].append(action[1][1])


        if action[0] == "EXIT":
            # Remove the piece from the board and update the player score
            self.getPlayer(colour)['positions'].remove(action[1])
            self.getPlayer(colour)['score'] += 1


        self.turns += 1


    def checkJumpOver(self, coordinates):
        fstpoint = coordinates[0]
        sndpoint = coordinates[1]

        midtile = ((fstpoint[0] + sndpoint[0])/2,(fstpoint[1] +sndpoint[1])/2)

        tile = self.findTile(midtile)

        if tile:
            return (tile,midtile)
        return None

    def tileDistance(self,a,b):
        return (abs(a[0] - b[0])
          + abs(a[0] + a[1] - b[0] - b[1])
          + abs(a[1] - b[1])) / 2

class Player:
    def __init__(self, colour, exploration_rate = 0.33, learning_rate = 0.5, discount_factor= 0.01):

        """
        This method is called once at the beginning of the game to initialise
        your player. You should use this opportunity to set up your own internal
        representation of the game state, and any other information about the
        game state you would like to maintain for the duration of the game.

        The parameter colour will be a string representing the player your
        program will play as (Red, Green or Blue). The value will be one of the
        strings "red", "green", or "blue" correspondingly.
        """
        # TODO: Set up state representation.
        self.state = GameState()
        self.colour = colour



    def action(self):
        """
        This method is called at the beginning of each of your turns to request
        a choice of action from your program.

        Based on the current state of the game, your player should select and
        return an allowed action to play on this turn. If there are no allowed
        actions, your player must return a pass instead. The action (or pass)
        must be represented based on the above instructions for representing
        actions.
        """
        result = {}
        for move in self.state.availableMoves(self.colour):
            self.state.updateState(self.colour, move)
            value = self.minimax(self.state, self.colour, 2, True, -sys.maxsize - 1, sys.maxsize)
            self.state.undo()
            result[move] = value

        return max(result, key=result.get) if len(result) != 0 else ('PASS',None)

    def minimax(self,state, colour, depth, maxPlayer, a, b):
        if state.winner():
            if state.winner() == colour:
                return sys.maxsize
            else:
                return -sys.maxsize - 1

        if depth == 0:
            return self.evaluateBoard(state, colour)

        if maxPlayer:
            best_value = -sys.maxsize - 1
            for move in state.getAllMoves():
                state.updateState(move[1],move[0])
                value = self.minimax(state, colour, depth - 1, False, a, b)
                state.undo()
                best_value = max(best_value, value)
                a = max(a, best_value)

                if b <= a:
                    break
            return best_value
        else:
            best_value = sys.maxsize
            for move in state.getAllMoves():
                state.updateState(move[1],move[0])
                value = self.minimax(state, colour, depth - 1, True, a, b)
                state.undo()
                best_value = min(best_value, value)
                b = min(b, best_value)

                if b <= a:
                    break
                    
            return best_value

    def evaluateBoard(self, state, colour_i):
        score = 0
        colours = ['red','green','blue']
        for colour in colours:
            if colour == colour_i:
                if state.getPlayer(colour)['score']  + len(state.getPlayer(colour)['positions'])  < 4:
                    score += len(state.getPlayer(colour)['positions']) * 100
                    score += state.getPlayer(colour)['eaten'] * 1000
                else:
                    score +=  state.getPlayer(colour)['score'] * 1000
                    score -= state.getPlayer(colour)['eaten'] * 1000
            else:
                score -= len(state.getPlayer(colour)['positions'])
                score -= state.getPlayer(colour)['score']
                #score += self.averageGoalDis(state, colour)
        score -= state.turns

        return score

#    def averageGoalDis(self, state, colour):
#        lst = []
#
#        for piece in state.getPlayer(colour)['positions']:
#            lst.append(self.closestGoalDis(state, piece, colour))
#        if len(lst) != 0:
#            return sum(lst)/len(lst)
#        return 0

#    def closestGoalDis(self, state, piece, colour):
#        min_distance = 9999
#        for goal in state.getPlayer(colour)['goals']:
#            if state.tileDistance(piece, goal) <= min_distance:
#                min_distance = state.tileDistance(piece, goal)
#        return min_distance

    def update(self, colour, action):
        """
        This method is called at the end of every turn (including your player’s
        turns) to inform your player about the most recent action. You should
        use this opportunity to maintain your internal representation of the
        game state and any other information about the game you are storing.

        The parameter colour will be a string representing the player whose turn
        it is (Red, Green or Blue). The value will be one of the strings "red",
        "green", or "blue" correspondingly.

        The parameter action is a representation of the most recent action (or
        pass) conforming to the above in- structions for representing actions.

        You may assume that action will always correspond to an allowed action
        (or pass) for the player colour (your method does not need to validate
        the action/pass against the game rules).
        """
        # TODO: Update state representation in response to action.
        self.state.updateState(colour,action)
