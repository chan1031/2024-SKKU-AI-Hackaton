import boto3
import base64

# Polly 클라이언트 생성
polly_client = boto3.client('polly')

def lambda_handler(event, context):
    # 경로 변수에서 텍스트 가져오기
    text = event.get('pathParameters', {}).get('id', 'default text')
    print("Text to be spoken:", text)  # 확인용 로그

    # 속도 조절을 위한 SSML 설정
    ssml_text = f"<speak><prosody rate='slow'>{text}</prosody></speak>"

    try:
        # Polly를 사용해 텍스트를 음성으로 변환 (한국어 음성 'Seoyeon' 사용)
        response = polly_client.synthesize_speech(
            Text=ssml_text,
            TextType="ssml",  # SSML을 사용하여 속도 조절
            OutputFormat='mp3',
            VoiceId='Seoyeon'  # 한국어 화자 선택
        )
        
        # AudioStream을 읽어 Base64로 인코딩
        audio_stream = response['AudioStream'].read()
        audio_base64 = base64.b64encode(audio_stream).decode('utf-8')
        
        # HTML 콘텐츠 생성 (큰 버튼으로 재생)
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>TTS Audio Playback</title>
            <style>
                /* 페이지 가운데 큰 버튼 스타일 */
                body {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    font-family: Arial, sans-serif;
                }}
                #playButton {{
                    font-size: 4em;
                    padding: 40px 80px;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 15px;
                    cursor: pointer;
                }}
                #playButton:hover {{
                    background-color: #45a049;
                }}
            </style>
        </head>
        <body>
            <button id="playButton">▶ 재생</button>
            <audio id="audio"></audio>

            <script>
                const base64Audio = "{audio_base64}";
                const audioElement = document.getElementById("audio");
                const playButton = document.getElementById("playButton");

                // 오디오 소스 설정
                audioElement.src = "data:audio/mp3;base64," + base64Audio;

                // 버튼 클릭 시 오디오 재생
                playButton.addEventListener("click", () => {{
                    audioElement.play().catch(error => {{
                        console.log("Audio play failed:", error);
                    }});
                }});
            </script>
        </body>
        </html>
        """
        
        # HTML 응답 반환
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html'
            },
            'body': html_content
        }
    
    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>"
        }
