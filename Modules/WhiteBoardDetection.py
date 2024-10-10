#It is flask app.py
# app.py
from flask import Flask, request, jsonify
import cv2
import numpy as np

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_image():
    # 이미지 파일 가져오기
    file = request.files['image']
    if not file:
        return jsonify({"error": "No file provided"}), 400
    
    # 이미지 읽기 및 전처리
    npimg = np.fromfile(file, np.uint8)
    image = cv2.imdecode(npimg, cv2.IMREAD_GRAYSCALE)
    
    # 이진화하여 배경 제거 (하얀색 배경)
    _, binary_image = cv2.threshold(image, 200, 255, cv2.THRESH_BINARY_INV)

    # 점 패턴 생성
    height, width = binary_image.shape
    dot_representation = ""
    for y in range(0, height, 5):  # 해상도를 줄이기 위해 5픽셀 단위로 간격 조정
        for x in range(0, width, 5):
            if binary_image[y, x] == 255:
                dot_representation += "•"
            else:
                dot_representation += " "
        dot_representation += "\n"
    
    # 점 패턴 결과 반환
    return jsonify({"dot_pattern": dot_representation})

if __name__ == '__main__':
    app.run(debug=True)
