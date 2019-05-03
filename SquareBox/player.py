import numpy as np
import SquareBox.Logger as Logger
import os
from copy import deepcopy
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
        self.turns = 0
        

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

    def boardToArray(self,state):
        r = state.red['positions']
        g = state.green['positions']
        b = state.blue['positions']
        
        arr = []
        for i in range(-3,4):
            for j in range(-3,4):
                if -i-j in range(-3,4):
                    if (i,j) in r:
                        arr.append(1)
                    elif (i,j) in g:
                        arr.append(2)
                    elif (i,j) in b:
                        arr.append(3)
                    else:
                        arr.append(0)
        return arr

class NeuralNetwork:
    
    def __init__(self):
        self.layers = []

    def add_layer(self,layer):
        self.layers.append(layer)

    def feed_forward(self, x):
        for layer in self.layers:
            x = layer.activate(x)
        return x

    def backprop(self, x, y, learning_rate):
        result = self.feed_forward(x)

        for i in reversed(range(len(self.layers))):
            layer = self.layers[i]

            if layer == self.layers[-1]:
                layer.error = y - result
                layer.delta = layer.error * layer.activate_i(result,True)
            else:
                layer_i = self.layers[i+1]
                layer.error = np.dot(layer_i.weights,layer_i.delta)
                layer.delta = layer.error * layer.activate_i(layer.last_act,True)

        for i in range(len(self.layers)):
            layer = self.layers[i]
            inp = np.atleast_2d(x)
            if i != 0:
              inp = np.atleast_2d(self.layers[i - 1].last_act)
            layer.weights += layer.delta * inp.T * learning_rate

    def predict(self, x):
        result = self.feed_forward(x)
        return np.argmax(result)

    def train(self, x,y,learning_rate,epochs):
        for i in range(epochs):
            for j in range(len(x)):
                self.backprop(x[j],y[j],learning_rate)

    def accurarcy(self,y_pred, y_true):
        return (y_pred == y_true).mean()
            
            
    
class Layer:

    def __init__(self,numInput,numNodes, activation=None,weights=None, bias = None):
        
        if not weights:
            self.weights = np.random.rand(numInput,numNodes)
        else:
            self.weights = weights

        if not bias:
            self.bias = np.random.rand(numNodes)
        else:
            self.bias = bias

        self.activation = activation
        self.last_act = None
        self.error = None
        self.delta = None

    def tanh(x,deriv = False):
        if deriv:
            return 1 - x ** 2
        return np.tanh(x)

    def sigmoid(x,deriv = False):
        if deriv:
            return x * (1 - x)
        return 1/(1+np.exp(-x))

    def reLu(x,deriv = False):
        if deriv:
            return np.greater(x,0).astype(int)
        return np.maximum(0,x)

    def activate(self,x):
        dt = np.dot(x,self.weights) + self.bias
        self.last_act = self.activate_i(dt)
        return self.last_act
                                                        
    def activate_i(self,x,deriv = False):
        
        if not self.activation:
            return x

        if self.activation == "sigmoid":
            return Layer.sigmoid(x,deriv)

        if self.activation == "relu":
            return Layer.reLu(x,deriv)

        if self.activation == "tanh":
            return Layer.tanh(x,deriv)
        return x

    
            
    
    
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
        self.last_move = None
        self.goals = self.state.getPlayer(colour)['goals']

        self.nn = NeuralNetwork()
        self.nn.add_layer(Layer(37,500, 'sigmoid'))
        self.nn.add_layer(Layer(500,500, 'sigmoid'))
        self.nn.add_layer(Layer(500,250, 'sigmoid'))
        self.nn.add_layer(Layer(250,150, 'sigmoid'))
        self.nn.add_layer(Layer(150,75, 'sigmoid'))
        self.nn.add_layer(Layer(75,38, 'sigmoid'))
        self.nn.add_layer(Layer(38,19, 'sigmoid'))
        self.nn.add_layer(Layer(19,10, 'sigmoid'))
        self.nn.add_layer(Layer(10,5, 'sigmoid'))
        self.nn.add_layer(Layer(5,3, 'relu'))

        if all([os.path.isfile('./layer-{0}.txt'.format(i)) for i in range(len(self.nn.layers))]):
            for i in range(len(self.nn.layers)):
                self.nn.layers[i].weights = np.loadtxt('layer-{0}.txt'.format(i))
        

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
        evalu = {}
        if len(self.state.getPlayer(self.colour)['positions']) == 0:
            return ('PASS',None)
        
        for piece in self.state.getPlayer(self.colour)['positions']:
            if len(self.availableMoves(piece)) == 0:
                continue
            for move in self.availableMoves(piece):
                tmp_state = deepcopy(self.state)
                if move[0] != "EXIT" and move[0] != "PASS":
                    tmp_state.getPlayer(self.colour)['positions'].remove(move[1][0])
                    tmp_state.getPlayer(self.colour)['positions'].append(move[1][1])

                    if any([i in self.goals for i in tmp_state.getPlayer(self.colour)['positions']]):
                        self.nn.backprop(self.state.boardToArray(tmp_state),2,0.25)
                        
                    if self.last_move:
                        if (move[1][1] == self.last_move[1][0]):
                            self.nn.backprop(self.state.boardToArray(tmp_state),0,0.5)
                else:
                    tmp_state.getPlayer(self.colour)['positions'].remove(move[1])
                evalu[move] = self.nn.predict(self.state.boardToArray(tmp_state))

        largest = max(evalu,key=evalu.get)
        self.last_move = largest

        # TODO: Decide what action to take.
        return largest
    


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

                if (check[0] == self.colour and colour != self.colour):
                    self.nn.backprop(self.state.boardToArray(self.state), 0, 0.25)
                elif (check[0] != self.colour and colour == self.colour):
                    self.nn.backprop(self.state.boardToArray(self.state), 2, 0.5)
                    
                
                # Update the jumped position
                self.state.getPlayer(colour)['positions'].remove(action[1][0])
                self.state.getPlayer(colour)['positions'].append(action[1][1])

        if action[0] == "EXIT":
            # Remove the piece from the board and update the player score
            self.state.getPlayer(colour)['positions'].remove(action[1])
            self.state.getPlayer(colour)['score'] += 1

            # Train weight
            if colour == self.colour:
                self.nn.backprop(self.state.boardToArray(self.state), 2, 0.5)
            else:
                self.nn.backprop(self.state.boardToArray(self.state), 0, 0.25)
            Logger.save(self.nn.layers)
            
        self.state.turns += 1
        

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
        
        if (x,y) in self.goals:
            result.append(("EXIT",(int(x),int(y))))
            return result
        
        # Range adapted from game.py
        ran = range(-3, +3+1)
        hexes = {(q,r) for q in ran for r in ran if -q-r in ran}
        directions = [(-1,0),(0,-1),(1,-1),(1,0),(0,1),(-1,1)]
        for (a,b) in directions:
            if (x+a,y+b) in hexes and not self.state.findTile((x+a,y+b)):
                result.append(("MOVE",((x,y), (int(x+a),int(y+b)))))
            elif (x+2*a,y+2*b) in hexes and not self.state.findTile((x+2*a,y+2*b)):
                result.append(("JUMP",((x,y), (int(x+2*a),int(y+2*b)))))

        if not any(result):
            result.append(("PASS",None))
        

                        
        return result

            
            
        

            

        
