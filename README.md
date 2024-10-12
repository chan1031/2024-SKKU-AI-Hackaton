# SKKU AI HACKATON
SKKU 2024 AI-Hackaton  
**2024.10.11 18:00 ~ 2024.10.12 11:00**

# 0. Introduce
Our service generates braille substitute materials for visually impaired students, providing an alternative to traditional textbooks. When a teacher’s lecture is received as an MP3 audio file, it is converted into text using AWS Lambda and a transcription service. The text is then refined through OpenAI's GPT-3.5 API to create a summarized version, which is transformed into braille format. For images, OpenCV is utilized to convert them into braille. Additionally, a TTS service is available for image descriptions: scanning a QR code initiates a generative AI analysis of the image, which is read aloud through AWS Lambda and API Gateway.

# 1. Architecture
![architecture](https://github.com/user-attachments/assets/c8fc6718-a731-42b1-9b88-e039b767617c)

# 2. Skills
AWS Lambda : Connect aws polly, transcriber  
AWS Ec2, Flask : Web Server  
S3: Store uploaded mp4 file and transcripts  
AWS polly: TTS  
AWS transcriber: convert audio to text  
GPT 3.5 api : Summarized text  
Azure Computer Vision api: describe image  
API Gateway : URL of image's described text  

# 3.Awards
## **2024 SKKU AI-Hackaton Silver Awards
**
