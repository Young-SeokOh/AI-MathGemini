from flask import Flask, request, render_template, jsonify
import os
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import re
import io
import google.generativeai as genai
import tempfile

app = Flask(__name__)

# 환경 변수에서 Google API 키를 가져오기
# Render에서는 환경 변수로 설정해야 함
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# 허용된 확장자
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_image(image_file):
    try:
        image = Image.open(image_file)
        text = pytesseract.image_to_string(image, lang='kor+eng')
        return text
    except Exception as e:
        print(f"이미지에서 텍스트 추출 중 오류: {e}")
        return ""

def extract_text_from_pdf(pdf_file):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(pdf_file.read())
            temp_file_path = temp_file.name
        
        text = ""
        with fitz.open(temp_file_path) as doc:
            for page in doc:
                text += page.get_text()
        
        # 임시 파일 삭제
        os.unlink(temp_file_path)
        return text
    except Exception as e:
        print(f"PDF에서 텍스트 추출 중 오류: {e}")
        return ""

def get_feedback_from_ai(problem_text, criteria_text=None):
    try:
        # Gemini Pro 모델 설정 - temperature를 0으로 설정
        model = genai.GenerativeModel('gemini-pro',
                                     generation_config=genai.GenerationConfig(
                                         temperature=0.0  # 완전히 결정적인 출력을 위해 0으로 설정
                                     ))
        
        system_prompt = "수학교육자 Anna Sfard의 관점에서 학생들의 수학 문제 풀이에 대해 분석하고 상세한 피드백을 제공합니다. 성취기준, 수학적 대상, 루틴, 내러티브를 바탕으로 학생의 답안을 분석하고, 잘한 점과 개선이 필요한 부분을 구체적으로 설명하며, 학생이 더 나은 문제 해결 능력을 기를 수 있도록 도와주세요."
        
        user_prompt = f"""
        학생이 작성한 수학 문제 답안에 대해 피드백을 제공해주세요. 
        
        답안:
        {problem_text}
        """
        
        if criteria_text:
            user_prompt += f"""
            피드백 고려사항:
            {criteria_text}
            """
        
        # Gemini API 호출 시 시스템 프롬프트 설정
        chat = model.start_chat(history=[
            {"role": "user", "parts": [system_prompt]}
        ])
        
        # 사용자 프롬프트로 응답 생성
        response = chat.send_message(user_prompt)
        
        return response.text
    except Exception as e:
        print(f"AI 피드백 생성 중 오류: {e}")
        return f"AI 피드백을 생성하는 동안 오류가 발생했습니다: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'problem-answer' not in request.files:
        return "문제 및 답안 파일이 없습니다", 400
    
    file = request.files['problem-answer']
    
    if file.filename == '':
        return "선택된 파일이 없습니다", 400
    
    if file and allowed_file(file.filename):
        # 파일 확장자 확인
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        
        # 파일 처리
        if file_ext in ['png', 'jpg', 'jpeg']:
            problem_text = extract_text_from_image(file)
        elif file_ext == 'pdf':
            problem_text = extract_text_from_pdf(file)
        else:
            return "지원하지 않는 파일 형식입니다", 400
        
        # 피드백 기준 처리
        criteria_text = ""
        
        # 피드백 기준 파일이 있는 경우
        if 'feedback-criteria' in request.files:
            criteria_file = request.files['feedback-criteria']
            if criteria_file.filename != '':
                criteria_text += extract_text_from_pdf(criteria_file)
        
        # 직접 입력한 피드백 기준 추가
        form_fields = ['achievement-standard', 'math-object', 'routine', 'narrative', 'other']
        for field in form_fields:
            if field in request.form and request.form[field]:
                criteria_text += f"\n{field}: {request.form[field]}"
        
        # AI에서 피드백 얻기
        feedback = get_feedback_from_ai(problem_text, criteria_text)
        
        return feedback
    
    return "처리 중 오류가 발생했습니다", 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)