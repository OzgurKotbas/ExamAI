import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';

export default function AuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();

  useEffect(() => {
    const token = searchParams.get('token');
    const email = searchParams.get('email');
    const name = searchParams.get('name');
    const userId = searchParams.get('user_id');
    const error = searchParams.get('error');

    if (error) {
      toast.error(`Giriş başarısız: ${decodeURIComponent(error)}`);
      navigate('/login');
      return;
    }

    if (token && email && name && userId) {
      const isNew = searchParams.get('is_new') === 'true';

      // Create user object
      const user = {
        id: userId,
        email: decodeURIComponent(email),
        full_name: decodeURIComponent(name),
        is_active: true,
        is_google_auth: true,
        is_oauth_user: true,
      };

      if (isNew) {
        // Yeni kullanıcı: henüz sistemde kayıtlı değil → Register sayfasına yönlendir
        // Google bilgilerini query param olarak taşı
        const registerParams = new URLSearchParams({
          from: 'google',
          token: token,
          email: email,
          name: name,
          user_id: userId,
        });
        toast('Google hesabınız bulundu. Lütfen kaydı tamamlayın.', { icon: '👋' });
        navigate(`/register?${registerParams.toString()}`);
      } else {
        // Mevcut kullanıcı: oturum aç ve dashboard'a yönlendir
        login(token, user);
        toast.success('Google ile giriş başarılı!');
        navigate('/dashboard');
      }
    } else {
      toast.error('Giriş bilgileri eksik');
      navigate('/login');
    }
  }, [searchParams, navigate, login]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center">
      <div className="text-center">
        <LoadingSpinner size="xl" />
        <p className="mt-4 text-white text-lg">Giriş yapılıyor...</p>
      </div>
    </div>
  );
}
