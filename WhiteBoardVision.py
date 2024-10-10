import cv2
import numpy as np

# 이미지 불러오기
image_path = 'chalkboard_image.jpg'  # 칠판 이미지 경로
image = cv2.imread(image_path)

# BGR에서 HSV 색상 공간으로 변환
hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# 초록색 범위 정의 (칠판 배경 색상 범위 설정)
lower_green = np.array([35, 40, 40])  # 색상, 채도, 명도 범위 조정 가능
upper_green = np.array([85, 255, 255])

# 초록색 마스크 생성 (배경 제거)
mask = cv2.inRange(hsv_image, lower_green, upper_green)
background_removed = cv2.bitwise_and(image, image, mask=cv2.bitwise_not(mask))

# 그레이스케일로 변환 및 이진화
gray = cv2.cvtColor(background_removed, cv2.COLOR_BGR2GRAY)
_, binary_image = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)

# 이미지 크기 조정 (점 형태 표현을 위해 해상도 축소)
resized_image = cv2.resize(binary_image, (100, 50))  # 원하는 크기로 조절

# 점 패턴 생성
dot_representation = ""
for y in range(resized_image.shape[0]):
    for x in range(resized_image.shape[1]):
        # 흰색(255)은 점을, 검정색(0)은 공백을 표시
        if resized_image[y, x] == 255:
            dot_representation += "•"
        else:
            dot_representation += " "
    dot_representation += "\n"

# 결과를 텍스트 파일로 저장
with open("dot_representation.txt", "w") as file:
    file.write(dot_representation)

# 콘솔에 점 패턴 출력
print(dot_representation)
