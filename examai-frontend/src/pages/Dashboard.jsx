import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FileText, 
  Plus, 
  History, 
  User, 
  BookOpen, 
  Brain,
  ChevronRight,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader2,
  Sparkles,
  Zap,
  Trash2,
  BarChart2,
  TrendingUp,
  TrendingDown,
  Globe,
  X,
  ChevronDown,
  ChevronUp,
  Key,
  Info
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';
import { notesApi, quizzesApi } from '../api';
import FileUpload from '../components/FileUpload';
import ProfileMenu from '../components/ProfileMenu';
import QuizCategories from '../components/QuizCategories';
import ConfirmModal from '../components/ConfirmModal';

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { theme } = useTheme();
  const { t, currentLanguage } = useLanguage();
  const [activeTab, setActiveTab] = useState('upload'); // upload, categories, history
  const [notes, setNotes] = useState([]);
  const [quizzes, setQuizzes] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showQuizModal, setShowQuizModal] = useState(false);
  const [selectedNote, setSelectedNote] = useState(null);
  const [generatingQuizIds, setGeneratingQuizIds] = useState(new Set());
  const [quizConfig, setQuizConfig] = useState({
    question_count: 10,
    test_ratio: 100,
    difficulty: 'medium',
    language: 'tr',  // Default: Turkish
  });
  const [creatingQuiz, setCreatingQuiz] = useState(false);
  const [quizToDelete, setQuizToDelete] = useState(null);
  const [noteToDelete, setNoteToDelete] = useState(null);
  const [isResourcesExpanded, setIsResourcesExpanded] = useState(false);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [showWelcomeModal, setShowWelcomeModal] = useState(false);
  // ref: generatingQuizIds'in güncel değerini interval callback'te okumak için
  const generatingQuizIdsRef = useRef(new Set());
  const generatingSinceRef = useRef(new Map());
  const staleWarnedRef = useRef(new Set());
  const STALE_PENDING_MS = 2 * 60 * 1000;

  useEffect(() => {
    fetchData();
    // Sync language config with app language
    setQuizConfig(prev => ({ ...prev, language: currentLanguage }));

    // Show welcome modal only on first login ever
    const hasSeenWelcome = localStorage.getItem('examai_welcome_shown');
    if (!hasSeenWelcome) {
      setTimeout(() => setShowWelcomeModal(true), 800);
    }
  }, []);

  const handleCloseWelcome = () => {
    setShowWelcomeModal(false);
    localStorage.setItem('examai_welcome_shown', '1');
  };

  // BUG FIX: Polling sadece aktif üretim varken çalışır.
  // Önceki sürümde interval HER ZAMAN 5sn'de bir tetikleniyordu;
  // bu gereksiz Redis komutlarına (LRANGE, GET vb.) yol açıyordu.
  useEffect(() => {
    if (generatingQuizIds.size === 0) return; // Üretim yoksa interval kurma
    const interval = setInterval(() => {
      checkGeneratingQuizzesRef.current();
    }, 8000); // 5s → 8s: komut sayısını %37 azaltır
    return () => clearInterval(interval);
  }, [generatingQuizIds.size]);

  const fetchData = async () => {
    try {
      const [notesRes, quizzesRes] = await Promise.all([
        notesApi.list(),
        quizzesApi.list(),
      ]);
      const noteItems = Array.isArray(notesRes.data)
        ? notesRes.data
        : notesRes.data?.notes || [];
      setNotes(noteItems.map((note) => ({
        ...note,
        id: note.id || note.note_id,
        filename: note.filename || note.original_filename,
      })));
      setQuizzes(quizzesRes.data);
      
      // Track generating quizzes
      const generating = new Set();
      quizzesRes.data.forEach(q => {
        if (q.status === 'pending' || q.status === 'generating') {
          generating.add(q.id);
          if (!generatingSinceRef.current.has(q.id)) {
            const startedAt = q.created_at ? new Date(q.created_at).getTime() : Date.now();
            generatingSinceRef.current.set(q.id, startedAt);
          }
        }
      });
      setGeneratingQuizIds(generating);
      generatingQuizIdsRef.current = generating;
    } catch (error) {
      toast.error(t('error'));
    }
  };

  const checkGeneratingQuizzes = useCallback(async () => {
    // Ref üzerinden güncel değeri oku (stale closure problemini önler)
    if (generatingQuizIdsRef.current.size === 0) return;
    
    try {
      const quizzesRes = await quizzesApi.list();
      const updatedQuizzes = quizzesRes.data;
      
      // Update generating set
      const stillGenerating = new Set();
      generatingQuizIdsRef.current.forEach(quizId => {
        const quiz = updatedQuizzes.find(q => q.id === quizId);
        if (quiz) {
          if (quiz.status === 'ready') {
            generatingSinceRef.current.delete(quizId);
            staleWarnedRef.current.delete(quizId);
            toast.success(
              currentLanguage === 'tr'
                ? `Sınav #${quiz.id?.slice(-6) || '...'} hazır!`
                : `Quiz #${quiz.id?.slice(-6) || '...'} is ready!`,
              { icon: '🎉' }
            );
          } else if (quiz.status === 'failed') {
            generatingSinceRef.current.delete(quizId);
            staleWarnedRef.current.delete(quizId);
            toast.error(
              currentLanguage === 'tr'
                ? `Sınav #${quiz.id?.slice(-6) || '...'} oluşturulamadı`
                : `Quiz #${quiz.id?.slice(-6) || '...'} failed`
            );
          } else {
            stillGenerating.add(quizId);
            const startedAt = generatingSinceRef.current.get(quizId)
              ?? (quiz.created_at ? new Date(quiz.created_at).getTime() : Date.now());
            generatingSinceRef.current.set(quizId, startedAt);
            if (
              Date.now() - startedAt > STALE_PENDING_MS
              && !staleWarnedRef.current.has(quizId)
            ) {
              staleWarnedRef.current.add(quizId);
              toast.error(t('quizStuckPending'), { duration: 8000, icon: '⚠️' });
            }
          }
        }
      });
      
      generatingQuizIdsRef.current = stillGenerating;
      setGeneratingQuizIds(new Set(stillGenerating));
      setQuizzes(updatedQuizzes);
    } catch (error) {
      console.error('Error checking quiz status:', error);
    }
  }, [currentLanguage, t]);

  // Ref'i her zaman güncel callback'i işaretle
  const checkGeneratingQuizzesRef = useRef(checkGeneratingQuizzes);
  useEffect(() => {
    checkGeneratingQuizzesRef.current = checkGeneratingQuizzes;
  }, [checkGeneratingQuizzes]);

  const handleNotesCreated = (newNotes) => {
    fetchData(); // Refresh notes list
  };

  const handleUploadComplete = (data) => {
    // Upload completed
    console.log('Upload complete:', data);
  };

  const handleCreateQuiz = async () => {
    if (!selectedNote) {
      toast.error(t('selectResource'));
      return;
    }

    // Check free quiz limit for users without API key
    if (!user?.gemini_api_key && user?.free_quiz_count >= 3) {
      toast.error(
        currentLanguage === 'tr' 
          ? 'Ücretsiz sınav limitine (3) ulaştınız. Daha fazla sınav oluşturmak için API key giriniz.' 
          : 'Free quiz limit (3) reached. Please enter an API key to create more quizzes.',
        { duration: 6000, icon: '🔑' }
      );
      return;
    }
    
    setCreatingQuiz(true);
    try {
      const response = await quizzesApi.create({
        note_id: selectedNote.id,
        total_questions: quizConfig.question_count,
        mc_ratio: quizConfig.test_ratio / 100.0,
        difficulty: quizConfig.difficulty,
        language: quizConfig.language,
      });
      
      // Track this quiz as generating
      const newId = response.data.quiz_id;
      generatingSinceRef.current.set(newId, Date.now());
      staleWarnedRef.current.delete(newId);
      setGeneratingQuizIds(prev => {
        const next = new Set(prev);
        next.add(newId);
        generatingQuizIdsRef.current = next;
        return next;
      });
      
      toast.success(t('creating'), { icon: '⏳' });
      setShowQuizModal(false);
      await fetchData();
      // Polling'i hemen tetiklemek için ref üzerinden çağır
      checkGeneratingQuizzes();
      
      // Don't navigate immediately - let user know it's being generated
      setActiveTab('categories');
    } catch (error) {
      const message = error.response?.data?.detail || t('error');
      toast.error(message);
    } finally {
      setCreatingQuiz(false);
    }
  };

  const fetchAnalytics = async () => {
    setAnalyticsLoading(true);
    try {
      const res = await quizzesApi.getAnalytics();
      setAnalyticsData(res.data);
    } catch (error) {
      console.error('Analytics error:', error);
    } finally {
      setAnalyticsLoading(false);
    }
  };

  const confirmDeleteQuiz = async () => {
    if (!quizToDelete) return;
    
    try {
      await quizzesApi.delete(quizToDelete);
      toast.success(t('deleteSuccess'));
      setQuizzes(prev => prev.filter(q => q.id !== quizToDelete));
      
      setGeneratingQuizIds(prev => {
        const next = new Set(prev);
        next.delete(quizToDelete);
        return next;
      });
    } catch (error) {
      toast.error(t('error'));
    } finally {
      setQuizToDelete(null);
    }
  };

  const handleDeleteQuiz = (quizId, e) => {
    if (e) e.stopPropagation();
    setQuizToDelete(quizId);
  };

  const handleDeleteNote = (noteId, e) => {
    if (e) e.stopPropagation();
    setNoteToDelete(noteId);
  };

  const confirmDeleteNote = async () => {
    if (!noteToDelete) return;
    
    try {
      await notesApi.delete(noteToDelete);
      toast.success(t('deleteSuccess'));
      setNotes(prev => prev.filter(n => n.id !== noteToDelete));
      
      // Kaynağa bağlı sınavlar da silinmiş olabilir, listeyi güncelle
      const quizzesRes = await quizzesApi.list();
      setQuizzes(quizzesRes.data);
      
      if (selectedNote?.id === noteToDelete) {
        setSelectedNote(null);
      }
    } catch (error) {
      toast.error(t('error'));
    } finally {
      setNoteToDelete(null);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'processing':
        return <Loader2 className="w-5 h-5 text-yellow-500 animate-spin" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'completed':
      case 'ready':
        return t('quizStatusReady');
      case 'processing':
      case 'generating':
        return t('quizStatusGenerating');
      case 'pending':
        return t('quizStatusPending');
      case 'failed':
        return t('quizStatusFailed');
      default:
        return status;
    }
  };

  // Derived: is the free quiz limit reached?
  const isFreeLimitReached = !user?.gemini_api_key && (user?.free_quiz_count ?? 0) >= 3;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      {/* Navbar */}
      <nav className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center">
                <span className="text-xl font-bold text-white">E</span>
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                ExamAI
              </span>
            </div>
            
            <div className="flex items-center gap-4">
              {/* Quiz Generation Indicator */}
              {generatingQuizIds.size > 0 && (
                <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg">
                  <Loader2 className="w-4 h-4 text-yellow-600 dark:text-yellow-400 animate-spin" />
                  <span className="text-sm text-yellow-700 dark:text-yellow-400">
                    {generatingQuizIds.size} {t('creating')}
                  </span>
                </div>
              )}
              
              <ProfileMenu />
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2 transition-colors">
            {t('welcome')}, {user?.full_name?.split(' ')[0]}! 👋
          </h1>
          <p className="text-gray-600 dark:text-gray-400 transition-colors">
            {currentLanguage === 'tr' 
              ? 'Yapay zeka destekli sınavlar oluşturun ve performansınızı takip edin.'
              : 'Create AI-powered quizzes and track your performance.'}
          </p>
        </div>

        {/* Free Limit Banner */}
        {isFreeLimitReached && (
          <div className="mb-6 rounded-2xl border-2 border-orange-300 dark:border-orange-600 bg-gradient-to-r from-orange-50 to-amber-50 dark:from-orange-900/30 dark:to-amber-900/30 p-5 shadow-md">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-12 h-12 bg-orange-100 dark:bg-orange-900/50 rounded-xl flex items-center justify-center">
                <Key className="w-6 h-6 text-orange-600 dark:text-orange-400" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-bold text-orange-800 dark:text-orange-300 text-lg mb-1">
                  {t('freeLimitTitle')}
                </h3>
                <p className="text-orange-700 dark:text-orange-400 text-sm mb-2">
                  {t('freeLimitDesc')}
                </p>
                <p className="text-orange-700 dark:text-orange-400 text-sm">
                  {t('freeLimitCta')}{' '}
                  <a
                    href="https://aistudio.google.com/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-bold underline underline-offset-2 hover:text-orange-900 dark:hover:text-orange-200 transition-colors"
                  >
                    {t('freeLimitLink')}
                  </a>
                  {' '}{t('freeLimitCta2')}
                </p>
                <button
                  onClick={() => window.dispatchEvent(new CustomEvent('open-profile-menu'))}
                  className="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white text-sm font-semibold rounded-lg transition-colors shadow-sm"
                >
                  <Key className="w-4 h-4" />
                  {t('freeLimitGoSettings')}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div 
            onClick={() => setActiveTab('upload')}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700 cursor-pointer hover:shadow-md hover:border-indigo-300 transition-all"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-indigo-100 dark:bg-indigo-900/50 rounded-lg flex items-center justify-center">
                <BookOpen className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
              </div>
              <div>
                <p className="text-sm text-gray-900 dark:text-white font-medium">{t('statsUploaded')}</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{notes.length}</p>
              </div>
            </div>
          </div>
          
          <div 
            onClick={() => setActiveTab('categories')}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700 cursor-pointer hover:shadow-md hover:border-purple-300 transition-all"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/50 rounded-lg flex items-center justify-center">
                <Brain className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-sm text-gray-900 dark:text-white font-medium">{t('statsCreated')}</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{quizzes.length}</p>
              </div>
            </div>
          </div>
          
          <div 
            onClick={() => setActiveTab('history')}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700 cursor-pointer hover:shadow-md hover:border-green-300 transition-all"
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-green-100 dark:bg-green-900/50 rounded-lg flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-sm text-gray-900 dark:text-white font-medium">{t('statsCompleted')}</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {quizzes.filter(q => q.latest_grading_id).length}
                </p>
              </div>
            </div>
          </div>

          {/* Free Quiz Count Card */}
          {!user?.gemini_api_key && (
            <div className="bg-gradient-to-r from-orange-500 to-amber-500 rounded-xl shadow-sm p-6 border border-orange-200 dark:border-orange-700">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-white font-medium">
                    {currentLanguage === 'tr' ? 'Ücretsiz Sınav' : 'Free Quizzes'}
                  </p>
                  <p className="text-2xl font-bold text-white">
                    {user?.free_quiz_count || 0} / 3
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 flex-wrap">
          <button
            onClick={() => setActiveTab('upload')}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'upload'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700'
            }`}
          >
            <Plus className="w-5 h-5" />
            {t('newQuiz')}
          </button>
          <button
            onClick={() => setActiveTab('categories')}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'categories'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700'
            }`}
          >
            <Zap className="w-5 h-5" />
            {t('categories')}
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'history'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700'
            }`}
          >
            <History className="w-5 h-5" />
            {t('quizHistory')}
          </button>
          <button
            onClick={() => { setActiveTab('analytics'); fetchAnalytics(); }}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-all ${
              activeTab === 'analytics'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700'
            }`}
          >
            <BarChart2 className="w-5 h-5" />
            {t('analytics')}
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'upload' && (
          <div className="space-y-6">
            {/* File Upload Section */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-8 border border-gray-100 dark:border-gray-700">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <FileText className="w-6 h-6 text-indigo-600" />
                1. {t('upload')}
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                {t('uploadDesc')} {t('supportedFormats')}
              </p>
              <FileUpload onUploadComplete={handleUploadComplete} onNotesCreated={handleNotesCreated} />
            </div>

            {/* Notes List */}
            {notes.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700">
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">{t('statsUploaded')}</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {(isResourcesExpanded ? notes : notes.slice(0, 6)).map((note) => (
                    <div
                      key={note.id}
                      onClick={() => {
                        setSelectedNote(note);
                        setShowQuizModal(true);
                      }}
                      className={`p-4 rounded-lg border-2 cursor-pointer transition-all relative group ${
                        selectedNote?.id === note.id
                          ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-900/30'
                          : 'border-gray-200 dark:border-gray-700 hover:border-indigo-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                      }`}
                    >
                      <button
                        onClick={(e) => handleDeleteNote(note.id, e)}
                        className="absolute -top-2 -right-2 w-7 h-7 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-full flex items-center justify-center text-gray-400 hover:text-red-600 hover:border-red-600 shadow-sm opacity-0 group-hover:opacity-100 transition-all z-10"
                        title={t('deleteResource')}
                      >
                        <X className="w-4 h-4" />
                      </button>
                      <div className="flex items-start gap-3">
                        <div className="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/50 rounded-lg flex items-center justify-center flex-shrink-0">
                          <FileText className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900 dark:text-white truncate">
                            {note.filename || 'Ders Notu'}
                          </p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {new Date(note.created_at).toLocaleDateString(currentLanguage === 'tr' ? 'tr-TR' : 'en-US')}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Show More/Less Toggle */}
                {notes.length > 6 && (
                  <div className="flex justify-center mt-6">
                    <button
                      onClick={() => setIsResourcesExpanded(!isResourcesExpanded)}
                      className="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 rounded-full transition-all border border-indigo-100 dark:border-indigo-800 shadow-sm hover:shadow-md"
                    >
                      {isResourcesExpanded ? (
                        <>
                          {currentLanguage === 'tr' ? 'Daha Az Göster' : 'Show Less'}
                          <ChevronUp className="w-4 h-4 animate-bounce-slow" />
                        </>
                      ) : (
                        <>
                          {currentLanguage === 'tr' ? `Tümünü Gör (${notes.length})` : `Show All (${notes.length})`}
                          <ChevronDown className="w-4 h-4 animate-bounce-slow" />
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Create Quiz Button */}
            {notes.length > 0 && (
              <div className="flex justify-center">
                <div className="w-full max-w-md">
                  {isFreeLimitReached ? (
                    <div className="text-center p-5 bg-orange-50 dark:bg-orange-900/20 border-2 border-dashed border-orange-300 dark:border-orange-600 rounded-xl">
                      <Key className="w-8 h-8 text-orange-500 mx-auto mb-2" />
                      <p className="text-orange-700 dark:text-orange-400 font-semibold text-sm">
                        {t('freeLimitCreateDisabled')}
                      </p>
                    </div>
                  ) : (
                    <button
                      onClick={() => setShowQuizModal(true)}
                      className="w-full flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl"
                    >
                      <Brain className="w-6 h-6" />
                      {currentLanguage === 'tr' ? 'Yapay Zeka ile Sınav Hazırlat' : 'Create Quiz with AI'}
                      <ChevronRight className="w-5 h-5" />
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'categories' && (
          <QuizCategories 
            quizzes={quizzes}
            notes={notes}
            onQuizSelect={(quizId) => navigate(`/quiz/${quizId}`)}
            t={t}
            currentLanguage={currentLanguage}
            activeTab={activeTab}
            onTabChange={setActiveTab}
            onDeleteQuiz={handleDeleteQuiz}
          />
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
            <div className="p-6 border-b border-gray-100 dark:border-gray-700">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">{t('quizHistory')}</h2>
            </div>
            
            {quizzes.length === 0 ? (
              <div className="p-12 text-center">
                <div className="w-16 h-16 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
                  <History className="w-8 h-8 text-gray-400 dark:text-gray-500" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  {currentLanguage === 'tr' ? 'Henüz sınav oluşturmadınız' : 'No quizzes yet'}
                </h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  {currentLanguage === 'tr' 
                    ? 'İlk sınavınızı oluşturmak için "Yeni Sınav Oluştur" sekmesine gidin.'
                    : 'Go to "Create New Quiz" tab to create your first quiz.'}
                </p>
                <button
                  onClick={() => setActiveTab('upload')}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
                >
                  <Plus className="w-5 h-5" />
                  {t('createQuiz')}
                </button>
              </div>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-700">
                {quizzes.map((quiz) => (
                  <div
                    key={quiz.id}
                    onClick={() => navigate(`/quiz/${quiz.id}`)}
                    className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-indigo-100 dark:bg-indigo-900/50 rounded-lg flex items-center justify-center">
                          <Brain className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900 dark:text-white">{t('quiz')} #{quiz.id?.slice(-6) || '...'}</h3>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {quiz.total_questions} {currentLanguage === 'tr' ? 'soru' : 'questions'} • {quiz.mc_ratio === 1.0 ? (currentLanguage === 'tr' ? 'Test' : 'Test') : (quiz.mc_ratio === 0.0 ? (currentLanguage === 'tr' ? 'Klasik' : 'Classic') : (currentLanguage === 'tr' ? 'Karma' : 'Mixed'))} • {quiz.difficulty === 'easy' ? t('easy') : quiz.difficulty === 'hard' ? t('hard') : t('medium')}
                          </p>
                          {quiz.api_source && (
                            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                              API: {quiz.api_source === 'user_gemini' ? (currentLanguage === 'tr' ? 'Kendi API Key' : 'Your API Key') : quiz.api_source === 'system_gemini' ? (currentLanguage === 'tr' ? 'Sistem Gemini' : 'System Gemini') : quiz.api_source === 'hugging_face' ? (currentLanguage === 'tr' ? 'Hugging Face' : 'Hugging Face') : quiz.api_source}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                          {quiz.latest_grading_id ? (
                            <div className="flex flex-col items-end gap-1">
                              <div className="flex items-center gap-1.5 px-2.5 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-full text-xs font-bold">
                                <CheckCircle className="w-3.5 h-3.5" />
                                {currentLanguage === 'tr' ? 'Çözüldü' : 'Solved'}
                              </div>
                              {quiz.score != null && (
                                <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400">
                                  {quiz.score.toFixed(1)} / {quiz.max_score}
                                </span>
                              )}
                            </div>
                          ) : getStatusIcon(quiz.status)}
                          <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                            {quiz.latest_grading_id ? '' : getStatusText(quiz.status)}
                          </span>
                        </div>
                        <button
                          onClick={(e) => handleDeleteQuiz(quiz.id, e)}
                          title={t('deleteQuiz')}
                          className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                        <ChevronRight className="w-5 h-5 text-gray-400 dark:text-gray-500" />
                      </div>
                    </div>
                    <p className="text-sm text-gray-400 dark:text-gray-500 mt-2 ml-16">
                      {quiz.created_at ? new Date(quiz.created_at).toLocaleDateString(currentLanguage === 'tr' ? 'tr-TR' : 'en-US', {
                        day: 'numeric',
                        month: 'long',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      }) : '...'}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Analytics Tab */}
        {activeTab === 'analytics' && (
          <div className="space-y-6">
            {analyticsLoading ? (
              <div className="flex items-center justify-center py-24">
                <Loader2 className="w-10 h-10 text-indigo-600 animate-spin" />
              </div>
            ) : !analyticsData || analyticsData.total_questions_answered === 0 ? (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-16 text-center">
                <div className="w-20 h-20 bg-indigo-100 dark:bg-indigo-900/40 rounded-full flex items-center justify-center mx-auto mb-4">
                  <BarChart2 className="w-10 h-10 text-indigo-600 dark:text-indigo-400" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">{t('noAnalytics')}</h3>
                <p className="text-gray-500 dark:text-gray-400">{t('noAnalyticsDesc')}</p>
              </div>
            ) : (
              <>
                {/* Summary Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-6 text-white shadow-lg">
                    <p className="text-indigo-200 text-sm font-medium mb-1">{t('overallScore')}</p>
                    <p className="text-4xl font-black">{analyticsData.overall_score.toFixed(1)}</p>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm">
                    <p className="text-gray-500 dark:text-gray-400 text-sm font-medium mb-1">{t('totalCompleted')}</p>
                    <p className="text-3xl font-black text-gray-900 dark:text-white">{analyticsData.total_quizzes_completed}</p>
                  </div>
                  <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border border-gray-100 dark:border-gray-700 shadow-sm">
                    <p className="text-gray-500 dark:text-gray-400 text-sm font-medium mb-1">{t('totalAnswered')}</p>
                    <p className="text-3xl font-black text-gray-900 dark:text-white">{analyticsData.total_questions_answered}</p>
                  </div>
                </div>

                {/* Topic Bar Chart */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-6">
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-6">{t('topicAccuracy')}</h3>
                  <div className="space-y-4">
                    {analyticsData.topic_stats.map((topic) => {
                      const isWeak = topic.accuracy < 40;
                      const isStrong = topic.accuracy >= 70;
                      const barColor = isWeak
                        ? 'bg-gradient-to-r from-red-500 to-red-400'
                        : isStrong
                        ? 'bg-gradient-to-r from-green-500 to-emerald-400'
                        : 'bg-gradient-to-r from-yellow-500 to-amber-400';
                      return (
                        <div key={topic.topic}>
                          <div className="flex justify-between items-center mb-1">
                            <div className="flex items-center gap-2">
                              {isWeak && <TrendingDown className="w-4 h-4 text-red-500" />}
                              {isStrong && <TrendingUp className="w-4 h-4 text-green-500" />}
                              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{topic.topic}</span>
                              <span className="text-xs text-gray-400">({topic.total_questions} {t('topicQuestionCount')})</span>
                            </div>
                            <span className={`text-sm font-bold ${
                              isWeak ? 'text-red-600' : isStrong ? 'text-green-600' : 'text-yellow-600'
                            }`}>
                              {topic.accuracy.toFixed(1)}
                            </span>
                          </div>
                          <div className="w-full h-3 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                            <div
                              className={`h-3 rounded-full transition-all duration-700 ${barColor}`}
                              style={{ width: `${Math.min(topic.accuracy, 100)}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Weak / Strong Topics */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {analyticsData.weak_topics.length > 0 && (
                    <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-xl p-6">
                      <h3 className="flex items-center gap-2 font-bold text-red-700 dark:text-red-400 mb-4">
                        <TrendingDown className="w-5 h-5" />
                        {t('weakTopics')}
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {analyticsData.weak_topics.map(topic => (
                          <span key={topic} className="px-3 py-1 bg-red-100 dark:bg-red-800/40 text-red-700 dark:text-red-300 rounded-full text-sm font-medium">
                            {topic}
                          </span>
                        ))}
                      </div>
                      <p className="mt-4 text-xs text-red-600 dark:text-red-400">{t('personalizedHint')}</p>
                    </div>
                  )}
                  {analyticsData.strong_topics.length > 0 && (
                    <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-xl p-6">
                      <h3 className="flex items-center gap-2 font-bold text-green-700 dark:text-green-400 mb-4">
                        <TrendingUp className="w-5 h-5" />
                        {t('strongTopics')}
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {analyticsData.strong_topics.map(topic => (
                          <span key={topic} className="px-3 py-1 bg-green-100 dark:bg-green-800/40 text-green-700 dark:text-green-300 rounded-full text-sm font-medium">
                            {topic}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}
      </main>

      {/* Quiz Config Modal */}
      {showQuizModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-md w-full p-6">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-6 h-6 text-indigo-600" />
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{t('quizSettings')}</h2>
            </div>

            {/* API Key Uyarı Banner'ı */}
            {!user?.gemini_api_key && (
              <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-900/30 border border-amber-300 dark:border-amber-700 rounded-lg flex items-start gap-2">
                <span className="text-amber-500 text-lg leading-none mt-0.5">🔑</span>
                <div className="flex-1 text-sm">
                  <p className="font-semibold text-amber-800 dark:text-amber-300">
                    {currentLanguage === 'tr' ? 'Gemini API Key Gerekli' : 'Gemini API Key Required'}
                  </p>
                  <p className="text-amber-700 dark:text-amber-400 mt-0.5">
                    {currentLanguage === 'tr'
                      ? 'Sınav oluşturabilmek için Gemini API anahtarınızı profil ayarlarından eklemeniz gerekiyor.'
                      : 'You need to add your Gemini API key in profile settings to create quizzes.'}
                  </p>
                  <button
                    onClick={() => {
                      setShowQuizModal(false);
                      // ProfileMenu'yü açmak için custom event
                      window.dispatchEvent(new CustomEvent('open-profile-menu'));
                    }}
                    className="mt-1.5 text-amber-800 dark:text-amber-300 font-semibold underline underline-offset-2 hover:text-amber-600 transition-colors"
                  >
                    {currentLanguage === 'tr' ? '→ Profil Ayarlarına Git' : '→ Go to Profile Settings'}
                  </button>
                </div>
              </div>
            )}
            
            {selectedNote ? (
              <div className="mb-4 p-3 bg-indigo-50 dark:bg-indigo-900/30 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400">{t('selectedResource')}:</p>
                <p className="font-medium text-indigo-900 dark:text-indigo-300">{selectedNote.filename || 'Ders Notu'}</p>
              </div>
            ) : (
              <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-xl">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-blue-800 dark:text-blue-300 text-sm">{t('uploadFirstTitle')}</p>
                    <p className="text-blue-700 dark:text-blue-400 text-xs mt-1">{t('uploadFirstDesc')}</p>
                    <p className="text-blue-500 dark:text-blue-500 text-xs mt-1 italic">{t('uploadFirstHint')}</p>
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('questionCount')}: {quizConfig.question_count}
                </label>
                <input
                  type="range"
                  min="5"
                  max="50"
                  value={quizConfig.question_count}
                  onChange={(e) => setQuizConfig({ ...quizConfig, question_count: parseInt(e.target.value) })}
                  className="w-full dark:bg-gray-700"
                />
                <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
                  <span>5</span>
                  <span>50</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('quizType')}
                </label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setQuizConfig({ ...quizConfig, test_ratio: 100 })}
                    className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all border-2 flex flex-col items-center justify-center gap-2 ${
                      quizConfig.test_ratio === 100
                        ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300'
                        : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:border-indigo-300'
                    }`}
                  >
                    <CheckCircle className={`w-6 h-6 ${quizConfig.test_ratio === 100 ? 'text-indigo-600' : 'text-gray-400'}`} />
                    {t('onlyTest')}
                  </button>
                  <button
                    onClick={() => setQuizConfig({ ...quizConfig, test_ratio: 0 })}
                    className={`flex-1 py-3 px-4 rounded-lg font-medium transition-all border-2 flex flex-col items-center justify-center gap-2 ${
                      quizConfig.test_ratio === 0
                        ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300'
                        : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:border-indigo-300'
                    }`}
                  >
                    <FileText className={`w-6 h-6 ${quizConfig.test_ratio === 0 ? 'text-indigo-600' : 'text-gray-400'}`} />
                    {t('onlyClassic')}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  {t('difficulty')}
                </label>
                <div className="flex gap-2">
                  {['easy', 'medium', 'hard'].map((level) => (
                    <button
                      key={level}
                      onClick={() => setQuizConfig({ ...quizConfig, difficulty: level })}
                      className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${
                        quizConfig.difficulty === level
                          ? 'bg-indigo-600 text-white'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                      }`}
                    >
                      {level === 'easy' ? t('easy') : level === 'medium' ? t('medium') : t('hard')}
                    </button>
                  ))}
                </div>
              </div>

              {/* Language Selector */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                  <Globe className="w-4 h-4 text-indigo-500" />
                  {t('quizLanguage')}
                </label>
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">{t('quizLangDesc')}</p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setQuizConfig({ ...quizConfig, language: 'tr' })}
                    className={`flex-1 py-2.5 px-4 rounded-lg font-medium transition-all border-2 ${
                      quizConfig.language === 'tr'
                        ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300'
                        : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:border-indigo-300'
                    }`}
                  >
                    {t('quizLangTurkish')}
                  </button>
                  <button
                    onClick={() => setQuizConfig({ ...quizConfig, language: 'en' })}
                    className={`flex-1 py-2.5 px-4 rounded-lg font-medium transition-all border-2 ${
                      quizConfig.language === 'en'
                        ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300'
                        : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:border-indigo-300'
                    }`}
                  >
                    {t('quizLangEnglish')}
                  </button>
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowQuizModal(false)}
                className="flex-1 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                {t('cancel')}
              </button>
              <button
                onClick={handleCreateQuiz}
                disabled={!selectedNote || creatingQuiz || !user?.gemini_api_key}
                title={!user?.gemini_api_key ? (currentLanguage === 'tr' ? 'Önce API key ekleyin' : 'Add API key first') : ''}
                className="flex-1 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {creatingQuiz ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    {t('creating')}
                  </>
                ) : (
                  <>
                    <Brain className="w-5 h-5" />
                    {t('createQuiz')}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Resource Delete Modal */}
      <ConfirmModal
        isOpen={!!noteToDelete}
        onClose={() => setNoteToDelete(null)}
        onConfirm={confirmDeleteNote}
        title={t('deleteResource')}
        message={t('deleteResourceConfirm')}
        confirmText={t('delete')}
        cancelText={t('cancel')}
        variant="danger"
      />

      {/* Quiz Delete Modal */}
      <ConfirmModal
        isOpen={!!quizToDelete}
        onClose={() => setQuizToDelete(null)}
        onConfirm={confirmDeleteQuiz}
        title={t('deleteQuiz')}
        message={t('deleteConfirm')}
        confirmText={t('delete')}
        cancelText={t('cancel')}
        variant="danger"
      />

      {/* Welcome Modal (first login) */}
      {showWelcomeModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-fadeIn">
          <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-2xl max-w-lg w-full p-8 relative">
            {/* Decorative gradient top bar */}
            <div className="absolute top-0 left-0 right-0 h-2 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-t-3xl" />

            <div className="text-center mb-6">
              <div className="w-20 h-20 bg-gradient-to-br from-indigo-100 to-purple-100 dark:from-indigo-900/50 dark:to-purple-900/50 rounded-2xl flex items-center justify-center mx-auto mb-4">
                <Brain className="w-10 h-10 text-indigo-600 dark:text-indigo-400" />
              </div>
              <h2 className="text-2xl font-black text-gray-900 dark:text-white">
                {t('welcomeModalTitle')}
              </h2>
              <p className="text-gray-500 dark:text-gray-400 mt-2 text-sm">
                {t('welcomeModalDesc')}
              </p>
            </div>

            <div className="space-y-4 mb-6">
              {/* API Key Section */}
              <div className="p-4 bg-indigo-50 dark:bg-indigo-900/30 rounded-2xl border border-indigo-200 dark:border-indigo-700">
                <h3 className="font-bold text-indigo-800 dark:text-indigo-300 mb-2 flex items-center gap-2">
                  <Key className="w-5 h-5" />
                  {t('welcomeModalApiTitle')}
                </h3>
                <p className="text-sm text-indigo-700 dark:text-indigo-400">
                  <a
                    href="https://aistudio.google.com/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-bold underline underline-offset-2 hover:text-indigo-900 dark:hover:text-indigo-200"
                  >
                    Google AI Studio
                  </a>
                  {' '}{t('welcomeModalApiDesc1')}
                </p>
              </div>

              {/* Free Trial Section */}
              <div className="p-4 bg-green-50 dark:bg-green-900/30 rounded-2xl border border-green-200 dark:border-green-700">
                <h3 className="font-bold text-green-800 dark:text-green-300 mb-2 flex items-center gap-2">
                  <Sparkles className="w-5 h-5" />
                  {t('welcomeModalFreeTitle')}
                </h3>
                <p className="text-sm text-green-700 dark:text-green-400">
                  {t('welcomeModalFreeDesc')}
                </p>
                {/* Progress bar */}
                <div className="mt-3">
                  <div className="flex justify-between text-xs text-green-600 dark:text-green-400 mb-1">
                    <span>{currentLanguage === 'tr' ? 'Ücretsiz Sınav Hakkı' : 'Free Quizzes'}</span>
                    <span>0 / 3</span>
                  </div>
                  <div className="w-full h-2 bg-green-200 dark:bg-green-800 rounded-full">
                    <div className="h-2 bg-green-500 rounded-full" style={{ width: '0%' }} />
                  </div>
                </div>
              </div>
            </div>

            <button
              onClick={handleCloseWelcome}
              className="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-bold rounded-2xl transition-all shadow-lg hover:shadow-xl text-lg"
            >
              {t('welcomeModalClose')}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
