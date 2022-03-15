# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

#import tensorflow as tf
import scipy.io
import numpy as np
import matplotlib.pyplot as plt
from keras import models
from keras.models import Model, Sequential
from keras.layers import Dense, Activation, Input
from keras.optimizers import Adam, SGD, Nadam, RMSprop
from keras.layers import Conv2D, MaxPooling2D, Flatten, Dropout
from keras.regularizers import l2
from keras import callbacks
from sklearn.preprocessing import MinMaxScaler
from sklearn import preprocessing
from keras.callbacks import ModelCheckpoint, ReduceLROnPlateau, CSVLogger, EarlyStopping
from keras.models import load_model
from sklearn.model_selection import train_test_split
from keras.models import load_model
from keras.utils import to_categorical
##classifier=load_model('classifier_300m_7n_5s.h5')
## from tensorflow.keras.layers.advanced_activations import LeakyReLU
#
x_data=scipy.io.loadmat(r'matrix_state.mat')
f = x_data['z']
#f[:, 0:4, :] = f[:, 0:4,:] / f.max()
#f = np.expand_dims(f, -1)

y_data=scipy.io.loadmat(r'next_hop.mat')
#pr = y_data['w']

x_data=x_data['z'].reshape(8343,6,9)
y_data=y_data['w'].reshape(8343,11)
#y_data=y_data[:-1,:]
#y = np.load('y.npy')
#y_data = to_categorical(y)

#normalize data
f[:,:3] = f[:,:3] / f.max()



x_train, x_test, y_train, y_test=train_test_split(f, y_data, test_size=0.2, shuffle=True)

##Data preprocessing
x_train=x_train.reshape(-1,6,9,1)
x_test=x_test.reshape(-1,6,9,1)
x_train.shape, x_test.shape

x_train=x_train.astype('float32')
x_test=x_test.astype('float32')

#print(x_train.shape, x_test.shape, y_train.shape, y_test.shape)

# Initialising the CNN
classifier = Sequential()

# Step 1 - Convolution
classifier.add(Conv2D(32, kernel_size=(3, 3), input_shape = (6,9,1), activation = 'relu', padding='same'))
classifier.add(MaxPooling2D((2,2), padding='same'))
classifier.add(Conv2D(64, kernel_size=(3, 3), activation = 'relu', padding='same'))
classifier.add(MaxPooling2D((2,2), padding='same'))
classifier.add(Dropout(0.1))
classifier.add(Conv2D(64, (3,3), activation='relu', padding='same'))
#classifier.add(MaxPooling2D(pool_size=(2,2), padding='same'))
#classifier.add(Dropout(0.15))
classifier.add(Conv2D(128, (3,3), activation='relu', padding='same'))
#classifier.add(MaxPooling2D(pool_size=(2,2), padding='same'))
#classifier.add(Dropout(0.2))
classifier.add(Conv2D(256, (3,3), activation='relu', padding='same'))
#classifier.add(MaxPooling2D(pool_size=(2,2), padding='same'))
#classifier.add(Dropout(0.2))

# Step 3 - Flattening
classifier.add(Flatten())
#
# Step 4 - Full connection
classifier.add(Dense(units = 128, activation = 'relu'))
classifier.add(Dropout(0.3))
classifier.add(Dense(units = 11, activation = 'softmax'))

# Compiling the CNN
classifier.compile(optimizer = 'Adam', loss = 'categorical_crossentropy', metrics = ['accuracy'])

import datetime
start=datetime.datetime.now()
history = classifier.fit(x_train, y_train,
                                  batch_size=128,
                                  epochs=80,
                                  verbose=1, 
                                  validation_split=0.2,
                                  shuffle=True)
end=datetime.datetime.now()
classifier.save('trained.h5')
##trained = load_model('trained.h5')
##
#start=datetime.datetime.now()
#trained.predict(x_test)
#end=datetime.datetime.now()
#elapse=end-start
#print(elapse)
#
#b = x_data[]
print(classifier.summary())

print(history.history.keys())


test_eval=classifier.evaluate(x_test, y_test, verbose=1)

print('Test loss: ', test_eval[0])
print('Test accuracy: ', test_eval[1])

#accuracy=history.history['accuracy']
#val_accuracy=history.history['val_accuracy']
#loss=history.history['loss']
#val_loss=history.history['val_loss']
#epochs=range(len(accuracy))
#plt.plot(epochs, accuracy, 'k', label='Training accuracy')
#plt.plot(epochs, val_accuracy, 'b', label='Validation accuracy')
#plt.plot('Training and validation accuracy')
#plt.legend()
#plt.figure()
#plt.plot(epochs, loss, 'bo', label='Training loss')
#plt.plot(epochs, val_loss, 'b', label='Validation loss')
#plt.plot('Training and validation loss')
#plt.legend()
#plt.show()

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
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train','validation'],loc='upper left')
plt.show()


#Test
#test_model = load_model('C:\\Users\\Sharif\\Desktop\\trained.h5')
#predictions = test_model.predict(x_test)
#img = load_img('D:/Kaggle_data/MNIST/Test/img_110.jpg',False,target_size=(img_width,img_height))
#x = img_to_array(img)
#x = np.expand_dims(x, axis=0)
#preds = test_model.predict_classes(x)
#prob = test_model.predict_proba(x)
#print(preds, prob)
