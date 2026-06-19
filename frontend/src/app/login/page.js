'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Lock, User, Eye, EyeOff, Stethoscope, ArrowRight, Activity } from 'lucide-react';
import { API_BASE_URL } from '@/config';

export default function LoginPage() {
    const router = useRouter();

    // 1. State untuk menampung input Form & Error
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    // 2. Fungsi Handlers saat tombol Masuk ditekan
    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const res = await fetch(`${API_BASE_URL}/api/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password }),
            });

            const data = await res.json();

            // Gunakan validasi berdasarkan flag .success dari payload Flask
            if (res.ok && data.success) {
                console.log("=== AIDEB LOGIN SUCCESS ===");
                localStorage.setItem('aideb_token', data.token);
                localStorage.setItem('detuji_token', data.token);

                // GANTI baris window.location.href menjadi router.push murni Next.js:
                router.push('/');
            } else {
                setError(data.message || 'Terjadi kesalahan login.');
            }
        } catch (err) {
            setError('Gagal terhubung ke server backend Flask.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen relative overflow-hidden font-sans">

            {/* ================= SISI KIRI: VISUAL BANNER DENGAN GAMBAR ================= */}
            <div className="hidden lg:flex lg:w-3/5 relative overflow-hidden">
                {/* Background Image */}
                <img
                    src="/background_detuji_ct.jpg"
                    alt="Neurologist examining Brain MRI Scan"
                    className="absolute inset-0 w-full h-full object-cover"
                />

                {/* Gradient Overlay — dark bottom for text readability */}
                <div className="absolute inset-0 bg-gradient-to-t from-dark-medis via-dark-medis/70 to-dark-medis/30 z-10" />
                <div className="absolute inset-0 bg-gradient-to-r from-transparent to-dark-medis/40 z-10" />

                {/* Ambient glow accents */}
                <div className="absolute top-[15%] left-[10%] w-64 h-64 bg-primary-medis/15 rounded-full blur-[100px] animate-pulse-slow z-20" />
                <div className="absolute bottom-[20%] right-[15%] w-80 h-80 bg-secondary-medis/10 rounded-full blur-[120px] animate-pulse-slow z-20" style={{ animationDelay: '4s' }} />

                {/* Content Overlay at Bottom */}
                <div className="relative z-30 flex flex-col justify-end p-14 w-full">
                    <div className="animate-fade-in">
                        <div className="flex items-center gap-2 mb-5">
                            <div className="w-9 h-9 rounded-xl bg-white/10 border border-white/15 flex items-center justify-center backdrop-blur-sm">
                                <Activity className="w-4 h-4 text-light-medis" />
                            </div>
                            <span className="text-[10px] font-black tracking-[0.2em] text-light-medis/80 uppercase">
                                AIDEB Brain Diagnostic Platform
                            </span>
                        </div>
                        <h1 className="text-4xl xl:text-5xl font-black text-white leading-[1.15] tracking-tight">
                            Sistem Deteksi{' '}
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-secondary-medis via-light-medis to-secondary-medis">
                                Epilepsi Otak
                            </span>
                            <br />
                            Berbasis Citra MRI
                        </h1>
                        <p className="text-slate-300/80 mt-4 text-sm leading-relaxed max-w-lg">
                            Gunakan kekuatan kecerdasan buatan berbasis deep learning untuk membantu proses skrining awal dan analisis medis tanda-tanda epilepsi secara cepat, presisi, dan aman.
                        </p>
                        <div className="flex items-center gap-3 mt-7">
                            <div className="h-[3px] w-16 bg-gradient-to-r from-secondary-medis to-light-medis rounded-full" />
                            <div className="h-[3px] w-8 bg-secondary-medis/40 rounded-full" />
                            <div className="h-[3px] w-4 bg-secondary-medis/20 rounded-full" />
                        </div>
                    </div>
                </div>
            </div>

            {/* ================= SISI KANAN: FORM LOGIN ================= */}
            <div className="w-full lg:w-2/5 flex items-center justify-center p-6 sm:p-8 bg-gradient-to-br from-slate-50 via-white to-slate-100 relative">
                {/* Subtle decorative elements */}
                <div className="absolute top-0 right-0 w-72 h-72 bg-light-medis/20 rounded-full blur-[80px] pointer-events-none" />
                <div className="absolute bottom-0 left-0 w-56 h-56 bg-primary-medis/5 rounded-full blur-[60px] pointer-events-none" />
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-secondary-medis/[0.02] rounded-full blur-[100px] pointer-events-none" />

                <div className="w-full max-w-[400px] relative z-10 animate-fade-in">

                    {/* Logo + Brand */}
                    <div className="flex items-center gap-3 justify-center mb-2">
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary-medis to-secondary-medis flex items-center justify-center text-white shadow-lg shadow-primary-medis/25">
                            <Stethoscope className="w-6 h-6" />
                        </div>
                        <span className="text-2xl font-black text-dark-medis tracking-tight">
                            AIDEB<span className="text-primary-medis">.AI</span>
                        </span>
                    </div>

                    {/* Subtitle */}
                    <div className="text-center mb-8">
                        <h2 className="text-xl font-extrabold text-dark-medis mt-4">Masuk Ke Sistem</h2>
                        <p className="text-slate-400 text-xs mt-1.5 font-medium">Akses dashboard skrining MRI Epilepsi berbasis AI</p>
                    </div>

                    {/* Login Card */}
                    <div className="bg-white p-7 sm:p-8 rounded-2xl shadow-xl shadow-slate-200/60 border border-slate-100/80">

                        {/* Alert Box jika username/password keliru */}
                        {error && (
                            <div className="mb-5 p-3.5 bg-red-50 border border-red-200 text-red-600 text-xs rounded-xl font-semibold flex items-center gap-2">
                                <span className="w-1.5 h-1.5 bg-red-500 rounded-full shrink-0 animate-pulse" />
                                {error}
                            </div>
                        )}

                        <form onSubmit={handleLogin} className="space-y-5">
                            {/* Input Username */}
                            <div>
                                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">
                                    Username<span className="text-red-500">*</span>
                                </label>
                                <div className="relative group">
                                    <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400 group-focus-within:text-primary-medis transition-colors">
                                        <User className="w-4 h-4" />
                                    </span>
                                    <input
                                        type="text"
                                        required
                                        placeholder="Masukkan username"
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
                                        className="w-full pl-11 pr-4 py-3 bg-slate-50/80 border border-slate-200 rounded-xl text-sm text-dark-medis placeholder:text-slate-400 focus:outline-none focus:border-primary-medis focus:ring-4 focus:ring-primary-medis/10 focus:bg-white transition-all duration-300 input-depth"
                                    />
                                </div>
                            </div>

                            {/* Input Password */}
                            <div>
                                <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">
                                    Password<span className="text-red-500">*</span>
                                </label>
                                <div className="relative group">
                                    <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 text-slate-400 group-focus-within:text-primary-medis transition-colors">
                                        <Lock className="w-4 h-4" />
                                    </span>
                                    <input
                                        type={showPassword ? "text" : "password"}
                                        required
                                        placeholder="Masukkan password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        className="w-full pl-11 pr-12 py-3 bg-slate-50/80 border border-slate-200 rounded-xl text-sm text-dark-medis placeholder:text-slate-400 focus:outline-none focus:border-primary-medis focus:ring-4 focus:ring-primary-medis/10 focus:bg-white transition-all duration-300 input-depth"
                                    />
                                    {/* Tombol Toggle Mata Password */}
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute inset-y-0 right-0 flex items-center pr-3.5 text-slate-400 hover:text-primary-medis transition-colors"
                                    >
                                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                    </button>
                                </div>
                            </div>

                            {/* Tombol Submit */}
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-3.5 bg-gradient-to-r from-primary-medis to-secondary-medis hover:brightness-110 active:scale-[0.98] text-white rounded-xl font-bold text-sm transition-all duration-300 transform shadow-lg shadow-primary-medis/20 disabled:opacity-50 disabled:scale-100 flex items-center justify-center gap-2 group"
                            >
                                {loading ? (
                                    <>
                                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                        Memvalidasi Kredensial...
                                    </>
                                ) : (
                                    <>
                                        Masuk Ke Dashboard
                                        <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                                    </>
                                )}
                            </button>
                        </form>
                    </div>

                    {/* Footer badge */}
                    <div className="mt-7 text-center">
                        <span className="text-[9px] text-slate-400 font-bold tracking-widest uppercase bg-slate-50 border border-slate-100 px-3.5 py-1.5 rounded-lg inline-flex items-center gap-1.5">
                            <Activity className="w-3 h-3 text-primary-medis" />
                            Powered by MRI-AI Deep Learning
                        </span>
                    </div>

                </div>
            </div>

        </div>
    );
}