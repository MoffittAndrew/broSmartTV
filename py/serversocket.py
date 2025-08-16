host_ip = '0.0.0.0'
port = 9559

import asyncio
from websockets.asyncio.server import serve
import json
import numpy as np
import cv2
import base64
import time

async def screen_share(websocket):
    print("Connected")
    connected = True
    frame_count = 0
    is_processing = False
    while connected:
        async for message in websocket.recv_streaming():
            #print(message)
            try:
                decoded = json.loads(message)
                if "leaving" in decoded and decoded["leaving"]:
                    connected = False
            except:
                 # Check if the client is already processing a frame
                if not is_processing:

                    # Check if the received response is empty (broken response) and skip it
                    if message:

                        # Set the processing flag to indicate that the client is busy
                        is_processing = True

                        frame_count += 1
                        print(f"Received frame {frame_count}...")

                        try:
                            # Decode the base64 frame and display it
                            frame_data = base64.b64decode(message)
                            print(frame_data)
                            frame_np = np.frombuffer(frame_data, np.uint8)
                            print(frame_np)
                            frame = cv2.imdecode(frame_np, cv2.IMREAD_GRAYSCALE)
                            print(frame)
                            #cv2.imshow("Frame", frame)
                            #cv2.waitKey(1)  # Adjust the delay as needed
                        except Exception as e:
                            print(f"Error decoding frame: {str(e)}")

                        # Reset the processing flag once frame processing is complete
                        is_processing = False
                    
                '''
                fps,st,frames_to_count,cnt = (0,0,20,0)
                data = base64.b64decode(message,' /')
                npdata = np.fromstring(data,dtype=np.uint8)
                frame = cv2.imdecode(npdata,1)
                frame = cv2.putText(frame,'FPS: '+str(fps),(10,40),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
                cv2.imshow("RECEIVING VIDEO",frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                if cnt == frames_to_count:
                    try:
                        fps = round(frames_to_count/(time.time()-st))
                        st=time.time()
                        cnt=0
                    except:
                        pass
                cnt+=1
                '''
    
    print("Disconnected")

async def main():
    async with serve(screen_share, "localhost", port) as server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
