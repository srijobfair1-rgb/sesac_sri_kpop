import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import time
from datetime import datetime, timedelta

def get_saramin_jobs_mobile(keyword):
    # 💡 해외 IP 차단을 피하기 위해 모바일 웹 URL 사용
    url = f"https://m.saramin.co.kr/job-search?searchword={keyword}&sort=pd"
    
    # 실제 스마트폰에서 접속하는 것처럼 위장하는 헤더
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        'Accept-Language': 'ko-KR,ko;q=0.9',
    }
    
    jobs = []
    
    try:
        # timeout을 15초로 늘려 안정성 확보
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 모바일 사람인 공고 리스트 추출
        recruit_items = soup.select('.list_recruiting .item_recruit')
        
        for item in recruit_items:
            try:
                corp_name = item.select_one('.corp_name').text.strip()
                title_elem = item.select_one('.job_tit')
                title = title_elem.text.strip()
                
                # 링크 가져오기
                link_elem = item.select_one('a')
                if link_elem and 'href' in link_elem.attrs:
                    link = "https://m.saramin.co.kr" + link_elem['href']
                else:
                    link = "https://m.saramin.co.kr"
                
                # 어제/오늘 등록 공고 필터링 (모바일 뱃지 기준)
                date_badge = item.select_one('.badge_date')
                date_text = date_badge.text.strip() if date_badge else ""
                
                # 등록일 조건 체크
                if any(k in date_text for k in ['어제', '오늘', '시간전', '분전']):
                    jobs.append({
                        'corp': corp_name,
                        'title': title,
                        'link': link
                    })
            except Exception:
                continue
                
    except Exception as e:
        print(f"'{keyword}' 크롤링 중 오류 발생: {e}")
        
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
        body = f"{date_str} 기준, 새로 등록된 신규 공고가 없습니다."
    else:
        body = f"총 {total_count}건의 신규 공고가 등록되었습니다.\n\n"
        for keyword, jobs in jobs_by_keyword.items():
            body += f"📌 [{keyword}] 검색 결과 ({len(jobs)}건)\n"
            body += "-" * 40 + "\n"
            if len(jobs) == 0:
                body += "신규 공고가 없습니다.\n\n"
            else:
                for i, job in enumerate(jobs, 1):
                    body += f"{i}. {job['corp']} | {job['title']}\n   👉 링크: {job['link']}\n"
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
        print(f"'{keyword}' 수집 시작...")
        jobs = get_saramin_jobs_mobile(keyword)
        jobs_by_keyword[keyword] = jobs
        print(f"'{keyword}' 수집 완료: {len(jobs)}건")
        
        # 연속 접속으로 인한 차단을 막기 위해 3초 대기
        time.sleep(3)
        
    print("메일 발송을 시작합니다...")
    send_email(jobs_by_keyword)
