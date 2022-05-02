from datetime import date
import yaml

from utility.utils import errEmbed, log
class FlowApp:

    def register(self, user_id: int):
        users = self.openFile('flow')
        today = date.today()
        users[user_id] = {'flow': 0, 'morning': today}
        self.transaction(user_id, 20)
        self.saveData(users, 'flow')

    def transaction(self, user_id: int, flow_for_user: int):
        users = self.openFile('flow')
        bank = self.openFile('bank')
        if user_id in users:
            users[user_id]['flow'] += flow_for_user
            bank['flow'] -= flow_for_user
            if flow_for_user > 0:
                flow_for_user = f'+{flow_for_user}'
            if -int(flow_for_user) > 0:
                bank_add = f'+{-int(flow_for_user)}'
            else:
                bank_add = -int(flow_for_user)
            print(log(True, False, 'Transaction',
                  f'user({user_id}): {str(flow_for_user)}, bank: {bank_add}'))
            sum = 0
            for user, value in users.items():
                sum += value['flow']
            print(log(True, False, 'Current', f"user_total: {sum}, bank: {bank['flow']}"))
            print(log(True, False, 'Total', sum+bank['flow']))
        self.saveData(users, 'flow')
        self.saveData(bank, 'bank')

    def checkFlowAccount(self, user_id: int):
        users = self.openFile('flow')
        if user_id not in users:
            self.register(user_id)
            embed = errEmbed('找不到flow帳號!',
                             f'<@{user_id}>\n現在申鶴已經創建了一個, 請重新執行操作')
            return False, embed
        else:
            return True, None

    def openFile(self, file_name:str):
        with open(f'data/{file_name}.yaml', 'r', encoding="utf-8") as f:
            return yaml.full_load(f)

    def saveData(self, data: dict, file_name: str):
        with open(f'data/{file_name}.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(data, f)

flow_app = FlowApp()