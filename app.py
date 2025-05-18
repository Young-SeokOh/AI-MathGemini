from flask import Flask, request, send_from_directory, render_template_string
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

# 인라인 CSS와 JS 포함
def get_styles():
    try:
        with open('styles.css', 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return """
        :root {
          --ku-crimson: #8B1F41;
          --ku-gold: #BE9730;
          --ku-gray: #f5f5f5;
          --ku-dark: #333333;
          --ku-light: #ffffff;
          --ku-crimson-light: rgba(139, 31, 65, 0.1);
          --ku-gold-light: rgba(190, 151, 48, 0.2);
          --error-color: #f56565;
        }
        body { font-family: '맑은 고딕', 'Malgun Gothic', sans-serif; margin: 0; padding: 0; background-color: var(--ku-gray); color: var(--ku-dark); line-height: 1.6; }
        .container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
        .header { text-align: center; margin-bottom: 40px; position: relative; padding-bottom: 20px; }
        .header:after { content: ''; position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); width: 100px; height: 3px; background: linear-gradient(to right, var(--ku-crimson), var(--ku-gold)); }
        h3 { font-size: 32px; margin: 0; color: var(--ku-crimson); font-weight: 600; }
        h4 { font-size: 22px; color: var(--ku-crimson); border-bottom: 2px solid var(--ku-gold); padding-bottom: 8px; margin-top: 0; }
        .subtitle { color: var(--ku-dark); font-size: 18px; margin-top: 10px; font-weight: 500; }
        .main-content { max-width: 800px; margin: 0 auto; }
        .form-group { margin-bottom: 25px; }
        label { display: block; margin-bottom: 8px; font-weight: 500; color: var(--ku-dark); }
        form { background: var(--ku-light); padding: 30px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); margin-bottom: 30px; border-top: 4px solid var(--ku-crimson); border-bottom: 4px solid var(--ku-gold); }
        input[type="file"] { width: 100%; padding: 10px; border: 2px dashed var(--ku-crimson); border-radius: 8px; background: rgba(139, 31, 65, 0.05); transition: all 0.3s ease; }
        input[type="file"]:hover { border-color: var(--ku-gold); background: rgba(190, 151, 48, 0.05); }
        .file-info { display: block; margin-top: 5px; color: #666; font-size: 14px; }
        .file-selected .file-info { color: var(--ku-crimson); font-weight: 500; }
        .feedback-input-container { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .feedback-input-item { margin-bottom: 15px; }
        .feedback-input-item label { display: block; margin-bottom: 5px; font-weight: 500; color: var(--ku-dark); font-size: 14px; }
        textarea { width: 100%; height: 80px; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-family: inherit; font-size: 14px; resize: vertical; box-sizing: border-box; transition: all 0.3s ease; }
        textarea:focus { outline: none; border-color: var(--ku-crimson); box-shadow: 0 0 0 2px var(--ku-crimson-light); }
        button { width: 100%; padding: 15px; font-size: 16px; background: linear-gradient(135deg, var(--ku-crimson), #7B1A39); color: white; border: none; border-radius: 8px; cursor: pointer; transition: all 0.3s ease; font-weight: 600; box-shadow: 0 4px 6px rgba(139, 31, 65, 0.2); }
        button:hover { background: linear-gradient(135deg, #7B1A39, var(--ku-crimson)); transform: translateY(-2px); box-shadow: 0 6px 8px rgba(139, 31, 65, 0.3); }
        button:disabled { background: #ccc; cursor: not-allowed; transform: none; box-shadow: none; }
        #loading { text-align: center; margin: 30px 0; }
        .spinner { width: 50px; height: 50px; border: 5px solid var(--ku-gray); border-top: 5px solid var(--ku-crimson); border-right: 5px solid var(--ku-gold); border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 20px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        #result { background: var(--ku-light); padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); margin-top: 30px; border-left: 4px solid var(--ku-crimson); }
        #result-content { white-space: pre-line; }
        #result-content h3, #result-content h4, #result-content h5 { color: var(--ku-crimson); margin-top: 1.5em; margin-bottom: 0.8em; }
        #result-content strong { color: var(--ku-crimson); }
        #result-content em { color: var(--ku-gold); font-style: italic; }
        .error { background-color: #fff5f5; border-left: 4px solid var(--error-color); color: #c53030; }
        footer { text-align: center; margin-top: 60px; color: var(--ku-dark); font-size: 14px; padding: 15px; border-top: 1px solid var(--ku-gold-light); }
        .powered-by { display: inline-block; padding: 5px 15px; background-color: var(--ku-gold-light); border-radius: 20px; font-size: 14px; margin-top: 10px; color: var(--ku-dark); }
        @media (max-width: 768px) { .feedback-input-container { grid-template-columns: 1fr; } h3 { font-size: 28px; } }
        """

def get_script():
    try:
        with open('script.js', 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return """
        document.addEventListener('DOMContentLoaded', function() {
          const form = document.getElementById('upload-form');
          const submitButton = form.querySelector('button[type="submit"]');
          const resultDiv = document.getElementById('result');
          const resultContentDiv = document.getElementById('result-content');
          const loadingDiv = document.getElementById('loading');
          
          // 파일 입력 UI 개선
          const fileInputs = document.querySelectorAll('input[type="file"]');
          fileInputs.forEach(input => {
            input.addEventListener('change', function() {
              if (this.files.length > 0) {
                const fileName = this.files[0].name;
                const fileInfo = this.nextElementSibling;
                fileInfo.textContent = `선택된 파일: ${fileName}`;
                fileInfo.style.color = '#8B1F41';
                this.parentElement.classList.add('file-selected');
              } else {
                const fileInfo = this.nextElementSibling;
                fileInfo.textContent = this.id === 'problem-answer' 
                  ? '문제와 작성한 답안을 JPEG, PNG 또는 PDF 파일로 업로드하세요.' 
                  : '성취기준, 수학적 대상, 루틴, 내러티브 등의 피드백 고려사항을 PDF 파일로 업로드하세요.';
                fileInfo.style.color = '#666';
                this.parentElement.classList.remove('file-selected');
              }
            });
          });
          
          // 폼 제출 처리
          form.onsubmit = async (e) => {
            e.preventDefault();
            
            try {
              // 제출 버튼 비활성화 및 로딩 표시
              submitButton.disabled = true;
              loadingDiv.style.display = 'block';
              resultDiv.style.display = 'none';
              resultDiv.classList.remove('error');
              
              // 스크롤 애니메이션
              window.scrollTo({
                top: loadingDiv.offsetTop - 100,
                behavior: 'smooth'
              });
              
              // 폼 요소 가져오기
              const problemAnswerFile = document.getElementById('problem-answer').files[0];
              const feedbackCriteriaFile = document.getElementById('feedback-criteria').files[0];
              
              // 텍스트 입력값 가져오기
              const achievementStandard = document.getElementById('achievement-standard').value;
              const mathObject = document.getElementById('math-object').value;
              const routine = document.getElementById('routine').value;
              const narrative = document.getElementById('narrative').value;
              const other = document.getElementById('other').value;
              
              // 파일 유효성 검사
              if (!problemAnswerFile) {
                throw new Error('문제 및 작성한 답안 파일을 업로드해주세요.');
              }
              
              // 서버용 FormData 생성
              const formData = new FormData();
              formData.append('problem-answer', problemAnswerFile);
              
              if (feedbackCriteriaFile) {
                formData.append('feedback-criteria', feedbackCriteriaFile);
              }
              
              // 텍스트 입력을 FormData에 추가
              formData.append('achievement-standard', achievementStandard);
              formData.append('math-object', mathObject);
              formData.append('routine', routine);
              formData.append('narrative', narrative);
              formData.append('other', other);
              
              // 서버로 전송
              const response = await fetch('/analyze', {
                method: 'POST',
                body: formData
              });
              
              if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`서버 오류 (${response.status}): ${errorText}`);
              }
              
              // 결과 처리
              const resultText = await response.text();
              
              // 텍스트에 마크다운 형식의 내용이 있으면 HTML로 변환
              const formattedText = resultText
                .replace(/\\n/g, '<br>')
                .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
                .replace(/\\*(.*?)\\*/g, '<em>$1</em>')
                .replace(/^# (.*?)$/gm, '<h3>$1</h3>')
                .replace(/^## (.*?)$/gm, '<h4>$1</h4>')
                .replace(/^### (.*?)$/gm, '<h5>$1</h5>');
              
              resultContentDiv.innerHTML = formattedText;
              resultDiv.style.display = 'block';
              
              // 결과로 스크롤 애니메이션
              setTimeout(() => {
                window.scrollTo({
                  top: resultDiv.offsetTop - 50,
                  behavior: 'smooth'
                });
              }, 300);
              
            } catch (error) {
              console.error('Error:', error);
              resultContentDiv.innerHTML = `<i class="fas fa-exclamation-triangle"></i> 오류가 발생했습니다: ${error.message}`;
              resultDiv.style.display = 'block';
              resultDiv.classList.add('error');
              
              // 오류 메시지로 스크롤
              setTimeout(() => {
                window.scrollTo({
                  top: resultDiv.offsetTop - 50,
                  behavior: 'smooth'
                });
              }, 300);
            } finally {
              // 제출 버튼 재활성화 및 로딩 숨기기
              submitButton.disabled = false;
              loadingDiv.style.display = 'none';
            }
          };
        });
        """

@app.route("/")
def index():
    html_template = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>"인공지능 수학" 문제풀이 피드백 AI 챗봇 (Gemini)</title>
      <style>
        {{ styles }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h3> "인공지능 수학" 문제풀이 피드백 AI 챗봇</h3>
          <p class="subtitle">AI MathGemini</p>
        </div>

        <div class="main-content">
          <form id="upload-form" enctype="multipart/form-data">
            <div class="form-group">
              <label for="problem-answer">문제 및 작성한 답</label>
              <input type="file" id="problem-answer" name="problem-answer" accept="image/jpeg,image/jpg,image/png,application/pdf" required />
              <small class="file-info">문제와 작성한 답안을 JPEG, PNG 또는 PDF 파일로 업로드하세요.</small>
            </div>
            
            <div class="form-group">
              <label for="feedback-criteria">피드백 고려사항 PDF (선택사항)</label>
              <input type="file" id="feedback-criteria" name="feedback-criteria" accept="application/pdf" />
              <small class="file-info">성취기준, 수학적 대상, 루틴, 내러티브 등의 피드백 고려사항을 PDF 파일로 업로드하세요.</small>
            </div>
            
            <div class="form-group">
              <label>피드백 고려사항 직접입력 (선택사항)</label>
              <div class="feedback-input-container">
                <div class="feedback-input-item">
                  <label for="achievement-standard">성취기준</label>
                  <textarea id="achievement-standard" name="achievement-standard" placeholder="수학적 성취기준을 입력하세요"></textarea>
                </div>
                
                <div class="feedback-input-item">
                  <label for="math-object">수학적 대상</label>
                  <textarea id="math-object" name="math-object" placeholder="다루는 수학적 대상을 입력하세요"></textarea>
                </div>
                
                <div class="feedback-input-item">
                  <label for="routine">루틴</label>
                  <textarea id="routine" name="routine" placeholder="문제 해결 루틴을 입력하세요"></textarea>
                </div>
                
                <div class="feedback-input-item">
                  <label for="narrative">내러티브</label>
                  <textarea id="narrative" name="narrative" placeholder="내러티브 요소를 입력하세요"></textarea>
                </div>
                
                <div class="feedback-input-item">
                  <label for="other">기타</label>
                  <textarea id="other" name="other" placeholder="기타 고려사항을 입력하세요"></textarea>
                </div>
              </div>
            </div>

            <button type="submit">피드백 받기</button>
          </form>

          <div id="loading" style="display: none;">
            <div class="spinner"></div>
            <p>답안을 분석하고 있습니다...</p>
          </div>

          <div id="result" style="display: none;">
            <h4>피드백 결과</h4>
            <div id="result-content"></div>
          </div>
        </div>

        <footer>
          <p>개발: 고려대학교 대학원 교과교육학과 수학교육전공 오영석</p>
          <div class="powered-by">
            <span>Powered by Gemini AI</span>
          </div>
        </footer>
      </div>

      <script>
        {{ script }}
      </script>
    </body>
    </html>
    """
    
    # CSS와 JS를 인라인으로 포함
    return render_template_string(
        html_template, 
        styles=get_styles(), 
        script=get_script()
    )

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
                criteria_ext = criteria_file.filename.rsplit('.', 1)[1].lower()
                if criteria_ext == 'pdf':
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
