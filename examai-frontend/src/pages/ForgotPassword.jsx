import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, ArrowRight, Lock, CheckCircle, ArrowLeft } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { authApi } from '../api';
import { useLanguage } from '../context/LanguageContext';

const emailSchema = (t) => z.object({
  email: z.string().email(t('emailInvalid')),
});

const resetSchema = (t) => z.object({
  email: z.string().email(t('emailInvalid')),
  code: z.string().length(6, t('codeLength')),
  new_password: z.string().min(6, t('passwordMin')),
  confirm_password: z.string(),
}).refine((data) => data.new_password === data.confirm_password, {
  message: t('passwordMatch'),
  path: ['confirm_password'],
});

export default function ForgotPassword() {
  const [step, setStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [email, setEmail] = useState('');
  const navigate = useNavigate();
  const { t, currentLanguage, setLanguage } = useLanguage();

  const {
    register: registerEmail,
    handleSubmit: handleSubmitEmail,
    formState: { errors: errorsEmail },
  } = useForm({
    resolver: zodResolver(emailSchema(t)),
  });

  const {
    register: registerReset,
    handleSubmit: handleSubmitReset,
    setValue: setValueReset,
    formState: { errors: errorsReset },
  } = useForm({
    resolver: zodResolver(resetSchema(t)),
  });

  const onSubmitEmail = async (data) => {
    setIsLoading(true);
    try {
      await authApi.forgotPassword(data.email);
      setEmail(data.email);
      setValueReset('email', data.email);
      toast.success(t('resetCodeSent'));
      setStep(2);
    } catch (error) {
      const message = error.response?.data?.detail || t('error');
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const onSubmitReset = async (data) => {
    setIsLoading(true);
    try {
      await authApi.resetPassword({
        email: data.email,
        code: data.code,
        new_password: data.new_password,
      });
      toast.success(t('resetSuccess'));
      setStep(3);
    } catch (error) {
      const message = error.response?.data?.detail || t('resetError');
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const renderStep1 = () => (
    <>
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-100 rounded-full mb-4">
          <Mail className="w-8 h-8 text-indigo-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Şifremi Unuttum</h2>
        <p className="text-gray-600">
          E-posta adresinizi girin, size şifre sıfırlama kodu gönderelim.
        </p>
      </div>

      <form onSubmit={handleSubmitEmail(onSubmitEmail)} className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            E-posta Adresi
          </label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              {...registerEmail('email')}
              type="email"
              placeholder="ornek@email.com"
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
            />
          </div>
          {errorsEmail.email && (
            <p className="mt-1 text-sm text-red-500">{errorsEmail.email.message}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              Kod Gönder
              <ArrowRight className="w-5 h-5" />
            </>
          )}
        </button>
      </form>
    </>
  );

  const renderStep2 = () => (
    <>
      <div className="text-center mb-6">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-100 rounded-full mb-4">
          <Lock className="w-8 h-8 text-indigo-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Yeni Şifre Belirle</h2>
        <p className="text-gray-600">
          E-postanıza gönderilen 6 haneli kodu ve yeni şifrenizi girin.
        </p>
        <p className="text-sm text-indigo-600 mt-2 font-medium">{email}</p>
      </div>

      <form onSubmit={handleSubmitReset(onSubmitReset)} className="space-y-4">
        <input type="hidden" {...registerReset('email')} />

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Doğrulama Kodu (6 haneli)
          </label>
          <input
            {...registerReset('code')}
            type="text"
            placeholder="123456"
            maxLength={6}
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all text-center text-2xl tracking-widest"
          />
          {errorsReset.code && (
            <p className="mt-1 text-sm text-red-500">{errorsReset.code.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Yeni Şifre
          </label>
          <input
            {...registerReset('new_password')}
            type="password"
            placeholder="••••••••"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
          />
          {errorsReset.new_password && (
            <p className="mt-1 text-sm text-red-500">{errorsReset.new_password.message}</p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Yeni Şifre Tekrar
          </label>
          <input
            {...registerReset('confirm_password')}
            type="password"
            placeholder="••••••••"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
          />
          {errorsReset.confirm_password && (
            <p className="mt-1 text-sm text-red-500">{errorsReset.confirm_password.message}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-4"
        >
          {isLoading ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              Şifreyi Sıfırla
              <ArrowRight className="w-5 h-5" />
            </>
          )}
        </button>

        <button
          type="button"
          onClick={() => setStep(1)}
          className="w-full text-gray-600 py-2 text-sm hover:text-gray-800 transition-colors flex items-center justify-center gap-1"
        >
          <ArrowLeft className="w-4 h-4" />
          Kodu tekrar gönder
        </button>
      </form>
    </>
  );

  const renderStep3 = () => (
    <div className="text-center">
      <div className="inline-flex items-center justify-center w-20 h-20 bg-green-100 rounded-full mb-6">
        <CheckCircle className="w-10 h-10 text-green-600" />
      </div>
      <h2 className="text-2xl font-bold text-gray-800 mb-2">Şifre Sıfırlandı!</h2>
      <p className="text-gray-600 mb-6">
        Şifreniz başarıyla değiştirildi. Yeni şifrenizle giriş yapabilirsiniz.
      </p>
      <Link
        to="/login"
        className="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-3 px-8 rounded-lg font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all"
      >
        Giriş Yap
        <ArrowRight className="w-5 h-5" />
      </Link>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-2xl shadow-lg">
            <span className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              E
            </span>
          </Link>
        </div>

        {/* Form Container */}
        <div className="bg-white rounded-2xl shadow-2xl p-8">
          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}
          {step === 3 && renderStep3()}

          {/* Giriş Yap Linki */}
          {step !== 3 && (
            <p className="mt-6 text-center text-gray-600">
              <Link
                to="/login"
                className="text-indigo-600 hover:text-indigo-700 font-semibold inline-flex items-center gap-1"
              >
                <ArrowLeft className="w-4 h-4" />
                Giriş sayfasına dön
              </Link>
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
