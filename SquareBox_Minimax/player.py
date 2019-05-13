import sys

# Bitboards that represent the vertical mask
_VERTICAL = [int(283691315109952/(2 ** i)) for i in range(7)]
# Bitboards that represent the horizontal mask
_HORIZONTAL = [127 * (128 ** i) for i in range(7)]

_LAST_MOVE = []
class GameState:

    # Initialise the game state.
    def __init__(self):

        self.boards = {
            "red":int("0000000000000000000001000000100000010000001000000",2),
            "green":int("0001111000000000000000000000000000000000000000000",2),
            "blue":int("0000000000000000000000000001000001000001000001000",2)
        }

        self.goals = {
            "red":{(3,-3), (3,-2), (3,-1), (3,0)},
            "green":{(-3,3), (-2,3), (-1,3), (0,3)},
            "blue":{(-3,0),(-2,-1),(-1,-2),(0,-3)}
        }

        self.scores = {
            "red":0,
            "green":0,
            "blue":0
        }

        self.exits = {
            "red":0,
            "green":0,
            "blue":0
        }

        self.weights = [1,0.2,0.2]

    # Function that converts coordinate to bitboard index.
    def coorToBitboard(self,q,r):
        # Checks if the coordinate is in range.
        if (self.isValidMove((q,r))):
            return int((r+3)*7 + (q+3))
        return None

    # Function that converts bitboard index to coordinate.
    def bitboardToCoor(self,index):
        return ((index % 7) - 3,int(index/7) -3)


    # Function that gets all the pieces on the board
    def getPositions(self, colour):
        result = []

        # Check if there is a piece on a column
        for i in range(len(_VERTICAL)):
            # Skip the column if there's no piece
            if (_VERTICAL[i] & self.boards[colour]) == 0:
                continue
            # Check the rows if there's a piece on a column
            for j in range(len(_HORIZONTAL)):
                if (_HORIZONTAL[j] & self.boards[colour] & _VERTICAL[i]) == 0:
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
        if (self.boards["red"] & mask) != 0:
            return "red"
        if (self.boards["green"] & mask) != 0:
            return "green"
        if (self.boards["blue"] & mask) != 0:
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
            if (x,y) in self.goals[colour]:
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
        x = coor[0]
        y = coor[1]
        if -3 > x or x > 3:
            return False
        if -3 > y or y > 3:
            return False
        if -3 > -x-y or -x-y > 3:
            return False
        return True


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
            tmp = 0
            if len(self.getPositions(colour)) != 0:
                result += self.scores[colour]
                result += self.exits[colour]
                #result -= (self.weights[i] * self.aveDist(colour))

            # Make it negative if it's an enemy
            if colour != colour_i:
                tmp = -tmp

            result += tmp
        return result



     #Calculates the average distance of pieces of a colour to
    #their respective closest goal
    def aveDist(self, colour):
        ave_dist = 0
        #Iterate self pieces and for each piece get min dist then sum all
        for piece in self.getPositions(colour):
            min_dist = sys.maxsize
            for goal in self.goals[colour]:
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

        score = 0
        score_e = 0

        # MOVE.
        if action[0] == "MOVE":
            self.boards[colour] = self.move(self.boards[colour], action[1][0],action[1][1])
            score -= 5
        # JUMP.
        if action[0] == "JUMP":
            # Check if there's a piece in between the jumps.
            check = self.checkJumpOver(action[1])
            if check:
                # Check if the piece is an enemy piece.
                if (check[0] != colour):
                    # Flip the piece.
                    self.boards[check[0]] = self.addrmPiece(self.boards[check[0]],check[1])
                    self.boards[colour] = self.addrmPiece(self.boards[colour],check[1],True)
                    score_e -= 1
                    score += 1
                    self.scores[check[0]] = score_e

                # Update the jumped position.
                score += 1
                self.boards[colour] = self.move(self.boards[colour], action[1][0],action[1][1])


        # EXIT
        if action[0] == "EXIT":
            # Remove the piece from the board and update the player score.
            self.boards[colour] = self.addrmPiece(self.boards[colour],action[1])
            self.exits[colour] += 1
            score += 100

        self.scores[colour] = score

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
            self.saveState(self.state)
            self.state.updateState(self.colour, move)
            value = self.minimax(self.state, self.colour, 3, True, -sys.maxsize - 1, sys.maxsize)
            self.loadState(self.state)


            # Give each state a score.
            result[move] = value
        # Return the move with the best score or return PASS if no move is
        # available.
        print(result)
        return max(result, key=result.get) if len(result) != 0 else ('PASS',None)

    # Minimax algorithm
    def minimax(self, state, colour, depth, maxPlayer, a, b):

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
                self.saveState(state)
                state.updateState(move[1],move[0])
                value = self.minimax(state, colour, depth - 1, False, a, b)
                self.loadState(state)
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
                self.saveState(state)
                state.updateState(move[1],move[0])
                value = self.minimax(state, colour, depth - 1, True, a, b)
                self.loadState(state)
                # Compare the best value and the value it gets from minimax
                best_value = min(best_value, value)

                # Ignore the branch if alpha is bigger than beta
                if best_value <= a:
                    break

                # Update the beta value
                b = min(b, best_value)

            return best_value

    # Save and load states
    def saveState(self,state):
        # Store the move.
        _LAST_MOVE.append({
            "boards":{"red":state.boards['red'],"green":state.boards['green'],"blue":state.boards['blue']},
            "scores":{"red":state.scores['red'],"green":state.scores['green'],"blue":state.scores['blue']},
            "exits":{"red":state.exits['red'],"green":state.exits['green'],"blue":state.exits['blue']},
        })



    def loadState(self,state):
        dic = _LAST_MOVE.pop()
        state.boards = dic['boards']
        state.scores = dic['scores']
        state.exits = dic['exits']



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
