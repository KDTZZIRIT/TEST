"use client"

import LoginForm from "./login-form"
import SignUpForm from "./signup-form"
import { cn } from "@/lib/utils"

interface AuthSliderPanelProps {
  mode: "login" | "signup"
  setMode: (mode: "login" | "signup") => void
  onLoginSuccess: () => void
}

export default function AuthSliderPanel({ mode, setMode, onLoginSuccess }: AuthSliderPanelProps) {
  return (
    <div className="relative w-[900px] max-w-full h-[600px] flex bg-[#101629] shadow-2xl rounded-2xl overflow-hidden">
      {/* 로그인 */}
      <div className="flex-1 flex flex-col justify-center items-center p-8 z-10">
        <LoginForm isActive={mode === "login"} onLoginSuccess={onLoginSuccess} />
      </div>
      {/* 회원가입 */}
      <div className="flex-1 flex flex-col justify-center items-center p-8 z-10">
        <SignUpForm isActive={mode === "signup"} onSignupSuccess={() => setMode("login")} />
      </div>

      {/* === 슬라이딩 가림막 === */}
      <div
        className={cn(
          "absolute top-0 w-1/2 h-full z-20 flex items-center justify-center transition-transform duration-700 ease-in-out",
          mode === "login" ? "translate-x-full" : "translate-x-0",
        )}
        style={{
          background: "rgba(16, 22, 41, 0.96)",
          boxShadow: "8px 0 40px 10px rgba(6,182,212,0.15)",
          backdropFilter: "blur(3px)",
        }}
      >
        <div className="w-full text-center px-10 select-none">
          {mode === "login" ? (
            <>
              <h3 className="text-2xl font-bold mb-3 text-cyan-300 drop-shadow">아직 회원이 아니신가요?</h3>
              <p className="text-gray-400 mb-6">
                계정이 없으시다면
                <br />
                회원가입을 진행해보세요.
              </p>
              <button
                className="mt-2 px-6 py-2 rounded-full font-semibold text-base bg-cyan-500 hover:bg-cyan-600 text-white shadow transition"
                onClick={() => setMode("signup")}
              >
                회원가입으로 전환
              </button>
            </>
          ) : (
            <>
              <h3 className="text-2xl font-bold mb-3 text-cyan-300 drop-shadow">이미 계정이 있으신가요?</h3>
              <p className="text-gray-400 mb-6">
                계정을 보유 중이시라면
                <br />
                로그인 해주세요.
              </p>
              <button
                className="mt-2 px-6 py-2 rounded-full font-semibold text-base bg-cyan-500 hover:bg-cyan-600 text-white shadow transition"
                onClick={() => setMode("login")}
              >
                로그인으로 전환
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
