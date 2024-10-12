import io
import base64
import qrcode
import requests

# Azure Computer Vision 및 Translator API 설정
vision_subscription_key = "b01a0d89b8f846c588b914066dfac8ee"
vision_endpoint = "https://koreacentral.api.cognitive.microsoft.com/vision/v3.1/analyze"
translator_subscription_key = "17cbe91caf264211984868a952a9c00a"
translator_endpoint = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0"

def process_image(image_path):
    # 이미지 파일을 바이너리로 읽기
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()

    # Azure Computer Vision API 호출 설정
    vision_headers = {
        'Ocp-Apim-Subscription-Key': vision_subscription_key,
        'Content-Type': 'application/octet-stream',
    }
    vision_params = {
        'visualFeatures': 'Description',
    }

    # Computer Vision API 호출
    vision_response = requests.post(vision_endpoint, headers=vision_headers, params=vision_params, data=image_data)
    vision_analysis = vision_response.json()

    # 이미지 설명 추출
    try:
        image_description = vision_analysis["description"]["captions"][0]["text"]
    except (KeyError, IndexError):
        print("이미지 설명을 가져오는 중 오류 발생:", vision_analysis)
        image_description = ""

    # Translator API를 사용하여 설명을 한국어로 번역
    if image_description:
        translator_headers = {
            'Ocp-Apim-Subscription-Key': translator_subscription_key,
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Region': 'koreacentral'
        }
        translator_data = [{
            "text": image_description
        }]
        translator_params = {
            'to': 'ko'
        }

        # Translator API 호출
        translator_response = requests.post(translator_endpoint, headers=translator_headers, json=translator_data, params=translator_params)
        translator_result = translator_response.json()

        # 번역된 텍스트 추출
        try:
            translated_text = translator_result[0]["translations"][0]["text"]
        except (KeyError, IndexError):
            print("번역된 텍스트를 가져오는 중 오류 발생:", translator_result)
            translated_text = ""

        # 존댓말로 변환 함수
        def convert_to_respectful(text):
            if text.endswith('다'):
                text = text.replace('다', '입니다.')
            elif text.endswith('다.'):
                text = text.replace('다.', '입니다.')
            else:
                text += '입니다.'
            return text

        # 존댓말로 변환된 최종 텍스트에 "이 이미지는" 추가
        respectful_description = "이 이미지는 " + convert_to_respectful(translated_text)
    else:
        respectful_description = "이미지 설명이 없습니다."

    # 생성된 텍스트를 API URL 뒤에 추가
    base_url = "https://26r1nswtkc.execute-api.ap-northeast-2.amazonaws.com/echo/"
    full_url = f"{base_url}{requests.utils.quote(respectful_description)}"

    # QR 코드 생성
    qr_code = qrcode.make(full_url)

    # QR 코드를 Base64로 인코딩
    buffered = io.BytesIO()
    qr_code.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return qr_code_base64
