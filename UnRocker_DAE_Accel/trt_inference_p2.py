#!/usr/bin/env python

# USAGE
# python train_conv_autoencoder.py

# set the matplotlib backend so figures can be saved in the background
import matplotlib
matplotlib.use("Agg")

# import the necessary packages
import matplotlib.pyplot as plt
import numpy as np
import argparse
import cv2
import socket
import errno
import sys
#import fdpexpect
import signal
import struct
import pexpect
import time
import select
import threading
import ctypes
import multiprocessing
import os
#from threading import Thread
from multiprocessing import Process, Queue, Value, Array
from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink2
from pymavlink.dialects.v20 import custom_messages as mavlink3

EPOCHS = 25
BS = 32
LENGTH = 256#1024#512#1024#128
DIALECT = 'custom'
time_log = 0
global return_value, pr_com

#os.environ['MAVLINK_DIALECT'] = 'custom_messages'
#os.environ['MAVLINK20'] = '1'
#os.environ['MDEF'] = '~/src_SITL_NeuroSensor/Firmware/mavlink/include/mavlink/v2.0/message_definitions'
#out_file = open('inference_time.txt', 'w')

#mavutil.set_dialect(DIALECT)

def interpret_address(addrstr):
    """Interpret a IP:port string."""
    a = addrstr.split(':')
    a[1] = int(a[1])
    return tuple(a)

def tonumpyarray(mp_arr):
    return np.frombuffer(mp_arr.get_obj())


def process_com(v_start, v_end, v_copy, v_trigger, v_inf_first, a_input, a_output, v_re_tr):
    
   # inf_out_address = interpret_address("127.0.0.1:9009")
   # inf_in_address = interpret_address("127.0.0.1:9010")
   # inf_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   # inf_in.bind(inf_in_address)
   # inf_in.setblocking(0) 
   # inf_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   # inf_out.connect(inf_out_address)
   # inf_out.setblocking(0)
#    inf_in = mavutil.mavlink_connection('/dev/ttyACM0', dialect = DIALECT)
   
    inf_in = mavutil.mavlink_connection('udpin:localhost:14548', dialect = DIALECT)
    #inf_in = mavutil.mavlink_connection('udpin:localhost:18570', dialect = DIALECT)
    inf_in.wait_heartbeat()
    print("Heartbeat from system (system %u component %u)" % (inf_in.target_system, inf_in.target_component))
    #inf_out = mavutil.mavlink_connection('udpout:localhost:14640', dialect = DIALECT)
    #inf_out.wait_heartbeat()
    #print("Heartbeat from system (system %u component %u)" % (inf_out.target_system, inf_out.target_component))

    recv_count = 0
    time_log = 0
    r_value = 0
#    attack_elapsed = 0
    
    input_dataset = np.empty(LENGTH)
    result_data = np.empty(LENGTH)

    print('p_com: process com started')
    inf_in.mav.request_data_stream_send(inf_in.target_system, inf_in.target_component, mavutil.mavlink.MAV_DATA_STREAM_ALL, 400, 1)

#    inf_in.mav.heartbeat_send(
#	    mavutil.mavlink.MAV_TYPE_ONBOARD_CONTROLLER,
#	    mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0)
	


#    try:
#        temp = inf_in.messages['DNN_SEND'].attack_trigger
#    except:
#        print('Nothing')

    while True:
        start_time = time.process_time()
    #    rin = [inf_in.fileno()]
    #    try:
    #        (rin, win, xin) = select.select(rin, [], [], 1.0)
    #    except select.error:
    #        util.check_parent()
    #        continue

    #    try: 
    #        v_trigger.value = the_connection.messages['DNN_SEND'].attack_trigger
    #        raw_signal = the_connection.messages['DNN_SEND'].compromised_signal
    #    except:
    #        print('No DNN_SEND message received')
 #       msg_temp = inf_in.recv_match(type='GPS_RAW_INT',blocking=True, timeout=1)
  #      print('GPS_RAW_INT received %d' % msg_temp.lat)
        msg = inf_in.recv_match(type='DNN_SEND',blocking=True, timeout=1)
 #       print('DNN Received')
     #   print('DNN_SEND received %d' % msg.attack_trigger)

        if not msg:
            print("Nothing")
#            time.sleep(3)

#            inf_in = mavutil.mavlink_connection('udpin:localhost:14540', dialect = DIALECT)
#            inf_in.wait_heartbeat()
#            print("Heartbeat from system (system %u component %u)" % (inf_in.target_system, inf_in.target_component))
            #inf_out = mavutil.mavlink_connection('udpout:localhost:14640', dialect = DIALECT)
        #    inf_out.wait_heartbeat()
         #   print("Heartbeat from system (system %u component %u)" % (inf_out.target_system, inf_out.target_component))

#            recv_count = 0
#            time_log = 0
        #    attack_elapsed = 0
    
#            input_dataset = np.empty(LENGTH)
#            result_data = np.empty(LENGTH)

#            print('p_com: process com started')
#            inf_in.mav.request_data_stream_send(inf_in.target_system, inf_in.target_component, mavutil.mavlink.MAV_DATA_STREAM_ALL, 400, 1)


            v_re_tr.value = -1
            return
        if msg.get_type() == "BAD_DATA":
            print("Bad data")
            if mavutil.all_printable(msg.data):
                sys.stdout.write(msg.data)
                sys.stdout.flush()
        else:
  #          print('DNN_SEND: %s %d' % (msg.compromised_signal, msg.attack_trigger))
            v_trigger.value = msg.attack_trigger
            raw_signal = msg.compromised_signal

            if(v_trigger.value == 1):#initialize the input array
                if recv_count < LENGTH:
                    input_dataset[recv_count] = raw_signal
                    recv_count = recv_count + 1
                    if recv_count == LENGTH:
                        if (v_start.value == 0) and (v_end.value == 0):
                            a_input[:] = input_dataset[:]
                            v_start.value = 1
                    recovered = raw_signal
                else:
                    v_start.value = 1
                    input_dataset[0:LENGTH-1] = input_dataset[1:LENGTH] 
                    input_dataset[LENGTH-1] = raw_signal
                    recv_count = LENGTH *2#recv_count + 1
                    if v_inf_first.value == 0:
                        recovered = raw_signal
                    else:
                        if v_end.value == 1:# and v_copy.value == 0:
                            temp_count2 = 0
                            result_data = np.frombuffer(a_output.get_obj())
                            a_input[:] = input_dataset[:]
                            v_end.value = 0
                            time_log = 1
                        recovered = result_data[LENGTH+temp_count2-20]
                        temp_count2 = temp_count2 + 1
                        temp_count2 = temp_count2%20#limit max index
            else:
                recovered = raw_signal
                v_start.value = 0
###################must be implemented
#            send_buf = mavlink3.MAVLink_dnn_recv_message(recovered)
#            send_buf.pack(inf_out)
            inf_in.mav.dnn_recv_send(recovered)
#            print('DNN_RECV: %f, %d' %(recovered, temp_count2))

            #write(send_buf.pack)
      #      try:
      #          inf_out.send(send_buf)
      #      except socket.error as e:
      #          if e.errno not in [errno.ECONNREFUSED]:
      #              raise
#############################################3
        end_time =time.process_time()
        if(time_log == 1):
###            print('p_com: com_processing time:', (end_time-start_time))
            time_log = 0
        #out_file.write('com_processing time: %f\n' %(end_time-start_time))

#
def process_com_inf(v_start, v_end, v_copy, v_trigger, v_inf_first, a_input, a_output):
    com_out_address = interpret_address("127.0.0.1:9011")
    com_in_address = interpret_address("127.0.0.1:9012")
    com_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    com_in.bind(com_in_address)
    com_in.setblocking(0) 
    com_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    com_out.connect(com_out_address)
    com_out.setblocking(0)

    com_out_buf = bytes()
#    com_in_buf = bytes()
#    print('process inf started')

    print('p_inf: process com inf started')

    while True:

        if (v_start.value == 1) and (v_end.value == 0):
            #print('p_inf: inference ing..')

            start_time = time.process_time()
            com_out_buf = struct.pack('f', a_input[0])

            for i in range(LENGTH-1):
                com_out_buf += struct.pack('f', a_input[i+1])

            try:
                com_out.send(com_out_buf)
            except socket.error as e:
                if e.errno not in [errno.ECONNREFUSED]:
                    raise
                
            rin = [com_in.fileno()]
            try:
                (rin, win, xin) = select.select(rin, [], [], 1.0)
            
            except select.error:
                util.check_parent()
                continue
            if com_in.fileno() in rin:
#                print('p_inf: Recieved Recovered Data')
                com_in_buf = com_in.recv(LENGTH*4)
                temp = struct.unpack('f'*LENGTH, com_in_buf)##
                for i in range(LENGTH):##
                    a_output[i] = temp[i]#struct.unpack('f', com_out_buf)##
                v_end.value = 1##
                end_time =time.process_time()##
#            print('p_inf: inference ended')
                v_inf_first.value = 1##
#            print('Input/output Data', a_input[0], a_output[0],temp[0])
#            print('p_inf: inf processing time:', (end_time-start_time))#, v_trigger.value, v_start.value, v_end.value)

def process_restart(v_re_tr, pr_com):
    print("Restart Process Run")
    while True:
        time.sleep(2)
        print("%d" % v_re_tr.value)
        if v_re_tr.value == -1:
            print("Restart Pr com")

            pr_com.terminate()
            time.sleep(3)
            pr_com.start()
            pr_com.join()


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


#valX = np.expand_dims(valX, axis=-1)
#valY = np.expand_dims(valY, axis=-1)


print("[INFO] making predictions...")


#jsjeong inference socket


#for i in range(0, 25):
#	N = np.arange(0, LENGTH)
#	index_n = i
#	#subplot_id = 661+i
#	plt.figure()#subplot(5,5,i+1)
#	plt.style.use("ggplot")
#	plt.plot(N, valX[index_n], label="input_data")
#	plt.plot(N, valY[index_n], label="true_data")
#	plt.plot(N, decoded2[index_n], label="decoded_data")
#	plt.title("Original & recovered data")
#	plt.xlabel("Times")
#	plt.ylabel("Value")
#	plt.ylim((-1,2))
#	plt.legend(loc="lower left")
#	graph = "./eval_results/graph_eval%d" %i
#	plt.savefig(graph)#args["graph"])# %i])



#plt.figure()
#for i in range(0, 25):
#	N = np.arange(0, LENGTH)
#	index_n = i
#	plt.subplot(5,5,i+1)
##	plt.style.use("ggplot")
#	plt.plot(N, valX[index_n], label="input_data")
#	plt.plot(N, valY[index_n], label="true_data")
#	plt.plot(N, decoded2[index_n], label="decoded_data")
#	plt.ylim((-1,2))
#graph = "./eval_results/graph_sum_eval"
#plt.savefig(graph)#args["graph"])# %i])


def main_loop():
    """Run main loop."""
   
    v_start = Value('i', 0)
    v_end = Value('i', 0)
    v_copy = Value('i', 0)

    v_trigger = Value('i', 0)
    v_inf_first = Value('i', 0)
    
    v_re_tr = Value('i',0)
    
    a_input = Array("d",LENGTH)#(c.c_float, 1024)
    a_output = Array("d",LENGTH)#(c.c_float, 1024)

    pr_list = []
    return_value = 0
    print('Start Main loop')

#    process_inf(v_start,v_end,v_trigger,v_inf_first,a_input,a_output)

    pr_com = Process(target=process_com, args=(v_start,v_end,v_copy,v_trigger,v_inf_first,a_input,a_output,v_re_tr))
    pr_inf = Process(target=process_com_inf, args=(v_start,v_end,v_copy,v_trigger,v_inf_first,a_input,a_output))

    pr_com.daemon = True
    pr_inf.daemon = True

    pr_list.append(pr_com)
    pr_list.append(pr_inf)

    pr_com.start()
    pr_inf.start()
    pr_com.join()
    pr_inf.join()

#    print("Restart Process Run")
#    while True:
#        time.sleep(5)
#        print("Restart Flag : %d" % v_re_tr.value)
#        if v_re_tr.value == -1:
#            print("Restart Pr com")
#            v_re_tr.value = 0
#            pr_com.terminate()
#            time.sleep(3)
#            pr_com = Process(target=process_com, args=(v_start,v_end,v_copy,v_trigger,v_inf_first,a_input,a_output,v_re_tr))
#            pr_com.daemon = True
#            pr_list.append(pr_com)
#            pr_com.start()
#            pr_com.join()


def exit_handler():
    """Exit the sim."""
    print("running exit handler")
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    #out_file.close()
    # JSBSim really doesn't like to die ...
#    if getattr(jsb, 'pid', None) is not None:
#        os.kill(jsb.pid, signal.SIGKILL)
#    jsb_console.send('quit\n')
#    jsb.close(force=True)
    ##util.pexpect_close_all()
    sys.exit(1)

signal.signal(signal.SIGINT, exit_handler)
signal.signal(signal.SIGTERM, exit_handler)

#if __name__=='__main__':
#    multiprocessing.set_start_method('spawn')
#    multiprocessing.set_start_method('forkserver', force=True)

try:
    main_loop()
except Exception as ex:
    print(ex)
    exit_handler()
    raise


