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
    # 봇 차단을 막기 위한 User-Agent 헤더
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
            
            # 조건: '어제' 등록된 공고 위주로 수집
            # (만약 모든 최신 공고를 다 받고 싶다면 아래 if문을 지우시면 됩니다)
            if '어제등록' in date_badge or '시간전' in date_badge or '오늘등록' in date_badge:
                jobs.append({
                    'corp': corp_name,
                    'title': title,
                    'link': link
                })
        except Exception as e:
            continue
            
    return jobs

def send_email(jobs):
    sender_email = "sri.jobfair1@gmail.com"
    receiver_email = "sesac@saramin.co.kr"
    # GitHub Secrets에서 가져올 앱 비밀번호
    password = os.environ.get('GMAIL_APP_PW') 
    
    if not password:
        print("이메일 앱 비밀번호가 설정되지 않았습니다.")
        return

    # 어제 날짜 계산
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime('%Y년 %m월 %d일')
    
    msg = MIMEMultipart()
    msg['Subject'] = f"[RPA] {date_str} 사람인 '공연' 신규 채용공고 리스트"
    msg['From'] = sender_email
    msg['To'] = receiver_email
    
    # 메일 본문 작성
    if len(jobs) == 0:
        body = f"{date_str} 기준, 새로 등록된 '공연' 관련 채용공고가 없습니다."
    else:
        body = f"총 {len(jobs)}건의 신규 공고가 등록되었습니다.\n\n"
        for i, job in enumerate(jobs, 1):
            body += f"{i}. {job['corp']} | {job['title']}\n   👉 링크: {job['link']}\n\n"
            
    msg.attach(MIMEText(body, 'plain'))
    
    # 지메일 SMTP 서버를 이용해 메일 발송
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.send_message(msg)
        print("메일 발송 성공!")
    except Exception as e:
        print(f"메일 발송 실패: {e}")

if __name__ == "__main__":
    print("사람인 크롤링 시작...")
    job_list = get_saramin_jobs("공연")
    print(f"{len(job_list)}개의 공고를 찾았습니다. 메일을 발송합니다...")
    send_email(job_list)
