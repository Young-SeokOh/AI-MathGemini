document.addEventListener('DOMContentLoaded', function() {
  // 폼 요소 참조
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
      resultDiv.classList.remove('error'); // 이전 오류 클래스 제거
      
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
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
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
