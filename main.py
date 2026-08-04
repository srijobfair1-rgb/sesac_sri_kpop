from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import time
from datetime import datetime, timedelta

def get_saramin_jobs_playwright(keyword):
    # 등록일 최신순 정렬 URL
    url = f"https://www.saramin.co.kr/zf_user/search/recruit?searchword={keyword}&recruit_sort=reg_dt"
    jobs = []
    
    with sync_playwright() as p:
        # 헤드리스 크롬 브라우저 실행
        browser = p.chromium.launch(headless=True)
        # 실제 일반 윈도우 크롬 브라우저인 것처럼 유저위장
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="ko-KR"
        )
        page = context.new_page()
        
        try:
            print(f"[{keyword}] 크롬 브라우저로 사람인 접속 중...")
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # 공고 엘리먼트가 화면에 나타날 때까지 대기
            page.wait_for_selector(".item_recruit", timeout=10000)
            
            # 자바스크립트 동적 로딩을 위해 스크롤을 살짝 내림
            page.evaluate("window.scrollTo(0, 600)")
            time.sleep(1.5)
            
            # 완벽히 로딩된 HTML 추출
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            recruit_items = soup.select('.item_recruit')
            print(f"👉 [{keyword}] 검색 결과 {len(recruit_items)}개 공고 카드 획득 성공!")
            
            for item in recruit_items:
                try:
                    # 1. 기업명
                    corp_elem = item.select_one('.corp_name a')
                    corp_name = corp_elem.text.strip() if corp_elem else "기업명 미상"
                    
                    # 2. 공고 제목
                    title_elem = item.select_one('.job_tit a')
                    if not title_elem:
                        continue
                    title = title_elem.get('title', title_elem.text).strip()
                    
                    # 3. 링크
                    href = title_elem.get('href', '')
                    link = "https://www.saramin.co.kr" + href if href.startswith('/') else href
                    
                    # 4. 등록일/뱃지 정보
                    date_badge = item.select_one('.job_date .date')
                    date_text = date_badge.text.strip() if date_badge else "최신"
                    
                    jobs.append({
                        'corp': corp_name,
                        'title': title,
                        'link': link,
                        'date': date_text
                    })
                    
                    # 최신순 정렬이므로 상위 15개까지만 담기
                    if len(jobs) >= 15:
                        break
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"[{keyword}] 크롤링 중 오류: {e}")
        finally:
            browser.close()
            
    return jobs

def send_email(jobs_by_keyword):
    sender_email = "sri.jobfair1@gmail.com"
    receiver_email = "sesac@saramin.co.kr"
    password = os.environ.get('GMAIL_APP_PW') 
    
    if not password:
        print("이메일 앱 비밀번호가 설정되지 않았습니다.")
        return

    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime('%Y년 %m월 %d일')
    keyword_str = ", ".join(jobs_by_keyword.keys())
    
    msg = MIMEMultipart()
    msg['Subject'] = f"[RPA] {date_str} 사람인 '{keyword_str}' 신규 채용공고"
    msg['From'] = sender_email
    msg['To'] = receiver_email
    
    total_count = sum(len(jobs) for jobs in jobs_by_keyword.values())
    
    if total_count == 0:
        body = f"{date_str} 기준, 수집된 신규 공고가 없습니다."
    else:
        body = f"총 {total_count}건의 최신 공고가 수집되었습니다.\n\n"
        for keyword, jobs in jobs_by_keyword.items():
            body += f"📌 [{keyword}] 검색 결과 ({len(jobs)}건)\n"
            body += "-" * 40 + "\n"
            if len(jobs) == 0:
                body += "검색된 공고가 없습니다.\n\n"
            else:
                for i, job in enumerate(jobs, 1):
                    body += f"{i}. {job['corp']} | {job['title']} ({job['date']})\n   👉 링크: {job['link']}\n"
            body += "\n"
            
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.send_message(msg)
        print("메일 발송 성공!")
    except Exception as e:
        print(f"메일 발송 실패: {e}")

if __name__ == "__main__":
    keywords = ["공연", "엔터테인먼트"]
    jobs_by_keyword = {}
    
    for keyword in keywords:
        jobs = get_saramin_jobs_playwright(keyword)
        jobs_by_keyword[keyword] = jobs
        print(f"'{keyword}' 최종 수집 건수: {len(jobs)}건")
        
    print("메일을 발송합니다...")
    send_email(jobs_by_keyword)
