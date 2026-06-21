import { useState, useEffect } from 'react';
import { 
  Folder, 
  Plus, 
  X, 
  Edit2, 
  Trash2, 
  ChevronRight,
  BookOpen,
  Brain,
  MoreVertical,
  CheckCircle
} from 'lucide-react';
import { toast } from 'react-hot-toast';

export default function QuizCategories({ 
  quizzes, 
  notes,
  onQuizSelect, 
  t,
  currentLanguage,
  activeTab,
  onTabChange,
  onDeleteQuiz
}) {
  const [categories, setCategories] = useState(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('quizCategories');
      return saved ? JSON.parse(saved) : [
        { id: 'all', name: t('allQuizzes'), icon: 'BookOpen', isDefault: true },
        { id: 'uncategorized', name: t('uncategorized'), icon: 'Folder', isDefault: true }
      ];
    }
    return [
      { id: 'all', name: t('allQuizzes'), icon: 'BookOpen', isDefault: true },
      { id: 'uncategorized', name: t('uncategorized'), icon: 'Folder', isDefault: true }
    ];
  });
  
  const [quizCategories, setQuizCategories] = useState(() => {
    if (typeof window !== 'undefined') {
      return JSON.parse(localStorage.getItem('quizToCategories') || '{}');
    }
    return {};
  });
  
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [editingCategory, setEditingCategory] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [openMenuId, setOpenMenuId] = useState(null);

  // Update default categories when language changes
  useEffect(() => {
    setCategories(prev => prev.map(cat => {
      if (cat.id === 'all') return { ...cat, name: t('allQuizzes') };
      if (cat.id === 'uncategorized') return { ...cat, name: t('uncategorized') };
      return cat;
    }));
  }, [currentLanguage, t]);

  // Save to localStorage whenever categories change
  useEffect(() => {
    localStorage.setItem('quizCategories', JSON.stringify(categories));
  }, [categories]);

  useEffect(() => {
    localStorage.setItem('quizToCategories', JSON.stringify(quizCategories));
  }, [quizCategories]);

  const createCategory = () => {
    if (!newCategoryName.trim()) {
      toast.error(t('categoryNameLabel'));
      return;
    }
    
    const newCategory = {
      id: Date.now().toString(),
      name: newCategoryName.trim(),
      icon: 'Folder',
      createdAt: new Date().toISOString()
    };
    
    setCategories([...categories, newCategory]);
    setNewCategoryName('');
    setShowCreateModal(false);
    toast.success(currentLanguage === 'tr' ? 'Kategori oluşturuldu' : 'Category created');
  };

  const updateCategory = (id, newName) => {
    setCategories(categories.map(cat => 
      cat.id === id ? { ...cat, name: newName } : cat
    ));
    setEditingCategory(null);
    toast.success(currentLanguage === 'tr' ? 'Kategori güncellendi' : 'Category updated');
  };

  const deleteCategory = (id) => {
    if (id === 'all' || id === 'uncategorized') {
      toast.error(currentLanguage === 'tr' ? 'Bu kategori silinemez' : 'This category cannot be deleted');
      return;
    }
    
    // Move quizzes in this category to uncategorized
    const updatedQuizCategories = { ...quizCategories };
    Object.keys(updatedQuizCategories).forEach(quizId => {
      if (updatedQuizCategories[quizId] === id) {
        updatedQuizCategories[quizId] = 'uncategorized';
      }
    });
    setQuizCategories(updatedQuizCategories);
    
    setCategories(categories.filter(cat => cat.id !== id));
    if (selectedCategory === id) {
      setSelectedCategory('all');
    }
    toast.success(currentLanguage === 'tr' ? 'Kategori silindi' : 'Category deleted');
  };

  const assignQuizToCategory = (quizId, categoryId) => {
    setQuizCategories({ ...quizCategories, [quizId]: categoryId });
    toast.success(currentLanguage === 'tr' ? 'Sınav kategoriye eklendi' : 'Quiz added to category');
  };

  const getFilteredQuizzes = () => {
    if (selectedCategory === 'all') {
      return quizzes;
    }
    return quizzes.filter(quiz => quizCategories[quiz.id] === selectedCategory || 
      (selectedCategory === 'uncategorized' && !quizCategories[quiz.id]));
  };

  const getQuizCount = (categoryId) => {
    if (categoryId === 'all') {
      return quizzes.length;
    }
    return quizzes.filter(quiz => 
      quizCategories[quiz.id] === categoryId || 
      (categoryId === 'uncategorized' && !quizCategories[quiz.id])
    ).length;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'ready':
      case 'completed':
        return <div className="w-2 h-2 bg-green-500 rounded-full" />;
      case 'pending':
        return <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />;
      case 'generating':
        return <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />;
      case 'failed':
        return <div className="w-2 h-2 bg-red-500 rounded-full" />;
      default:
        return <div className="w-2 h-2 bg-gray-400 rounded-full" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'ready':
      case 'completed':
        return t('quizStatusReady');
      case 'pending':
        return t('quizStatusPending');
      case 'generating':
        return t('quizStatusGenerating');
      case 'failed':
        return t('quizStatusFailed');
      default:
        return status;
    }
  };

  const filteredQuizzes = getFilteredQuizzes();

  return (
    <div className="flex gap-6">
      {/* Sidebar Categories */}
      <div className="w-64 flex-shrink-0">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="p-4 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
            <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Folder className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
              {t('categories')}
            </h3>
            <button
              onClick={() => setShowCreateModal(true)}
              className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
              title={t('createCategory')}
            >
              <Plus className="w-4 h-4 text-gray-600" />
            </button>
          </div>
          
          <div className="divide-y divide-gray-100">
            {categories.map((category) => (
              <div
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`flex items-center justify-between px-4 py-3 cursor-pointer transition-colors ${
                  selectedCategory === category.id 
                    ? 'bg-indigo-50 border-r-2 border-indigo-600' 
                    : 'hover:bg-gray-50'
                }`}
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <Folder className={`w-4 h-4 ${selectedCategory === category.id ? 'text-indigo-600' : 'text-gray-400'}`} />
                  <span className={`text-sm font-medium truncate ${selectedCategory === category.id ? 'text-indigo-900' : 'text-gray-700'}`}>
                    {category.name}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                    {getQuizCount(category.id)}
                  </span>
                  {!category.isDefault && (
                    <div className="relative">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setOpenMenuId(openMenuId === category.id ? null : category.id);
                        }}
                        className="p-1 hover:bg-gray-200 rounded"
                      >
                        <MoreVertical className="w-3 h-3 text-gray-400" />
                      </button>
                      
                      {openMenuId === category.id && (
                        <>
                          <div 
                            className="fixed inset-0 z-40" 
                            onClick={() => setOpenMenuId(null)}
                          />
                          <div className="absolute right-0 mt-1 w-32 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setEditingCategory(category);
                                setOpenMenuId(null);
                              }}
                              className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-2"
                            >
                              <Edit2 className="w-3 h-3" />
                              {t('edit')}
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                deleteCategory(category.id);
                                setOpenMenuId(null);
                              }}
                              className="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                            >
                              <Trash2 className="w-3 h-3" />
                              {t('delete')}
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quiz List */}
      <div className="flex-1">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          <div className="p-4 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {categories.find(c => c.id === selectedCategory)?.name}
            </h3>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {filteredQuizzes.length} {t('quizzesCount')}
            </span>
          </div>
          
          {filteredQuizzes.length === 0 ? (
            <div className="p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <BookOpen className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">{t('noQuizzesYet')}</h3>
              <p className="text-gray-500 dark:text-gray-400 mb-4">{t('noQuizzesInCategory')}</p>
              <button
                onClick={() => onTabChange('upload')}
                className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
              >
                <Plus className="w-5 h-5" />
                {t('createQuiz')}
              </button>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {filteredQuizzes.map((quiz) => (
                <div
                  key={quiz.id}
                  className="p-4 hover:bg-gray-50 transition-colors group"
                >
                  <div className="flex items-center justify-between">
                    <div 
                      onClick={() => onQuizSelect(quiz.id)}
                      className="flex items-center gap-4 flex-1 cursor-pointer"
                    >
                      <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                        <Brain className="w-6 h-6 text-indigo-600" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold text-gray-900">{t('quiz')} #{quiz.id?.slice(-6) || '...'}</h4>
                          {quiz.latest_grading_id ? (
                            <div className="flex flex-col items-end gap-1">
                              <div className="flex items-center gap-1.5 px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-[10px] font-bold">
                                <CheckCircle className="w-3 h-3" />
                                {currentLanguage === 'tr' ? 'ÇÖZÜLDÜ' : 'SOLVED'}
                              </div>
                              {quiz.score != null && (
                                <span className="text-[10px] font-bold text-indigo-600">
                                  {quiz.score.toFixed(1)} / {quiz.max_score}
                                </span>
                              )}
                            </div>
                          ) : (
                            <>
                              {getStatusIcon(quiz.status)}
                              <span className="text-xs text-gray-500">{getStatusText(quiz.status)}</span>
                            </>
                          )}
                        </div>
                        <p className="text-sm text-gray-500">
                          {quiz.total_questions} {t('questionsLabel')} • {quiz.mc_ratio === 1.0 ? (currentLanguage === 'tr' ? 'Test' : 'Test') : (quiz.mc_ratio === 0.0 ? (currentLanguage === 'tr' ? 'Klasik' : 'Classic') : (currentLanguage === 'tr' ? 'Karma' : 'Mixed'))} • {quiz.difficulty === 'easy' ? t('easy') : quiz.difficulty === 'hard' ? t('hard') : t('medium')}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          {quiz.created_at ? new Date(quiz.created_at).toLocaleDateString(currentLanguage === 'tr' ? 'tr-TR' : 'en-US', {
                            day: 'numeric',
                            month: 'long',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          }) : '...'}
                        </p>
                      </div>
                    </div>
                    
                    {/* Category Assignment */}
                    <div className="flex items-center gap-2">
                      <select
                        value={quizCategories[quiz.id] || 'uncategorized'}
                        onChange={(e) => assignQuizToCategory(quiz.id, e.target.value)}
                        className="text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {categories.filter(c => !c.isDefault || c.id === 'uncategorized').map(cat => (
                          <option key={cat.id} value={cat.id}>{cat.name}</option>
                        ))}
                      </select>
                      <button
                        onClick={(e) => onDeleteQuiz && onDeleteQuiz(quiz.id, e)}
                        title={t('deleteQuiz')}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Category Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">{t('createCategory')}</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('categoryNameLabel')}</label>
                <input 
                  type="text" 
                  value={newCategoryName}
                  onChange={(e) => setNewCategoryName(e.target.value)}
                  placeholder={t('categoryNamePlaceholder')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  autoFocus
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setNewCategoryName('');
                }}
                className="flex-1 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
              >
                {t('cancel')}
              </button>
              <button
                onClick={createCategory}
                className="flex-1 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 transition-all"
              >
                {t('createCategory')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Category Modal */}
      {editingCategory && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">{t('editCategory')}</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('categoryNameLabel')}</label>
                <input 
                  type="text" 
                  defaultValue={editingCategory.name}
                  onChange={(e) => setEditingCategory({ ...editingCategory, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                  autoFocus
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setEditingCategory(null)}
                className="flex-1 py-3 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
              >
                {t('cancel')}
              </button>
              <button
                onClick={() => updateCategory(editingCategory.id, editingCategory.name)}
                className="flex-1 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 transition-all"
              >
                {t('save')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
