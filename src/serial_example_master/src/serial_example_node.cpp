#include <ros/ros.h>
#include <stdio.h>
#include <sstream>
#include <math.h>
#include <serial/serial.h>
#include <std_msgs/String.h>
#include <std_msgs/Float64.h>
#include <std_msgs/Empty.h>



serial::Serial ser;
std_msgs::Float64 result;
bool flag = false;
char holder[10];


void write_callback(const std_msgs::Float64::ConstPtr& msg)
{	
    //ROS_INFO_STREAM("I'm in the callback function");
     if(ser.available())
    {
            //ROS_INFO_STREAM("Reading from serial port in callback func ");
            result.data = atof(ser.readline(65536, "\n").c_str());
            ROS_INFO_STREAM("Read from callback: " << result.data);
            ser.flush();
            // read_pub.publish(result);
    }

    // ser.write(reinterpret_cast<const uint8_t*>(&msg->data), 24);
    std::stringstream ss;
    ss<<(msg->data)<<"\n";

    ser.write(ss.str());
    ROS_INFO_STREAM("Writing to serial port " << ss.str());
    // ros::Duration(0.08).sleep();
    ser.flush();	

}

int main (int argc, char** argv){
    ros::init(argc, argv, "serial_example_node");
    ros::NodeHandle nh;
    ros::NodeHandle nh_priv("~");
    std::string port_name;
    port_name = "/dev/ttyACM0";
    nh_priv.getParam("param", port_name);
    // nh_priv.deleteParam("param");
    ROS_INFO("Got parameter : %s", port_name.c_str());
    ros::Publisher read_pub = nh.advertise<std_msgs::Float64>("state", 1000); 
    ros::Subscriber write_sub = nh.subscribe("comm_out", 1, write_callback);

    try
    {
        //ser.setPort("/dev/ttyUSB0");
        ser.setPort(port_name.c_str());
        ser.setBaudrate(57600);
        serial::Timeout to = serial::Timeout::simpleTimeout(1000);
        ser.setTimeout(to);
        ser.open();
    }
    catch (serial::IOException& e)
    {
        ROS_ERROR_STREAM("Unable to open port ");
        return -1;
    }

    if(ser.isOpen()){
        ROS_INFO_STREAM("Serial Port initialized");
    }else{
        return -1;
    }

    ros::Rate loop_rate(2000);
    while(ros::ok())
    {
        ros::spinOnce();

        if(ser.available())
        {
            ROS_INFO_STREAM("Reading from serial port");
            result.data = atof(ser.readline(65536, "\n").c_str());
            ROS_INFO_STREAM("Read: " << result.data);
            ser.flush();
            flag = true;
            if(result.data>180)result.data=result.data-360;
            result.data=result.data/180;
            read_pub.publish(result);
        }
        loop_rate.sleep();

    }
}

