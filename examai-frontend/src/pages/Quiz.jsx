import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, Brain, CheckCircle, Loader2, AlertCircle, Award, Download
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { quizzesApi } from '../api';
import { useLanguage } from '../context/LanguageContext';

export default function Quiz() {
  const { quizId } = useParams();
  const navigate = useNavigate();
  const { t, currentLanguage } = useLanguage();
  
  const [quizStatus, setQuizStatus] = useState('pending'); // pending, generating, ready, failed
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [gradingId, setGradingId] = useState(null);
  const [gradingStatus, setGradingStatus] = useState(null); // pending, grading, completed, failed
  const [results, setResults] = useState(null);
  const [isExporting, setIsExporting] = useState(false);
  const resultsRef = useRef(null);

  useEffect(() => {
    fetchQuizStatus();
  }, [quizId]);

  useEffect(() => {
    let interval;
    if (quizStatus === 'pending' || quizStatus === 'generating') {
      interval = setInterval(fetchQuizStatus, 5000);
    }
    return () => clearInterval(interval);
  }, [quizStatus]);

  useEffect(() => {
    let interval;
    if (gradingId && (gradingStatus === 'pending' || gradingStatus === 'grading')) {
      interval = setInterval(checkGradingStatus, 5000);
    }
    return () => clearInterval(interval);
  }, [gradingId, gradingStatus]);

  const fetchQuizStatus = async () => {
    try {
      const res = await quizzesApi.getStatus(quizId);
      setQuizStatus(res.data.status);
      
      if (res.data.status === 'ready' && questions.length === 0) {
        fetchQuestions();
        if (res.data.latest_grading_id) {
          setGradingId(res.data.latest_grading_id);
          setGradingStatus('completed');
          fetchResults(res.data.latest_grading_id);
        }
      }
    } catch (error) {
      toast.error(t('quizStatusError'));
    }
  };

  const fetchQuestions = async () => {
    try {
      const res = await quizzesApi.getQuestions(quizId);
      setQuestions(res.data);
    } catch (error) {
      toast.error(t('quizQuestionsError'));
    }
  };

  const checkGradingStatus = async () => {
    try {
      const res = await quizzesApi.getGradingStatus(quizId, gradingId);
      setGradingStatus(res.data.status);
      
      if (res.data.status === 'completed') {
        fetchResults();
      }
    } catch (error) {
      console.error(error);
    }
  };

  const fetchResults = async (gId) => {
    const idToUse = gId || gradingId;
    if (!idToUse) return;
    
    try {
      const res = await quizzesApi.getResults(quizId, idToUse);
      setResults(res.data);
      if (!gId) toast.success(t('gradingCompleteInfo'));
    } catch (error) {
      toast.error(t('gradingResultsError'));
    }
  };

  const handleAnswerChange = (questionId, value) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      // Tüm soruları gönder; cevaplanmamış olanları boş string olarak dahil et
      const formattedAnswers = questions.map((q) => ({
        question_id: q.id,
        user_answer: answers[q.id] || ''
      }));

      const res = await quizzesApi.submit(quizId, formattedAnswers);
      const { grading_id, status } = res.data;
      
      setGradingId(grading_id);
      setGradingStatus(status);

      if (status === 'completed') {
        toast.success(t('quizSubmitted'));
        // Fetch results immediately if already completed
        const resultsRes = await quizzesApi.getResults(quizId, grading_id);
        setResults(resultsRes.data);
        
        // If it was a test, we might already have the answers in questions,
        // but fetching results is the canonical way to get the feedback.
      } else {
        toast.success(t('quizSubmitted'));
      }

    } catch (error) {
      toast.error(t('quizSubmitError'));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!resultsRef.current) return;
    setIsExporting(true);
    toast.loading('PDF hazırlanıyor...', { id: 'pdf-export' });
    try {
      const { default: jsPDF } = await import('jspdf');
      const { default: html2canvas } = await import('html2canvas');

      const element = resultsRef.current;

      // ── Seçenek C: scale 1.5 + JPEG %85 ──────────────────────────────────
      const canvas = await html2canvas(element, {
        scale: 1.5,           // 2'den 1.5'e düşürüldü → piksel sayısı %44 azaldı
        useCORS: true,
        backgroundColor: '#f9fafb',
        logging: false,
      });

      const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
      const pageWidth  = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const margin     = 10;
      const imgWidth   = pageWidth - margin * 2;

      let remainingHeight = (canvas.height * imgWidth) / canvas.width;
      let sourceY         = 0;
      let isFirstPage     = true;

      while (remainingHeight > 0) {
        const sliceHeight  = Math.min(remainingHeight, pageHeight - margin * 2);
        const sliceCanvas  = document.createElement('canvas');
        sliceCanvas.width  = canvas.width;
        sliceCanvas.height = Math.round((sliceHeight * canvas.width) / imgWidth);

        const ctx = sliceCanvas.getContext('2d');
        ctx.drawImage(
          canvas,
          0, sourceY, canvas.width, sliceCanvas.height,
          0, 0,       canvas.width, sliceCanvas.height
        );

        // JPEG %85 – PNG'den ~%60 daha küçük
        const sliceData = sliceCanvas.toDataURL('image/jpeg', 0.85);

        if (!isFirstPage) pdf.addPage();
        pdf.addImage(sliceData, 'JPEG', margin, margin, imgWidth, sliceHeight);

        sourceY         += sliceCanvas.height;
        remainingHeight -= sliceHeight;
        isFirstPage      = false;
      }

      const fileName = `ExamAI_Sonuc_${new Date().toLocaleDateString('tr-TR').replace(/\./g, '-')}.pdf`;
      const pdfBlob  = pdf.output('blob');

      // ── Klasör seçimi: File System Access API (Chrome/Edge) ───────────────
      if (typeof window.showSaveFilePicker === 'function') {
        try {
          const fileHandle = await window.showSaveFilePicker({
            suggestedName: fileName,
            types: [{
              description: 'PDF Dosyası',
              accept: { 'application/pdf': ['.pdf'] },
            }],
          });
          const writable = await fileHandle.createWritable();
          await writable.write(pdfBlob);
          await writable.close();
          toast.success('PDF seçilen konuma kaydedildi!', { id: 'pdf-export' });
        } catch (pickerErr) {
          // Kullanıcı "İptal" düğmesine bastıysa sessizce çık
          if (pickerErr.name === 'AbortError') {
            toast.dismiss('pdf-export');
          } else {
            // Picker çalıştı ama yazma başarısız → fallback
            pdf.save(fileName);
            toast.success('PDF indirildi!', { id: 'pdf-export' });
          }
        }
      } else {
        // Fallback: Firefox / Safari – tarayıcının varsayılan indirme klasörüne kaydet
        pdf.save(fileName);
        toast.success('PDF başarıyla indirildi!', { id: 'pdf-export' });
      }

    } catch (err) {
      console.error(err);
      toast.error('PDF oluşturulamadı.', { id: 'pdf-export' });
    } finally {
      setIsExporting(false);
    }
  };

  if (quizStatus === 'pending' || quizStatus === 'generating') {

    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-900">
        <Loader2 className="w-12 h-12 text-indigo-600 animate-spin mb-4" />
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          {t('quizGeneratingTitle')}
        </h2>
        <p className="text-gray-500 mt-2">{t('quizGeneratingDesc')}</p>
        <button 
          onClick={() => navigate('/dashboard')}
          className="mt-6 text-indigo-600 hover:underline"
        >
          {t('backToHome')}
        </button>
      </div>
    );
  }

  if (quizStatus === 'failed') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-900">
        <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">{t('quizFailedTitle')}</h2>
        <button 
          onClick={() => navigate('/dashboard')}
          className="mt-6 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
        >
          {t('backToHome')}
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <button 
            onClick={() => navigate('/dashboard')}
            className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-indigo-600 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            {t('goBack')}
          </button>
          <div className="flex items-center gap-3">
            <Brain className="w-8 h-8 text-indigo-600" />
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t('aiQuiz')}</h1>
          </div>
          {/* PDF Download Button – only shown when results are ready */}
          {results ? (
            <button
              onClick={handleDownloadPDF}
              disabled={isExporting}
              title="Sınav sonuçlarını PDF olarak indir"
              className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-indigo-200 dark:border-indigo-700 text-indigo-600 dark:text-indigo-400 rounded-xl font-semibold text-sm shadow-sm hover:bg-indigo-50 dark:hover:bg-indigo-900/30 hover:border-indigo-400 active:scale-95 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {isExporting
                ? <Loader2 className="w-4 h-4 animate-spin" />
                : <Download className="w-4 h-4" />}
              {isExporting ? 'Hazırlanıyor...' : 'PDF İndir'}
            </button>
          ) : (
            <div className="w-28" /> /* spacer to keep header balanced */
          )}
        </div>



        {/* Grading Status */}
        {gradingId && !results && (
          <div className="bg-white dark:bg-gray-800 rounded-xl p-8 mb-8 text-center shadow-sm">
            <Loader2 className="w-10 h-10 text-indigo-600 animate-spin mx-auto mb-4" />
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
              {t('gradingTitle')}
            </h3>
            <p className="text-gray-500 mt-2">{t('gradingDesc')}</p>
          </div>
        )}

        {/* Questions List */}
        {!results && !gradingId && questions.map((q, index) => (
          <div key={q.id} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 mb-6 border border-gray-100 dark:border-gray-700">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-8 h-8 bg-indigo-100 dark:bg-indigo-900/50 rounded-full flex items-center justify-center font-bold text-indigo-600 dark:text-indigo-400">
                {index + 1}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  {q.text}
                </h3>
                
                {q.type === 'multiple_choice' ? (
                  <div className="space-y-3">
                    {Object.entries(q.options || {}).map(([key, value]) => (
                      <label 
                        key={key}
                        className={`flex items-center p-4 border rounded-lg cursor-pointer transition-colors ${
                          answers[q.id] === key 
                            ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20' 
                            : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                        }`}
                      >
                        <input
                          type="radio"
                          name={`question-${q.id}`}
                          value={key}
                          checked={answers[q.id] === key}
                          onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                          className="w-4 h-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                        />
                        <span className="ml-3 font-medium text-gray-700 dark:text-gray-300 w-6">{key})</span>
                        <span className="text-gray-900 dark:text-gray-100">{value}</span>
                      </label>
                    ))}
                  </div>
                ) : (
                  <textarea
                    rows={4}
                    placeholder={t('writeAnswerPlaceholder')}
                    value={answers[q.id] || ''}
                    onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                    className="w-full p-4 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
                  />
                )}
              </div>
            </div>
          </div>
        ))}

        {/* Results View – wrapped in ref for PDF export */}
        {results && (
          <div ref={resultsRef} className="pdf-export-zone">
            {/* Results Banner inside PDF zone */}
            <div className="bg-gradient-to-r from-green-500 to-emerald-600 rounded-2xl p-6 mb-8 text-white shadow-lg flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold mb-1">{t('quizResultTitle')}</h2>
                <p className="opacity-90">{t('quizResultDesc')}</p>
              </div>
              <div className="text-center">
                <span className="text-4xl font-black">{results.total_score}</span>
                <span className="text-xl"> / {results.max_score}</span>
                <p className="text-sm opacity-90 mt-1">% {results.percentage.toFixed(1)} {t('successRate')}</p>
              </div>
            </div>

            {/* Question result cards */}
            {questions.map((q, index) => {
              const result = results.grading_results.find(r => r.question_id === q.id);
              const questionScore = result?.score ?? 0;
              const maxPerQuestion = questions.length > 0 ? (results.max_score / questions.length) : 100;
              const isZero = questionScore === 0;
              const isFull = Math.round(questionScore) >= Math.round(maxPerQuestion);
              const scoreColor = isZero ? 'bg-red-500' : isFull ? 'bg-green-500' : 'bg-orange-500';
              const cardBg = isZero
                ? 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800'
                : isFull
                  ? 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800'
                  : 'bg-orange-50 dark:bg-orange-950/20 border-orange-200 dark:border-orange-800';
              const feedbackBorder = isZero
                ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
                : isFull
                  ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                  : 'border-orange-500 bg-orange-50 dark:bg-orange-900/20';
              const iconColor = isZero ? 'text-red-500' : isFull ? 'text-green-500' : 'text-orange-500';
              return (
                <div key={q.id} className={`rounded-xl shadow-sm p-6 mb-6 border relative overflow-hidden ${cardBg}`}>
                  {/* Score indicator badge */}
                  <div className={`absolute top-0 right-0 px-4 py-1 font-bold text-white text-sm rounded-bl-xl ${scoreColor}`}>
                    {t('score')}: {Math.round(questionScore)}
                  </div>

                  <div className="flex items-start gap-4">
                    <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center font-bold text-white ${scoreColor}`}>
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0 pr-16">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                        {q.text}
                      </h3>

                      {/* User's Answer */}
                      <div className="mb-4 bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
                        <p className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-1">{t('yourAnswer')}:</p>
                        {q.type === 'multiple_choice' ? (
                          <p className="text-gray-900 dark:text-white font-medium">
                            {result.user_answer} - {q.options[result.user_answer]}
                          </p>
                        ) : (
                          <p className="text-gray-900 dark:text-white whitespace-pre-wrap">
                            {result.user_answer}
                          </p>
                        )}
                      </div>

                      {/* Feedback Details */}
                      {result && (
                        <div className={`p-4 rounded-lg border-l-4 ${feedbackBorder}`}>
                          <h4 className="flex items-center gap-2 font-bold mb-2 text-gray-900 dark:text-white">
                            <Award className={`w-5 h-5 ${iconColor}`} />
                            {t('feedbackInfo')}
                          </h4>
                          <p className="text-gray-700 dark:text-gray-300 leading-relaxed text-sm whitespace-pre-wrap">
                            {result.feedback}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}



        {/* Action Button */}
        {!results && !gradingId && (
          <div className="flex justify-end mt-8 mb-12">
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="flex items-center gap-2 px-8 py-4 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 disabled:opacity-50 transition-all shadow-md"
            >
              {isSubmitting ? <Loader2 className="w-5 h-5 animate-spin" /> : <CheckCircle className="w-5 h-5" />}
              {t('submitQuiz')}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
