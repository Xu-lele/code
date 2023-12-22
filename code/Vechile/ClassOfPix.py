import can
import time
import cantools

# [message('V2A_DriveStaFb', 0x530, False, 8, {None: '³µÁ¾Çý¶¯×´Ì¬·´À¡'}),
#  message('V2A_BrakeStaFb', 0x531, False, 8, {None: '³µÁ¾ÖÆ¶¯×´Ì¬·´À¡'}),
#  message('V2A_SteerStaFb', 0x532, False, 8, {None: '³µÁ¾×ªÏò×´Ì¬·´À¡'}),
#  message('V2A_VehicleWorkStaFb', 0x534, False, 8, {None: '³µÁ¾¹¤×÷×´Ì¬·´À¡'}),
#  message('V2A_PowerStaFb', 0x535, False, 8, {None: '³µÁ¾¶¯Á¦µçÔ´×´Ì¬·´À¡'}),
#  message('V2A_VehicleStaFb', 0x536, False, 8, {None: '³µÁ¾³µÉí¼°µÆ¹â·´À¡'}),
#  message('V2A_VehicleFltSta', 0x537, False, 8, {None: '³µÁ¾¾¯¸æºÍ¹ÊÕÏ'}),
#  message('V2A_ChassisWheelRpmFb', 0x539, False, 8, {None: '³µÂÖ×ªËÙ·´À¡'}),
#  message('V2A_ChassisWheelTorqueFb', 0x542, False, 8, {None: '³µÂÖÅ¤¾Ø·´À¡'}),


#  message('A2V_DriveCtrl', 0x130, False, 8, {None: 'Çý¶¯¿ØÖÆ±¨ÎÄ'}),
#  message('A2V_BrakeCtrl', 0x131, False, 8, {None: 'ÖÆ¶¯¿ØÖÆ±¨ÎÄ'}),
#  message('A2V_SteerCtrl', 0x132, False, 8, {None: '×ªÏò¿ØÖÆ±¨ÎÄ'}),
#  message('A2V_VehicleCtrl', 0x133, False, 8, {None: '³µÉí¿ØÖÆ1'}),
#  message('A2V_WheelTorqueCtrl', 0x135, False, 8, {None: 'µç»úµ¥¶À¿ØÖÆ(Ô¤Áô)'})]

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
            pass
            # 创建can总线
            self._can_bus = can.interface.Bus(channel = 'can0', bustype='socketcan', bitrate = 500000)
        except Exception as e:
            print(f"创建can总线失败: {e},请检查1.通道是否正确 2.比特率是否正确 3.是否有权限 4.是否有其他程序占用can")
            exit(0)

        # 通过帧id获取解析报文的格式
        self._Drive_Command = self._db.get_message_by_frame_id(0x130)

        self._Brake_Command = self._db.get_message_by_frame_id(0x131)

        self._Steer_Command = self._db.get_message_by_frame_id(0x132)

        self._VehicleCtrl = self._db.get_message_by_frame_id(0x133)

        self._WheelTorqueCtrl = self._db.get_message_by_frame_id(0x135)

        self._init_self_driving_mode(self)

    def send_message(self,drive_pedal_cmd,brake_pedal_cmd,steer_angle_cmd,turn_signal_cmd, gear_cmd):
        """
        参数:
        drive_pedal_cmd: 0-100%
        brake_pedal_cmd: 0-100%
        steer_angle_cmd: -0.524-0.524rad
        turn_signal_cmd: 0-3 0: None 1: Left 2: Right 3: Hazard
        gear_cmd: 0-4 0: None 1: Park 2: Reverse 3: Neutral 4: Drive
        """
        # 修改数据
        self._set_drive(self,drive_pedal_cmd)
        self._set_brake(self,brake_pedal_cmd)
        self._set_steer_angle(self,steer_angle_cmd)
        self._set_turn_signal(self,turn_signal_cmd)
        self._set_gear(self,gear_cmd)


    def disable_self_driving(self):
        # 退出自动驾驶模式
        self._control_task.modify_data({'VIN_REQ_CMD': 0})

    def enable_self_driving(self):
        # 进入自动驾驶模式
        self._control_task.modify_data({'VIN_REQ_CMD': 1})

    def shutdown(self):
         # 关闭can总线

        self._can_bus.shutdown()

    def recv(self):
        # 创建数据列表
        data_list = [0, 0, 0, 0, 0, 0,]

        # 循环接收can数据
        for i in range(0, 1000) :
        
            message = self._can_bus.recv()

            if(message.arbitration_id == self._Drive_Command.frame_id):
                data_list[0] = self._db.decode_message(message.arbitration_id, message.data)
            if(message.arbitration_id == self._Brake_Command.frame_id):
                data_list[1] = self._db.decode_message(message.arbitration_id, message.data)
            if(message.arbitration_id == self._Steer_Command.frame_id):    
                data_list[2] = self._db.decode_message(message.arbitration_id, message.data)
            if(message.arbitration_id == self._Turnsignal_Command.frame_id):
                data_list[3] = self._db.decode_message(message.arbitration_id, message.data)
            if(message.arbitration_id == self._Gear_Command.frame_id):
                data_list[4] = self._db.decode_message(message.arbitration_id, message.data)
            if(message.arbitration_id == self._Control_Command.frame_id):
                data_list[5] = self._db.decode_message(message.arbitration_id, message.data)

            print(data_list)

    def _init_self_driving_mode(self):

        # 构建初始的二进制数据
        # [signal('ACU_ChassisDriverEnCtrl', 0, 1, 'little_endian', False, None, 1, 0, 0, 1, 'None', False, None, {0: 'disable', 1: 'enable'}, None, {None: '³µÁ¾Çý¶¯¿ØÖÆÊ¹ÄÜ'}),
        #  signal('ACU_ChassisDriverModeCtrl', 2, 2, 'little_endian', False, None, 1, 0, 0, 3, 'None', False, None, {0: 'speed ctrl mode', 1: 'throttle ctrl mode', 2: 'reserve1', 3: 'reserve2'}, None, {None: 'Çý¶¯Ä£Ê½¿ØÖÆ'}),
        #  signal('ACU_ChassisGearCtrl', 4, 2, 'little_endian', False, None, 1, 0, 0, 3, 'None', False, None, {0: 'default N', 1: 'D', 2: 'N', 3: 'R'}, None, {None: 'µµÎ»¿ØÖÆ'}),
        #  signal('ACU_ChassisSpeedCtrl', 8, 16, 'little_endian', False, None, 0.01, 0, 0, 50, 'm/s', False, None, None, None, {None: '³µÁ¾ËÙ¶È¿ØÖÆ'}),
        #  signal('ACU_ChassisThrottlePdlTarget', 24, 10, 'little_endian', False, None, 0.1, 0, 0, 100, '%', False, None, None, None, {None: '³µÁ¾ÓÍÃÅ¿ØÖÆ'}),
        #  signal('ACU_DriveLifeSig', 48, 4, 'little_endian', False, None, 1, 0, 0, 15, 'None', False, None, None, None, {None: 'Ñ\xad»·¼ÆÊý0~15'}),
        #  signal('ACU_CheckSum_130', 56, 8, 'little_endian', False, None, 1, 0, 0, 255, 'None', False, None, None, None, {None: 'Ð£Ñésum=byte0 xor byte1 xor...byte6'})]        self._Drive_Command_raw = self._Drive_Command.encode({'THROTTLE_PEDAL_EN_CTRL': 1, 'THROTTLE_PEDAL_CMD': 0,})
        self._Drive_Command_raw = self._Drive_Command.encode({  'ACU_ChassisDriverEnCtrl': 1, 
                                                                'ACU_ChassisDriverModeCtrl': 0, 
                                                                'ACU_ChassisGearCtrl': 0, 
                                                                'ACU_ChassisSpeedCtrl': 0, 
                                                                'ACU_ChassisThrottlePdlTarget': 0,})
        
        # [signal('ACU_ChassisBrakeEn', 0, 1, 'little_endian', False, None, 1, 0, 0, 1, 'None', False, None, {0: 'disable', 1: 'enable'}, None, {None: '³µÁ¾É²³µ¿ØÖÆÊ¹ÄÜ'}),
        #  signal('ACU_ChassisBrakeLampCtrl', 1, 1, 'little_endian', False, None, 1, 0, 0, 1, 'None', False, None, {0: 'off£¨ÓëVCU¿ØÖÆÖÆ¶¯µÆÊÇ»òµÄ¹ØÏµ£©', 1: 'on'}, None, {None: '³µÁ¾É²³µµÆ¿ØÖÆ'}),
        #  signal('ACU_ChassisBrakePdlTarget', 8, 10, 'little_endian', False, None, 0.1, 0, 0, 100, '%', False, None, None, None, {None: '³µÁ¾É²³µ¿ØÖÆ'}),
        #  signal('ACU_ChassisEpbCtrl', 24, 2, 'little_endian', False, None, 1, 0, 0, 2, 'None', False, None, {0: 'default', 1: 'brake', 2: 'release'}, None, {None: '×¤³µ¿ØÖÆ'}),
        #  signal('ACU_BrakeLifeSig', 48, 4, 'little_endian', False, None, 1, 0, 0, 15, 'None', False, None, None, None, {None: 'Ñ\xad»·¼ÆÊý0~15'}),
        #  signal('ACU_CheckSum_131', 56, 8, 'little_endian', False, None, 1, 0, 0, 255, 'None', False, None, None, None, {None: 'Ð£Ñésum=byte0 xor byte1 xor...byte6'})]
        self._Brake_Command_raw = self._Brake_Command.encode({'ACU_ChassisBrakeEn': 1, 
                                                              'ACU_ChassisBrakeLampCtrl': 0, 
                                                              'ACU_ChassisBrakePdlTarget': 0, 
                                                              'ACU_ChassisEpbCtrl': 0,})

        # [signal('ACU_ChassisSteerEnCtrl', 0, 1, 'little_endian', False, None, 1, 0, 0, 1, 'None', False, None, {0: 'disable', 1: 'enable'}, None, {None: '³µÁ¾×ªÏò¿ØÖÆÊ¹ÄÜ'}),
        #  signal('ACU_ChassisSteerModeCtrl', 4, 4, 'little_endian', False, None, 1, 0, 0, 4, 'None', False, None, {0: 'front ackerman', 1: 'same front and back', 2: 'front different back', 3: 'back ackrman', 4: 'front back'}, None, {None: '×ªÏòÄ£Ê½¿ØÖÆ'}),
        #  signal('ACU_ChassisSteerAngleTarget', 8, 16, 'little_endian', True, None, 1, 0, -500, 500, 'deg', False, None, None, None, {None: '³µÁ¾×ªÏò¿ØÖÆ£¨Ç°£©'}),
        #  signal('ACU_ChassisSteerAngleRearTarget', 24, 16, 'little_endian', True, None, 1, 0, -500, 500, 'deg', False, None, None, None, {None: '³µÁ¾×ªÏò¿ØÖÆ£¨ºó£©'}),
        #  signal('ACU_ChassisSteerAngleSpeedCtrl', 40, 8, 'little_endian', False, None, 2, 0, 0, 500, 'deg/s', False, None, None, None, {None: '³µÁ¾·½ÏòÅÌ×ª½ÇËÙ¶È¿ØÖÆ'}),
        #  signal('ACU_SteerLifeSig', 48, 4, 'little_endian', False, None, 1, 0, 0, 15, 'None', False, None, None, None, {None: 'Ñ\xad»·¼ÆÊý0~15'}),
        #  signal('ACU_CheckSum_132', 56, 8, 'little_endian', False, None, 1, 0, 0, 255, 'None', False, None, None, None, {None: 'Ð£Ñésum=byte0 xor byte1 xor...byte6'})]        self._Steer_Command_raw = self._Steer_Command.encode({'STEER_ANGLE_EN_CTRL': 1, 'STEER_ANGLE_CMD': 0.3,})
        self._Steer_Command_raw = self._Steer_Command.encode({'ACU_ChassisSteerEnCtrl': 1, 
                                                              'ACU_ChassisSteerModeCtrl': 0, 
                                                              'ACU_ChassisSteerAngleTarget': 300, 
                                                              'ACU_ChassisSteerAngleRearTarget': 0, 
                                                              'ACU_ChassisSteerAngleSpeedCtrl': 300,})

        # [signal('ACU_VehiclePosLampCtrl', 0, 1, 'little_endian', False, None, 1, 0, 0, 1, 'None', False, None, {0: 'off', 1: 'on'}, None, {None: 'Î»ÖÃµÆ¿ØÖÆ'}),
        #  signal('ACU_VehicleHeadLampCtrl', 1, 1, 'little_endian', False, None, 1, 0, 0, 1, 'None', False, None, {0: 'off', 1: 'on'}, None, {None: '½ü¹âµÆ¿ØÖÆ'}),
        #  signal('ACU_VehicleLeftLampCtrl', 2, 1, 'little_endian', False, None, 1, 0, 0, 1, 'None', False, None, {0: 'off', 1: 'on'}, None, {None: '×ó×ªÏòµÆ¿ØÖÆ'}),
        #  signal('ACU_VehicleRightLampCtrl', 3, 1, 'little_endian', False, None, 1, 0, 0, 1, 'None', False, None, {0: 'off', 1: 'on'}, None, {None: 'ÓÒ×ªÏòµÆ¿ØÖÆ'}),
        #  signal('ACU_ChassisSpeedLimiteMode', 24, 1, 'little_endian', False, None, 1, 0, 0, 1, 'None', False, None, {0: 'default', 1: 'limit'}, None, {None: 'ÏÞËÙ¿ØÖÆ'}),
        #  signal('ACU_ChassisSpeedLimiteVal', 32, 8, 'little_endian', False, None, 0.1, 0, 1, 20, 'm/s', False, None, None, None, {None: 'ËÙ¶ÈÏÞÖÆÖµ'}),
        #  signal('ACU_CheckSumEn', 48, 1, 'little_endian', False, None, 1, 0, 0, 1, 'None', False, None, {0: 'enable', 1: 'disable'}, None, {None: 'Ð£ÑéÄ£Ê½Ê¹ÄÜ(Ô¤Áô)'})]
        self._VehicleCtrl_raw = self._Gear_Command.encode({'ACU_VehiclePosLampCtrl': 0, 
                                                           'ACU_VehicleHeadLampCtrl': 0, 
                                                           'ACU_VehicleLeftLampCtrl': 0, 
                                                           'ACU_VehicleRightLampCtrl': 0, 
                                                           'ACU_ChassisSpeedLimiteMode': 1, 
                                                           'ACU_ChassisSpeedLimiteVal': 5, 
                                                           'ACU_CheckSumEn': 0,})

        # [signal('ACU_MotorTorqueLfCtrl', 0, 16, 'little_endian', True, None, 0.1, 0, -200, 200, 'Nm', False, None, None, None, {None: '×óÇ°µç»úÅ¤¾Ø'}),
        #  signal('ACU_MotorTorqueRfCtrl', 16, 16, 'little_endian', True, None, 0.1, 0, -200, 200, 'Nm', False, None, None, None, {None: 'ÓÒÇ°µç»úÅ¤¾Ø'}),
        #  signal('ACU_MotorTorqueLrCtrl', 32, 16, 'little_endian', True, None, 0.1, 0, -200, 200, 'Nm', False, None, None, None, {None: '×óºóµç»úÅ¤¾Ø'}),
        #  signal('ACU_MotorTorqueRrCtrl', 48, 16, 'little_endian', True, None, 0.1, 0, -200, 200, 'Nm', False, None, None, None, {None: 'ÓÒºóµç»úÅ¤¾Ø'}
        self._WheelTorqueCtrl_raw = self._Control_Command.encode({'ACU_MotorTorqueLfCtrl': 0, 
                                                                  'ACU_MotorTorqueRfCtrl': 0, 
                                                                  'ACU_MotorTorqueLrCtrl': 0, 
                                                                  'ACU_MotorTorqueRrCtrl': 0})

        # 通过初始的报文数据
        self._Drive_Command_message = can.Message(arbitration_id=self._Drive_Command.frame_id, data=self._Drive_Command_raw)

        self._Brake_Command_message = can.Message(arbitration_id=self._Brake_Command.frame_id, data=self._Brake_Command_raw)

        self._Steer_Command_message = can.Message(arbitration_id=self._Steer_Command.frame_id, data=self._Steer_Command_raw)

        self._VehicleCtrl_message = can.Message(arbitration_id=self._VehicleCtrl.frame_id, data=self._VehicleCtrl_raw)
        
        self._WheelTorqueCtrl_message = can.Message(arbitration_id=self._WheelTorqueCtrl.frame_id, data=self._WheelTorqueCtrl_raw)
        

        # 循环发送报文数据
        self._drive_task = self._can_bus.send_periodic(msg=self._Drive_Command_message, period=0.02)

        self._brak_task = self._can_bus.send_periodic(msg=self._Brake_Command_message, period=0.02)

        self._steer_task = self._can_bus.send_periodic(msg=self._Steer_Command_message, period=0.02)

        self._VehicleCtrl_task = self._can_bus.send_periodic(msg=self._VehicleCtrl_message, period=0.02)

        self._WheelTorqueCtrl_task = self._can_bus.send_periodic(msg=self._WheelTorqueCtrl_message, period=0.02)

        time.sleep(2)

        self._steer_task.modify_data({'ACU_ChassisSteerAngleTarget': -300})

        time.sleep(2)

        self._steer_task.modify_data({'ACU_ChassisSteerAngleTarget': 0})


    def _set_drive(self,speed,gear_cmd):
        self._drive_task.modify_data({'ACU_ChassisSpeedCtrl': speed, 'ACU_ChassisGearCtrl': gear_cmd})

    def _set_brake(self,brake,hold_brake):
        self._brak_task.modify_data({'ACU_ChassisBrakePdlTarget': brake, 'ACU_ChassisEpbCtrl' : hold_brake })    

    def _set_steer_angle(self,steer):
        self._steer_task.modify_data({'ACU_ChassisSteerAngleRearTarget': steer})

    def _set_vehiclectrl(self,pose,head,left,right):
        self._turnsignal_task.modify_data({'ACU_VehiclePosLampCtrl': pose, 'ACU_VehicleHeadLampCtrl': head, 'ACU_VehicleLeftLampCtrl': left, 'ACU_VehicleRightLampCtrl': right})



