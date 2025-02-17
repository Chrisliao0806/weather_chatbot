import datetime
import json
import os

import requests
from dotenv import load_dotenv
from langchain_community.agent_toolkits import JsonToolkit, create_json_agent
from langchain_community.tools.json.tool import JsonSpec
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

load_dotenv()

TEMPLATE_FINAL = """你是一個天氣機器人，請根據提供的陣列資料回答使用者問題，今天的日期是{{date}}，請依據今天的日期回覆使用者其他日期或是相對時間的資訊。
        接下來，以下我們目前從中央氣象局收到的json資料:
        
        {{weather_data}}
        
        基本上所有的天氣資訊都會在'WeatherElement'裡面
        
        ['records']['Locations'][0]['Location'][0]['WeatherElement'][0]['Time']是一個陣列，會有非常多筆時間的資訊，如果在查詢多天資料的時候，請切記一定要將這個陣列的資料全部列出來，不然會有問題。
        如：詢問一個禮拜的資料的話，我們就需要搜集['records']['Locations'][0]['Location'][0]['WeatherElement'][0]['Time'][0], ['records']['Locations'][0]['Location'][0]['WeatherElement'][0]['Time'][1], ['records']['Locations'][0]['Location'][0]['WeatherElement'][0]['Time'][2]...等等，直到把所有的資料都列出來。

        
        最後回覆請以中文回覆。
""".replace("{{date}}", datetime.datetime.now().strftime("%Y-%m-%d"))

TEMPLATE = """你是一個將客戶問題轉換成json格式的機器人。今天客戶的目標是要去詢問台北的天氣資訊，我們的目標是要將客戶的問題轉換成json格式的資料，然後再回答客戶的問題。

一個json的格式如下:
```json
{{"Authorization": 'env',
  "format": "JSON",
  "LocationName":"北投區",
  "ElementName": "天氣預報綜合描述"
}}
```

注意內容：
1. "Authorization" 是一個字串，代表授權碼(填上'env'即可)。"format" 是一個字串，代表格式。這兩個都不要有任何變動。
2. "LocationName" 是一個字串，代表台北某一地區的名稱（不能填寫台北）。"LocationName"一定要是台北市的其中一個區域，台北總共有12個區，如果使用者有說到台北市什麼區的話，要確定區域名稱是否為台北市的再填入，如果使用者說的有問題或是使用者沒特別說明的話，則不用填寫這個欄位，直接拔掉"LocationName"。
3. "ElementName" 是一個字串，裡面包含了天氣資料的名稱，例如"最高溫度"、"最低溫度"、"天氣狀況"等等，這個欄位一定要填寫，因為這是客戶問題的重點。
4. 天氣資料陣列內容有: [ "最高溫度", "天氣預報綜合描述", "平均相對濕度", "最高體感溫度", "12小時降雨機率", "風向", "平均露點溫度", "最低體感溫度", "平均溫度", "最大舒適度指數", "最小舒適度指數", "風速", "紫外線指數", "天氣現象", "最低溫度" ]，我們要根據使用者提供的資訊，找出最相近的資訊，然後填寫進去。
5. 只有"LocationName"是選填的，其他都是必填的。

最後，請將結果以**純 JSON** 回傳，不要添加多餘解釋或文字。
"""


class WeatherChatBot:
    """
    互動式天氣預測機器人，利用先前儲存的 JSON 天氣資料與 LLM 來回覆使用者的天氣問題。
    """

    def __init__(self, verbose=False):
        """
        初始化機器人，建立 LLM 與 JSON Agent。

        參數:
            json_file_path (str): 天氣資料 JSON 檔案的路徑，預設為 "weather.json"。
            verbose (bool): 是否在 Agent 執行時顯示詳細資訊。
        """
        self.verbose = verbose
        self.url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-063"
        self.llm = ChatOpenAI(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
        self.json_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", TEMPLATE),
                MessagesPlaceholder("history"),
                ("human", "{question}"),
            ]
        )
        self.final_prompt = None

    def prompt_template_add(self, template):
        """
        Helper function to add a new prompt template to the final prompt.
        """
        self.final_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", template),
                MessagesPlaceholder("history"),
                ("human", "{question}"),
            ]
        )

    def _json_format(self, llm_code_output):
        """
        Helper function to clean up triple-backtick formatting if GPT returns them,
        ensuring we only store valid JSON.
        """
        change_line = False
        lines = llm_code_output.strip().splitlines()
        if lines and lines[0].strip().startswith("```"):
            change_line = True
            lines = lines[1:]
        if lines and lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        clean_json = "\n".join(lines)
        if change_line:
            llm_code_output = clean_json
        return llm_code_output

    def fetch_data(self, params: dict = None) -> dict:
        """
        Fetches data from the specified URL with the given parameters.

        Makes a GET request to the URL stored in the instance variable `self.url`
        with the parameters stored in `self.params`.
        If the request is successful (status code 200), it returns the response data in JSON format.
        If the request fails, it returns None.

        Returns:
            dict or None: The response data in JSON format if the request is successful,
            otherwise None.
        """
        response = requests.get(self.url, params=params, timeout=10)
        print(response.url)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return None

    def init_json_toolkit(self, json_output: dict):
        """
        初始化 JSON Toolkit。
        """
        self.json_spec = JsonSpec(dict_=json_output)
        self.json_toolkit = JsonToolkit(spec=self.json_spec)
        self.agent = create_json_agent(
            llm=self.llm,
            toolkit=self.json_toolkit,
            verbose=self.verbose,
        )

    def ask_question(self, question: str, chat_history: list) -> str:
        """
        接收使用者的天氣問題，並利用 JSON Agent 回覆答案。

        參數:
            question (str): 使用者的天氣問題，例如「明天台北的天氣如何？」。

        回傳:
            str: 機器人根據 JSON 資料所生成的回答。
        """
        chain_to_json = self.json_prompt | self.llm
        params = chain_to_json.invoke({"history": chat_history, "question": question})
        params = self._json_format(params.content)
        print(params)
        params = json.loads(params)
        params["Authorization"] = os.getenv("WEB_KEY")
        weather_data = self.fetch_data(params)
        escaped_weather_data = str(weather_data).replace("{", "{{").replace("}", "}}")
        self.prompt_template_add(
            TEMPLATE_FINAL.replace("{{weather_data}}", escaped_weather_data)
        )

        # self.init_json_toolkit(weather_data["records"]["Locations"][0]["Location"][0])
        chain = self.final_prompt | self.llm
        answer = chain.invoke({"history": chat_history, "question": question})
        return answer


if __name__ == "__main__":
    # 建立 WeatherChatBot 實例
    chatbot = WeatherChatBot(verbose=False)
    chat_history = []

    # 使用者輸入問題
    user_question = "明天台北的天氣如何？"
    print("使用者問題:", user_question)

    # 取得回覆
    response = chatbot.ask_question(user_question, chat_history)
    print("機器人回覆:", response.content)

    for _ in range(10):
        chat_history.extend([HumanMessage(content=user_question), response.content])
        user_question = input("使用者問題:")
        response = chatbot.ask_question(user_question, chat_history)
        print("機器人回覆:", response.content)
