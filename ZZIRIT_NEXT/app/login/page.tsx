"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  CircuitBoard, Mail, Lock, Eye, EyeOff, User, Building, Briefcase, ArrowRight, ChevronDown, X, MapPin
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select, SelectTrigger, SelectValue, SelectContent, SelectItem
} from "@/components/ui/select";
import Chatbot from "@/components/chatbot/chatbot";
import LocationSearchModal from "@/components/location-search-modal";

const slides = [
  {
    icon: <CircuitBoard className="w-14 h-14 mb-3 text-white/90" />,
    title: "클라우드 기반 대시보드",
    desc: "스마트폰, 태블릿, PC에서 언제 어디서나.\n관리자·엔지니어 모두를 위한 통합 플랫폼."
  },
  {
    icon: <CircuitBoard className="w-14 h-14 mb-3 text-white/90" />,
    title: "실시간 PCB 모니터링",
    desc: "AI 기반 결함 감지 및 품질 관리.\n24시간 실시간 모니터링으로 생산성 향상."
  },
  {
    icon: <CircuitBoard className="w-14 h-14 mb-3 text-white/90" />,
    title: "스마트 인벤토리 관리",
    desc: "자동 재고 추적 및 알림 시스템.\n효율적인 부품 관리로 비용 절감."
  }
];

const translations = {
  ko: {
    loginTitle: "로그인",
    signupTitle: "회원가입",
    email: "이메일",
    password: "비밀번호",
    confirmPassword: "비밀번호 확인",
    name: "이름",
    company: "회사명",
    position: "직책",
    rememberMe: "로그인 상태 유지",
    loginButton: "로그인",
    signupButton: "회원가입",
    noAccountDesc: "계정이 없으신가요?",
    hasAccountDesc: "이미 계정이 있으신가요?",
    signupSwitch: "회원가입",
    loginSwitch: "로그인",
    termsText: "이용약관 및 개인정보처리방침에 동의합니다.",
    positionOptions: {
      engineer: "엔지니어",
      manager: "관리자",
      operator: "작업자",
      supervisor: "감독자",
      qc: "품질관리",
      other: "기타"
    }
  },
  en: {
    loginTitle: "Login",
    signupTitle: "Sign Up",
    email: "Email",
    password: "Password",
    confirmPassword: "Confirm Password",
    name: "Name",
    company: "Company",
    position: "Position",
    rememberMe: "Remember me",
    loginButton: "Login",
    signupButton: "Sign Up",
    noAccountDesc: "Don't have an account?",
    hasAccountDesc: "Already have an account?",
    signupSwitch: "Sign Up",
    loginSwitch: "Login",
    termsText: "I agree to the Terms of Service and Privacy Policy.",
    positionOptions: {
      engineer: "Engineer",
      manager: "Manager",
      operator: "Operator",
      supervisor: "Supervisor",
      qc: "Quality Control",
      other: "Other"
    }
  }
};

export default function LoginPage() {
  const searchParams = useSearchParams();
  const initialMode = (searchParams.get('mode') as "login" | "signup") || "login";
  
  const [mode, setMode] = useState<"login" | "signup">(initialMode);
  const [language, setLanguage] = useState<"ko" | "en">("ko");
  const [isLoading, setIsLoading] = useState(false);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);
  const [showLocationModal, setShowLocationModal] = useState(false);
  const router = useRouter();
  const t = translations[language];

  // URL 파라미터 변경 감지
  useEffect(() => {
    const newMode = (searchParams.get('mode') as "login" | "signup") || "login";
    setMode(newMode);
  }, [searchParams]);

  // 광고 배경 회전 (움직이는 conic-gradient)
  const [bgAngle, setBgAngle] = useState(0);
  useEffect(() => {
    const interval = setInterval(() => setBgAngle(a => (a + 1) % 360), 40);
    return () => clearInterval(interval);
  }, []);

  // 슬라이드 자동 전환
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slides.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  // 언어 드롭다운
  const [langOpen, setLangOpen] = useState(false);
  const langMenuRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (!langMenuRef.current?.contains(e.target as Node)) setLangOpen(false);
    };
    if (langOpen) document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [langOpen]);

  // 양방향 슬라이드 모션
  const [direction, setDirection] = useState(1); // 1: 로그인→회원가입, -1: 회원가입→로그인

  // 모션: 폼이 광고패널(왼쪽 -32vw) 안으로 사라지고, 새 폼은 오른쪽(40vw)에서 진입
  const formVariants = {
    initial: {
      x: "40vw",
      opacity: 0,
      scale: 0.88
    },
    animate: {
      x: 0,
      opacity: 1,
      scale: 1,
      transition: { type: "spring" as const, duration: 0.45, bounce: 0.11 }
    },
    exit: {
      x: "-32vw",
      opacity: 0,
      scale: 0.72,
      transition: { duration: 0.35 }
    }
  };

  // 폼 상태
  const [loginData, setLoginData] = useState({ email: "", password: "", rememberMe: false });
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [signupData, setSignupData] = useState({
    name: "", email: "", company: "", position: "",
    password: "", confirmPassword: "", agreeTerms: false,
    location: { address: "", lat: 0, lng: 0 }
  });
  const [showSignupPassword, setShowSignupPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // 하드코딩된 로그인 정보
  const VALID_EMAIL = "bigdata5us@gknu.ac.kr";
  const VALID_PASSWORD = "andong5!";

  // 사용자 정보 매핑
  const USER_DATA: { [key: string]: { name: string; email: string; position: string } } = {
    "bigdata5us@gknu.ac.kr": {
      name: "강호근",
      email: "bigdata5us@gknu.ac.kr",
      position: "선임 관리자"
    }
  };

  // 로그인 처리
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    
    // 입력된 이메일과 비밀번호 검증
    if (loginData.email === VALID_EMAIL && loginData.password === VALID_PASSWORD) {
      setTimeout(() => {
        // 토큰과 사용자 정보 저장
        localStorage.setItem("auth-token", "demo-token");
        localStorage.setItem("user-info", JSON.stringify(USER_DATA[loginData.email]));
        router.push("/dashboard");
        setIsLoading(false);
      }, 700);
    } else {
      setTimeout(() => {
        setIsLoading(false);
        alert(language === "ko" ? "이메일 또는 비밀번호가 올바르지 않습니다." : "Invalid email or password.");
      }, 700);
    }
  };
  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (signupData.password !== signupData.confirmPassword) {
      alert(language === "ko" ? "비밀번호가 일치하지 않습니다." : "Passwords do not match.");
      return;
    }
    if (!signupData.agreeTerms) {
      alert(language === "ko" ? "이용약관에 동의해주세요." : "Please agree to the terms.");
      return;
    }
    if (!signupData.location.address) {
      alert(language === "ko" ? "회사 위치를 선택해주세요." : "Please select company location.");
      return;
    }
    setIsLoading(true);
    setTimeout(() => {
      localStorage.setItem("auth-token", "demo-token");
      router.push("/dashboard");
      setIsLoading(false);
    }, 900);
  };

  // 위치 선택 핸들러
  const handleLocationSelect = (address: string, lat: number, lng: number) => {
    setSignupData(prev => ({
      ...prev,
      location: { address, lat, lng }
    }));
  };

  // 홈 이동
  const goHome = () => router.push("/");

  // 폼 전환 방향
  const handleSwitchMode = (to: "login" | "signup") => {
    setDirection(to === "signup" ? 1 : -1);
    setMode(to);
  };

  return (
    <div className="min-h-screen w-full flex flex-row bg-white relative overflow-hidden">
      {/* 배경 패턴 */}
      <div className="absolute inset-0 pointer-events-none opacity-30">
        <div className="absolute inset-0" style={{
          backgroundImage: `
            radial-gradient(circle at 25% 25%, #f3f4f6 1px, transparent 1px),
            radial-gradient(circle at 75% 75%, #f3f4f6 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px'
        }} />
      </div>

      {/* 광고 패널 (1/4) */}
      <div
        className="flex flex-col items-center justify-between min-h-screen relative z-20"
        style={{
          width: "25vw", minWidth: 220, maxWidth: 420,
          background: `conic-gradient(from ${bgAngle}deg at 150% 200%, #1b2836, #20465a 40%, #09c8e8 65%, #23282f 100%)`
        }}
      >
        {/* 상단 로고 */}
        <div className="flex items-center justify-center w-full px-8 pt-8 select-none">
          <button className="flex items-center gap-2 group" onClick={goHome}>
            <CircuitBoard className="w-11 h-11 text-white drop-shadow" />
            <span className="text-3xl font-extrabold text-white group-hover:underline">PCB-Manager</span>
          </button>
        </div>

        {/* 광고 슬라이드 */}
        <div className="flex-1 flex flex-col justify-center items-center px-8 pt-2 relative">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentSlide}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5 }}
              className="text-center"
            >
              {slides[currentSlide].icon}
              <div className="text-2xl font-bold text-white mb-3">{slides[currentSlide].title}</div>
              <div className="text-lg text-white/80 text-center max-w-[250px] whitespace-pre-line">{slides[currentSlide].desc}</div>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* 슬라이드 인디케이터 - 하단 고정 */}
        <div className="flex justify-center items-center pb-8">
          <div className="flex space-x-2">
            {slides.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentSlide(index)}
                className={`w-2 h-2 rounded-full transition-all duration-300 ${
                  index === currentSlide ? 'bg-white w-6' : 'bg-white/50'
                }`}
              />
            ))}
          </div>
        </div>

        {/* PCB 패턴 배경 (움직임) */}
        <motion.div
          animate={{
            opacity: [0.14, 0.22, 0.14],
            y: [0, -16, 0]
          }}
          transition={{ repeat: Infinity, duration: 5, ease: "linear" }}
          className="absolute inset-0 pointer-events-none z-0"
        >
          <svg className="w-full h-full" viewBox="0 0 480 1080" fill="none">
            <defs>
              <pattern id="circuit" width="56" height="56" patternUnits="userSpaceOnUse">
                <rect width="56" height="56" fill="none" />
                <circle cx="12" cy="12" r="1.5" fill="#fff" />
                <circle cx="44" cy="44" r="1.5" fill="#fff" />
                <rect x="20" y="28" width="12" height="5" fill="#fff" rx="2" />
                <line x1="12" y1="12" x2="44" y2="44" stroke="#fff" strokeWidth="0.8" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#circuit)" opacity={0.17} />
          </svg>
        </motion.div>
      </div>

      {/* 오른쪽 (로그인/회원가입) */}
      <div className="flex-1 flex flex-col justify-center items-center min-h-screen bg-white relative z-30">
        <div className="w-full max-w-2xl px-8 py-10 flex flex-col justify-center">
          <AnimatePresence initial={false} mode="wait">
            <motion.div
              key={mode}
              variants={formVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              className="w-full"
            >
              {mode === "login" ? (
                <>
                  <h2 className="text-5xl font-bold mb-14 mt-10 text-center text-gray-900 tracking-tight">{t.loginTitle}</h2>
                  <form onSubmit={handleLogin} className="space-y-11">
                    <div className="flex flex-col gap-7">
                      <div>
                        <Label htmlFor="login-email" className="text-lg font-bold">{t.email}</Label>
                        <div className="relative mt-1">
                          <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-6 h-6" />
                          <Input
                            id="login-email"
                            type="email"
                            value={loginData.email}
                            onChange={e => setLoginData(prev => ({ ...prev, email: e.target.value }))}
                            className="pl-12 h-14 text-lg bg-gray-50 border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                            placeholder="example@company.com"
                            required
                            disabled={isLoading}
                          />
                        </div>
                      </div>
                      <div>
                        <Label htmlFor="login-password" className="text-lg font-bold">{t.password}</Label>
                        <div className="relative mt-1">
                          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-6 h-6" />
                          <Input
                            id="login-password"
                            type={showLoginPassword ? "text" : "password"}
                            value={loginData.password}
                            onChange={e => setLoginData(prev => ({ ...prev, password: e.target.value }))}
                            className="pl-12 pr-12 h-14 text-lg bg-gray-50 border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                            placeholder="••••••••"
                            required
                            disabled={isLoading}
                          />
                          <button
                            type="button"
                            onClick={() => setShowLoginPassword(v => !v)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                            disabled={isLoading}
                          >
                            {showLoginPassword ? <EyeOff className="w-6 h-6" /> : <Eye className="w-6 h-6" />}
                          </button>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 pt-2">
                      <Checkbox
                        id="remember"
                        checked={loginData.rememberMe}
                        onCheckedChange={checked => setLoginData(prev => ({ ...prev, rememberMe: Boolean(checked) }))}
                        className="data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600"
                        disabled={isLoading}
                      />
                      <Label htmlFor="remember" className="text-lg text-gray-600">{t.rememberMe}</Label>
                    </div>
                    <Button
                      type="submit"
                      disabled={isLoading}
                      className="w-full h-14 rounded-full bg-gradient-to-r from-blue-600 to-green-500 hover:from-blue-700 hover:to-green-600 text-white font-extrabold text-xl shadow-lg tracking-wide mt-3"
                    >
                      {isLoading ? (language === "ko" ? "로그인 중..." : "Logging in...") : t.loginButton}
                    </Button>
                  </form>
                  <div className="mt-12 flex flex-col items-center">
                    <div className="text-center text-gray-400 text-lg mb-3">{t.noAccountDesc}</div>
                    <Button
                      onClick={() => handleSwitchMode("signup")}
                      className="w-48 h-14 bg-green-600 hover:bg-green-700 text-white font-extrabold rounded-full text-xl flex items-center justify-center gap-2 group shadow-lg tracking-wide"
                    >
                      <span>{t.signupButton}</span>
                      <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
                    </Button>
                  </div>
                </>
              ) : (
                <>
                  <h2 className="text-5xl font-bold mb-14 mt-10 text-center text-gray-900 tracking-tight">{t.signupTitle}</h2>
                                                        <form onSubmit={handleSignup} className="space-y-8">
                     <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                       {/* 왼쪽 컬럼 */}
                       <div className="space-y-6">
                         {/* 이름 */}
                         <div>
                           <Label htmlFor="signup-name" className="text-lg font-bold">{t.name}</Label>
                           <div className="relative mt-1">
                             <User className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
                             <Input id="signup-name" value={signupData.name}
                               onChange={e => setSignupData(prev => ({ ...prev, name: e.target.value }))}
                               className="pl-12 h-12 text-lg bg-gray-50 border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                               placeholder={language === "ko" ? "홍길동" : "John Doe"} required disabled={isLoading} />
                           </div>
                         </div>
                         
                         {/* 회사명 */}
                         <div>
                           <Label htmlFor="signup-company" className="text-lg font-bold">{t.company}</Label>
                           <div className="relative mt-1">
                             <Building className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
                             <Input id="signup-company" value={signupData.company}
                               onChange={e => setSignupData(prev => ({ ...prev, company: e.target.value }))}
                               className="pl-12 h-12 text-lg bg-gray-50 border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                               placeholder={language === "ko" ? "회사명을 입력하세요" : "Your company"} required disabled={isLoading} />
                           </div>
                         </div>
                         
                         {/* 직책 */}
                         <div>
                           <Label className="text-lg font-bold">{t.position}</Label>
                           <Select onValueChange={value => setSignupData(prev => ({ ...prev, position: value }))}
                             disabled={isLoading}>
                             <SelectTrigger className="h-12 text-lg bg-gray-50 border-gray-200 focus:border-blue-500 focus:ring-blue-500">
                               <div className="flex items-center gap-2">
                                 <Briefcase className="w-5 h-5 text-gray-400" />
                                 <SelectValue placeholder={t.position} />
                               </div>
                             </SelectTrigger>
                             <SelectContent className="bg-white border-gray-200">
                               <SelectItem value="engineer">{t.positionOptions.engineer}</SelectItem>
                               <SelectItem value="manager">{t.positionOptions.manager}</SelectItem>
                               <SelectItem value="operator">{t.positionOptions.operator}</SelectItem>
                               <SelectItem value="supervisor">{t.positionOptions.supervisor}</SelectItem>
                               <SelectItem value="qc">{t.positionOptions.qc}</SelectItem>
                               <SelectItem value="other">{t.positionOptions.other}</SelectItem>
                             </SelectContent>
                           </Select>
                         </div>
                         
                         {/* 약관 동의 */}
                         <div className="flex items-start space-x-2 py-4">
                           <Checkbox
                             id="terms"
                             checked={signupData.agreeTerms}
                             onCheckedChange={checked => setSignupData(prev => ({ ...prev, agreeTerms: Boolean(checked) }))}
                             className="data-[state=checked]:bg-green-600 data-[state=checked]:border-green-600 mt-1"
                             disabled={isLoading}
                           />
                           <Label htmlFor="terms" className="text-base text-gray-600 leading-relaxed">
                             {language === "ko" ? (
                               <>
                                 <button
                                   type="button"
                                   onClick={() => setShowTermsModal(true)}
                                   className="text-blue-600 hover:text-blue-800 underline"
                                 >
                                   이용약관
                                 </button>
                                 <span> 및 </span>
                                 <button
                                   type="button"
                                   onClick={() => setShowPrivacyModal(true)}
                                   className="text-blue-600 hover:text-blue-800 underline"
                                 >
                                   개인정보처리방침
                                 </button>
                                 <span>에 동의합니다.</span>
                               </>
                             ) : (
                               <>
                                 <span>I agree to the </span>
                                 <button
                                   type="button"
                                   onClick={() => setShowTermsModal(true)}
                                   className="text-blue-600 hover:text-blue-800 underline"
                                 >
                                   Terms of Service
                                 </button>
                                 <span> and </span>
                                 <button
                                   type="button"
                                   onClick={() => setShowPrivacyModal(true)}
                                   className="text-blue-600 hover:text-blue-800 underline"
                                 >
                                   Privacy Policy
                                 </button>
                                 <span>.</span>
                               </>
                             )}
                           </Label>
                         </div>
                       </div>
                       
                       {/* 오른쪽 컬럼 */}
                       <div className="space-y-6">
                         {/* 이메일 */}
                         <div>
                           <Label htmlFor="signup-email" className="text-lg font-bold">{t.email}</Label>
                           <div className="relative mt-1">
                             <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
                             <Input id="signup-email" type="email" value={signupData.email}
                               onChange={e => setSignupData(prev => ({ ...prev, email: e.target.value }))}
                               className="pl-12 h-12 text-lg bg-gray-50 border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                               placeholder="example@company.com" required disabled={isLoading} />
                           </div>
                         </div>
                         
                                                   {/* 회사 위치 */}
                          <div>
                            <Label htmlFor="signup-location" className="text-lg font-bold">회사 위치</Label>
                            <div className="relative mt-1 flex gap-2">
                              <Button
                                type="button"
                                onClick={() => setShowLocationModal(true)}
                                className="px-4 h-12 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg text-sm whitespace-nowrap"
                                disabled={isLoading}
                              >
                                위치 검색
                              </Button>
                              <div className="flex-1 flex items-center px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg">
                                {signupData.location.address ? (
                                  <div className="flex items-center gap-2 text-gray-700">
                                    <MapPin className="w-4 h-4 text-green-600" />
                                    <span className="text-sm font-medium">{signupData.location.address}</span>
                                  </div>
                                ) : (
                                  <div className="flex items-center gap-2 text-gray-400">
                                    <MapPin className="w-4 h-4" />
                                    <span className="text-sm">위치 검색 버튼을 클릭하여 주소를 선택하세요</span>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                         
                         {/* 비밀번호 */}
                         <div>
                           <Label htmlFor="signup-password" className="text-lg font-bold">{t.password}</Label>
                           <div className="relative mt-1">
                             <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
                             <Input id="signup-password"
                               type={showSignupPassword ? "text" : "password"}
                               value={signupData.password}
                               onChange={e => setSignupData(prev => ({ ...prev, password: e.target.value }))}
                               className="pl-12 pr-12 h-12 text-lg bg-gray-50 border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                               placeholder="••••••••" required disabled={isLoading} />
                             <button
                               type="button"
                               onClick={() => setShowSignupPassword(v => !v)}
                               className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                               disabled={isLoading}
                             >
                               {showSignupPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                             </button>
                           </div>
                         </div>
                         
                         {/* 비밀번호 확인 */}
                         <div>
                           <Label htmlFor="confirm-password" className="text-lg font-bold">{t.confirmPassword}</Label>
                           <div className="relative mt-1">
                             <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-5 h-5" />
                             <Input id="confirm-password"
                               type={showConfirmPassword ? "text" : "password"}
                               value={signupData.confirmPassword}
                               onChange={e => setSignupData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                               className="pl-12 pr-12 h-12 text-lg bg-gray-50 border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                               placeholder="••••••••" required disabled={isLoading} />
                             <button
                               type="button"
                               onClick={() => setShowConfirmPassword(v => !v)}
                               className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                               disabled={isLoading}
                             >
                               {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                             </button>
                           </div>
                         </div>
                       </div>
                     </div>
                                         
                    <Button type="submit" disabled={isLoading}
                      className="w-full h-14 rounded-full bg-gradient-to-r from-blue-600 to-green-500 hover:from-blue-700 hover:to-green-600 text-white font-extrabold text-xl shadow-lg tracking-wide mt-3">
                      {isLoading ? (language === "ko" ? "가입 중..." : "Signing up...") : t.signupButton}
                    </Button>
                  </form>
                  <div className="mt-12 flex flex-col items-center">
                    <div className="text-center text-gray-500 text-lg mb-3">{t.hasAccountDesc}</div>
                    <Button
                      onClick={() => handleSwitchMode("login")}
                      className="w-48 h-14 bg-green-600 hover:bg-green-700 text-white font-extrabold rounded-full text-xl flex items-center justify-center gap-2 group shadow-lg tracking-wide"
                    >
                      <span>{t.loginSwitch}</span>
                      <ArrowRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
                    </Button>
                  </div>
                </>
              )}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* 하단 고정 푸터 */}
        <footer className="w-full flex items-center justify-center py-6 gap-3 border-t mt-auto">
          <CircuitBoard className="w-7 h-7 text-gray-500 drop-shadow" />
          <span className="text-gray-500 text-lg font-semibold tracking-wide">PCB-Manager © 2025</span>
          
          {/* 언어 변경 버튼 */}
          <div className="relative ml-4" ref={langMenuRef}>
            <button
              onClick={() => setLangOpen(v => !v)}
              className="flex items-center text-gray-500 bg-transparent font-bold text-lg rounded px-2 py-1 border border-gray-300 focus:outline-none hover:bg-gray-50"
            >
              {language === "ko" ? "한국어" : "English"}
              <ChevronDown className="ml-1 w-5 h-5" />
            </button>
            {langOpen && (
              <div className="absolute bottom-full right-0 mb-2 w-32 bg-white border border-gray-200 rounded-md shadow z-50 py-1 text-lg animate-fadeIn">
                <button
                  className={`block w-full px-4 py-2 text-left hover:bg-blue-50 ${language === "en" ? "font-semibold text-blue-600" : "text-gray-800"}`}
                  onClick={() => { setLanguage("en"); setLangOpen(false); }}
                >English</button>
                <button
                  className={`block w-full px-4 py-2 text-left hover:bg-blue-50 ${language === "ko" ? "font-semibold text-blue-600" : "text-gray-800"}`}
                  onClick={() => { setLanguage("ko"); setLangOpen(false); }}
                >한국어</button>
              </div>
            )}
          </div>
        </footer>
      </div>

                           {/* 챗봇 컴포넌트 */}
        <Chatbot />

        {/* 위치 검색 모달 */}
        <LocationSearchModal
          isOpen={showLocationModal}
          onClose={() => setShowLocationModal(false)}
          onLocationSelect={handleLocationSelect}
        />

               {/* 이용약관 모달 */}
        {showTermsModal && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl h-[80vh] relative flex flex-col">
              <div className="flex items-center justify-between p-6 border-b flex-shrink-0">
                <h2 className="text-2xl font-bold text-gray-900">
                  {language === "ko" ? "이용약관" : "Terms of Service"}
                </h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowTermsModal(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <X className="w-6 h-6" />
                </Button>
              </div>
              <div className="flex-1 overflow-y-auto p-6">
                <div className="prose max-w-none">
                 <p className="text-lg font-semibold text-gray-800 mb-4">
                   {language === "ko" ? "예시용입니다." : "This is for demonstration purposes."}
                 </p>
                 
                 {language === "ko" ? (
                   <>
                     <h3 className="text-xl font-bold text-gray-900 mb-3">제1조 (목적)</h3>
                     <p className="text-gray-700 mb-4">
                       본 약관은 PCB-Manager 서비스(이하 "서비스")의 이용과 관련하여 서비스 제공자와 이용자 간의 권리, 의무 및 책임사항을 규정함을 목적으로 합니다.
                     </p>
                     
                     <h3 className="text-xl font-bold text-gray-900 mb-3">제2조 (정의)</h3>
                     <p className="text-gray-700 mb-4">
                       1. "서비스"란 PCB-Manager가 제공하는 PCB 관리 및 모니터링 서비스를 의미합니다.<br/>
                       2. "이용자"란 본 약관에 따라 서비스를 이용하는 회원을 의미합니다.<br/>
                       3. "회원"이란 서비스에 접속하여 본 약관에 동의하고 회원가입을 한 자를 의미합니다.
                     </p>
                     
                     <h3 className="text-xl font-bold text-gray-900 mb-3">제3조 (서비스의 제공)</h3>
                     <p className="text-gray-700 mb-4">
                       서비스는 다음과 같은 기능을 제공합니다:<br/>
                       • PCB 실시간 모니터링<br/>
                       • AI 기반 결함 감지<br/>
                       • 인벤토리 관리<br/>
                       • 품질 관리 시스템
                     </p>
                     
                     <h3 className="text-xl font-bold text-gray-900 mb-3">제4조 (서비스 이용)</h3>
                     <p className="text-gray-700 mb-4">
                       1. 서비스 이용은 서비스의 정상적인 운영에 지장을 주지 않는 범위 내에서 가능합니다.<br/>
                       2. 이용자는 서비스를 이용할 때 관련 법령 및 본 약관을 준수해야 합니다.<br/>
                       3. 이용자는 서비스 이용 중 발생한 모든 책임을 부담합니다.
                     </p>
                     
                     <h3 className="text-xl font-bold text-gray-900 mb-3">제5조 (서비스 중단)</h3>
                     <p className="text-gray-700 mb-4">
                       서비스 제공자는 다음의 경우 서비스 제공을 중단할 수 있습니다:<br/>
                       • 서비스 점검 및 보수<br/>
                       • 천재지변 등 불가항력적 사유<br/>
                       • 기타 서비스 제공자가 필요하다고 인정하는 경우
                     </p>
                   </>
                 ) : (
                   <>
                     <h3 className="text-xl font-bold text-gray-900 mb-3">Article 1 (Purpose)</h3>
                     <p className="text-gray-700 mb-4">
                       These terms and conditions govern the rights, obligations, and responsibilities between the service provider and users regarding the use of PCB-Manager service (hereinafter "Service").
                     </p>
                     
                     <h3 className="text-xl font-bold text-gray-900 mb-3">Article 2 (Definitions)</h3>
                     <p className="text-gray-700 mb-4">
                       1. "Service" means the PCB management and monitoring service provided by PCB-Manager.<br/>
                       2. "User" means a member who uses the service in accordance with these terms.<br/>
                       3. "Member" means a person who accesses the service, agrees to these terms, and completes registration.
                     </p>
                     
                     <h3 className="text-xl font-bold text-gray-900 mb-3">Article 3 (Service Provision)</h3>
                     <p className="text-gray-700 mb-4">
                       The service provides the following features:<br/>
                       • Real-time PCB monitoring<br/>
                       • AI-based defect detection<br/>
                       • Inventory management<br/>
                       • Quality control system
                     </p>
                     
                     <h3 className="text-xl font-bold text-gray-900 mb-3">Article 4 (Service Usage)</h3>
                     <p className="text-gray-700 mb-4">
                       1. Service usage is possible within the scope that does not interfere with normal service operation.<br/>
                       2. Users must comply with relevant laws and these terms when using the service.<br/>
                       3. Users are responsible for all consequences arising from service usage.
                     </p>
                     
                     <h3 className="text-xl font-bold text-gray-900 mb-3">Article 5 (Service Suspension)</h3>
                     <p className="text-gray-700 mb-4">
                       The service provider may suspend service provision in the following cases:<br/>
                       • Service maintenance and repair<br/>
                       • Force majeure such as natural disasters<br/>
                       • Other cases deemed necessary by the service provider
                     </p>
                   </>
                 )}
               </div>
             </div>
           </div>
         </div>
       )}

               {/* 개인정보처리방침 모달 */}
        {showPrivacyModal && (
          <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl h-[80vh] relative flex flex-col">
              <div className="flex items-center justify-between p-6 border-b flex-shrink-0">
                <h2 className="text-2xl font-bold text-gray-900">
                  {language === "ko" ? "개인정보처리방침" : "Privacy Policy"}
                </h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowPrivacyModal(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <X className="w-6 h-6" />
                </Button>
              </div>
              <div className="flex-1 overflow-y-auto p-6">
                <div className="prose max-w-none">
                 <p className="text-lg font-semibold text-gray-800 mb-4">
                   {language === "ko" ? "예시용입니다." : "This is for demonstration purposes."}
                 </p>
                 
                 {language === "ko" ? (
                   <>
                     <h3 className="text-xl font-bold text-gray-900 mb-3">1. 개인정보의 수집 및 이용목적</h3>
                     <p className="text-gray-700 mb-4">
                       PCB-Manager는 서비스 제공을 위해 다음과 같은 개인정보를 수집하고 이용합니다:<br/>
                       • 필수항목: 이름, 이메일, 회사명, 직책<br/>
                       • 선택항목: 프로필 정보, 사용 설정
                     </p>
                     
                     <h3 className="text-xl font-bold text-gray-900 mb-3">2. 개인정보의 보유 및 이용기간</h3>
                     <p className="text-gray-700 mb-4">
                       회원 탈퇴 시까지 또는 법정 보유기간이 경과할 때까지 개인정보를 보유합니다. 단, 관련 법령에 따라 보존이 필요한 경우 해당 기간 동안 보관됩니다.
                     </p>
                     
                     <h3 className="text-xl font-bold text-gray-900 mb-3">3. 개인정보의 제3자 제공</h3>
                     <p className="text-gray-700 mb-4">
                       PCB-Manager는 원칙적으로 이용자의 개인정보를 제3자에게 제공하지 않습니다. 다만, 다음의 경우에는 예외로 합니다:<br/>
                       • 이용자가 사전에 동의한 경우<br/>
                       • 법령의 규정에 의거하거나, 수사 목적으로 법령에 정해진 절차와 방법에 따라 수사기관의 요구가 있는 경우
                     </p>
                     
                     <h3 className="text-xl font-bold text-gray-900 mb-3">4. 개인정보의 처리위탁</h3>
                     <p className="text-gray-700 mb-4">
                       서비스 향상을 위해 개인정보 처리업무를 외부 전문업체에 위탁할 수 있으며, 위탁 시 관련 법령에 따라 위탁계약 등을 체결하여 개인정보 보호를 보장합니다.
                     </p>
                     
                     <h3 className="text-xl font-bold text-gray-900 mb-3">5. 이용자의 권리</h3>
                     <p className="text-gray-700 mb-4">
                       이용자는 언제든지 등록되어 있는 자신의 개인정보를 조회하거나 수정할 수 있으며, 회원탈퇴를 요청할 수 있습니다. 개인정보 관련 문의사항은 고객센터를 통해 접수해 주시기 바랍니다.
                     </p>
                   </>
                 ) : (
                   <>
                     <h3 className="text-xl font-bold text-gray-900 mb-3">1. Collection and Use of Personal Information</h3>
                     <p className="text-gray-700 mb-4">
                       PCB-Manager collects and uses the following personal information for service provision:<br/>
                       • Required: Name, email, company name, position<br/>
                       • Optional: Profile information, usage settings
                     </p>
                     
                     <h3 className="text-xl font-bold text-gray-900 mb-3">2. Retention and Use Period of Personal Information</h3>
                     <p className="text-gray-700 mb-4">
                       Personal information is retained until member withdrawal or until the statutory retention period expires. However, if preservation is required by relevant laws, it will be stored for the required period.
                     </p>
                     
                     <h3 className="text-xl font-bold text-gray-900 mb-3">3. Third-Party Provision of Personal Information</h3>
                     <p className="text-gray-700 mb-4">
                       PCB-Manager does not provide users' personal information to third parties in principle. However, exceptions apply in the following cases:<br/>
                       • When the user has given prior consent<br/>
                       • When required by law or when requested by investigative agencies in accordance with procedures and methods prescribed by law for investigation purposes
                     </p>
                     
                     <h3 className="text-xl font-bold text-gray-900 mb-3">4. Outsourcing of Personal Information Processing</h3>
                     <p className="text-gray-700 mb-4">
                       To improve services, personal information processing tasks may be outsourced to external specialized companies. When outsourcing, we ensure personal information protection by concluding outsourcing contracts in accordance with relevant laws.
                     </p>
                     
                     <h3 className="text-xl font-bold text-gray-900 mb-3">5. User Rights</h3>
                     <p className="text-gray-700 mb-4">
                       Users can view or modify their registered personal information at any time and request membership withdrawal. For personal information-related inquiries, please contact our customer service center.
                     </p>
                   </>
                 )}
               </div>
             </div>
           </div>
         </div>
       )}
     </div>
   );
 }
