from datetime import date
from operator import is_

from utility.utils import errEmbed, log, openFile, saveFile
class FlowApp:

    def register(self, user_id: int):
        self.transaction(user_id, 20, is_new_account=True)

    def transaction(self, user_id: int, flow_for_user: int, is_morning: bool = False, is_new_account: bool = False):
        users = openFile('flow')
        bank = openFile('bank')
        if is_new_account:
            today = date.today()
            users[user_id] = {'flow': 0, 'morning': today}
        if user_id in users:
            users[user_id]['flow'] += int(flow_for_user)
            bank['flow'] -= int(flow_for_user)
            if is_morning:
                today = date.today()
                users[user_id]['morning'] = today
            saveFile(users, 'flow')
            saveFile(bank, 'bank')
            user_log = '{0:+d}'.format(int(flow_for_user))
            bank_log = '{0:+d}'.format(-int(flow_for_user))
            print(log(True, False, 'Transaction',
                  f'user({user_id}): {user_log}, bank: {bank_log}'))
            sum = 0
            for user, value in users.items():
                sum += value['flow']
            print(log(True, False, 'Current', f"user_total: {sum}, bank: {bank['flow']}"))
            print(log(True, False, 'Total', sum+bank['flow']))
        else:
            print(log(True, True, 'Transaction', f"can't find id {user_id}" ))

    def checkFlowAccount(self, user_id: int):
        users = openFile('flow')
        if user_id not in users:
            self.register(user_id)
            embed = errEmbed('找不到flow帳號!',
                             f'<@{user_id}>\n現在申鶴已經創建了一個, 請重新執行操作')
            return False, embed
        else:
            return True, None

flow_app = FlowApp()