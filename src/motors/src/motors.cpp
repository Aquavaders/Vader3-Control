#include "ros/ros.h"
#include <sensor_msgs/Joy.h>
#include <sensor_msgs/JoyFeedbackArray.h>
#include "std_msgs/String.h"
#include <iostream>
#include <math.h>
#include "std_msgs/Float64.h"
#include <sstream>
#include <chrono>
#include <algorithm>
#define REPLACE_ME_WITH_REAL_VALUE 1500

#define min(a,b) (a<b? (a):(b))

sensor_msgs::Joy msg;
std_msgs::String out;
ros::Publisher* pub;
int pid=0,f=0;
float x=0.0;

void chatterCallback(const sensor_msgs::Joy::ConstPtr& in)
{
  	f=1;
	msg=*in;
}

int main(int argc, char **argv)
{
  ros::init(argc, argv, "motor");
  ros::NodeHandle n;
  ros:: Rate rate(100);

  ros::Publisher chatter_pub = n.advertise<std_msgs::String>("comm_out", 1000);
  pub=&chatter_pub;

  ros::Subscriber sub = n.subscribe("joy", 1000, chatterCallback);
  while(ros::ok()){

    //ROS_INFO("%d", f);
    if(f){
    	double 
    		axis1 = msg.axes[REPLACE_ME_WITH_REAL_VALUE], //delta X
    		axis2 = msg.axes[REPLACE_ME_WITH_REAL_VALUE], //delta Z
    		axis3 = msg.axes[REPLACE_ME_WITH_REAL_VALUE], //delta y
    		axis4 = msg.axes[REPLACE_ME_WITH_REAL_VALUE], //delta Motor_Line 2 and 3
    		axis5 = msg.axes[REPLACE_ME_WITH_REAL_VALUE]; //delta Motor_Line 1


/*to do:
  handele the rotation
*/
    	int 
    		pwm1 = (axis3 + ((axis3+1) * axis5)/2)* 400 + 500, //Motor_Line 1
    		pwm2 = ((
	 				(axis1-axis2)/2)
    				+(
    					(((axis1-axis2)/2)+1) * axis4
					 )/2
    												)* 400 + 500 , //Motor_Line 2
    		pwm3 = ((
	 				(axis1+axis2)/2)
    				+(
    					(((axis1+axis2)/2)+1) * axis4
					 )/2
    												)* 400 + 500 , //Motor_Line 3
    		pwm4 = (axis3 - ((1 - axis3) * axis5)/2)* 400  + 500 , //Motor_Line 1
    		pwm5 = ((
	 				(axis1-axis2)/2)
    				+(
    					((1-(axis1-axis2)/2)) * axis4
					 )/2
    												)* 400 + 500 , //Motor_Line 2
    		pwm6 = ((
	 				(axis1+axis2)/2)
    				+(
    					((1 -(axis1+axis2)/2)) * axis4
					 )/2
    												)* 400 + 500 ; //Motor_Line 3


    	std::stringstream ss;
     	ss<<"A"<<pwm1<<"B"<<pwm2<<"C"<<pwm3<<"D"<<pwm4<<"E"<<pwm5<<"F"<<pwm6<<"Z";
      	out.data=ss.str();
      	ROS_INFO("%s", out.data);
      	pub->publish(out);
      /*-----------------------------------------------------------------------------------------
      bool direction0, direction1;
      double value0, value1, h0, h1;
      direction0=1;
      direction1=1;
      h0=(msg.axes[1])*255.0;
      h1=(msg.axes[3])*255.0;
      value0=min(h0+h1/2,255);
      value1=min(h0-h1/2,255);
      if(value0<0||value0==-0)direction0=0,value0*=-1;
      if(value1<0||value1==-0)direction1=0,value1*=-1;




      int flags=0,pwm0=0,pwm1=0;
      flags|=(direction0? 1<<7:0);
      flags|=(!direction1? 1<<6:0);
      flags|=(msg.buttons[11]? 1<<5:0);
      flags|=(msg.buttons[12]? 1<<4:0);
      flags|=(!msg.buttons[4]? 1<<3:0);
      flags|=(!msg.buttons[6]? 1<<2:0);
      flags|=(!msg.buttons[5]? 1<<1:0);
      flags|=(!msg.buttons[7]? 1<<0:0);
      pwm0=(int)value0;
      pwm1=(int)value1;

      char send[3];
      send[0]=flags;
      send[1]=pwm1;
      send[2]=pwm0;
      std::stringstream ss;
      ss<<flags<<" "<<pwm1<<" "<<pwm0;
      out.data=ss.str();
      ROS_INFO("%s", out.data);
      pub->publish(out);
      -----------------------------------------------------------------------------------------*/
  	}
    ros::spinOnce();
    rate.sleep();
  }

  //ros::spin();
  return 0;
}
