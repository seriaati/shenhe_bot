from datetime import datetime

from utility.utils import errEmbed, log, openFile, saveFile
class FlowApp:

    def register(self, user_id: int):
        self.transaction(user_id, 20, is_new_account=True)

    def transaction(self, user_id: int, flow_for_user: int, time_state:str = None, is_new_account: bool = False, is_removing_account: bool = False):
        users = openFile('flow')
        bank = openFile('bank')
        trans_log = openFile('transaction_log')
        now = datetime.now()
        if is_removing_account:
            print(log(True, False, 'Removing Acc',user_id))
            bank['flow']+=flow_for_user
            del users[user_id]
            saveFile(users, 'flow')
            saveFile(bank, 'bank')
            return
        if is_new_account:
            users[user_id] = {'flow': 0}
            users[user_id]['morning'] = datetime(year=now.year, month=now.month, day=now.day-1, hour=now.hour, minute=now.minute, second=now.second, microsecond=now.microsecond)
            users[user_id]['noon'] = datetime(year=now.year, month=now.month, day=now.day-1, hour=now.hour, minute=now.minute, second=now.second, microsecond=now.microsecond)
            users[user_id]['night'] = datetime(year=now.year, month=now.month, day=now.day-1, hour=now.hour, minute=now.minute, second=now.second, microsecond=now.microsecond)
            saveFile(users, 'flow')
        if user_id in users:
            users[user_id]['flow'] += int(flow_for_user)
            bank['flow'] -= int(flow_for_user)
            if time_state is not None:
                if time_state == 'morning':
                    users[user_id]['morning'] = now
                elif time_state == 'noon':
                    users[user_id]['noon'] = now
                elif time_state == 'night':
                    users[user_id]['night'] = now
            saveFile(users, 'flow')
            saveFile(bank, 'bank')
            user_log = '{0:+d}'.format(int(flow_for_user))
            bank_log = '{0:+d}'.format(-int(flow_for_user))
            trans_log[user_id] = datetime.now()
            saveFile(trans_log, 'transaction_log')
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
            embed = errEmbed(
                '找不到flow帳號!',
                f'<@{user_id}>\n現在申鶴已經創建了一個, 請重新執行操作')
            return False, embed
        else:
            return True, None

flow_app = FlowApp()