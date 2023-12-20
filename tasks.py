from robocorp.tasks import task
from robocorp import browser

from RPA.HTTP import HTTP
#from RPA.FileSystem import FileSystem
from RPA.Robocorp.Vault import Vault
from RPA.Email.ImapSmtp import ImapSmtp
from RPA.Robocorp.Storage import Storage
#import tweepy
import datetime

_secret = Vault().get_secret("credentials")

#IMAP Confs
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT=587

#Mail Secrets
GMAIL_ACCOUNT = _secret["gmail_account"]
GMAIL_APP_PASSWORD = _secret["gmail_app_password"]
RECIPIENT = _secret["recipient"]

#Placeholder to migrate from API to browser selectors, traditional access
#Needs updates to ones personal vault as well
#USER_NAME = _secret["username"]
#PASSWORD = _secret["password"]

#20.12.2023 rpaframework 27.7.0 depends on tweepy<4.0.0 and >=3.8.0
#Placeholder in case one gets to use this at some point.
#TWITTER_CONSUMER_KEY = _secret["OAUTH_KEY"]
#TWITTER_CONSUMER_SECRET = _secret["OAUTH_SECRET"]
#TWITTER_ACCESS_TOKEN = _secret["ACCESS_KEY"]
#TWITTER_ACCESS_TOKEN_SECRET = _secret["ACCESS_SECRET"]

#Placeholder for Tweepy
#Twitter Free tier sub requires V2 methods
#client = tweepy.Client(
#    consumer_key=TWITTER_CONSUMER_KEY,
#    consumer_secret=TWITTER_CONSUMER_SECRET,
#    access_token=TWITTER_ACCESS_TOKEN,
#    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
#)

@task
def fetch_and_mail_menu():
    browser.configure(
        browser_engine="chromium",
        screenshot="only-on-failure",
        headless=False
    )

    http = HTTP()
    http.download("https://ruokalistat.seinajoki.fi/AromieMenus/FI/Default/tervetuloa/KerttuPk/Rss.aspx?Id=9973548d-c031-472f-a5fd-14e0ed0f0809&DateMode=0", overwrite=True)
    
    #in case one would need whole week or next week menus
    #https://ruokalistat.seinajoki.fi/AromieMenus/FI/Default/tervetuloa/KerttuPk/Rss.aspx?Id=9973548d-c031-472f-a5fd-14e0ed0f0809&DateMode=2 next week
    #https://ruokalistat.seinajoki.fi/AromieMenus/FI/Default/tervetuloa/KerttuPk/Rss.aspx?Id=9973548d-c031-472f-a5fd-14e0ed0f0809&DateMode=1 current week
    #https://ruokalistat.seinajoki.fi/AromieMenus/FI/Default/tervetuloa/KerttuPk/Rss.aspx?Id=9973548d-c031-472f-a5fd-14e0ed0f0809&DateMode=0 current day

    parsed_content = parse_content()
    
    #In case daily menus are needed on locally
    #save_menu_locally(parsed_content)

    #Saving the daily content to Control Room
    manage_assets(parsed_content)
    
    #Option to use browser selectors instead of Twitter API
    #push_to_x(parsed_content)
    
    #Option to tweet via Twitter API
    #push_to_x_tweepy(parsed_content)

    send_mail(parsed_content)

#This is spaghetti but does the job..
def parse_content():
    with open("Rss.aspx", "r") as file:
        for line in file:
            content = line.split('<item>')

    content.pop(0)
    content[0] = content[0].replace("<![CDATA[", "")
    content[0] = content[0].replace("]]", "#")
    content[0] = content[0].replace("<br><br>", "\n")
    content[0] = content[0].replace("Ã¶", "ö")
    content[0] = content[0].replace("Ã¤", "ä")
    content[0] = content[0].replace("<title>", "")
    content[0] = content[0].replace("</title>", "\n")
    content[0] = content[0].replace("<description>", "")
    content[0] = content[0].replace(":", ": ")
    content[0] = content[0].split("#")[0]
    content[0] = content[0].split("Vegaani")[0]
    return content

#This part was in use in a local workstation before Control Room Assets were taken into use
#In case one needs the info later on, the contents are saved locally to daily files.
#def save_menu_locally(parsed_content):
#    file_system = FileSystem()
#    file_system.touch_file(f"output/{datetime.date.today()}_menu.txt")
#    file_system.append_to_file(f"output/{datetime.date.today()}_menu.txt", parsed_content[0] + "\n")

#Push to X using selectors
#def push_to_x(parsed_content):
#    page = browser.goto("https://twitter.com/i/flow/login")
#    page.fill("//input[@name='text']", USER_NAME)
#    page.click("//div[@id='layers']/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div/div/div[6]/div/span/span")
#    page.fill("//input[@name='password']", PASSWORD)
#    page.click("//div[@id='layers']/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div/div/div/div/div/span/span")
#    page.fill("//div[@id='react-root']/div/div/div[2]/main/div/div/div/div/div/div[3]/div/div[2]/div/div/div/div/div[2]/div/div/div/div/div/div/div/div/div/div/div/label/div/div/div/div/div/div/div[2]/div/div/div/div", parsed_content[0])
#    page.click("//div[@id='react-root']/div/div/div[2]/main/div/div/div/div/div/div[3]/div/div[2]/div/div/div/div/div[2]/div[2]/div[2]/div/div/div/div[3]")

#Push to X using X API
#def push_to_x_tweepy(parsed_content):
#    client.create_tweet(text=parsed_content[0])
    
def manage_assets(parsed_content):
    storage = Storage()
    storage.set_text_asset(f"{datetime.date.today()}_menu.txt", parsed_content[0])

def send_mail(parsed_content):
    mail = ImapSmtp(SMTP_SERVER, SMTP_PORT)
    mail.authorize(account=GMAIL_ACCOUNT, password=GMAIL_APP_PASSWORD)
    mail.send_message(
        sender=GMAIL_ACCOUNT,
        recipients=RECIPIENT,
        subject=f"Päiväkodin ruokalista {datetime.date.today()}",
        body=parsed_content[0]
)