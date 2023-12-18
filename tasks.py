from robocorp.tasks import task
from robocorp import browser

from RPA.HTTP import HTTP
from RPA.FileSystem import FileSystem
from RPA.Robocorp.Vault import Vault
import datetime

_secret = Vault().get_secret("credentials")
USER_NAME = _secret["username"]
PASSWORD = _secret["password"]

file_system = FileSystem()
http = HTTP()

@task
def fetch_and_push_menu():
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
    save_menu_locally(parsed_content)
    push_to_x(parsed_content)

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

#In case I need the info later on, the contents are saved locally to daily files.
def save_menu_locally(parsed_content):
    file_system.touch_file(f"output/{datetime.date.today()}_menu.txt")
    file_system.append_to_file(f"output/{datetime.date.today()}_menu.txt", parsed_content[0] + "\n")

#Push to X
def push_to_x(parsed_content):
    page = browser.goto("https://twitter.com/i/flow/login")
    page.fill("//input[@name='text']", USER_NAME)
    page.click("//div[@id='layers']/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div/div/div[6]/div/span/span")
    page.fill("//input[@name='password']", PASSWORD)
    page.click("//div[@id='layers']/div/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div/div/div/div/div/span/span")
    page.fill("//div[@id='react-root']/div/div/div[2]/main/div/div/div/div/div/div[3]/div/div[2]/div/div/div/div/div[2]/div/div/div/div/div/div/div/div/div/div/div/label/div/div/div/div/div/div/div[2]/div/div/div/div", parsed_content[0])
    page.click("//div[@id='react-root']/div/div/div[2]/main/div/div/div/div/div/div[3]/div/div[2]/div/div/div/div/div[2]/div[2]/div[2]/div/div/div/div[3]")