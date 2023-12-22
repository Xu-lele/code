import can
import time
import cantools



# 根据frame_id获取message
class Yunle:

    def __init__(self, dbc_file):
        try:
            # 加载dbc文件
            self._db = cantools.db.load_file(dbc_file)
        except Exception as e:
            print(f"加载文件失败: {e},请检查文件路径是否正确")
            exit(0)

        try:
            # 创建can总线
            self._can_bus = can.interface.Bus(channel = 'can0', bustype='socketcan', bitrate = 500000)
        except Exception as e:
            print(f"创建can总线失败: {e},请检查1.通道是否正确 2.比特率是否正确 3.是否有权限 4.是否有其他程序占用can")
            exit(0)

        # 通过帧id获取解析报文的格式
        self._Control_Command = self._db.get_message_by_frame_id(0x120)

        self._init_self_driving_mode(self)


    def send_message(self,shiftlevel_req,scu_acc_mode, scu_brake_mode, scu_steering_wheel_angle, scu_target_speed):

        """
        参数:
        SCU_ACC_Mode: 0-3 0: None 1: 加速1档 2: 加速2档 3: 加速3档
        SCU_Brake_Mode: 0-3 0: None 1: 制动1档 2: 制动2档 3: 制动3档
        SCU_Steering_Wheel_Angle: -3276.8-3276.7
        SCU_Target_Speed: 0-51m/s
        SCU_ShiftLevel_Req:    
        SCU_Drive_Mode_Req: 0: None 1: 自动驾驶模式请求 2: 驾驶员-PAD模式请求 3: 驾驶员-方向盘模式请求
        SCU_Brk_En: 0: None 1: 紧急制动

        #转向灯用不到,先不配置
        GW_Left_Turn_Light_Req: 0-3 0: None 1: Left 2: Right 3: Hazard
        GW_Right_Turn_Light_Req: 0-3 0: None 1: Left 2: Right 3: Hazard
        GW_Hazard_Light_Req: 0-3 0: None 1: Left 2: Right 3: Hazard
        GW_Position_Light_Req: 0-3 0: None 1: Left 2: Right 3: Hazard
        GW_LowBeam_Req: 0-3 0: None 1: Left 2: Right 3: Hazard
        GW_HighBeam_Req: 0-3 0: None 1: Left 2: Right 3: Hazard
        GW_RearFogLight_Req: 0-3 0: None 1: Left 2: Right 3: Hazard
        GW_Horn_Req: 0-3 0: None 1: Left 2: Right 3: Hazard
        """

        self._Control_Command_task.modify_data({'SCU_ShiftLevel_Req': shiftlevel_req,'SCU_Target_Speed': scu_target_speed, 'SCU_ACC_Mode': scu_acc_mode, 'SCU_Brake_Mode': scu_brake_mode, 'SCU_Steering_Wheel_Angle': scu_steering_wheel_angle})
        

    def emergency_brake(self):
        # 紧急制动
        self._Control_Command_task.modify_data({'SCU_Brk_En': 1})
    
    def dismiss_emergency_brake(self):
        # 取消紧急制动
        self._Control_Command_task.modify_data({'SCU_Brk_En': 0})

    def disable_self_driving(self):
        # 退出自动驾驶模式
        self._Control_Command_task.modify_data({'SCU_Drive_Mode_Req': 0})

    def enable_self_driving(self):
        # 进入自动驾驶模式
        self._Control_Command_task.modify_data({'SCU_Drive_Mode_Req': 1})

    def shutdown(self):
         # 关闭can总线

        self._can_bus.shutdown()

    def _init_self_driving_mode(self):

        # 构建初始的二进制数据
        self._Control_Command_raw = self._Control_Command.encode({'SCU_Brk_En': 1, 'SCU_Drive_Mode_Req': 1, 'SCU_ShiftLevel_Req' : 0, 'SCU_ACC_Mode': 0, 'SCU_Brake_Mode': 0, 'SCU_Steering_Wheel_Angle': 2000, 'SCU_Target_Speed': 0, 'GW_Left_Turn_Light_Req': 0, 'GW_Right_Turn_Light_Req': 0, 'GW_Hazard_Light_Req': 0, 'GW_Position_Light_Req': 0, 'GW_LowBeam_Req': 0, 'GW_HighBeam_Req': 0, 'GW_RearFogLight_Req': 0, 'GW_Horn_Req': 0})


        # 通过初始的报文数据
        self._Control_Command_message = can.Message(arbitration_id=self._Control_Command.frame_id, data=self._Control_Command_raw)

        # 循环发送报文数据
        self._Control_Command_task = self._can_bus.send_periodic(msg=self._Control_Command_message, period=0.05)

        time.sleep(2)

        self._Control_Command_task.modify_data({'SCU_Steering_Wheel_Angle': -2000})

        time.sleep(2)

        self._Control_Command_task.modify_data({'SCU_Steering_Wheel_Angle': 0})


    #接收消息,有机会再弄
    # def recv(self):
    #     # 创建数据列表
    #     data_list = [0, 0, 0, 0, 0, 0,]

    #     # 循环接收can数据
    #     for i in range(0, 1000) :
        
    #         message = self._can_bus.recv()

    #         if(message.arbitration_id == self._Throttle_Command.frame_id):
    #             data_list[0] = self._db.decode_message(message.arbitration_id, message.data)
    #         if(message.arbitration_id == self._Brake_Command.frame_id):
    #             data_list[1] = self._db.decode_message(message.arbitration_id, message.data)
    #         if(message.arbitration_id == self._Steer_Command.frame_id):    
    #             data_list[2] = self._db.decode_message(message.arbitration_id, message.data)
    #         if(message.arbitration_id == self._Turnsignal_Command.frame_id):
    #             data_list[3] = self._db.decode_message(message.arbitration_id, message.data)
    #         if(message.arbitration_id == self._Gear_Command.frame_id):
    #             data_list[4] = self._db.decode_message(message.arbitration_id, message.data)
    #         if(message.arbitration_id == self._Control_Command.frame_id):
    #             data_list[5] = self._db.decode_message(message.arbitration_id, message.data)

    #         print(data_list)