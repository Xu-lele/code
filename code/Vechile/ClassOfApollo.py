import can
import time
import cantools

'''apollo notice                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     '''

#  message('Throttle_Command', 0x110, False, 8, {None: 'Vehicle open-loop control command: THROTTLE_PEDAL_CMD'}),
#  message('Brake_Command', 0x111, False, 8, {None: 'Vehicle open-loop control command: BRAKE_PEDAL_CMD'}),
#  message('Steer_Command', 0x112, False, 8, {None: 'Vehicle open-loop control command: STEER_ANGLE_CMD'}),
#  message('Turnsignal_Command', 0x113, False, 8, {None: 'Vehicle open-loop control command: TURN_SIGNAL_CMD'}),
#  message('Gear_Command', 0x114, False, 8, {None: 'Vehicle open-loop control command: GEAR_CMD'}),
#  message('Vehicle_Mode_Command', 0x116, False, 8, {None: 'Request VIN command: VIN_REQ_CMD'}),

# [message('WheelSpeed_Report', 0x51e, False, 8, {None: 'AGV status 4: Ultrasound status ext'}),
#  message('VIN_Resp3', 0x51d, False, 8, {None: 'VIN Respons: VIN01-VIN08'}),
#  message('VIN_Resp2', 0x51c, False, 8, {None: 'VIN Respons: VIN01-VIN08'}),
#  message('Throttle_Status_', 0x510, False, 8, {None: 'Vehicle open-loop control status: THROTTLE_PEDAL_STS'}),
#  message('Brake_Status_', 0x511, False, 8, {None: 'Vehicle open-loop control status: BRAKE_PEDAL_STS'}),
#  message('Steer_Status_', 0x512, False, 8, {None: 'Vehicle open-loop control status: STEER_ANGLE_STS'}),
#  message('Turnsignal_Status_', 0x513, False, 8, {None: 'Vehicle open-loop control status: TURN_SIGNAL_STS'}),
#  message('Gear_Status', 0x514, False, 8, {None: 'Vehicle open-loop control status: GEAR_STS'}),
#  message('ECU_Status_1', 0x515, False, 8, {None: 'AGV status 1: speed, accelerated speed, out of control, chassis status, chassis error code'}),
#  message('ECU_Status_2', 0x516, False, 8, {None: 'AGV status 2: BMS status'}),
#  message('VIN_Resp1', 0x51b, False, 8, {None: 'VIN Respons: VIN01-VIN08'})]

# 根据frame_id获取message
class Apollo:

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
        self._Throttle_Command = self._db.get_message_by_frame_id(0x110)

        self._Brake_Command = self._db.get_message_by_frame_id(0x111)

        self._Steer_Command = self._db.get_message_by_frame_id(0x112)

        self._Turnsignal_Command = self._db.get_message_by_frame_id(0x113)

        self._Gear_Command = self._db.get_message_by_frame_id(0x114)

        self._Control_Command = self._db.get_message_by_frame_id(0x116)

        self._init_self_driving_mode() # 初始化自动驾驶模式,必须保证所有的指令都发送默认值。此后才能开启自动驾驶模式

    def send_message(self,throttle_pedal_cmd = 0, brake_pedal_cmd = 0, steer_angle_cmd = 0, turn_signal_cmd = 0, gear_cmd = 1):
        """
        参数:
        throttle_pedal_cmd: 0-100%
        brake_pedal_cmd: 0-100%
        steer_angle_cmd: -0.524-0.524rad
        turn_signal_cmd: 0-3 0: None 1: Left 2: Right 3: Hazard
        gear_cmd: 1-4 1: Park 2: Reverse 3: Neutral 4: Drive
        """
        # 修改数据
        self._set_throttle(throttle_pedal_cmd)
        self._set_brake(brake_pedal_cmd)
        self._set_steer_angle(steer_angle_cmd)
        self._set_turn_signal(turn_signal_cmd, low_beam_cmd = 1)
        self._set_gear(gear_cmd)


    # def recv(self):
    #     # 创建数据列表
    #     data_list = [0, 0, 0, 0, 0, 0,]

    #     # 循环接收can数据
    #     for i in range(0, 1000) :
        
    #         message = self._can_bus.recv()tle_Command_raw)
    #             data_list[3] = self._db.decode_message(message.arbitration_id, message.data)
    #         if(message.arbitration_id == self._Gear_Command.frame_id):
    #             data_list[4] = self._db.decode_message(message.arbitration_id, message.data)
    #         if(message.arbitration_id == self._Control_Command.frame_id):
    #             data_list[5] = self._db.decode_message(message.arbitration_id, message.data)

    #         print(data_list)

    def _init_self_driving_mode(self):

        # 构建初始的二进制数据
        #  [signal('THROTTLE_PEDAL_EN_CTRL', 0, 8, 'little_endian', False, None, 1, 0, 0, 1, 'None', False, None, {1: 'ENABLE', 0: 'DISABLE'}, None, {None: 'throttle pedal enable bit(Command)'}),
        #  signal('THROTTLE_PEDAL_CMD', 8, 8, 'little_endian', False, None, 1, 0, 0, 100, '%', False, None, None, None, {None: 'Percentage of throttle pedal(Command)'})]
        self._Throttle_Command_raw = self._Throttle_Command.encode({'THROTTLE_PEDAL_EN_CTRL': 0, 'THROTTLE_PEDAL_CMD': 0,})
        
        # [signal('BRAKE_PEDAL_EN_CTRL', 0, 8, 'little_endian', False, None, 1, 0, 0, 1, 'None', False, None, {1: 'ENABLE', 0: 'DISABLE'}, None, {None: 'brake pedal enable bit(Command)'}),
        # signal('BRAKE_PEDAL_CMD', 8, 8, 'little_endian', False, None, 1, 0, 0, 100, '%', False, None, None, None, {None: 'Percentage of brake pedal(Command)'})]
        self._Brake_Command_raw = self._Brake_Command.encode({'BRAKE_PEDAL_EN_CTRL': 0, 'BRAKE_PEDAL_CMD': 0,})

        # [signal('STEER_ANGLE_EN_CTRL', 0, 8, 'little_endian', False, None, 1, 0, 0, 1, 'None', False, None, {1: 'ENABLE', 0: 'DISABLE'}, None, {None: 'steering angle enable bit(Command)'}),
        #  signal('STEER_ANGLE_CMD', 8, 16, 'little_endian', True, None, 0.001, 0, -0.524, 0.524, 'radian', False, None, None, None, {None: 'Current steering angle(Command)'})]
        self._Steer_Command_raw = self._Steer_Command.encode({'STEER_ANGLE_EN_CTRL': 0, 'STEER_ANGLE_CMD': 0,})

        # [signal('TURN_SIGNAL_CMD', 0, 8, 'little_endian', False, None, 1, 0, 0, 2, 'None', False, None, {3: 'Hazard_Warning_Lampsts', 2: 'RIGHT', 1: 'LEFT', 0: 'NONE'}, None, {None: 'Lighting control(Command)'}),
        # signal('LOW_BEAM_CMD', 8, 2, 'little_endian', False, None, 1, 0, 0, 2, 'None', False, None, {1: 'ON', 0: 'OFF'}, None, {None: 'Lighting control(Command)'})]
        self._Turnsignal_Command_raw = self._Turnsignal_Command.encode({'TURN_SIGNAL_CMD': 0, 'LOW_BEAM_CMD': 0})
                
        # [signal('GEAR_CMD', 0, 8, 'little_endian', False, None, 1, 0, 1, 4, 'None', False, None, {4: 'DRIVE', 3: 'NEUTRAL', 2: 'REVERSE', 1: 'PARK'}, None, {None: 'PRND control(Command)'})] 
        self._Gear_Command_raw = self._Gear_Command.encode({'GEAR_CMD': 1,})

        #[signal('VIN_REQ_CMD', 0, 1, 'little_endian', False, None, 1, 0, 0, 1, 'None', False, None, {1: 'VIN_req_enable', 0: 'VIN_req_disable'}, None, {None: 'Request VIN(Command)'})]
        self._Control_Command_raw = self._Control_Command.encode({'VIN_REQ_CMD': 1,})

        # 通过初始的报文数据
        self._Throttle_Command_message = can.Message(arbitration_id=self._Throttle_Command.frame_id, data=self._Throttle_Command_raw, extended_id=False)

        self._Brake_Command_message = can.Message(arbitration_id=self._Brake_Command.frame_id, data=self._Brake_Command_raw, extended_id=False)

        self._Steer_Command_message = can.Message(arbitration_id=self._Steer_Command.frame_id, data=self._Steer_Command_raw, extended_id=False)

        self._Turnsignal_Command_message = can.Message(arbitration_id=self._Turnsignal_Command.frame_id, data=self._Turnsignal_Command_raw, extended_id=False)
        
        self._Gear_Command_message = can.Message(arbitration_id=self._Gear_Command.frame_id, data=self._Gear_Command_raw, extended_id=False)
        
        self._Control_Command_message = can.Message(arbitration_id=self._Control_Command.frame_id, data=self._Control_Command_raw, extended_id=False)

        # 循环发送报文数据
        self._throttle_task = self._can_bus.send_periodic(msg=self._Throttle_Command_message, period=0.02)

        self._brak_task = self._can_bus.send_periodic(msg=self._Brake_Command_message, period=0.02)

        self._steer_task = self._can_bus.send_periodic(msg=self._Steer_Command_message, period=0.02)

        self._turnsignal_task = self._can_bus.send_periodic(msg=self._Turnsignal_Command_message, period=0.02)

        self._gear_task = self._can_bus.send_periodic(msg=self._Gear_Command_message, period=0.02)

        self._control_task = self._can_bus.send_periodic(msg=self._Control_Command_message, period=0.02)

        time.sleep(1)



    def enable_self_driving(self):
        # 进入自动驾驶模式
        self.send_message()
        # self._set_throttle(0)
        # self._set_brake(0)
        # self._set_steer_angle(0)
        # self._set_turn_signal(turn_signal_cmd=0,low_beam_cmd=1)
        # self._set_gear(1)

    def disable_self_driving(self):
        # 退出自动驾驶模式
        self.send_message(brake_pedal_cmd=50)#先刹车制动
        time.sleep(1)
        self.send_message(brake_pedal_cmd=0)
        time.sleep(0.2) #解除刹车并且回到初始值
        #close low beam light 再让速度disable，并且速度为0
        self._Turnsignal_Command_raw = self._Turnsignal_Command.encode({'TURN_SIGNAL_CMD': 0, 'LOW_BEAM_CMD': 0})
        self._Turnsignal_Command_message = can.Message(arbitration_id=self._Turnsignal_Command.frame_id, data=self._Turnsignal_Command_raw, extended_id=False)
        self._turnsignal_task.modify_data(self._Turnsignal_Command_message)
        
        self._Throttle_Command_raw = self._Throttle_Command.encode({'THROTTLE_PEDAL_EN_CTRL': 0, 'THROTTLE_PEDAL_CMD': 0,})
        self._Throttle_Command_message = can.Message(arbitration_id=self._Throttle_Command.frame_id, data=self._Throttle_Command_raw)
        self._throttle_task.modify_data(self._Throttle_Command_message)

    def shutdown(self):
        self.disable_self_driving()
         # 关闭can总线
        self._can_bus.shutdown()


    def _set_throttle(self,throttle_pedal_cmd):
        # 构建初始的二进制数据
        #  [signal('THROTTLE_PEDAL_EN_CTRL', 0, 8, 'little_endian', False, None, 1, 0, 0, 1, 'None', False, None, {1: 'ENABLE', 0: 'DISABLE'}, None, {None: 'throttle pedal enable bit(Command)'}),
        #  signal('THROTTLE_PEDAL_CMD', 8, 8, 'little_endian', False, None, 1, 0, 0, 100, '%', False, None, None, None, {None: 'Percentage of throttle pedal(Command)'})]
        self._Throttle_Command_raw = self._Throttle_Command.encode({'THROTTLE_PEDAL_EN_CTRL': 1, 'THROTTLE_PEDAL_CMD': throttle_pedal_cmd,})
        self._Throttle_Command_message = can.Message(arbitration_id=self._Throttle_Command.frame_id, data=self._Throttle_Command_raw, extended_id=False)
        self._throttle_task.modify_data(self._Throttle_Command_message)

    def _set_brake(self,brake_pedal_cmd):
        self._Brake_Command_raw = self._Brake_Command.encode({'BRAKE_PEDAL_EN_CTRL': 1, 'BRAKE_PEDAL_CMD': brake_pedal_cmd,})
        self._Brake_Command_message = can.Message(arbitration_id=self._Brake_Command.frame_id, data=self._Brake_Command_raw, extended_id=False)
        self._brak_task.modify_data(self._Brake_Command_message)   

    def _set_steer_angle(self,steer_angle_cmd):
        self._Steer_Command_raw = self._Steer_Command.encode({'STEER_ANGLE_EN_CTRL': 1, 'STEER_ANGLE_CMD': steer_angle_cmd,})
        self._Steer_Command_message = can.Message(arbitration_id=self._Steer_Command.frame_id, data=self._Steer_Command_raw, extended_id=False)
        self._steer_task.modify_data(self._Steer_Command_message)

    def _set_turn_signal(self,turn_signal_cmd, low_beam_cmd):
        self._Turnsignal_Command_raw = self._Turnsignal_Command.encode({'TURN_SIGNAL_CMD': turn_signal_cmd, 'LOW_BEAM_CMD': low_beam_cmd})
        self._Turnsignal_Command_message = can.Message(arbitration_id=self._Turnsignal_Command.frame_id, data=self._Turnsignal_Command_raw, extended_id=False)
        self._turnsignal_task.modify_data(self._Turnsignal_Command_message)

    def _set_gear(self,gear_cmd):
        self._Gear_Command_raw = self._Gear_Command.encode({'GEAR_CMD': gear_cmd,})
        self._Gear_Command_message = can.Message(arbitration_id=self._Gear_Command.frame_id, data=self._Gear_Command_raw, extended_id=False)
        self._gear_task.modify_data(self._Gear_Command_message)

