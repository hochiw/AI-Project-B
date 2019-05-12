import numpy as np
import os
from copy import deepcopy
from random import choice
import sys

# Bitboards that represent the vertical mask
_VERTICAL = [int(283691315109952/(2 ** i)) for i in range(7)]
# Bitboards that represent the horizontal mask
_HORIZONTAL = [127 * (128 ** i) for i in range(7)]

_LAST_MOVE = []
class GameState:

    # Initialise the game state.
    def __init__(self):

        self.red = {
            'board': int("0000000000000000000001000000100000010000001000000",2),
            'goals': {(3,-3), (3,-2), (3,-1), (3,0)},
            'score':0,
            'exit':0
            }
        self.green = {
            'board': int("0001111000000000000000000000000000000000000000000",2),
            'goals':{(-3,3), (-2,3), (-1,3), (0,3)},
            'score':0,
            'exit':0
            }
        self.blue = {
            'board': int("0000000000000000000000000001000001000001000001000",2),
            'goals':{(-3,0),(-2,-1),(-1,-2),(0,-3)},
            'score':0,
            'exit':0
            }
        self.last_move = []
        self.weights = [1,0.2,0.2]

    # Function that converts coordinate to bitboard index.
    def coorToBitboard(self,q,r):
        ran = range(-3,4)
        # Checks if the coordinate is in range.
        if (q in ran and r in ran and -q-r in ran):
            return int((r+3)*7 + (q+3))
        return None

    # Function that converts bitboard index to coordinate.
    def bitboardToCoor(self,index):
        return ((index % 7) - 3,int(index/7) -3)

    # Get the player details through passing colour string.
    def getPlayer(self,colour):
        if colour == "red":
            return self.red
        elif colour == 'green':
            return self.green
        elif colour == 'blue':
            return self.blue
        else:
            return None

    # Function that gets all the pieces on the board
    def getPositions(self, colour):
        player = self.getPlayer(colour)['board']
        result = []

        # Check if there is a piece on a column
        for i in range(len(_VERTICAL)):
            # Skip the column if there's no piece
            if (_VERTICAL[i] & player) == 0:
                continue
            # Check the rows if there's a piece on a column
            for j in range(len(_HORIZONTAL)):
                if (_HORIZONTAL[j] & player & _VERTICAL[i]) == 0:
                    continue
                # Add the coordinate of the piece to the result lists
                result.append((i -3 ,3 - j))
        # Return the result
        return result

    # Function that check if there's a piece on a tile.
    def findTile(self,coor):
        # Convert the coordinate into bitboard index.
        index = self.coorToBitboard(coor[0],coor[1])

        # Create mask of the index
        mask = 1 << (48 - index)

        # Check if the tile is occupied by a colour.
        if (self.red['board'] & mask) != 0:
            return "red"
        if (self.green['board'] & mask) != 0:
            return "green"
        if (self.blue['board'] & mask) != 0:
            return "blue"
        return None

    # Get all the available moves on the board including enemies.
    def getAllMoves(self):
        moves = []
        colours = ['red','green','blue']
        for colour in colours:
            for move in self.availableMoves(colour):
                moves.append((move,colour))
        return moves

    # Get the available moves of all the pieces of the given colour.
    def availableMoves(self, colour):
        result = []
        for x,y in self.getPositions(colour):
            # Check if the piece is on top of a goal.
            if (x,y) in self.getPlayer(colour)['goals']:
                result.append(("EXIT",(int(x),int(y))))
                break

            # Range adapted from game.py.
            ran = range(-3, +3+1)
            # All the directions.
            directions = [(-1,0),(0,-1),(1,-1),(1,0),(0,1),(-1,1)]
            for (a,b) in directions:
                # Check if the tile in the direction is available.
                if self.isValidMove((x+a,y+b)) and not self.findTile((x+a,y+b)):
                    result.append(("MOVE",((x,y), (int(x+a),int(y+b)))))
                # If not, check the next tile in the same direction.
                elif self.isValidMove((x+2*a,y+2*b)) and not self.findTile((x+2*a,y+2*b)):
                    result.append(("JUMP",((x,y), (int(x+2*a),int(y+2*b)))))

                # Return PASS if there's no available move.
            if not any(result):
                result.append(("PASS",None))
        return result

    def isValidMove(self, coor):
        ran = range(-3, 4)
        return coor[0] in ran and coor[1] in ran and -coor[0]-coor[1] in ran


    # Function that undo the last move.
    def undo(self):
        dic = _LAST_MOVE.pop()
        self.red = dic['red']
        self.green = dic['green']
        self.blue = dic['blue']


    # Function that executes piece movement.
    def move(self,lst,fst,secd):

        lst = self.addrmPiece(lst, fst)
        lst = self.addrmPiece(lst, secd, True)

        # Return the 'exclusive or' of both bitstrings.
        return lst

    # Function that adds or removes a piece from the board.
    def addrmPiece(self,lst,coor, add = False):
        # Convert the coordinate into a bitboard index.
        index = self.coorToBitboard(coor[0],coor[1])
        # Construct a bitstring that shows the position of the piece we want to
        mask = 1 << (48 - index)
        # If we want to add then return the 'or' of the two bitstrings or else
        # return the 'exclusive or ' of the two bitstrings to remove the piece.
        if add:
            lst |= mask
        else:
            lst ^= mask

        return lst

    # Function that checks if there's a piece in between
    # the landing position and the original position.
    def checkJumpOver(self, coordinates):
        fstpoint = coordinates[0]
        sndpoint = coordinates[1]

        # Get the tile in between two tiles.
        midtile = ((fstpoint[0] + sndpoint[0])/2,(fstpoint[1] +sndpoint[1])/2)

        # Check if the midtile is occupied.
        tile = self.findTile(midtile)

        # Return the colour and the coordinate of the midtile if it's occupied
        # Or else return None.
        if tile:
            return (tile,midtile)
        return None

    def heuristic(self, colour_i):
        result = 0
        i = 0
        colours = ["red", "green", "blue"]

        for colour in colours:
            #Modify update to record : No of Opponent/our Jumps, No of Exits
            # Adds self ave_dist score
            if colour == colour_i:
                if len(self.getPositions(colour)) != 0:
                    result += self.getPlayer(colour)['score']  * 1000
                    result -= (self.weights[i] * self.aveDist(colour))
                    result += self.getPlayer(colour_i)['exit'] * 100
            else:
                # Deducts opponent's ave_dist score
                if len(self.getPositions(colour)) != 0:
                    result += (self.weights[i] * self.aveDist(colour))
                    result -= self.getPlayer(colour_i)['score']
                    result -= self.getPlayer(colour_i)['exit']


        return result



     #Calculates the average distance of pieces of a colour to
    #their respective closest goal
    def aveDist(self, colour):
        ave_dist = 0
        #Iterate self pieces and for each piece get min dist then sum all
        for piece in self.getPositions(colour):
            min_dist = sys.maxsize
            for goal in self.getPlayer(colour)['goals']:
                dist = self.hex_distance(piece,goal)
                if dist < min_dist:
                    min_dist = dist
            ave_dist += min_dist
        ave_dist = ave_dist/len(self.getPositions(colour))
        return ave_dist

    # Helper function that calculates the distance between two tiles.
    # Adapted from https://www.redblobgames.com/grids/hexagons.
    def hex_distance(self,a,b):
        return (abs(a[0] - b[0])
          + abs(a[0] + a[1] - b[0] - b[1])
          + abs(a[1] - b[1])) / 2

    # Function that handles all the updates that happen on the board.
    def updateState(self, colour, action):
        # Store the move.
        _LAST_MOVE.append({
            #"red":{"board":self.red['board'],"goals":self.red['goals'],"score":int(self.red['score']),"exit":int(self.red['exit'])},
            #"green":{"board":self.green['board'],"goals":self.green['goals'],"score":int(self.green['score']),"exit":int(self.green['exit'])},
            #"blue":{"board":self.blue['board'],"goals":self.blue['goals'],"score":int(self.blue['score']),"exit":int(self.blue['exit'])},
            "red":deepcopy(self.red),
            "green":deepcopy(self.green),
            "blue":deepcopy(self.blue)
        })

        player = self.getPlayer(colour)
        score = 0
        score_e = 0

        # MOVE.
        if action[0] == "MOVE":
            player['board'] = self.move(player['board'], action[1][0],action[1][1])
            score -= 5
        # JUMP.
        if action[0] == "JUMP":
            # Check if there's a piece in between the jumps.
            check = self.checkJumpOver(action[1])
            if check:
                # Check if the piece is an enemy piece.
                if (check[0] != colour):
                    # Flip the piece.
                    self.getPlayer(check[0])['board'] = self.addrmPiece(self.getPlayer(check[0])['board'],check[1])
                    player['board'] = self.addrmPiece(player['board'],check[1],True)
                    score_e -= 1
                    score += 1

                # Update the jumped position.
                score += 1
                player['board'] = self.move(player['board'], action[1][0],action[1][1])
            self.getPlayer(check[0])['score'] = score_e

        # EXIT
        if action[0] == "EXIT":
            # Remove the piece from the board and update the player score.
            player['board'] = self.addrmPiece(player['board'],action[1])
            score += 100

        player['score'] = score

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
        # Find all the available moves for the player.
        for move in self.state.availableMoves(self.colour):
            # Update the state, pass the modified state to minimax, then undo.
            self.state.updateState(self.colour, move)
            value = self.minimax(self.state, self.colour, 2, True, -sys.maxsize - 1, sys.maxsize)
            self.state.undo()

            # Give each state a score.
            result[move] = value
        # Return the move with the best score or return PASS if no move is
        # available.
        print(result)
        return max(result, key=result.get) if len(result) != 0 else ('PASS',None)

    # Minimax algorithm
    def minimax(self, state, colour, depth, maxPlayer, a, b, score = None, exit = None):

        # Evaluate the board if it reaches the maximum depth
        #if depth == 0 or state.winner():
        if depth == 0:

            return state.heuristic(colour)

        # Check the max
        if maxPlayer:
            # Initialise the best value to be negative infinity
            best_value = -sys.maxsize - 1
            # Get all the possible moves
            for move in state.getAllMoves():
                # Update the state, pass the modified state to the minimax algorithm
                # with a lower depth, then undo
                state.updateState(move[1],move[0])
                value = self.minimax(state, colour, depth - 1, False, a, b)
                state.undo()
                # Compare the best value and the value it gets from minimax
                best_value = max(best_value, value)

                # Ignore the branch if alpha is bigger than beta
                if best_value >= b:
                    break
                # Update the alpha value
                a = max(a, best_value)


            return best_value
        # Check the min
        else:
            # Initialise the best value to be positive infinity
            best_value = sys.maxsize
            # Get all the possible moves
            for move in state.getAllMoves():
                # Update the state, pass the modified state to the minimax algorithm
                # with a lower depth, then undo
                state.updateState(move[1],move[0])
                value = self.minimax(state, colour, depth - 1, True, a, b)
                state.undo()
                # Compare the best value and the value it gets from minimax
                best_value = min(best_value, value)

                # Ignore the branch if alpha is bigger than beta
                if best_value <= a:
                    break

                # Update the beta value
                b = min(b, best_value)

            return best_value


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
