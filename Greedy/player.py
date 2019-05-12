import sys

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
        # TODO: Decide what action to take.

        #Find the closest piece to its closest goals
        pieces = []
        best_piece = None
        min_dist = sys.maxsize
        for piece in self.position:
            # Checks if any pieces are ready to exit board
            if piece in self.goals:
                return ('EXIT', piece)
            #find closest goal to given piece
            for goal in self.goals:
                dist = self.hex_distance(piece,goal)
                if dist < min_dist:
                    min_dist = dist
                    target_goal = goal
                    best_piece = piece

        #find best neighbour for given pieces
        # generate 6 directions
        min_dist = sys.maxsize
        for x in [-1,0,1]:
            for y in [-1,0,1]:
                if (abs(x+y) != 2) and (x,y) != (0,0) and best_piece:
                    # set the default action
                    action = "MOVE"
                    # calculate the coordinate for the successors
                    move = (x + best_piece[0] , y + best_piece[1])

                    # check if the successor is a piece
                    tile = self.state.findTile(move)
                    if tile:
                        # find the direction from the parent to the block successor
                        direction = (move[0] - best_piece[0], move[1] - best_piece[1])
                        # calculate the coordinate for the landing hex
                        move = (move[0] + direction[0], move[1] + direction[1])
                        action = "JUMP"
                        # check if the landing hex is also a block or piece
                        if self.state.findTile((move[0],move[1])):
                            continue
                    # check if the successor is within the board
                    ran = range(-3, +3+1)
                    hexes = {(q,r) for q in ran for r in ran if -q-r in ran}
                    if move in hexes:
                        dist = self.hex_distance(move, target_goal)
                        #the neighbour closest to the target goal
                        if dist < min_dist:
                            return (action, (best_piece, move))

        return ("PASS", None)


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


    def checkJumpOver(self, colour, coordinates):
        fstpoint = coordinates[0]
        sndpoint = coordinates[1]

        midtile = ((fstpoint[0] + sndpoint[0])/2,(fstpoint[1] +sndpoint[1])/2)

        tile = self.state.findTile(midtile)

        if tile:
            return (tile,midtile)
        return None

    # calculates distance
    def hex_distance(self,tile,other):
        return (abs(tile[0] - other[0]) +
                abs(tile[0] - other[0] + tile[1] - other[1]) +
                abs(tile[1] - other[1])) / 2
