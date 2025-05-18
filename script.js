document.getElementById('upload-form').onsubmit = async (e) => {
    e.preventDefault();
    
    const form = document.getElementById('upload-form');
    const submitButton = form.querySelector('button[type="submit"]');
    const resultDiv = document.getElementById('result');
    const resultContentDiv = document.getElementById('result-content');
    const loadingDiv = document.getElementById('loading');
    
    try {
      // Disable submit button and show loading
      submitButton.disabled = true;
      loadingDiv.style.display = 'block';
      resultDiv.style.display = 'none';
      
      // Get form elements
      const problemAnswerFile = document.getElementById('problem-answer').files[0];
      const feedbackCriteriaFile = document.getElementById('feedback-criteria').files[0];
      
      // Get text input values
      const achievementStandard = document.getElementById('achievement-standard').value;
      const mathObject = document.getElementById('math-object').value;
      const routine = document.getElementById('routine').value;
      const narrative = document.getElementById('narrative').value;
      const other = document.getElementById('other').value;
      
      // Validate files
      if (!problemAnswerFile) {
        throw new Error('문제 및 작성한 답안 파일을 업로드해주세요.');
      }
      
      // Create FormData for server
      const formData = new FormData();
      formData.append('problem-answer', problemAnswerFile);
      
      if (feedbackCriteriaFile) {
        formData.append('feedback-criteria', feedbackCriteriaFile);
      }
      
      // Add text inputs to FormData
      formData.append('achievement-standard', achievementStandard);
      formData.append('math-object', mathObject);
      formData.append('routine', routine);
      formData.append('narrative', narrative);
      formData.append('other', other);
      
      // Send to server
      const response = await fetch('/analyze', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`서버 오류 (${response.status}): ${errorText}`);
      }
      
      const resultText = await response.text();
      resultContentDiv.innerHTML = resultText.replace(/\n/g, '<br>');
      resultDiv.style.display = 'block';
      
    } catch (error) {
      console.error('Error:', error);
      resultContentDiv.innerHTML = `오류가 발생했습니다: ${error.message}`;
      resultDiv.style.display = 'block';
      resultDiv.classList.add('error');
    } finally {
      // Re-enable submit button and hide loading
      submitButton.disabled = false;
      loadingDiv.style.display = 'none';
    }
  };