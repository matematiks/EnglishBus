import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, ArrowRight, Zap, Trophy, Volume2, X, Flame } from 'lucide-react';
import confetti from 'canvas-confetti';

const API_URL = 'http://localhost:8001';
const USER_ID = 1;
const COURSE_ID = 1;

function App() {
  const [screen, setScreen] = useState('landing'); // landing, dashboard, learning
  const [currentStep, setCurrentStep] = useState(1);
  const [sessionCards, setSessionCards] = useState([]);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const startSession = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/session/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: USER_ID, course_id: COURSE_ID })
      });

      const data = await res.json();

      if (data.items && data.items.length > 0) {
        setSessionCards(data.items);
        setCurrentStep(data.current_step);
        setCurrentCardIndex(0);
        setIsFlipped(false);
        setScreen('learning');
      } else {
        alert('🎉 Tebrikler! Tüm kartlar tamamlandı.');
      }
    } catch (err) {
      console.error(err);
      alert('Backend hatası! Server çalışıyor mu?');
    } finally {
      setIsLoading(false);
    }
  };

  const handleComplete = async () => {
    const currentCard = sessionCards[currentCardIndex];

    try {
      await fetch(`${API_URL}/session/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: USER_ID,
          course_id: COURSE_ID,
          completed_word_ids: [currentCard.word_id]
        })
      });

      // Next card
      if (currentCardIndex < sessionCards.length - 1) {
        setCurrentCardIndex(currentCardIndex + 1);
        setIsFlipped(false);
      } else {
        // Session complete!
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 }
        });
        setTimeout(() => {
          setScreen('dashboard');
        }, 1500);
      }
    } catch (err) {
      console.error(err);
      alert('Kayıt hatası!');
    }
  };

  const playAudio = (url) => {
    if (!url) return;
    const audio = new Audio(url);
    audio.play().catch(console.error);
  };

  // LANDING SCREEN
  if (screen === 'landing') {
    return (
      <div className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white">

        {/* Floating Blobs */}
        <motion.div
          animate={{ scale: [1, 1.2, 1], rotate: [0, 90, 0] }}
          transition={{ duration: 20, repeat: Infinity }}
          className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-yellow-400 rounded-full mix-blend-multiply filter blur-3xl opacity-30"
        />
        <motion.div
          animate={{ scale: [1, 1.1, 1], rotate: [0, -60, 0] }}
          transition={{ duration: 15, repeat: Infinity, delay: 2 }}
          className="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-green-400 rounded-full mix-blend-multiply filter blur-3xl opacity-30"
        />

        <div className="z-10 text-center px-6 max-w-md w-full">
          {/* Logo */}
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ type: "spring", stiffness: 260, damping: 20 }}
            className="w-32 h-32 bg-white rounded-3xl mx-auto mb-8 shadow-2xl flex items-center justify-center"
          >
            <Zap size={64} className="text-yellow-500 fill-current" />
          </motion.div>

          {/* Title */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-5xl font-black mb-2 tracking-tight drop-shadow-md"
          >
            EnglishBus
          </motion.h1>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="text-xl font-semibold text-white/90 mb-12"
          >
            Fibonacci Spaced Repetition
          </motion.p>

          {/* CTA Button */}
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setScreen('dashboard')}
            className="group relative w-full bg-white text-purple-600 text-xl font-black py-5 rounded-2xl shadow-[0_10px_20px_rgba(0,0,0,0.2)] border-b-8 border-purple-200 active:border-b-0 active:translate-y-2 transition-all flex items-center justify-center gap-3"
          >
            BAŞLAYALIM MI?
            <ArrowRight className="group-hover:translate-x-1 transition-transform" strokeWidth={3} />
          </motion.button>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
            className="mt-6 text-sm text-white/60 font-medium"
          >
            🚀 Step-based learning system
          </motion.p>
        </div>
      </div>
    );
  }

  // DASHBOARD SCREEN
  if (screen === 'dashboard') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50">
        <div className="max-w-md mx-auto p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-black text-gray-800">Dashboard</h2>
              <p className="text-gray-500 text-sm">Adım {currentStep}</p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
              <Trophy size={24} className="text-purple-600" />
            </div>
          </div>

          {/* Course Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-3xl p-6 shadow-xl border-b-4 border-purple-200 mb-6"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-purple-500 rounded-2xl flex items-center justify-center">
                <span className="text-2xl">🇬🇧</span>
              </div>
              <div>
                <h3 className="font-black text-xl text-gray-800">A1 English</h3>
                <p className="text-sm text-gray-500">122 Kelime</p>
              </div>
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={startSession}
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white font-black py-4 rounded-xl shadow-lg disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <>
                  <Flame size={20} />
                  ÇALIŞMAYA BAŞLA
                </>
              )}
            </motion.button>
          </motion.div>
        </div>
      </div>
    );
  }

  // LEARNING SCREEN
  if (screen === 'learning' && sessionCards.length > 0) {
    const currentCard = sessionCards[currentCardIndex];
    const progress = ((currentCardIndex + 1) / sessionCards.length) * 100;

    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 flex flex-col">
        {/* Header */}
        <div className="bg-white shadow-sm p-4">
          <div className="max-w-md mx-auto flex items-center justify-between">
            <button onClick={() => setScreen('dashboard')} className="p-2">
              <X size={24} className="text-gray-600" />
            </button>
            <div className="flex-1 mx-4">
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-purple-500"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>
            </div>
            <span className="text-sm font-bold text-gray-600">
              {currentCardIndex + 1}/{sessionCards.length}
            </span>
          </div>
        </div>

        {/* Card */}
        <div className="flex-1 flex items-center justify-center p-6">
          <div className="w-full max-w-md">
            <motion.div
              key={currentCardIndex}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white rounded-3xl shadow-2xl p-8 min-h-[500px] flex flex-col"
            >
              {/* Audio Button */}
              <div className="flex justify-end mb-4">
                <button
                  onClick={() => playAudio(isFlipped ? currentCard.audio_tr_url : currentCard.audio_en_url)}
                  className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center hover:bg-purple-200 transition-colors"
                >
                  <Volume2 size={20} className="text-purple-600" />
                </button>
              </div>

              {/* Word */}
              <div className="flex-1 flex flex-col items-center justify-center text-center">
                <motion.h2
                  className="text-5xl font-black text-gray-800 mb-8"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  {currentCard.english}
                </motion.h2>

                <AnimatePresence>
                  {isFlipped && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                    >
                      <p className="text-3xl font-bold text-purple-600 mb-4">
                        {currentCard.turkish}
                      </p>
                      <p className="text-gray-500 italic">
                        "{currentCard.english}"
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* CTA */}
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => {
                  if (!isFlipped) {
                    setIsFlipped(true);
                  } else {
                    handleComplete();
                  }
                }}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white font-black py-4 rounded-xl shadow-lg"
              >
                {isFlipped ? 'TAMAMLADIM ✓' : 'ANLAMI GÖSTER'}
              </motion.button>
            </motion.div>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

export default App;
