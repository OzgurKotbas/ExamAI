import { useState } from 'react';
import { 
  User, 
  Settings, 
  Lock, 
  Moon, 
  Sun, 
  Globe, 
  LogOut,
  ChevronDown,
  Edit3,
  Camera,
  Loader2
} from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';
import { useAuth } from '../context/AuthContext';
import { authApi } from '../api';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';

export default function ProfileMenu() {
  const [isOpen, setIsOpen] = useState(false);
  const [showAccountModal, setShowAccountModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showNameModal, setShowNameModal] = useState(false);
  
  const { theme, toggleTheme } = useTheme();
  const { t, currentLanguage, setLanguage } = useLanguage();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
    toast.success(t('logout') + ' ' + t('success'));
  };

  const toggleLanguage = () => {
    setLanguage(currentLanguage === 'tr' ? 'en' : 'tr');
  };

  return (
    <>
      <div className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <div className="w-8 h-8 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-full flex items-center justify-center">
            <span className="text-sm font-bold text-white">
              {user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
            </span>
          </div>
          <span className="text-sm font-medium text-gray-700 hidden sm:block">
            {user?.full_name?.split(' ')[0]}
          </span>
          <ChevronDown className={`w-4 h-4 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {isOpen && (
          <>
            <div 
              className="fixed inset-0 z-40" 
              onClick={() => setIsOpen(false)}
            />
            <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 py-2 z-50">
              {/* Profile Header */}
              <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
                <p className="font-medium text-gray-900 dark:text-white">{user?.full_name}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400 truncate">{user?.email}</p>
              </div>

              {/* Menu Items */}
              <div className="py-1">
                <button
                  onClick={() => {
                    setIsOpen(false);
                    setShowAccountModal(true);
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2"
                >
                  <User className="w-4 h-4" />
                  {t('accountInfo')}
                </button>
                
                <button
                  onClick={() => {
                    setIsOpen(false);
                    setShowPasswordModal(true);
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2"
                >
                  <Lock className="w-4 h-4" />
                  {t('changePassword')}
                </button>
              </div>

              <div className="border-t border-gray-100 dark:border-gray-700 py-1">
                {/* Theme Toggle */}
                <button
                  onClick={() => {
                    toggleTheme();
                    setIsOpen(false);
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2"
                >
                  {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                  {theme === 'dark' ? t('lightMode') : t('darkMode')}
                </button>

                {/* Language Toggle */}
                <button
                  onClick={() => {
                    toggleLanguage();
                    setIsOpen(false);
                  }}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2"
                >
                  <Globe className="w-4 h-4" />
                  {currentLanguage === 'tr' ? t('english') : t('turkish')}
                </button>
              </div>

              <div className="border-t border-gray-100 dark:border-gray-700 py-1">
                <button
                  onClick={handleLogout}
                  className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 flex items-center gap-2"
                >
                  <LogOut className="w-4 h-4" />
                  {t('logout')}
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Account Info Modal */}
      {showAccountModal && (
        <AccountModal 
          onClose={() => setShowAccountModal(false)} 
          user={user}
          t={t}
        />
      )}

      {/* Change Password Modal */}
      {showPasswordModal && (
        <PasswordModal 
          onClose={() => setShowPasswordModal(false)} 
          t={t}
        />
      )}
    </>
  );
}

function AccountModal({ onClose, user, t }) {
  const [editName, setEditName] = useState(user?.full_name || '');
  const [editEmail, setEditEmail] = useState(user?.email || '');
  const [editGeminiKey, setEditGeminiKey] = useState(user?.gemini_api_key || '');
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const { setUser } = useAuth();

  const handleSave = async () => {
    if (!editName.trim() || !editEmail.trim()) {
      toast.error(t('nameRequired') || 'Name and email are required');
      return;
    }
    
    setIsLoading(true);
    try {
      const response = await authApi.updateProfile(editName, editEmail, editGeminiKey);
      // Update user in context
      setUser(response.data);
      toast.success(t('success'));
      setIsEditing(false);
      onClose();
    } catch (error) {
      const message = error.response?.data?.detail || t('error');
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-md w-full p-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">{t('accountInfo')}</h2>
        
        <div className="space-y-4">
          <div className="flex justify-center mb-6">
            <div className="relative">
              <div className="w-24 h-24 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-full flex items-center justify-center">
                <span className="text-3xl font-bold text-white">
                  {(isEditing ? editName : user?.full_name)?.charAt(0)?.toUpperCase() || 'U'}
                </span>
              </div>
              <button className="absolute bottom-0 right-0 w-8 h-8 bg-white dark:bg-gray-700 rounded-full shadow-md flex items-center justify-center hover:bg-gray-50 dark:hover:bg-gray-600">
                <Camera className="w-4 h-4 text-gray-600 dark:text-gray-300" />
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('fullName')}</label>
            <input 
              type="text" 
              value={isEditing ? editName : user?.full_name || ''} 
              onChange={(e) => setEditName(e.target.value)}
              disabled={!isEditing || isLoading}
              className={`w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg ${
                isEditing 
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500' 
                  : 'bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
              }`}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('email')}</label>
            <input 
              type="email" 
              value={isEditing ? editEmail : user?.email || ''} 
              onChange={(e) => setEditEmail(e.target.value)}
              disabled={!isEditing || isLoading}
              className={`w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg ${
                isEditing 
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500' 
                  : 'bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
              }`}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('geminiApiKey') || 'Gemini API Key'}
            </label>
            <input 
              type="password" 
              value={isEditing ? editGeminiKey : user?.gemini_api_key || ''} 
              onChange={(e) => setEditGeminiKey(e.target.value)}
              placeholder="AIzaSy..."
              disabled={!isEditing || isLoading}
              className={`w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg ${
                isEditing 
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500' 
                  : 'bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
              }`}
            />
            <p className="text-[10px] text-gray-500 mt-1 italic">
              {t('apiHint') || 'Optional. Your personal key will be used for AI tasks.'}
            </p>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="flex-1 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
          >
            {t('cancel')}
          </button>
          {isEditing ? (
            <button
              onClick={handleSave}
              disabled={isLoading}
              className="flex-1 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {t('loading') || 'Loading...'}
                </>
              ) : (
                <>{t('success') === 'Başarılı!' ? 'Kaydet' : 'Save'}</>
              )}
            </button>
          ) : (
            <button
              onClick={() => setIsEditing(true)}
              className="flex-1 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 transition-all"
            >
              {t('success') === 'Başarılı!' ? 'Düzenle' : 'Edit'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function PasswordModal({ onClose, t }) {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast.error(t('passwordMatch'));
      return;
    }
    if (newPassword.length < 6) {
      toast.error(t('passwordMin') || 'Password must be at least 6 characters');
      return;
    }
    
    setIsLoading(true);
    try {
      await authApi.changePassword(currentPassword, newPassword);
      toast.success(t('success'));
      onClose();
      // Clear form
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error) {
      const message = error.response?.data?.detail || t('error');
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-md w-full p-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">{t('changePassword')}</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('password')}</label>
            <input 
              type="password" 
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              disabled={isLoading}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('newPassword')}</label>
            <input 
              type="password" 
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              disabled={isLoading}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('confirmPassword')}</label>
            <input 
              type="password" 
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={isLoading}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              required
            />
          </div>

          <div className="flex gap-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="flex-1 py-3 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
            >
              {t('cancel')}
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:from-indigo-700 hover:to-purple-700 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {t('loading') || 'Loading...'}
                </>
              ) : (
                t('changePassword')
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
