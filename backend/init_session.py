import time
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

def init_session():
    # Load config dynamically if needed, or hardcode safe values for this script
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    session_dir = Path(__file__).resolve().parent / "playwright-session"
    
    print("="*50)
    print("🚀 ChatGPT 브라우저 세션 초기화 스크립트")
    print("="*50)
    print("브라우저를 열어 ChatGPT에 접속합니다...")
    print("Cloudflare 로딩이 끝날 때까지 기다린 후 로그인을 진행하세요.")
    print("로그인 완료 시 터미널에서 Enter를 누르시면 저장됩니다.")
    print("="*50)

    try:
        with sync_playwright() as p:
            # anti-bot measures: set user agent, viewport, and ignore webdriver flag
            ctx = p.chromium.launch_persistent_context(
                str(session_dir),
                headless=False,
                user_agent=user_agent,
                viewport={"width": 1280, "height": 800},
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized"
                ],
                ignore_default_args=["--enable-automation"]
            )
            
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            
            # Add stealth scripts to bypass CF
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            # Navigate to ChatGPT
            page.goto("https://chatgpt.com/")
            
            # Wait for user input
            input("\n🎯 로그인이 완료되었나요? 완료되었으면 터미널 창에서 [Enter] 키를 누르세요...")
            
            print("세션을 저장하고 브라우저를 닫습니다...")
            try:
                ctx.close()
            except Exception:
                pass # 이미 사용자가 창을 닫은 경우 무시
            
            print("✅ 세션 저장 완료! 이제 npm run dev를 통해 서버를 실행하세요.")
            
    except Exception as e:
        print(f"\n❌ 세션 초기화 중 에러 발생: {e}")

if __name__ == "__main__":
    init_session()
