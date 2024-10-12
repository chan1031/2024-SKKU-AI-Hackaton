import boto3
import time
import json  # json 모듈을 추가합니다.

s3 = boto3.client('s3')
transcribe = boto3.client('transcribe')

def lambda_handler(event, context):
    bucket = event['bucket']
    key = event['key']
    job_name = f"transcribe-{int(time.time())}"
    job_uri = f"s3://{bucket}/{key}"

    # Transcribe 작업 시작
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={'MediaFileUri': job_uri},
        MediaFormat='mp3',
        LanguageCode='ko-KR',  # 한국어
        OutputBucketName=bucket,
        OutputKey=f"transcripts/{job_name}.json"
    )

    # Transcribe 작업 완료 대기
    while True:
        status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
            break
        time.sleep(5)
    
    # 변환된 텍스트 추출
    if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
        transcript_file_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
        transcript_data = s3.get_object(Bucket=bucket, Key=f"transcripts/{job_name}.json")
        transcript_json = transcript_data['Body'].read().decode('utf-8')
        transcript_text = json.loads(transcript_json)['results']['transcripts'][0]['transcript']
        
        return {
            'status': 'success',
            'transcript_text': transcript_text
        }
    else:
        return {
            'status': 'failed',
            'message': 'Transcription job failed'
        }
