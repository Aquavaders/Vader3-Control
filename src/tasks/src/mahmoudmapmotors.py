 #!/usr/bin/env python
    import rospy
    from std_msgs.msg import String
    from sensor_msgs.msg import Joy

    # Author: Andrew Dai
    # This ROS Node converts Joystick inputs from the joy node
    # into commands for turtlesim

    # Receives joystick messages (subscribed to Joy topic)
    # then converts the joysick inputs into Twist commands
    # axis 1 aka left stick vertical controls linear speed
    # axis 0 aka left stick horizonal controls angular speed

    #########################################################
    #                         4                             #         
    #                 0              1                      #            
    #                                                       #        
    #                                                       #         
    #                 3              2                      #         
    #                         5                             #      
    #                                                       #           
    #                                                       #      
    #                                                       #         
    #########################################################
    def callback(data):
        values = []
        x = data.axes[0];
        y = data.axes[1];
        if(x == 0):
            values.append(int(400*data.axes[1]+1500))
            values.append(int(400*data.axes[1]+1500))
            values.append(int(400*data.axes[1]+1500))
            values.append(int(400*data.axes[1]+1500))
            

        elif( y == 0):
            values.append(int(400*data.axes[0]+1500))
            values.append(int(400*data.axes[0]+1500))
            values.append(int(400*data.axes[0]+1500))
            values.append(int(400*data.axes[0]+1500))
        
        else:
            if(x>0): #up left , down left
                values.append(int(400*data.axes[0]+1500))
                values.append(int(1500))
                values.append(int(400*data.axes[0]+1500))
                values.append(int(1500))
            if(x<0): #up right, down right
                values.append(int(1500))
                values.append(int(400*data.axes[0]+1500))
                values.append(int(1500))
                values.append(int(400*data.axes[0]+1500))
             
        if(data.buttons[4]==1):
            values.append(int(1900))
        elif(data.buttons[5]==1):
            values.append(int(1100))
        if(data.buttons[6]==1):
            values.append(int(1900))
        elif(data.buttons[7]==1):
            values.append(int(1100))

        str = ""
        for value in values:
            str += string(value)+" "
        
        pub.publish(str)

    # Intializes everything
    def start():
        global pub
        pub = rospy.Publisher('joysticker', String)
        # subscribed to joystick inputs on topic "joy"
        rospy.Subscriber("joy", Joy, callback)
        # starts the node
        rospy.init_node('Joy2Turtle')
        rospy.spin()

    if __name__ == '__main__':
        start()
