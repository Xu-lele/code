import ClassOfApollo
import time

apollo = ClassOfApollo.Apollo('dbc/Apollo.dbc')
apollo.enable_self_driving()
time.sleep(5)
print('okkkkk')
apollo.send_message(steer_angle_cmd=0.3)
time.sleep(3)
apollo.send_message(steer_angle_cmd=-0.3)
time.sleep(2)
apollo.shutdown()
