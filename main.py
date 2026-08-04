import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime, timedelta

def get_saramin_jobs(keyword):
    # 등록일순으로 정렬된 사람인 검색 URL
    url = f"https://www.saramin.co.kr/zf_user/search/recruit?searchword={keyword}&recruit_sort=reg_dt"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    jobs = []
    recruit_items = soup.select('.item_recruit')
    
    for item in recruit_items:
        try:
            corp_name = item.select_one('.corp_name a').text.strip()
            title = item.select_one('.job_tit a')['title'].strip()
            link = "https://www.saramin.co.kr" + item.select_one('.job_tit a')['href']
            date_badge = item.select_one('.job_date .date').text.strip()
            
            # 조건: '어제' 혹은 '오늘' 등록된 신규 공고만 수집
            if '어제등록' in date_badge or '시간전' in date_badge or '오늘등록' in date_badge:
                jobs.append({
                    'corp': corp_name,
                    'title': title,
                    'link': link
                })
        except Exception as e:
            continue
            
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
    
    # 여러 키워드를 메일 제목에 반영 (예: '공연, 엔터테인먼트')
    keyword_str = ", ".join(jobs_by_keyword.keys())
    
    msg = MIMEMultipart()
    msg['Subject'] = f"[RPA] {date_str} 사람인 '{keyword_str}' 신규 채용공고"
    msg['From'] = sender_email
    msg['To'] = receiver_email
    
    # 전체 수집된 공고 개수 계산
    total_count = sum(len(jobs) for jobs in jobs_by_keyword.values())
    
    # 메일 본문 작성
    if total_count == 0:
        body = f"{date_str} 기준, 새로 등록된 채용공고가 없습니다."
    else:
        body = f"총 {total_count}건의 신규 공고가 등록되었습니다.\n\n"
        
        # 키워드별로 나눠서 보여주기
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
    
    # 메일 발송
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.send_message(msg)
        print("메일 발송 성공!")
    except Exception as e:
        print(f"메일 발송 실패: {e}")

if __name__ == "__main__":
    # 💡 이 부분에 검색하고 싶은 키워드를 얼마든지 추가할 수 있습니다!
    keywords = ["공연", "엔터테인먼트"]
    
    jobs_by_keyword = {} # 키워드별 결과를 저장할 바구니
    
    for keyword in keywords:
        print(f"'{keyword}' 크롤링 시작...")
        jobs = get_saramin_jobs(keyword)
        jobs_by_keyword[keyword] = jobs
        print(f"'{keyword}' 관련 {len(jobs)}개의 공고를 찾았습니다.")
        
    print("모든 검색 완료. 메일을 발송합니다...")
    send_email(jobs_by_keyword)
