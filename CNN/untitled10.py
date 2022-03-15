import scipy.io as sio
from scipy.sparse import vstack
import numpy as np
# import matplotlib.pyplot as plt
# from tensorflow import keras
# import keras
# from tensorflow.keras import models
# from tensorflow.keras.models import Model, Sequential
# from tensorflow.keras.layers import Dense, Activation, Input
# from tensorflow.keras.optimizers import Adam, SGD, Nadam, RMSprop
# from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dropout
# from tensorflow.keras.regularizers import l2
# from tensorflow.keras import callbacks
# from sklearn.preprocessing import MinMaxScaler
# from sklearn import preprocessing
# from tensorflow.keras.callbacks import ModelCheckpoint, ReduceLROnPlateau, CSVLogger, EarlyStopping
# from tensorflow.keras.models import load_model
# from sklearn.model_selection import train_test_split
# from tensorflow.keras.utils import to_categorical
## from tensorflow.keras.layers.advanced_activations import LeakyReLU

x_data=sio.loadmat('/home/hasti/ryu_project/ryu_controller_notes/matrix_state_9.mat')
f = x_data['z']
print(f.shape)
# f1 = x_data1['z']
# f2 = x_data2['z']
# f_concat1 = vstack([f, f1]).toarray()
# f1 = np.delete(f, np.s_[:210], axis=0)
# sio.savemat('/home/hasti/Desktop/data_set/matrix_state9.mat', {'f1':f1})
# print(f.shape)

y_data=sio.loadmat('/home/hasti/ryu_project/ryu_controller_notes/next_hop_9.mat')
pr = y_data['w']
print(pr.shape)
print(f.max())

# pr1 = np.delete(pr, np.s_[:210], axis=0)
# sio.savemat('/home/hasti/Desktop/data_set/next_hop9.mat', {'pr1':pr1})

# trained = load_model('trained.h5')
