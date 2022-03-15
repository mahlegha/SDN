import tensorflow as tf
import scipy.io as sio
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.utils import plot_model
from tensorflow.keras import models
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import Dense, Activation, Input
from tensorflow.keras.optimizers import Adam, SGD, Nadam, RMSprop
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dropout
from tensorflow.keras.regularizers import l2
from tensorflow.keras import callbacks
from sklearn.preprocessing import MinMaxScaler
from sklearn import preprocessing
from tensorflow.keras.callbacks import ModelCheckpoint, ReduceLROnPlateau, CSVLogger, EarlyStopping
from tensorflow.keras.models import load_model
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import load_model
from tensorflow.keras.utils import to_categorical

x_data=sio.loadmat('matrix_state_9.mat')
f = x_data['z']
print(f.shape)

y_data=sio.loadmat('next_hop_9.mat')

x_data=x_data['z'].reshape(13181,7,9)
y_data=y_data['w'].reshape(13181,10)

print(f.max())
print(f.min())

# normalize data
f[:,0:4] = f[:,0:4] / 50.0

x_train, x_test, y_train, y_test=train_test_split(f, y_data, test_size=0.1, shuffle=True)

# Data preprocessing
x_train=x_train.reshape(-1,7,9,1)
x_test=x_test.reshape(-1,7,9,1)
x_train.shape, x_test.shape

x_train=x_train.astype('float32')
x_test=x_test.astype('float32')

# Initialising the CNN
classifier = Sequential()

# Step 1 - Convolution
classifier.add(Conv2D(8, kernel_size=(3, 3), input_shape = (7,9,1), activation = 'relu', padding='same'))
# classifier.add(MaxPooling2D((2,2), padding='same'))
classifier.add(Dropout(0.2))
# classifier.add(Conv2D(64, kernel_size=(3, 3), activation = 'relu', padding='same'))
# # # #classifier.add(MaxPooling2D((2,2), padding='same'))
# classifier.add(Dropout(0.3))
# classifier.add(Conv2D(128, (3,3), activation='relu', padding='same'))
# #classifier.add(MaxPooling2D(pool_size=(2,2), padding='same'))
# classifier.add(Dropout(0.15))
# classifier.add(Conv2D(128, (3,3), activation='relu', padding='same'))
# # #classifier.add(MaxPooling2D(pool_size=(2,2), padding='same'))
# classifier.add(Dropout(0.2))
# classifier.add(Conv2D(256, (3,3), activation='relu', padding='same'))
#classifier.add(MaxPooling2D(pool_size=(2,2), padding='same'))
#classifier.add(Dropout(0.2))

# Step 3 - Flattening
classifier.add(Flatten())

# Step 4 - Full connection
classifier.add(Dense(units = 16, activation = 'relu'))
# classifier.add(Dropout(0.3))
classifier.add(Dense(units = 32, activation = 'relu'))
classifier.add(Dropout(0.2))
classifier.add(Dense(units = 32, activation = 'relu'))
# classifier.add(Dropout(0.2))
# classifier.add(Dense(units = 128, activation = 'relu'))
classifier.add(Dense(units = 10, activation = 'softmax'))

# Compiling the CNN
classifier.compile(optimizer = 'Adam', loss = 'categorical_crossentropy', metrics = ['accuracy'])

import datetime
start=datetime.datetime.now()
history = classifier.fit(x_train, y_train,
                                 batch_size=128,
                                 epochs=120,
                                 verbose=1, 
                                 validation_split=0.2,
                                 shuffle=True)
end=datetime.datetime.now()
classifier.save('trained_16.h5')

print(classifier.summary())
plot_model(classifier, to_file='model_plot.png', show_shapes=True, show_layer_names=True)

print(history.history.keys())

plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Train and validation loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train','validation'],loc='upper left')
plt.show()

plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('Train and validation accuracy')
plt.ylabel('accuracy')
plt.xlabel('epoch')
plt.legend(['train','validation'],loc='upper left')
plt.show()