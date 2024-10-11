import os
import boto3
import json
from openai import OpenAI
from flask import Flask, render_template, request, redirect, url_for
from image_to_braille import convert_image_to_braille  # 함수 이름 수정
from bs4 import BeautifulSoup
import base64
import cv2

app = Flask(__name__)

# OpenAI API 키 설정
OPENAI_API_KEY = 'your key'
client = OpenAI(api_key=OPENAI_API_KEY)

s3 = boto3.client('s3', region_name='ap-northeast-2')
lambda_client = boto3.client('lambda', region_name='ap-northeast-2')
bucket_name = 'skkuhackatons3'

# 초성, 중성, 종성에 대한 점자 매핑
chosung_map = {
    'ㄱ': '⠁', 'ㄴ': '⠉', 'ㄷ': '⠙', 'ㄹ': '⠑', 'ㅁ': '⠋',
    'ㅂ': '⠃', 'ㅅ': '⠓', 'ㅇ': '⠊', 'ㅈ': '⠚', 'ㅊ': '⠒',
    'ㅋ': '⠅', 'ㅌ': '⠜', 'ㅍ': '⠞', 'ㅎ': '⠟', 'ㄲ': '⠠⠁',
    'ㄸ': '⠠⠙', 'ㅃ': '⠠⠃', 'ㅆ': '⠠⠓', 'ㅉ': '⠠⠚'
}

jungsung_map = {
    'ㅏ': '⠣', 'ㅑ': '⠜', 'ㅓ': '⠎', 'ㅕ': '⠱', 'ㅗ': '⠥',
    'ㅛ': '⠬', 'ㅜ': '⠍', 'ㅠ': '⠹', 'ㅡ': '⠤', 'ㅣ': '⠆',
    'ㅐ': '⠖', 'ㅒ': '⠶', 'ㅔ': '⠦', 'ㅖ': '⠴', 'ㅘ': '⠣⠥',
    'ㅙ': '⠣⠖', 'ㅚ': '⠣⠆', 'ㅝ': '⠎⠍', 'ㅞ': '⠎⠖', 'ㅟ': '⠍⠆',
    'ㅢ': '⠤⠆'
}

jongsung_map = {
    '': '', 'ㄱ': '⠁', 'ㄴ': '⠉', 'ㄷ': '⠙', 'ㄹ': '⠑',
    'ㅁ': '⠋', 'ㅂ': '⠃', 'ㅅ': '⠓', 'ㅇ': '⠊', 'ㅈ': '⠚',
    'ㅊ': '⠒', 'ㅋ': '⠅', 'ㅌ': '⠜', 'ㅍ': '⠞', 'ㅎ': '⠟',
    'ㄲ': '⠠⠁', 'ㅆ': '⠠⠓', 'ㄳ': '⠁⠓', 'ㄵ': '⠉⠚',
    'ㄶ': '⠉⠟', 'ㄺ': '⠑⠁', 'ㄻ': '⠑⠋', 'ㄼ': '⠑⠃',
    'ㄽ': '⠑⠓', 'ㄾ': '⠑⠜', 'ㄿ': '⠑⠞', 'ㅀ': '⠑⠟'
}

def split_hangul(char):
    code = ord(char) - 0xAC00
    cho = code // 588
    jung = (code - (cho * 588)) // 28
    jong = code % 28
    return cho, jung, jong

def text_to_braille(text):
    braille_output = []
    for char in text:
        if '가' <= char <= '힣':
            cho, jung, jong = split_hangul(char)
            cho_char = list(chosung_map.keys())[cho]
            jung_char = list(jungsung_map.keys())[jung]
            jong_char = list(jongsung_map.keys())[jong]
            braille_output.append(
                chosung_map[cho_char] + jungsung_map[jung_char] + jongsung_map[jong_char]
            )
        else:
            braille_output.append(char)
    return ''.join(braille_output)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_mp3():
    # Lambda 호출 대신 테스트 텍스트 사용
    transcript_text = """한국 윤석열 대통령이 동남아시아 국가들의 연합인 아세안 정상회의 참석을 계기로 일본의 이시 바 시계로 신임 총리와 첫 정상회담을 가질 예정입니다.
한일 정상은 이번 회담에서 지난 이천이십이 년 윤석열 정부 출범 이후 개선된 한일 관계의 흐름을 주력할 것으로 보입니다.
다만 여러 국가들이 모이는 자리를 계기로 성사된 한일 정상회담이기 때문에 구체적인 현안을 논의하기 보단 윤 대통령이 일본의 신임 총리와 처음 만나는 자리로
서로의 신뢰를 구축하는 데 의미를 둘 전망입니다."""

    # GPT 호출 대신 테스트 텍스트 요약 사용
    summarized_text = transcript_text

    return render_template('index.html', transcript_text=transcript_text, summarized_text=summarized_text, show_editor=True)

@app.route('/convert_to_braille', methods=['POST'])
def convert_to_braille():
    html_content = request.form['text']
    soup = BeautifulSoup(html_content, 'html.parser')

    # 텍스트와 이미지를 순서대로 변환하여 점자 형태로 저장
    text_content = []
    for element in soup.descendants:
        if isinstance(element, str):
            text_content.append(text_to_braille(element.strip()))
        elif element.name == 'img':
            src = element.get('src', '')
            if src.startswith('data:image'):
                # Base64 인코딩된 이미지 데이터 추출
                image_data = src.split(',')[1]
                image_bytes = base64.b64decode(image_data)

                # 임시 파일로 저장
                temp_path = 'temp_image.png'
                with open(temp_path, 'wb') as f:
                    f.write(image_bytes)

                # 원본 크기 유지하여 이미지 점자 변환
                braille_image_path = convert_image_to_braille(temp_path)

                # 변환된 이미지를 다시 Base64로 인코딩하여 HTML에 삽입
                with open(braille_image_path, "rb") as img_file:
                    encoded_string = base64.b64encode(img_file.read()).decode("utf-8")
                    img_tag = f'<img src="data:image/png;base64,{encoded_string}" alt="Braille Image"/>'
                    text_content.append(img_tag)

                # 임시 파일 삭제
                os.remove(temp_path)
                os.remove(braille_image_path)
            else:
                text_content.append("[이미지]")

    # 변환된 점자 텍스트와 이미지 결과를 HTML로 표시
    braille_text = "\n\n".join(text_content)
    return render_template('index.html', braille_text=braille_text, transcript_text=html_content, show_editor=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
