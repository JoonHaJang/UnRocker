# USAGE
# python train_conv_autoencoder.py

# set the matplotlib backend so figures can be saved in the background
import matplotlib
matplotlib.use("Agg")

# import the necessary packages
from pyimagesearch.convautoencoder_1D import ConvAutoencoder_1D
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.datasets import mnist
import matplotlib.pyplot as plt
import numpy as np
import argparse
import cv2
import time
from tensorflow.compat.v1.keras.experimental import export_saved_model 
import tensorflow as tf
import math

config = tf.compat.v1.ConfigProto()
config.gpu_options.allow_growth = True
config.gpu_options.per_process_gpu_memory_fraction =0.8

session = tf.compat.v1.Session(config=config)
out_file = open('inference_test.txt', 'w')


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-s", "--samples", type=int, default=8,
	help="# number of samples to visualize when decoding")
ap.add_argument("-o", "--output", type=str, default="output.png",
	help="path to output visualization file")
ap.add_argument("-p", "--plot", type=str, default="plot.png",
	help="path to output plot file")
args = vars(ap.parse_args())

# initialize the number of epochs to train for and batch size
EPOCHS = 25
BS = 32
LENGTH = 256

(valX, valY, input_min, input_max, input_median, data_min, data_max, data_median, testset_h) = ConvAutoencoder_1D.file_load_test()
data_range = (data_max - data_min)
input_range = (input_max - input_min)

valX = np.expand_dims(valX, axis=-1)
valY = np.expand_dims(valY, axis=-1)


print("[INFO] making predictions...")

##
(eval_encoder, eval_decoder, eval_model) = ConvAutoencoder_1D.build(LENGTH)

eval_model.load_weights('./checkpoints_IRIS_x/my_checkpoint')
recovered = eval_model.predict(valX)
reference  = (valY-0.5) * data_range + data_median
compromised = (valX-0.5) * input_range + input_median
recovery = (recovered-0.5) * data_range + data_median

error_sum = np.empty((2,testset_h))
result1 = 0
result2 = 0
for i in range(0, testset_h):
	error_sum[0][i] = recovery[i][255] - reference[i][255] 
	error_sum[1][i] = compromised[i][255] - reference[i][255]
	out_file.write('Results : %f, %f, %f\n' %(recovery[i][255], compromised[i][255], reference[i][255]))


for i in range(0, testset_h):
	result1 = result1 + error_sum[0][i]*error_sum[0][i]
	result2 = result2 + error_sum[1][i]*error_sum[1][i]

result1 = result1 / testset_h
result2 = result2 / testset_h
sigma1 = math.sqrt(result1)
sigma2 = math.sqrt(result2)
print("Error results %f, %f" % (sigma1, sigma2))


plt.figure()
for i in range(0, 25):
	N = np.arange(0, LENGTH)
	index_n = i
	plt.subplot(5,5,i+1)
	plt.plot(N, valX[index_n], label="input_data")
	plt.plot(N, valY[index_n], label="true_data")
	plt.plot(N, recovered[index_n], label="decoded_data")
	plt.ylim((-1,2))
graph = "./test_results/graph_sum_eval"
plt.savefig(graph)
out_file.close()

