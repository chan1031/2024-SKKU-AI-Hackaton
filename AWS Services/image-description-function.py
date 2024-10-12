import json
import boto3

# 하드코딩된 S3 버킷 이름
BUCKET_NAME = "skkuhackatons3"

def lambda_handler(event, context):
    # S3 객체 키 정보 가져오기
    object_key = event['key']
    
    # Rekognition 클라이언트 생성
    rekognition = boto3.client('rekognition')
    
    try:
        # Rekognition을 통한 이미지 분석 (S3에서 직접 불러오기)
        response = rekognition.detect_labels(
            Image={'S3Object': {'Bucket': BUCKET_NAME, 'Name': object_key}}
        )
        
        # 상위 5개 라벨 추출
        labels = [label['Name'] for label in response['Labels'][:5]]
        
        # 간단한 설명 생성
        description = f"이 이미지에는 다음과 같은 요소가 포함되어 있습니다: {', '.join(labels)}."
        
        return {
            'statusCode': 200,
            'description': description
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'description': f"이미지 분석 중 오류 발생: {str(e)}"
        }
