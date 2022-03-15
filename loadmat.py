# import scipy.io as sio
# import numpy as np
# a = sio.loadmat('next_hop.mat')
# b = sio.loadmat('matrix_state.mat')
# print(a.shape)
# a.popitem()
# print a
# sio.savemat('next_hop1.mat', {''})
# print(self.C)
# sio.savemat('matrix.mat', {'C':self.C})
# self.matrix = sio.loadmat('matrix.mat')
# self.matrix = self.matrix['C'].reshape(-1,7,9,1)
# from tensorflow.keras.models import load_model
# trained = load_model('trained.h5')
# print(trained)
from datetime import datetime
start = datetime.now()
a = 10 + 20
end = datetime.now()
print(end-start)


