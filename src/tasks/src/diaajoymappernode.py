#!/usr/bin/env python

# Revision $Id$

import rospy

from std_msgs.msg import String
from sensor_msgs.msg import Joy

pub = rospy.Publisher('arduin', String, queue_size=100)

def translate(value, leftMin, leftMax, rightMin, rightMax):
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin
    valueScaled = float(value - leftMin) / float(leftSpan)
    return rightMin + (valueScaled * rightSpan)

def yaw(ry):
    m=translate(ry, -1.0, 1.0, 1100, 1900);
    nm=translate(-ry, -1.0, 1.0, 1100, 1900);
    return [m,nm];

def forward(ly):
    m=translate(ly, -1.0, 1.0, 1100, 1900);
    return [m,m,m,m]

def rise(rt):
    m=translate(rt, 0, 1.0, 1500, 1900);
    return [m,m]
    
def fall(lt):
    m=translate(-lt, -1.0, 0, 1100, 1500);
    return [m,m]

def straffe(lx):
    m=translate(lx, -1.0, 1.0, 1100, 1900);
    nm=translate(-lx, -1.0, 1.0, 1100, 1900);
    return [m,nm,m,nm]

def rotate(rx):
    m=translate(rx, -1.0, 1.0, 1100, 1900);
    nm=translate(-rx, -1.0, 1.0, 1100, 1900);
    return [m,nm,nm,m]

def lateral(lx,ly,rx):
    lat_denom = abs(ly)+abs(lx)+abs(rx);
    if(lat_denom==0):
        lat=[1500,1500,1500,1500]
        print("lateral: "+ str(lat))
        return lat
    else:
        forw = [x * abs(ly)/lat_denom for x in forward(ly)]
        stra = [x * abs(lx)/lat_denom for x in straffe(lx)]
        rota = [x * abs(rx)/lat_denom for x in rotate(rx)]
        lat = [x+y+z for x,y,z in zip(forw,stra,rota)]
        print("forw: "+ str(forw))
        print("stra: "+ str(stra))
        print("rota: "+ str(rota))
        print("lateral: "+ str(lat))
        return lat

def vertical(lt, rt, ry):
    ver_denom = abs(lt)+abs(rt)+abs(ry);
    if(ver_denom==0):
        ver = [1500, 1500]
        print("vertical: "+ str(ver))
        return ver
    else:
        rise_v = [x * abs(rt)/ver_denom for x in rise(rt)]
        fall_v = [x * abs(lt)/ver_denom for x in fall(lt)]
        yaw_v = [x * abs(ry)/ver_denom for x in yaw(ry)] 
        ver = [x+y+z for x,y,z in zip(rise_v,fall_v,yaw_v)]
        print("rise: "+ str(rise_v))
        print("fall: "+ str(fall_v))
        print("yaw: "+ str(yaw_v))
        print("vertical: "+ str(ver))
        return ver

def map_axes(msg):
    axes = msg.axes
    lx = -axes[0]
    ly = axes[1]
    rx = -axes[2]
    ry = axes[3]
    rt = abs(axes[4]-1)/2
    lt = abs(axes[5]-1)/2 
    print("raw: "+str(axes))  
    lat = lateral(lx,ly,rx)
    ver = vertical(lt,rt,ry)
    val = lat + ver
    #val = map_motors(val)
    res = ""; 
    for i in range(6):
        res+=str(i)
        res+=":"
        res+=str(int(val[i]))
        res+=";"
    pub.publish(res)

if __name__ == '__main__':
    rospy.init_node('joymapper', anonymous=True)
    rospy.Subscriber('joy', Joy, map_axes)
    rospy.spin()
