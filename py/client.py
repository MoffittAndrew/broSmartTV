import socket, cv2, pickle, struct

# create socket
client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
host_ip = '192.168.137.170' # paste your server ip address here
port = 9559
client_socket.connect((host_ip,port)) # a tuple
data = b""
payload_size = struct.calcsize("Q")
while True:
    vid = cv2.VideoCapture(0)
    while(vid.isOpened()):
        img,frame = vid.read()
        a = pickle.dumps(frame)
        message = struct.pack("Q",len(a))+a
        client_socket.sendall(message)
        
        cv2.imshow('TRANSMITTING VIDEO',frame)
        key = cv2.waitKey(1) & 0xFF
        if key ==ord('q'):
            client_socket.close()