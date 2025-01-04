import socket
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import json

# UDP server setup
UDP_IP = "0.0.0.0"  # 监听所有网络接口
UDP_PORT = 5005     # 监听的端口

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# 设置窗口大小
window_size = 100  # 只显示最近的100个点

# 创建图形
fig, ax = plt.subplots()
max_power = 500
labels = ["power", "wheel_revs", "crank_revs"]
data_list = [0, 0, 0]
colors = ["green", "red", "blue"]

bar = ax.bar(labels, data_list, color=colors)
ax.set_ylim(0, max_power)
ax.set_ylabel("Power Level")

# 更新函数
def update(frame):
    global power
    
    # 从 UDP 接收数据
    sock.setblocking(0)  # 设置非阻塞模式
    try:
        data, _ = sock.recvfrom(1024)  # 数据缓冲区大小为1024字节
        obj = json.loads(data.decode())
        print(obj)
        print(type(obj))
        if "CP" in obj["type"] :
            power = int(obj["instantaneous_power"])
            print(f"power={power}")
            power = (power + 5) % (max_power + 1)  # 每次增加5，超出100归零
            bar[0].set_height(power)  # 更新条的高度
        if "CSC" in obj["type"] :
            wheel_revs = int(obj["cumulative_wheel_revs"])
            crank_revs= int(obj["cumulative_crank_revs"])
            print(f"wheel_revs={wheel_revs}")
            print(f"crank_revs={crank_revs}")
            bar[1].set_height(wheel_revs)
            bar[2].set_height(crank_revs)

    except Exception as e:
        pass

    return bar

# 动画
ani = FuncAnimation(fig, update, interval=50, blit=False)

# 显示图形
plt.show()
