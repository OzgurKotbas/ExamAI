import { createContext, useContext, useState, useCallback } from 'react';

const translations = {
  tr: {
    // Login
    loginTitle: 'Giriş Yap',
    email: 'E-posta Adresi',
    emailPlaceholder: 'ornek@email.com',
    password: 'Şifre',
    forgotPassword: 'Şifremi Unuttum',
    loginButton: 'Giriş Yap',
    or: 'veya',
    googleLogin: 'Google ile Giriş Yap',
    noAccount: 'Hesabınız yok mu?',
    register: 'Kayıt Ol',
    loginSuccess: 'Giriş başarılı!',
    loginError: 'Giriş başarısız. Lütfen bilgilerinizi kontrol edin.',
    
    // Register
    registerTitle: 'Kayıt Ol',
    fullName: 'Ad Soyad',
    fullNamePlaceholder: 'Ahmet Yılmaz',
    confirmPassword: 'Şifre Tekrar',
    registerButton: 'Kayıt Ol',
    googleRegister: 'Google ile Kayıt Ol',
    haveAccount: 'Zaten hesabınız var mı?',
    registerSuccess: 'Kayıt başarılı! Hoş geldiniz.',
    registerError: 'Kayıt başarısız. Lütfen tekrar deneyin.',
    
    // Forgot Password
    forgotTitle: 'Şifremi Unuttum',
    forgotDescription: 'E-posta adresinizi girin, size şifre sıfırlama kodu gönderelim.',
    sendCode: 'Kod Gönder',
    resetTitle: 'Yeni Şifre Belirle',
    resetDescription: 'E-postanıza gönderilen 6 haneli kodu ve yeni şifrenizi girin.',
    verificationCode: 'Doğrulama Kodu (6 haneli)',
    codePlaceholder: '123456',
    newPassword: 'Yeni Şifre',
    resetButton: 'Şifreyi Sıfırla',
    resendCode: 'Kodu tekrar gönder',
    resetSuccess: 'Şifre Sıfırlandı!',
    resetSuccessDesc: 'Şifreniz başarıyla değiştirildi. Yeni şifrenizle giriş yapabilirsiniz.',
    goToLogin: 'Giriş Yap',
    
    // Validation
    emailRequired: 'E-posta adresi gerekli',
    emailInvalid: 'Geçerli bir e-posta adresi giriniz',
    passwordRequired: 'Şifre gerekli',
    passwordMin: 'Şifre en az 6 karakter olmalıdır',
    passwordMatch: 'Şifreler eşleşmiyor',
    nameRequired: 'İsim gerekli',
    nameMin: 'İsim en az 2 karakter olmalıdır',
    codeRequired: 'Doğrulama kodu gerekli',
    codeLength: 'Kod 6 haneli olmalıdır',
    
    // Dashboard
    welcome: 'Hoş geldin',
    upload: 'Kaynak Yükle',
    uploadDesc: 'Sınav oluşturmak istediğiniz ders notlarınızı yükleyin.',
    supportedFormats: 'PDF, DOCX, TXT, JPG, JPEG veya PNG formatları desteklenmektedir.',
    quizSettings: 'Sınav Ayarları',
    questionCount: 'Soru Sayısı',
    difficulty: 'Zorluk Seviyesi',
    easy: 'Kolay',
    medium: 'Orta',
    hard: 'Zor',
    cancel: 'İptal',
    createQuiz: 'Sınav Oluştur',
    creating: 'Oluşturuluyor...',
    newQuiz: 'Yeni Sınav Oluştur',
    quizHistory: 'Geçmiş Sınavlar',
    logout: 'Çıkış',
    profile: 'Profil',
    accountInfo: 'Hesap Bilgileri',
    changePassword: 'Şifre Değiştir',
    changeName: 'İsim Değiştir',
    darkMode: 'Karanlık Mod',
    lightMode: 'Aydınlık Mod',
    language: 'Dil',
    turkish: 'Türkçe',
    english: 'English',
    categories: 'Kategoriler',
    allQuizzes: 'Tüm Sınavlar',
    createCategory: 'Kategori Oluştur',
    quizStatusPending: 'Bekliyor',
    quizStatusGenerating: 'Oluşturuluyor',
    quizStatusReady: 'Hazır',
    quizStatusFailed: 'Başarısız',
    statsUploaded: 'Yüklenen Kaynak',
    statsCreated: 'Oluşturulan Sınav',
    statsCompleted: 'Tamamlanan',
    
    // File Upload
    dropFilesHere: 'Dosyaları buraya bırakın',
    clickOrDropFiles: 'Dosya yüklemek için tıklayın veya sürükleyin',
    maxFilesInfo: 'PDF, DOCX, TXT, JPG, JPEG, PNG (max 10 dosya, toplam 20MB)',
    filesSelected: 'dosya seçildi',
    totalSize: 'Toplam',
    selectedFiles: 'Seçilen Dosyalar',
    removeAll: 'Tümünü Kaldır',
    addMoreFiles: 'Daha Fazla Dosya Ekle',
    uploadAndProcess: 'Dosyayı Yükle ve İşle',
    uploadError: 'Dosya yüklenirken hata oluştu',
    selectFileError: 'Lütfen en az bir dosya seçin',
    maxFilesError: 'En fazla 10 dosya yükleyebilirsiniz',
    totalSizeError: 'Toplam dosya boyutu 20MB\'ı aşıyor',
    file: 'dosya',
    files: 'dosya',
    resourcesUploaded: 'kaynak yüklendi',
    createQuizTitle: 'Sınav Oluştur',
    questions: 'Soru Sayısı',
    mcRatio: 'Çoktan Seçmeli Oranı',
    openEnded: 'Açık Uçlu',
    mixed: 'Karışık',
    allMultipleChoice: 'Tamamı Çoktan Seçmeli',
    difficultyLevel: 'Zorluk Seviyesi',
    later: 'Sonra',
    creatingQuiz: 'Oluşturuluyor...',
    unsupportedFormat: 'Desteklenmeyen format',
    
    // Quiz View
    quizGeneratingTitle: 'Sınavınız Yapay Zeka Tarafından Hazırlanıyor...',
    quizGeneratingDesc: 'Lütfen bekleyin, bu işlem biraz sürebilir.',
    backToHome: 'Ana Sayfaya Dön',
    quizFailedTitle: 'Sınav Hazırlanamadı',
    goBack: 'Geri Dön',
    aiQuiz: 'AI Sınavı',
    quizResultTitle: 'Sınav Sonucunuz',
    quizResultDesc: 'Yapay zeka değerlendirmesi tamamlandı.',
    gradingTitle: 'Cevaplarınız Değerlendiriliyor...',
    gradingDesc: 'Semantik analiz ve puanlama yapılıyor.',
    writeAnswerPlaceholder: 'Cevabınızı buraya yazın...',
    score: 'Puan',
    yourAnswer: 'Senin Cevabın',
    feedbackInfo: 'Açıklama / Feedback',
    submitQuiz: 'Sınavı Tamamla ve Değerlendir',
    quizStatusError: 'Sınav durumu alınamadı.',
    quizQuestionsError: 'Sorular alınamadı.',
    gradingCompleteInfo: 'Sınav değerlendirmesi tamamlandı!',
    gradingResultsError: 'Sonuçlar alınamadı.',
    answerAllQuestions: 'Lütfen tüm soruları yanıtlayın.',
    quizSubmitted: 'Sınav gönderildi, değerlendiriliyor...',
    quizSubmitError: 'Sınav gönderilemedi.',
    quizType: 'Sınav Türü',
    onlyTest: 'Sadece Test',
    onlyClassic: 'Sadece Klasik (Açık Uçlu)',
    successRate: 'Başarı',
    deleteQuiz: 'Sınavı Sil',
    deleteConfirm: 'Bu sınavı silmek istediğinize emin misiniz? (Tüm değerlendirme raporu kaybolacaktır)',
    deleteSuccess: 'Sınav başarıyla silindi',
    
    // Quiz Language Selection
    quizLanguage: 'Sınav Dili',
    quizLangTurkish: '🇹🇷 Türkçe',
    quizLangEnglish: '🇬🇧 English',
    quizLangDesc: 'Sorular ve cevaplar seçilen dilde hazırlanacaktır.',
    
    // Categories
    uncategorized: 'Kategorisiz',
    quizzesCount: 'sınav',
    noQuizzesYet: 'Henüz sınav yok',
    noQuizzesInCategory: 'Bu kategoride henüz sınav bulunmuyor.',
    categoryNameLabel: 'Kategori Adı',
    categoryNamePlaceholder: 'Örn: Matematik, Fizik, Tarih...',
    editCategory: 'Kategori Düzenle',
    save: 'Kaydet',
    edit: 'Düzenle',
    delete: 'Sil',
    questionsLabel: 'soru',
    
    // Analytics
    analytics: 'Analitik',
    analyticsTitle: 'Performans Raporu',
    analyticsDesc: 'Konu bazında başarı oranlarınız ve gelişim takibi.',
    topicAccuracy: 'Konu Başarı Oranları',
    weakTopics: 'Geliştirilmesi Gereken Konular',
    strongTopics: 'Güçlü Konular',
    overallScore: 'Genel Ortalama',
    totalCompleted: 'Tamamlanan Sınav',
    totalAnswered: 'Cevaplanan Soru',
    noAnalytics: 'Henüz analitik veri yok',
    noAnalyticsDesc: 'Sınav çözdükten sonra performans raporunuz burada görünecektir.',
    accuracyPct: 'Doğruluk',
    topicQuestionCount: 'soru',
    personalizedHint: '💡 Bu konulardan özelleştirilmiş sorular üretildi.',
    
    // Common
    appName: 'ExamAI',
    appDescription: 'Yapay Zeka Destekli Sınav Platformu',
    loading: 'Yükleniyor...',
    success: 'Başarılı!',
    quiz: 'Sınav',
    geminiApiKey: 'Gemini API Anahtarı',
    apiHint: 'İsteğe bağlı. Kişisel anahtarınız sınav ve değerlendirme işlemlerinde kullanılacaktır.',
    geminiModel: 'Gemini Model İsmi (Opsiyonel)',
    modelHint: 'Boş bırakılırsa sistem çalışan modeli otomatik bulur ve kaydeder.',
  },
  en: {
    // Login
    loginTitle: 'Sign In',
    email: 'Email Address',
    emailPlaceholder: 'example@email.com',
    password: 'Password',
    forgotPassword: 'Forgot Password?',
    loginButton: 'Sign In',
    or: 'or',
    googleLogin: 'Sign in with Google',
    noAccount: "Don't have an account?",
    register: 'Sign Up',
    loginSuccess: 'Login successful!',
    loginError: 'Login failed. Please check your credentials.',
    
    // Register
    registerTitle: 'Sign Up',
    fullName: 'Full Name',
    fullNamePlaceholder: 'John Doe',
    confirmPassword: 'Confirm Password',
    registerButton: 'Sign Up',
    googleRegister: 'Sign up with Google',
    haveAccount: 'Already have an account?',
    registerSuccess: 'Registration successful! Welcome.',
    registerError: 'Registration failed. Please try again.',
    
    // Forgot Password
    forgotTitle: 'Forgot Password',
    forgotDescription: 'Enter your email address and we will send you a password reset code.',
    sendCode: 'Send Code',
    resetTitle: 'Set New Password',
    resetDescription: 'Enter the 6-digit code sent to your email and your new password.',
    verificationCode: 'Verification Code (6 digits)',
    codePlaceholder: '123456',
    newPassword: 'New Password',
    resetButton: 'Reset Password',
    resendCode: 'Resend code',
    resetSuccess: 'Password Reset!',
    resetSuccessDesc: 'Your password has been changed successfully. You can now sign in with your new password.',
    goToLogin: 'Sign In',
    
    // Validation
    emailRequired: 'Email is required',
    emailInvalid: 'Please enter a valid email address',
    passwordRequired: 'Password is required',
    passwordMin: 'Password must be at least 6 characters',
    passwordMatch: 'Passwords do not match',
    nameRequired: 'Name is required',
    nameMin: 'Name must be at least 2 characters',
    codeRequired: 'Verification code is required',
    codeLength: 'Code must be 6 digits',
    
    // Dashboard
    welcome: 'Welcome',
    upload: 'Upload Resource',
    uploadDesc: 'Upload your study materials to create quizzes.',
    supportedFormats: 'Supported formats: PDF, DOCX, TXT, JPG, JPEG, PNG.',
    quizSettings: 'Quiz Settings',
    questionCount: 'Question Count',
    difficulty: 'Difficulty Level',
    easy: 'Easy',
    medium: 'Medium',
    hard: 'Hard',
    cancel: 'Cancel',
    createQuiz: 'Create Quiz',
    creating: 'Creating...',
    newQuiz: 'Create New Quiz',
    quizHistory: 'Quiz History',
    logout: 'Logout',
    profile: 'Profile',
    accountInfo: 'Account Info',
    changePassword: 'Change Password',
    changeName: 'Change Name',
    darkMode: 'Dark Mode',
    lightMode: 'Light Mode',
    language: 'Language',
    turkish: 'Türkçe',
    english: 'English',
    categories: 'Categories',
    allQuizzes: 'All Quizzes',
    createCategory: 'Create Category',
    quizStatusPending: 'Pending',
    quizStatusGenerating: 'Generating',
    quizStatusReady: 'Ready',
    quizStatusFailed: 'Failed',
    statsUploaded: 'Uploaded Resources',
    statsCreated: 'Created Quizzes',
    statsCompleted: 'Completed',
    
    // File Upload
    dropFilesHere: 'Drop files here',
    clickOrDropFiles: 'Click to upload or drag and drop',
    maxFilesInfo: 'PDF, DOCX, TXT, JPG, JPEG, PNG (max 10 files, total 20MB)',
    filesSelected: 'files selected',
    totalSize: 'Total',
    selectedFiles: 'Selected Files',
    removeAll: 'Remove All',
    addMoreFiles: 'Add More Files',
    uploadAndProcess: 'Upload and Process',
    uploadError: 'Error uploading file',
    selectFileError: 'Please select at least one file',
    maxFilesError: 'You can upload max 10 files',
    totalSizeError: 'Total file size exceeds 20MB',
    file: 'file',
    files: 'files',
    resourcesUploaded: 'resources uploaded',
    createQuizTitle: 'Create Quiz',
    questions: 'Question Count',
    mcRatio: 'Multiple Choice Ratio',
    openEnded: 'Open Ended',
    mixed: 'Mixed',
    allMultipleChoice: 'All Multiple Choice',
    difficultyLevel: 'Difficulty Level',
    later: 'Later',
    creatingQuiz: 'Creating...',
    
    // Quiz View
    quizGeneratingTitle: 'Your Quiz is Being Generated by AI...',
    quizGeneratingDesc: 'Please wait, this may take a moment.',
    backToHome: 'Back to Home',
    quizFailedTitle: 'Failed to Generate Quiz',
    goBack: 'Go Back',
    aiQuiz: 'AI Quiz',
    quizResultTitle: 'Your Quiz Result',
    quizResultDesc: 'AI evaluation is complete.',
    gradingTitle: 'Your Answers are Being Verified...',
    gradingDesc: 'Semantic analysis and scoring in progress.',
    writeAnswerPlaceholder: 'Write your answer here...',
    score: 'Score',
    yourAnswer: 'Your Answer',
    feedbackInfo: 'Explanation / Feedback',
    submitQuiz: 'Submit and Evaluate Quiz',
    quizStatusError: 'Failed to get quiz status.',
    quizQuestionsError: 'Failed to get questions.',
    gradingCompleteInfo: 'Quiz evaluation completed!',
    gradingResultsError: 'Failed to get results.',
    answerAllQuestions: 'Please answer all questions.',
    quizSubmitted: 'Quiz submitted, being evaluated...',
    quizSubmitError: 'Failed to submit quiz.',
    quizType: 'Quiz Type',
    onlyTest: 'Multiple Choice Only',
    onlyClassic: 'Open Ended Only',
    successRate: 'Success',
    deleteQuiz: 'Delete Quiz',
    deleteConfirm: 'Are you sure you want to delete this quiz? (All evaluation reports will be lost)',
    deleteSuccess: 'Quiz deleted successfully',
    
    // Quiz Language Selection
    quizLanguage: 'Exam Language',
    quizLangTurkish: '🇹🇷 Turkish',
    quizLangEnglish: '🇬🇧 English',
    quizLangDesc: 'Questions and answers will be prepared in the selected language.',
    
    // Categories
    uncategorized: 'Uncategorized',
    quizzesCount: 'quiz',
    noQuizzesYet: 'No quizzes yet',
    noQuizzesInCategory: 'No quizzes in this category yet.',
    categoryNameLabel: 'Category Name',
    categoryNamePlaceholder: 'E.g: Math, Physics, History...',
    editCategory: 'Edit Category',
    save: 'Save',
    edit: 'Edit',
    delete: 'Delete',
    questionsLabel: 'questions',
    
    // Analytics
    analytics: 'Analytics',
    analyticsTitle: 'Performance Report',
    analyticsDesc: 'Topic-based accuracy rates and progress tracking.',
    topicAccuracy: 'Topic Accuracy Rates',
    weakTopics: 'Topics to Improve',
    strongTopics: 'Strong Topics',
    overallScore: 'Overall Average',
    totalCompleted: 'Completed Quizzes',
    totalAnswered: 'Questions Answered',
    noAnalytics: 'No analytics data yet',
    noAnalyticsDesc: 'Your performance report will appear here after you complete quizzes.',
    accuracyPct: 'Accuracy',
    topicQuestionCount: 'questions',
    personalizedHint: '💡 Personalized questions were generated from these topics.',
    
    // Common
    appName: 'ExamAI',
    appDescription: 'AI-Powered Exam Platform',
    loading: 'Loading...',
    success: 'Success!',
    quiz: 'Quiz',
    geminiApiKey: 'Gemini API Key',
    apiHint: 'Optional. Your personal key will be used for quiz generation and grading.',
    geminiModel: 'Gemini Model Name (Optional)',
    modelHint: 'If left blank, the system will automatically find and save the working model.',
  },
};

const LanguageContext = createContext(null);

export function LanguageProvider({ children }) {
  const [currentLanguage, setCurrentLanguage] = useState(() => {
    // Try to get from localStorage, default to 'tr'
    if (typeof window !== 'undefined') {
      return localStorage.getItem('language') || 'tr';
    }
    return 'tr';
  });

  const setLanguage = useCallback((lang) => {
    setCurrentLanguage(lang);
    if (typeof window !== 'undefined') {
      localStorage.setItem('language', lang);
    }
  }, []);

  const t = useCallback(
    (key) => {
      return translations[currentLanguage]?.[key] || translations['en'][key] || key;
    },
    [currentLanguage]
  );

  return (
    <LanguageContext.Provider value={{ t, currentLanguage, setLanguage }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLanguage must be used within LanguageProvider');
  return ctx;
}
