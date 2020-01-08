#!/usr/bin/env python
# Software License Agreement (BSD License)
#
# Copyright (c) 2008, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Revision $Id$

## Simple talker demo that listens to std_msgs/Strings published 
## to the 'chatter' topic

import rospy
import serial
import time
from serial.tools import list_ports
from std_msgs.msg import String

ser = serial.Serial()
pub = rospy.Publisher('arduout', String, queue_size=100)

def init_serial():
    ports = [p.name for p in serial.tools.list_ports.comports()]
    if len(ports)>0:
        print('Available ports: ' + str(ports))
        ch = int(input("choose (0-"+str(len(ports)-1)+"):"))
        port = ports[ch]
        baudrate = int(input("baudrate:"))
        ser.baudrate = baudrate
        ser.port='/dev/'+port
        ser.open()
    else:
        rospy.logerr('No serial ports found')
        return False;
    if(ser.is_open):
        return True;
    else:
        rospy.logerr('port cannot be openned')
        return False;
        
def publish_from_serial(timer):
    string = ""
    while ser.in_waiting:
        string+=ser.readline()
    if(string!=""):
        pub.publish(string)

def write_to_serial(msg):
    rospy.loginfo(msg)
    ser.write(str(msg.data))
    
if __name__ == '__main__':
    rospy.init_node('serial', anonymous=True)
    if init_serial():
        rospy.Timer(rospy.Duration(0.1), publish_from_serial)
        rospy.Subscriber('arduin', String, write_to_serial)
        rospy.spin()
    else:
        rospy.logerr("serial failed to connect")
    ser.close()
