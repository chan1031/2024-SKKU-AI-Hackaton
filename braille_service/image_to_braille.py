import cv2
import numpy as np

def convert_image_to_braille(image_path, output_path="braille_image.png"):
    # 이미지 불러오기
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 밝기와 대비 조정
    adjusted = cv2.convertScaleAbs(gray, alpha=1.2, beta=30)

    # 가우시안 블러 적용
    blurred = cv2.GaussianBlur(adjusted, (5, 5), 0)

    # Adaptive Thresholding 이진화
    binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)

    # 경계 검출
    edges = cv2.Canny(binary, 100, 200)

    # 점 형태로 변환
    dot_image = np.full((edges.shape[0] * 10, edges.shape[1] * 10), 255, dtype=np.uint8)
    for y in range(edges.shape[0]):
        for x in range(edges.shape[1]):
            if edges[y, x] > 128:  # 경계 부분에 점 찍기
                cv2.circle(dot_image, (x * 10 + 5, y * 10 + 5), 2, 0, -1)  # 점 크기 및 간격 조정

    cv2.imwrite(output_path, dot_image)
    return output_path
