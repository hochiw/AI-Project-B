import numpy as np
import sys
from random import choice

class GameState:

    def __init__(self):

        self.red = {
            'positions':[(-3,3), (-3,2), (-3,1), (-3,0)],
            'goals':{(3,-3), (3,-2), (3,-1), (3,0)},
            'score':0
            }
        self.green = {
            'positions':[(0,-3), (1,-3), (2,-3), (3,-3)],
            'goals':{(-3,3), (-2,3), (-1,3), (0,3)},
            'score':0
            }
        self.blue = {
            'positions':[(3,0),(2,1),(1,2),(0,3)],
            'goals':{(-3,0),(-2,-1),(-1,-2),(0,-3)},
            'score':0
            }
        self.turn = 0
        self.enemy_exits = 0
        self.own_exits = 0
        self.enemy_jumps = 0
        self.own_jumps = 0


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

class Player:
    def __init__(self, colour):

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
        self.position = self.state.getPlayer(self.colour)['positions']
        self.goals = self.state.getPlayer(self.colour)['goals']
        self.weights = [1,0.2,0.2]

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
        if len(self.state.getPlayer(self.colour)['positions']) == 0:
            return ('PASS',None)
        piece = choice(self.state.getPlayer(self.colour)['positions'])
        result = [i for i in self.availableMoves(piece) if i]
        if len(result) == 0:
            return ('PASS',None)
        return choice(result)

        # TODO: Decide what action to take.



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
        if action[0] == "MOVE":
            # Remove the original position and append the new position
            self.state.getPlayer(colour)['positions'].remove(action[1][0])
            self.state.getPlayer(colour)['positions'].append(action[1][1])

        if action[0] == "JUMP":
            # Check if there's a piece in between the jumps
            check = self.checkJumpOver(colour,action[1])
            if check:
                # Check if the piece is an enemy piece
                if (check[0] != colour):
                    # Flip the piece
                    self.state.getPlayer(check[0])['positions'].remove(check[1])
                    self.state.getPlayer(colour)['positions'].append(check[1])
                # Update the jumped position
                self.state.getPlayer(colour)['positions'].remove(action[1][0])
                self.state.getPlayer(colour)['positions'].append(action[1][1])

        if action[0] == "EXIT":
            # Remove the piece from the board and update the player score
            self.state.getPlayer(colour)['positions'].remove(action[1])
            self.state.getPlayer(colour)['score'] += 1
            if colour == self.colour:
                self.state.own_exits += 1
            else:
                self.state.enemy_exits += 1
        self.state.turn += 1

        print("Heuristic value:  ")
        value = self.heuristic()
        print(value)


    def checkJumpOver(self, colour, coordinates):
        fstpoint = coordinates[0]
        sndpoint = coordinates[1]

        midtile = ((fstpoint[0] + sndpoint[0])/2,(fstpoint[1] +sndpoint[1])/2)

        tile = self.state.findTile(midtile)

        if tile:
            return (tile,midtile)
        return None

    def availableMoves(self,coor):
        x = coor[0]
        y = coor[1]

        result = []
        # Range adapted from game.py
        ran = range(-3, +3+1)
        hexes = {(q,r) for q in ran for r in ran if -q-r in ran}
        directions = [(-1,0),(0,-1),(1,-1),(1,0),(0,1),(-1,1)]
        for (a,b) in directions:
            if (x+a,y+b) in hexes and not self.state.findTile((x+a,y+b)):
                result.append(("MOVE",((x,y), (x+a,y+b))))
            elif (x+2*a,y+2*b) in hexes and not self.state.findTile((x+2*a,y+2*b)):
                result.append(("JUMP",((x,y), (x+2*a,y+2*b))))
            else:
                result.append(None)
        if not any(result):
            result.append(("PASS",None))
        else:
            result.append(None)

        if (x,y) in self.goals:
            result.append(("EXIT",(x,y)))
        else:
            result.append(None)

        return result

    def heuristic(self):
        result = 0
        i = 0
        colours = ["red", "green", "blue"]
        #Modify update to record : No of Opponent/our Jumps, No of Exits
        # Adds self ave_dist score
        if len(self.position) != 0:
            result += (self.weights[i] * self.aveDist(self.colour))
        # Deducts opponent's ave_dist score
        for colour in colours:
            if colour == self.colour:
                continue
            if len(self.state.getPlayer(colour)['positions']) != 0:
                result -= (self.weights[i] * self.aveDist(colour))

        return result

    #Calculates the average distance of pieces of a colour to
    #their respective closest goal
    def aveDist(self, colour):
        ave_dist = 0
        min_dist = sys.maxsize
        #Iterate self pieces and for each piece get min dist then sum all
        for piece in self.state.getPlayer(colour)['positions']:
            for goal in self.goals:
                dist = self.hex_distance(piece,goal)
                if dist < min_dist:
                    min_dist = dist
            ave_dist += min_dist
        ave_dist = ave_dist/len(self.state.getPlayer(colour)['positions'])
        return ave_dist

    # calculates distance
    def hex_distance(self,tile,other):
        return (abs(tile[0] - other[0]) +
                abs(tile[0] - other[0] + tile[1] - other[1]) +
                abs(tile[1] - other[1])) / 2
