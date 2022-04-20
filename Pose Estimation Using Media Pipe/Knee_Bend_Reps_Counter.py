import cv2
import mediapipe as mp
import numpy as np
import time
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
# Standard PySceneDetect imports:
from scenedetect import VideoManager
from scenedetect import SceneManager

# For content-aware scene detection:
from scenedetect.detectors import ContentDetector

# Function to calculate for the connection between 3 joints in body
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle >180.0:
        angle = 360-angle
        
    return angle   


# Function to find all the cut/fluctuated scenes of the video to find the dummy frames in it using scene_detect library
def find_scenes(video_path, threshold=10.0):
    # Create our video & scene managers, then add the detector.
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(
        ContentDetector(threshold=threshold, min_scene_len=5))

    # Improve processing speed by downscaling before processing.
    video_manager.set_downscale_factor()

    # Start the video manager and perform the scene detection.
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)

    # Each returned scene is a tuple of the (start, end) timecode.
    return scene_manager.get_scene_list() 

# Function to get the list of all dummy_frames from the cut scenes 
def get_dummy_frames(scenes, dummy_frames_list):
    for i in range(len(scenes)-1):
        if (scenes[i+1][1].frame_num) - (scenes[i][1].frame_num) <=25: # Since dummy frames stays for less than 1 second and frames are running at 25 fps
            for x in range(scenes[i][1].frame_num, scenes[i+1][1].frame_num):
                dummy_frames_list.append(x)
    return dummy_frames_list

# Function to count the reps for knee bend using mediapipe and opencv
def get_knee_bend_reps_counter(input_video, output_video, dummy_frames):
    cap = cv2.VideoCapture(input_video)
    result = cv2.VideoWriter(output_video, 
                             cv2.VideoWriter_fourcc(*'MJPG'),
                             25, (854, 640))
    i = -1
    counter = 0
    stage = None
    hold = False
    ## Setup mediapipe instance
    with mp_pose.Pose(min_detection_confidence=0.8, min_tracking_confidence=0.8) as pose:
        while cap.isOpened():
            i+=1
            ret, frame = cap.read()

            if i not in dummy_frames: # The code will not run for all the dummy frames
                if ret == False:
                    break

                # Recolor image to RGB
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image.flags.writeable = False

                # Make detection
                results = pose.process(image)

                # Recolor back to BGR
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                # Extract landmarks
                try:
                    landmarks = results.pose_landmarks.landmark

                    # Get coordinates
                    hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                    knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                    ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

                    # Calculate angle
                    angle = calculate_angle(hip, knee, ankle)

                    # Visualize angle
                    cv2.putText(image, f"Angle: {str(angle)}", 
                                   tuple(np.multiply(knee, [854, 600]).astype(int)), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                    # Rep Counter Logic
                    if angle > 140:
                        if stage == "bent" and hold == False:
                            cv2.putText(image, "Keep your knee bent", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2, cv2.LINE_AA)
                        stage = "straight"
                        hold = False
                    elif angle < 140 and stage == "straight":
                        stage = "bent"
                        start = round(time.perf_counter())
                    elif angle < 140 and stage == "bent" and hold == False:
                        cv2.putText(image, f"Holding Time: {str(round(time.perf_counter()) - start)}", (80, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1)
                        if round(time.perf_counter()) - start < 8:
                            completed = False
                        elif round(time.perf_counter()) - start == 8:
                            hold = True
                            counter+=1
                    elif angle < 140 and stage == "bent" and hold == True:
                        cv2.putText(image, f"Holding Time: {str(round(time.perf_counter()) - start)}", (80, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1)


                    cv2.putText(image, f"No. of Reps: {str(counter)}", (120, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (40, 100, 255), 2, cv2.LINE_AA)


                except:
                    pass


                # Render detections
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                        mp_drawing.DrawingSpec(color=(0,117,0), thickness=2, circle_radius=2), 
                                        mp_drawing.DrawingSpec(color=(0,66,230), thickness=2, circle_radius=2) 
                                         )               
                # Save processed video
                result.write(image)
                # Uncomment to show the processed video
    #             cv2.imshow('Knee Bend Rep Counter', image) 

    #             if cv2.waitKey(1) & 0xFF == ord('q'):
    #                 break

        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    input_video_path = 'KneeBendVideo.mp4'
    output_video_name = 'vidout.avi'
    dummy_frames_list = []
    scenes = find_scenes(input_video_path)
    dummy_frames = get_dummy_frames(scenes, dummy_frames_list)
    get_knee_bend_reps_counter(input_video_path, output_video_name, dummy_frames)