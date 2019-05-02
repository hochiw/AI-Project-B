import numpy as np
import json
    
dic = {}
def save(arr):
    count = 0
    for i in arr:
        np.savetxt('layer-{0}.txt'.format(count),i.weights)
        count += 1

