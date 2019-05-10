import numpy as np
import os
from copy import deepcopy
from random import choice
import sys


class GameState:

    # Initialise the game state.
    def __init__(self):

        self.red = {
            'board': int("0000000000000000000001000000100000010000001000000",2),
            'goals': {(3,-3), (3,-2), (3,-1), (3,0)},
            'eaten':0,
            'score':0
            }
        self.green = {
            'board': int("0001111000000000000000000000000000000000000000000",2),
            'goals':{(-3,3), (-2,3), (-1,3), (0,3)},
            'eaten':0,
            'score':0
            }
        self.blue = {
            'board': int("0000000000000000000000000001000001000001000001000",2),
            'goals':{(-3,0),(-2,-1),(-1,-2),(0,-3)},
            'eaten':0,
            'score':0
            }
        self.turns = 0
        self.last_move = []

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

    # Function that check if there's a piece on a tile.
    def findTile(self,coor):
        # Convert the coordinate into bitboard index.
        index = self.coorToBitboard(coor[0],coor[1])

        # Check if the tile is occupied by a colour.
        if list("{:049b}".format(self.red['board']))[index] == '1':
            return "red"
        if list("{:049b}".format(self.green['board']))[index] == '1':
            return "green"
        if list("{:049b}".format(self.blue['board']))[index] == '1':
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
        # Convert the bitboard int into a list of bitboard string.
        lst = list("{:049b}".format(self.getPlayer(colour)['board']))
        for i in range(len(lst)):
            # if a piece is found.
            if lst[i] == '1':
                # Convert the index into coordinate.
                x,y = self.bitboardToCoor(i)
                # Check if the piece is on top of a goal.
                if (x,y) in self.getPlayer(colour)['goals']:
                    result.append(("EXIT",(int(x),int(y))))
                    continue

                # Range adapted from game.py.
                ran = range(-3, +3+1)
                hexes = {(q,r) for q in ran for r in ran if -q-r in ran}
                # All the directions.
                directions = [(-1,0),(0,-1),(1,-1),(1,0),(0,1),(-1,1)]
                for (a,b) in directions:
                    # Check if the tile in the direction is available.
                    if (x+a,y+b) in hexes and not self.findTile((x+a,y+b)):
                        result.append(("MOVE",((x,y), (int(x+a),int(y+b)))))
                    # If not, check the next tile in the same direction.
                    elif (x+2*a,y+2*b)in hexes and not self.findTile((x+2*a,y+2*b)):
                        result.append(("JUMP",((x,y), (int(x+2*a),int(y+2*b)))))

                # Return PASS if there's no available move.
                if not any(result):
                    result.append(("PASS",None))
        return result

    # Check if there is a winner.
    def winner(self):
        if self.red['score'] == 4:
            return "red"
        elif self.green['score'] == 4:
            return "green"
        elif self.blue['score'] == 4:
            return "blue"
        else:
            return None

    # Function that undo the last move.
    def undo(self):
        dic = self.last_move.pop()
        self.red['board'] = dic['red']
        self.green['board'] = dic['green']
        self.blue['board'] = dic['blue']

    # Function that executes piece movement.
    def move(self,lst,fst,secd):
        lst = "{:049b}".format(lst)
        # Turn both coordinates into bitboard index.
        index_1 = self.coorToBitboard(fst[0],fst[1])
        index_2 = self.coorToBitboard(secd[0],secd[1])

        # Construct a bitstring that shows both the original position and
        # the modified position of the piece.
        result = ''.join(['1' if i == index_1 or i == index_2 else '0' for i in range(len(list(lst)))])

        # Return the 'exclusive or' of both bitstrings.
        return int(lst,2) ^ int(result,2)

    # Function that adds or removes a piece from the board.
    def addrmPiece(self,lst,coor, add = False):
        lst = "{:049b}".format(lst)
        # Convert the coordinate into a bitboard index.
        index = self.coorToBitboard(coor[0],coor[1])
        # Construct a bitstring that shows the position of the piece we want to
        # add or remove.
        result = ''.join(['1' if i == index else '0' for i in range(len(list(lst)))])
        # If we want to add then return the 'or' of the two bitstrings or else
        # return the 'exclusive or ' of the two bitstrings to remove the piece.
        if add:
            return (int(lst,2) | int(result,2))
        return (int(lst,2)  ^ int(result,2))


    # Function that handles all the updates that happen on the board.
    def updateState(self, colour, action):
        # Store the move.
        self.last_move.append({
            "red":self.red['board'],
            "green":self.green['board'],
            "blue":self.blue['board']
        })

        # MOVE.
        if action[0] == "MOVE":
            self.getPlayer(colour)['board'] = self.move(self.getPlayer(colour)['board'], action[1][0],action[1][1])

        # JUMP.
        if action[0] == "JUMP":
            # Check if there's a piece in between the jumps.
            check = self.checkJumpOver(action[1])
            if check:
                # Check if the piece is an enemy piece.
                if (check[0] != colour):
                    # Flip the piece.
                    self.getPlayer(check[0])['board'] = self.addrmPiece(self.getPlayer(check[0])['board'],check[1])
                    self.getPlayer(colour)['board'] = self.addrmPiece(self.getPlayer(colour)['board'],check[1],True)
                    self.getPlayer(colour)['eaten'] += 1
                    self.getPlayer(check[0])['eaten'] -= 1
                # Update the jumped position.
                self.getPlayer(colour)['board'] = self.move(self.getPlayer(colour)['board'], action[1][0],action[1][1])

        # EXIT
        if action[0] == "EXIT":
            # Remove the piece from the board and update the player score.
            self.getPlayer(colour)['board'] = self.addrmPiece(self.getPlayer(colour)['board'],action[1])
            self.getPlayer(colour)['score'] += 1

        # Count the number of turns.
        self.turns += 1


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

    # Helper function that calculates the distance between two tiles.
    # Adapted from https://www.redblobgames.com/grids/hexagons.
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
        # Find all the available moves for the player.
        for move in self.state.availableMoves(self.colour):
            # Update the state, pass the modified state to minimax, then undo.
            self.state.updateState(self.colour, move)
            value = self.minimax(self.state, self.colour, 4, True, -sys.maxsize - 1, sys.maxsize)
            self.state.undo()

            # Give each state a score.
            result[move] = value

        # Return the move with the best score or return PASS if no move is
        # available.
        return max(result, key=result.get) if len(result) != 0 else ('PASS',None)

    # Minimax algorithm
    def minimax(self,state, colour, depth, maxPlayer, a, b):
        # Check if it is a terminal state .
        if state.winner():
            # Return max score if the player wins
            # or return minimum score other players win.
            if state.winner() == colour:
                return sys.maxsize
            else:
                return -sys.maxsize - 1

        # Evaluate the board if it reaches the maximum depth
        if depth == 0:
            return self.evaluateBoard(state, colour)

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

                # Update the alpha value
                a = max(a, best_value)
                # Ignore the branch if alpha is bigger than beta
                if b <= a:
                    break
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
                # Update the beta value
                b = min(b, best_value)
                # Ignore the branch if alpha is bigger than beta
                if b <= a:
                    break

            return best_value

    # The heuristic function used to evaluate the board
    def evaluateBoard(self, state, colour_i):
        # Initialise the score
        score = 0
        colours = ['red','green','blue']
        for colour in colours:
            if colour == colour_i:
                # Check the number of pieces the player has 
                piece = len([1 for i in list("{:049b}".format(state.getPlayer(colour)['board'])) if i == "1"])
                score += piece * 100
                score += state.getPlayer(colour)['score'] * 100000000
            else:
                score -= piece
                score -= state.getPlayer(colour)['score']

        return score


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
