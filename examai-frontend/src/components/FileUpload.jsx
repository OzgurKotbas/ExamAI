import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, Loader2, Plus, BookOpen, CheckCircle, FileText, Globe } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { notesApi, quizzesApi } from '../api';
import { useLanguage } from '../context/LanguageContext';

// Quiz Creation Modal Component
function QuizCreationModal({ notes, onClose, onQuizCreated }) {
  const [totalQuestions, setTotalQuestions] = useState(10);
  const [mcRatio, setMcRatio] = useState(1.0);
  const [difficulty, setDifficulty] = useState('medium');
  const [isCreating, setIsCreating] = useState(false);
  const { t, currentLanguage } = useLanguage();
  const [quizLanguage, setQuizLanguage] = useState(currentLanguage); // default: app language

  const handleCreateQuiz = async () => {
    if (!notes || notes.length === 0) return;
    
    setIsCreating(true);
    try {
      const response = await quizzesApi.create({
        note_id: notes[0].note_id,
        total_questions: totalQuestions,
        mc_ratio: mcRatio,
        difficulty: difficulty,
        language: quizLanguage,
      });
      
      toast.success(t('creating'));
      onQuizCreated(response.data);
      onClose();
    } catch (error) {
      console.error('Quiz creation error:', error);
      toast.error(error.response?.data?.detail || t('uploadError'));
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-md w-full p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 bg-indigo-100 dark:bg-indigo-900/50 rounded-xl flex items-center justify-center">
            <BookOpen className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">{t('createQuizTitle')}</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">{notes.length} {t('resourcesUploaded')}</p>
          </div>
        </div>

        <div className="space-y-4 mb-6">
          {/* Total Questions */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('questions')}: <span className="text-indigo-600 font-bold">{totalQuestions}</span>
            </label>
            <input
              type="range"
              min="1"
              max="30"
              value={totalQuestions}
              onChange={(e) => setTotalQuestions(Number(e.target.value))}
              className="w-full h-2 bg-gray-200 dark:bg-gray-600 rounded-lg appearance-none cursor-pointer accent-indigo-600"
            />
            <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
              <span>1</span>
              <span>30</span>
            </div>
          </div>

          {/* MC Ratio */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('quizType')}
            </label>
            <div className="flex gap-2">
              <button
                onClick={() => setMcRatio(1.0)}
                className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all border-2 flex flex-col items-center justify-center gap-2 ${
                  mcRatio === 1.0
                    ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300'
                    : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:border-indigo-300'
                }`}
              >
                <CheckCircle className={`w-6 h-6 ${mcRatio === 1.0 ? 'text-indigo-600' : 'text-gray-400'}`} />
                {t('onlyTest')}
              </button>
              <button
                onClick={() => setMcRatio(0.0)}
                className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all border-2 flex flex-col items-center justify-center gap-2 ${
                  mcRatio === 0.0
                    ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300'
                    : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:border-indigo-300'
                }`}
              >
                <FileText className={`w-6 h-6 ${mcRatio === 0.0 ? 'text-indigo-600' : 'text-gray-400'}`} />
                {t('onlyClassic')}
              </button>
            </div>
          </div>

          {/* Difficulty */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {t('difficultyLevel')}
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { value: 'easy', label: t('easy'), color: 'green' },
                { value: 'medium', label: t('medium'), color: 'yellow' },
                { value: 'hard', label: t('hard'), color: 'red' },
              ].map((level) => (
                <button
                  key={level.value}
                  onClick={() => setDifficulty(level.value)}
                  className={`py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                    difficulty === level.value
                      ? `bg-${level.color}-100 text-${level.color}-700 ring-2 ring-${level.color}-500`
                      : 'bg-gray-100 dark:bg-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-500'
                  }`}
                >
                  {level.label}
                </button>
              ))}
            </div>
          </div>

          {/* Language Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 flex items-center gap-2">
              <Globe className="w-4 h-4 text-indigo-500" />
              {t('quizLanguage')}
            </label>
            <p className="text-xs text-gray-400 dark:text-gray-500 mb-2">{t('quizLangDesc')}</p>
            <div className="flex gap-2">
              <button
                onClick={() => setQuizLanguage('tr')}
                className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-semibold transition-all border-2 ${
                  quizLanguage === 'tr'
                    ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300'
                    : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:border-indigo-300'
                }`}
              >
                {t('quizLangTurkish')}
              </button>
              <button
                onClick={() => setQuizLanguage('en')}
                className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-semibold transition-all border-2 ${
                  quizLanguage === 'en'
                    ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300'
                    : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:border-indigo-300'
                }`}
              >
                {t('quizLangEnglish')}
              </button>
            </div>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 py-3 px-4 bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-200 rounded-lg font-medium hover:bg-gray-200 transition-colors"
            disabled={isCreating}
          >
            {t('later')}
          </button>
          <button
            onClick={handleCreateQuiz}
            disabled={isCreating}
            className="flex-1 py-3 px-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {isCreating ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                {t('creatingQuiz')}
              </>
            ) : (
              <>
                <CheckCircle className="w-5 h-5" />
                {t('createQuizTitle')}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function FileUpload({ onUploadComplete, onNotesCreated }) {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadedNotes, setUploadedNotes] = useState(null);
  const [showQuizModal, setShowQuizModal] = useState(false);
  const { t } = useLanguage();

  const ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.txt', '.docx'];

  const validateFile = (file) => {
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return { valid: false, reason: t('unsupportedFormat') || `Unsupported format: ${ext}` };
    }
    return { valid: true };
  };

  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    let filesToProcess = [];
    let rejectedCount = 0;

    const allFiles = [...acceptedFiles, ...rejectedFiles.map(r => r.file)];
    
    if (allFiles.length === 0) return;

    const totalFiles = selectedFiles.length + allFiles.length;
    if (totalFiles > 10) {
      toast.error(t('maxFilesError'));
      return;
    }

    const currentTotalSize = selectedFiles.reduce((acc, f) => acc + f.size, 0);
    let newTotalSize = currentTotalSize;

    allFiles.forEach((file) => {
      const validation = validateFile(file);
      if (validation.valid) {
        if (newTotalSize + file.size > 20 * 1024 * 1024) {
          rejectedCount++;
          toast.error(`${file.name}: ${t('totalSizeError')}`);
        } else {
          filesToProcess.push(file);
          newTotalSize += file.size;
        }
      } else {
        rejectedCount++;
        toast.error(`${file.name}: ${validation.reason}`);
      }
    });

    if (filesToProcess.length > 0) {
      setSelectedFiles((prev) => [...prev, ...filesToProcess]);
      if (rejectedCount > 0) {
        toast.success(`${filesToProcess.length} ${t('file')}, ${rejectedCount} ${t('file')}`);
      }
    }
  }, [selectedFiles, t]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 10,
    disabled: isLoading,
  });

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      toast.error(t('selectFileError'));
      return;
    }

    setIsLoading(true);
    try {
      const response = await notesApi.upload(selectedFiles);
      
      if (response.data.notes && response.data.notes.length > 0) {
        toast.success(`${response.data.notes.length} ${t('files')}!`);
        setUploadedNotes(response.data.notes);
        setShowQuizModal(true);
        if (onNotesCreated) {
          onNotesCreated(response.data.notes);
        }
      }
      
      if (onUploadComplete) {
        onUploadComplete(response.data);
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(error.response?.data?.detail?.message || t('uploadError'));
    } finally {
      setIsLoading(false);
    }
  };

  const removeFile = (index) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const clearAllFiles = () => {
    setSelectedFiles([]);
    setUploadedNotes(null);
    setShowQuizModal(false);
  };

  return (
    <>
      <div className="space-y-4">
        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
            isDragActive
              ? 'border-indigo-500 bg-indigo-50'
              : selectedFiles.length > 0
              ? 'border-green-500 bg-green-50'
              : 'border-gray-300 hover:border-indigo-300 hover:bg-gray-50'
          } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <input {...getInputProps()} />
          
          {selectedFiles.length > 0 ? (
            <div className="flex items-center justify-center gap-3">
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900/50 rounded-lg flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="text-left">
                <p className="font-medium text-gray-900 dark:text-white">{selectedFiles.length} {t('filesSelected')}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {t('totalSize')} {(selectedFiles.reduce((acc, f) => acc + f.size, 0) / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
          ) : (
            <div>
              <div className="w-16 h-16 bg-indigo-100 dark:bg-indigo-900/50 rounded-full flex items-center justify-center mx-auto mb-4">
                <Upload className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
              </div>
              <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                {isDragActive ? t('dropFilesHere') : t('clickOrDropFiles')}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {t('maxFilesInfo')}
              </p>
            </div>
          )}
        </div>

        {/* Selected Files List */}
        {selectedFiles.length > 0 && (
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 space-y-2">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{t('selectedFiles')} ({selectedFiles.length}/10)</span>
              <button
                onClick={clearAllFiles}
                className="text-xs text-red-500 hover:text-red-700 font-medium"
                disabled={isLoading}
              >
                {t('removeAll')}
              </button>
            </div>
            {selectedFiles.map((file, index) => (
              <div key={index} className="flex items-center justify-between bg-white p-3 rounded-lg shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <File className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-gray-900 truncate max-w-[200px] sm:max-w-xs">{file.name}</p>
                    <p className="text-xs text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
                {!isLoading && (
                  <button
                    onClick={() => removeFile(index)}
                    className="p-1 hover:bg-red-100 rounded-full transition-colors flex-shrink-0"
                  >
                    <X className="w-5 h-5 text-red-500" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Add More Files Button (if less than 5 files) */}
        {selectedFiles.length > 0 && selectedFiles.length < 10 && !isLoading && (
          <button
            {...getRootProps()}
            className="w-full py-2 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg text-gray-600 dark:text-gray-400 hover:border-indigo-400 hover:text-indigo-600 transition-all flex items-center justify-center gap-2"
          >
            <input {...getInputProps()} />
            <Plus className="w-4 h-4" />
            {t('addMoreFiles')}
          </button>
        )}

        {/* Upload Button */}
        {selectedFiles.length > 0 && (
          <button
            onClick={handleUpload}
            disabled={isLoading}
            className="w-full py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                {t('loading')}
              </>
            ) : (
              <>
                <Upload className="w-5 h-5" />
                {selectedFiles.length} {t('uploadAndProcess')}
              </>
            )}
          </button>
        )}
      </div>

      {/* Quiz Creation Modal */}
      {showQuizModal && uploadedNotes && (
        <QuizCreationModal
          notes={uploadedNotes}
          onClose={() => {
            setShowQuizModal(false);
            clearAllFiles();
          }}
          onQuizCreated={(quizData) => {
            // Quiz created successfully
            console.log('Quiz created:', quizData);
          }}
        />
      )}
    </>
  );
}
