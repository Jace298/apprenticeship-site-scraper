import json
from bs4 import BeautifulSoup
import requests
import regex
from time import sleep
from discord_webhook import DiscordWebhook, DiscordEmbed
from datetime import datetime
from dotenv import load_dotenv
import os
from requests.exceptions import ConnectionError

class ApprenticeScraper:
    def __init__(self):
        load_dotenv()

        self.url = os.environ.get("URL")
        self.discordUrl = os.environ.get("DISCORD_URL")
        self.embedInline = os.environ.get("EMBED_INLINE")
        self.timeToWait = int(os.environ.get("TIME_WAIT"))

        self.HEADER = '\033[95m'
        self.OKBLUE = '\033[94m'
        self.OKCYAN = '\033[96m'
        self.OKGREEN = '\033[92m'
        self.WARNING = '\033[93m'
        self.FAIL = '\033[91m'
        self.ENDC = '\033[0m'
        self.BOLD = '\033[1m'
        self.UNDERLINE = '\033[4m'

        self.loopController()

    def loopController(self):
        while True:
            self.main()
            print(f"{self.OKBLUE}[{self.now()}][INFO]{self.ENDC} Sleeping for {self.timeToWait}m")
            sleep(self.timeToWait * 60)

    def main(self):
        self.r = self.makeRequest(self.url)

        if (self.r.status_code != 200):
            print(f"{self.FAIL}[{self.now()}][INFO]{self.ENDC} An error occured. Status Code: {self.r.status_code}")
            quit()

        print(f"{self.OKBLUE}[{self.now()}][INFO]{self.ENDC} Parsing response")

        self.soup = BeautifulSoup(self.r.text, "lxml")
        self.results = self.soup.find_all("li", class_="search-result sfa-section-bordered")

        apprenticeships = {}
        for res in self.results:
            appTitle = self.formatStr(res.h2.text)
            appCompany = self.formatStr(res.ul.li.text)
            appDatePosted = res.find("span", id=regex.compile("posted-date")).text.replace("(Added ",   "")
            appNumPositions = self.formatStr(res.find("span", id=regex.compile("number-of-positions")).text)
            appDescription = self.formatStr(res.p.text)
            appShortDesc = appDescription[:130]
            appDistance = res.find("span", id="distance-value").text
            appClosingDate = res.find("span", id="closing-date-value").text
            appStartDate = res.find("span", id="start-date-value").text
            appLevel = self.formatStr(res.find("li", attrs={"data-show":"DisplayApprenticeshipLevel"}).text)
            appWage = self.formatStr(res.find("li", attrs={"data-show":"DisplayWage"}).text)
            appURL = f"https://www.findapprenticeship.service.gov.uk/{res.h2.a['href']}"

            subR = self.makeRequest(appURL, True)
            ss = BeautifulSoup(subR.text, "lxml")

            qualsReq = ss.find("div", id="vacancy-qualifications-required").contents
            provider = ss.find("p", id="vacancy-provider-name").text
            compURL = ss.find("a", id="vacancy-employer-website")["href"]
            startDate = ss.find("p", id="vacancy-start-date").text
            fullDesc = self.formatStr(ss.find("div", id="vacancy-full-descrpition").text)

            fullDesc = self.boldStr(fullDesc, "What will the apprentice be doing?")
            fullDesc = self.boldStr(fullDesc, "What training will the apprentice take and what qualification will the apprentice get at the end?")
            fullDesc = self.boldStr(fullDesc, "What is the expected career progression after this apprenticeship?")


            for i in qualsReq:
                if str(i) == "<br/>": qualsReq.remove(i)

            for i in range(len(qualsReq)): qualsReq[i] = self.formatStr(qualsReq[i])
            
            apprenticeships.update({appCompany: {
                "Title": appTitle,
                "Company": appCompany,
                "Date Posted": appDatePosted,
                "Number of Positions": appNumPositions,
                "Description": appDescription,
                "Short Description": appShortDesc,
                "Distance": appDistance,
                "Closing Date": appClosingDate,
                "Start Date": appStartDate,
                "Apprenticeship Level": appLevel,
                "Wage": appWage,
                "URL": appURL,
                "Provider": provider,
                "Company URL": compURL,
                "Start Date": startDate,
                "Qualifications Required": qualsReq,
                "Full Description": fullDesc
                }})

            # print(f"Title: {appTitle}\nCompany: {appCompany}\nDate Posted: {appDatePosted}\nNumber of  Positions: {appNumPositions}\nDistance: {appDistance} miles\nClosing Date: {appClosingDate}  \nPotential Start Date: {appStartDate}\nLevel: {appLevel}\nWage: {appWage}\nDescription   (Short): {appShortDesc}\n")

        updated = self.saveJSON(apprenticeships)
        print(f"{self.OKBLUE}[{self.now()}][INFO]{self.ENDC} Parsing complete, Found {str(len(updated))} new apprenticeships.")

        self.sendWebhook(updated)

    def sendWebhook(self, data):
        for k in data:
            v = data[k]

            webhook = DiscordWebhook(url=self.discordUrl, content=f"<@370886991065382912> New apprenticeship available at {k}")
            embed = DiscordEmbed(title=v["Title"], description=v["Description"], color=0x000000)
            embed.set_timestamp()
            embed.set_author(name="Link to Apprenticeship", url=v["URL"], icon_url="https://cdn.icon-icons.com/icons2/2389/PNG/512/gov_uk_logo_icon_145225.png")
            embed.set_footer(text="National Apprenticeship Site Scraper", icon_url="https://cdn.icon-icons.com/icons2/2389/PNG/512/gov_uk_logo_icon_145225.png")

            embed.add_embed_field(name="Title", value=v["Title"], inline=self.embedInline)
            embed.add_embed_field(name="Company", value=f"[{v['Company']}]({v['Company URL']})", inline=self.embedInline)
            embed.add_embed_field(name="Date Posted", value=v["Date Posted"], inline=self.embedInline)
            embed.add_embed_field(name="Number of Positions", value=v["Number of Positions"], inline=self.embedInline)
            embed.add_embed_field(name="Distance", value=f"{v['Distance']} miles", inline=self.embedInline)
            embed.add_embed_field(name="Closing Date", value=v["Closing Date"], inline=self.embedInline)
            embed.add_embed_field(name="Start Date", value=v["Start Date"], inline=self.embedInline)
            embed.add_embed_field(name="Apprenticeship Level", value=v["Apprenticeship Level"], inline=self.embedInline)
            embed.add_embed_field(name="Provider", value=v["Provider"], inline=self.embedInline)
            embed.add_embed_field(name="Wage", value=v["Wage"], inline=self.embedInline)

            qualsReqStr = ""
            for qual in v["Qualifications Required"]:
                qualsReqStr += f"• {qual}\n"
            embed.add_embed_field(name="Qualifications Required", value=qualsReqStr, inline=self.embedInline)
            
            if ("per week" in v["Wage"]):
                wageInt = int(float(v["Wage"].replace(" per week", "").replace("£", "").replace(",", "")))
                embed.add_embed_field(name="Wage (per year)", value=f"£{wageInt * 52} per year", inline=self.embedInline)

            webhook.add_embed(embed)
            resp = webhook.execute()

            webhook = DiscordWebhook(url=self.discordUrl, content=v["Full Description"])
            resp2 = webhook.execute()

            print(f"{self.OKBLUE}[{self.now()}][INFO]{self.ENDC} Webhooks complete. Codes: {resp.status_code}, {resp2.status_code}")
    
    def sendLogWebhook(self, err):
        webhook = DiscordWebhook(url=self.discordUrl, content=f"<@370886991065382912>Connection error, check logs for more info.")
        embed = DiscordEmbed(title="Connection Error", description="", color=0xFF0000)
        embed.set_timestamp()
        embed.add_embed_field(name="Error", value=f"{err}", inline=self.embedInline)
        print(err)

        webhook.add_embed(embed)
        resp = webhook.execute()
        print(f"{self.OKBLUE}[{self.now()}][INFO]{self.ENDC} Error Logging Webhook completed, code: {resp.status_code}")
            
    def saveJSON(self, data):
        newData = {}
        compData = self.loadJSON()

        for d in data:
            foundMatch = False

            if compData == {}:
                newData.update({d: data[d]})
                continue

            for cd in compData:
                if d == cd:
                    foundMatch = True
                    break
                
            if foundMatch == False:
                newData.update({d: data[d]})

        with open("data.json", "w") as f:
            json.dump(data, f, indent=2)

        return newData

    def loadJSON(self):
        try:
            with open("data.json", "r") as f:
                return json.load(f)
        except:
            return {}

    def formatStr(self, string):
        if "position available" in string:
            string = string.lstrip().rstrip().replace("- ", "").replace(")", "").replace("position    available", "").replace("s", "")
            return string[:4] + "s" + string[4:]
        elif "positions available" in string:
            return string.lstrip().rstrip().replace("- ", "").replace(")", "").replace("position    available", "")
        elif "Apprenticeship level: " in string:
            return string.lstrip().rstrip().replace("Apprenticeship level: ", "")
        elif "Wage: " in string:
            return string.lstrip().rstrip().replace("Wage: ", "")
        elif "•" in string:
            return string.lstrip().rstrip().replace("•", "\n•")

        return string.lstrip().rstrip()

    def now(self):
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    def makeRequest(self, url, secondary = False):
        print(f"{self.OKBLUE}[{self.now()}][INFO]{self.ENDC} Making web request") if not secondary else print(f"{self.OKBLUE}[{self.now()}][INFO]{self.ENDC} Making secondary web request")
        try:
            r = requests.get(url)
        except ConnectionError as err:
            print(f"{self.FAIL}[{self.now()}][ERROR]{self.ENDC} Connection error (Rate Limited)")
            self.sendLogWebhook(err)
            return
        print(f"{self.OKBLUE}[{self.now()}][INFO]{self.ENDC} Web request completed") if not secondary else print(f"{self.OKBLUE}[{self.now()}][INFO]{self.ENDC} Secondary web request completed")
        secondary = False
        return r

    def boldStr(self, str, subStr):
        startPos = str.index(subStr)
        endPos = startPos + len(subStr) + 3

        if startPos != 0:
            str = str[:startPos] + "\n**" + str[startPos:]
        else: 
            str = str[:startPos] + "**" + str[startPos:]

        return str[:endPos] + "**\n" + str[endPos:]

if __name__ == "__main__":
    ApprenticeScraper()
