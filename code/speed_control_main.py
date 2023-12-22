import ClassOfApollo
import ClassOfPix
import ClassOfYunle

# Create an instance of ClassOfApollo

pix_dbc_file = 'dbc/Pix.dbc'
yunle_dbc_file = 'dbc/Yunle.dbc'
apollo_dbc_file = 'dbc/Apollo.dbc'

pix = ClassOfPix.Pix(pix_dbc_file)
apollo = ClassOfApollo.Apollo(apollo_dbc_file)
yunle = ClassOfYunle.Yunle(yunle_dbc_file)











def recommand_throttle_cmd(yaw, roll, pitch, 车速):
    # 离散数据表
    data_table = {

         # (yaw, roll, pitch, 车速): 油门开度 
        (0, 0, 0, 5): 10, 
        (0, 0, 0, 10): 20,
        (0, 0, 0, 15): 30,
        (0, 0, 0, 20): 40,
        (0, 0, 0, 25): 50
        # 添加更多的数据...
        
    }

    def find_nearest_speed(pose1, pose2, pose3, speed):
        # 初始化最小差值和对应的车速
        min_difference = float('inf')
        nearest_speed = None

        # 遍历数据表
        for key in data_table:
            # 计算姿态和车速之间的差值
            pose_difference1 = abs(key[0] - pose1)
            pose_difference2 = abs(key[1] - pose2)
            pose_difference3 = abs(key[2] - pose3)
            speed_difference = abs(key[3] - speed) 
            speed_factor = 0.1

            # 计算总差值
            total_difference = pose_difference1 + pose_difference2 + pose_difference3 + speed_difference*speed_factor

            # 如果总差值更小，则更新最小差值和对应的车速
            if total_difference < min_difference:
                min_difference = total_difference
                nearest_speed = data_table[key]

        return nearest_speed


# PID controller parameters
kp = 0.5  # Proportional gain
ki = 0.1  # Integral gain
kd = 0.2  # Derivative gain

# Variables for PID controller
error_sum = 0
prev_error = 0

def throttle_control(self,throttle_pedal_cmd, current_speed, target_speed, vehicle_pose):

    """throttle_pedal_cmd: 0-100"""

    # Calculate error
    error = target_speed - current_speed

    # Update error sum
    error_sum += error

    # Calculate PID controller output
    pid_output = kp * error + ki * error_sum + kd * (error - prev_error)

    # Update previous error
    prev_error = error

    recommand_throttle_cmd = recommand_throttle_cmd()

    # Send throttle command
    self.apollo.send_throttle_command(THROTTLE_PEDAL_CMD = recommand_throttle_cmd + pid_output)

