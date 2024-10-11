import boto3
import json
import time
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
s3 = boto3.client('s3', region_name='ap-northeast-2')
lambda_client = boto3.client('lambda', region_name='ap-northeast-2')
bucket_name = 'skkuhackatons3'  # S3 버킷 이름

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

# 한글 음절을 초성, 중성, 종성으로 분리하는 함수
def split_hangul(char):
    code = ord(char) - 0xAC00
    cho = code // 588
    jung = (code - (cho * 588)) // 28
    jong = code % 28
    return cho, jung, jong

# 텍스트를 점자로 변환하는 함수
def text_to_braille(text):
    braille_output = []
    for char in text:
        if '가' <= char <= '힣':  # 한글 음절 범위 확인
            cho, jung, jong = split_hangul(char)
            cho_char = list(chosung_map.keys())[cho]
            jung_char = list(jungsung_map.keys())[jung]
            jong_char = list(jongsung_map.keys())[jong]

            braille_output.append(
                chosung_map[cho_char] + jungsung_map[jung_char] + jongsung_map[jong_char]
            )
        else:
            braille_output.append(char)  # 점자로 변환할 수 없는 문자
    return ''.join(braille_output)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_mp3():
    # MP3 파일 업로드
    if 'file' not in request.files:
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))

    # S3에 파일 업로드
    file_key = f'uploads/{file.filename}'
    s3.upload_fileobj(file, bucket_name, file_key)

    # Lambda 호출로 MP3 파일을 텍스트로 변환
    response = lambda_client.invoke(
        FunctionName='mp3-to-text',  # Lambda 함수 이름
        InvocationType='RequestResponse',
        Payload=json.dumps({'bucket': bucket_name, 'key': file_key})
    )

    # Lambda 응답 처리
    response_payload = json.loads(response['Payload'].read())

    # transcript_key 대신 transcript_text 사용
    if 'transcript_text' in response_payload:
        transcript_text = response_payload['transcript_text']
        return render_template('index.html', transcript_text=transcript_text)
    else:
        error_message = response_payload.get('errorMessage', 'Lambda 함수에서 변환 결과를 찾을 수 없습니다.')
        return render_template('index.html', error=error_message)

@app.route('/convert_to_braille', methods=['POST'])
def convert_to_braille():
    text = request.form['text']
    braille_text = text_to_braille(text)
    return render_template('index.html', braille_text=braille_text, transcript_text=text)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
