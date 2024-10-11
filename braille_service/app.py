import os
import boto3
import json
from openai import OpenAI
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# OpenAI API 키 설정
OPENAI_API_KEY = 'Enter your KEY'
client = OpenAI(api_key=OPENAI_API_KEY)

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

        # 디버깅: 원본 텍스트 출력
        print("원본 텍스트:", transcript_text)

        try:
            # GPT API 호출
            gpt_response = client.chat.completions.create(
                model="gpt-3.5-turbo-16k",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes content accurately and concisely."},
                    {"role": "user", "content": f"다음 텍스트는 수업 내용인데 이를 요약해서 정리해주세요:\n\n{transcript_text}"}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            summarized_text = gpt_response.choices[0].message.content

            # 디버깅: GPT 응답을 서버 콘솔에 출력
            print("GPT 응답:", summarized_text)

            return render_template('index.html', summarized_text=summarized_text)
        except Exception as e:
            print("GPT API 호출 에러:", str(e))
            return render_template('index.html', error=f"GPT API 호출 에러: {str(e)}")
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
