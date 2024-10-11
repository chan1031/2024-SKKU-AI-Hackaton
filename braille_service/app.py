import os
import boto3
import json
from openai import OpenAI
from flask import Flask, render_template, request, redirect, url_for
from image_to_braille import convert_image_to_braille  # 함수 이름 수정
from bs4 import BeautifulSoup
import base64

app = Flask(__name__)

# OpenAI API 키 설정
OPENAI_API_KEY = 'INSERT YOUR KEY'
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
    if 'file' not in request.files:
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))

    file_key = f'uploads/{file.filename}'
    s3.upload_fileobj(file, bucket_name, file_key)

    response = lambda_client.invoke(
        FunctionName='mp3-to-text',
        InvocationType='RequestResponse',
        Payload=json.dumps({'bucket': bucket_name, 'key': file_key})
    )

    response_payload = json.loads(response['Payload'].read())

    if 'transcript_text' in response_payload:
        transcript_text = response_payload['transcript_text']
        print("원본 텍스트:", transcript_text)

        try:
            gpt_response = client.chat.completions.create(
                model="gpt-3.5-turbo-16k",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes content accurately and concisely."},
                    {"role": "user", "content": f"다음 텍스트의 주요 내용을 300단어 이내로 요약해주세요:\n\n{transcript_text}"}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            summarized_text = gpt_response.choices[0].message.content
            print("GPT 응답:", summarized_text)

            return render_template('index.html', transcript_text=transcript_text, summarized_text=summarized_text, show_editor=True)
        except Exception as e:
            print("GPT API 호출 에러:", str(e))
            return render_template('index.html', error=f"GPT API 호출 에러: {str(e)}")
    else:
        error_message = response_payload.get('errorMessage', 'Lambda 함수에서 변환 결과를 찾을 수 없습니다.')
        return render_template('index.html', error=error_message)

@app.route('/convert_to_braille', methods=['POST'])
def convert_to_braille():
    html_content = request.form['text']
    soup = BeautifulSoup(html_content, 'html.parser')

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

                # 변환 함수 호출 시 이름 수정
                braille_image_path = convert_image_to_braille(temp_path)

                # 변환된 이미지를 다시 Base64로 인코딩하여 HTML에 삽입
                with open(braille_image_path, "rb") as img_file:
                    encoded_string = base64.b64encode(img_file.read()).decode("utf-8")
                    img_tag = f'<img src="data:image/png;base64,{encoded_string}" alt="Braille Image" style="width: 100px; height: 100px;"/>'
                    text_content.append(img_tag)

                # 임시 파일 삭제
                os.remove(temp_path)
                os.remove(braille_image_path)
            else:
                text_content.append("[이미지]")

    braille_text = "\n\n".join(text_content)
    return render_template('index.html', braille_text=braille_text, transcript_text=html_content, show_editor=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
